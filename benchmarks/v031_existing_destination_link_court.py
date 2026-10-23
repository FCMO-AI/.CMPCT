"""Frozen exact-source r24 pre-existing destination symlink extraction court.

Research witness only. All filesystem writes are confined to TemporaryDirectory.
A PASS means the predicted boundary violation was REPRODUCED, not repaired.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import tempfile

from cmpct.builder import Builder
from cmpct.reader import CMPCT
from cmpct.codec import K_FILE, K_SYMLINK, S_BLOB


def digest(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def check_case(case: str) -> dict:
    payload = b"EXACT_CMPCT_DESTINATION_BOUNDARY_PAYLOAD:" + case.encode()
    sentinel = b"ORIGINAL_OUTSIDE_SENTINEL:" + case.encode()
    with tempfile.TemporaryDirectory(prefix="cmpct-existing-link-court-") as tmp:
        work = Path(tmp)
        source = work / "source"
        source.mkdir()
        rel = "nested/member.bin" if case == "ancestor" else "member.bin"
        member = source / rel
        member.parent.mkdir(parents=True, exist_ok=True)
        member.write_bytes(payload)

        archive = work / "source.cmpct"
        Builder(source, workers=1, reproducible=True).build(archive)
        with CMPCT(archive) as reader:
            assert all(row[1] != K_SYMLINK for row in reader.files)
            assert reader.by[rel][1] == K_FILE
            assert reader.by[rel][6][0] == S_BLOB, reader.by[rel][6]
            assert reader.read(rel) == payload
            assert reader.verify() >= 1
            outside = work / "outside"
            outside.mkdir()
            victim = outside / "member.bin"
            victim.write_bytes(sentinel)
            dest = work / "destination"
            dest.mkdir()

            if case == "ancestor":
                (dest / "nested").symlink_to(outside, target_is_directory=True)
            elif case == "leaf":
                (dest / "member.bin").symlink_to(victim)
            elif case != "clean":
                raise ValueError(case)

            assert victim.read_bytes() == sentinel
            assert not any(p == ".." for p in Path(rel).parts)
            status = "RETURNED"
            try:
                reader.extractall(dest, safe_symlinks=True)
            except Exception as exc:
                status = "RAISED:" + type(exc).__name__
            victim_bytes = victim.read_bytes()
            extracted = dest / rel
            observed_outside_change = victim_bytes == payload
            observed_clean = case == "clean" and extracted.is_file() and extracted.read_bytes() == payload
            if case in ("ancestor", "leaf"):
                assert status == "RETURNED", (case, status)
                assert observed_outside_change, (case, digest(victim_bytes))
            else:
                assert status == "RETURNED", status
                assert observed_clean
                assert victim_bytes == sentinel
            return dict(
                case=case,
                archive_sha256=digest(archive.read_bytes()),
                source_sha256=digest(payload),
                original_victim_sha256=digest(sentinel),
                post_victim_sha256=digest(victim_bytes),
                archive_has_symlink=False,
                member_storage="S_BLOB",
                safe_symlinks=True,
                extraction_status=status,
                outside_changed_to_source=observed_outside_change,
                clean_control_pass=observed_clean,
            )


def main():
    if not hasattr(os, "symlink"):
        raise RuntimeError("POSIX os.symlink required")
    cases = [check_case(x) for x in ("clean", "ancestor", "leaf")]
    assert [x["outside_changed_to_source"] for x in cases] == [False, True, True]
    print(json.dumps(dict(
        schema="cmpct-existing-destination-link-v1",
        source_branch="agent/v031-development",
        source_sha="4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b",
        hypothesis="PREEXISTING_DESTINATION_LINK_ESCAPES_ARCHIVE_ONLY_SYMLINK_CHECK",
        result="BASELINE_BOUNDARY_REPRODUCED_NOT_FIXED",
        cases=cases,
        limits="TemporaryDirectory static symlinks only; no concurrent races, native/platform, "
               "CDC/sparse/hardlink, or remote exploit claim.",
    ), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
