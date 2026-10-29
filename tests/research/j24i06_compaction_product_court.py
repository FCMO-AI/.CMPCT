"""J24I06 installed-source compaction semantics: exact metadata and private link custody.

A research/product-candidate court, not general release authorization. The tests use
genuine Builder output and keep source, destination and external sentinel checks separate.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path

from cmpct.builder import Builder
from cmpct.codec import BHDR, K_FILE, K_HARDLINK, K_SYMLINK, S_BLOB
from cmpct.reader import CMPCT
from cmpct.transactions import (
    _compaction_source_metadata,
    _private_compaction_guard,
    compact_archive,
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot(path: Path):
    with CMPCT(path) as archive:
        return {
            "rows": [(row[0], row[1], row[2], row[3], row[4], row[6][0] if row[1] == K_HARDLINK else None)
                     for row in archive.files],
            "metadata": _compaction_source_metadata(archive),
            "digests": {row[0]: archive.file_sha256(row[0]).hex()
                        for row in archive.files if row[1] != 1},
            "verified": archive.verify(),
        }


def run() -> dict:
    cases = []
    with tempfile.TemporaryDirectory(prefix="j24i06-court-") as scratch:
        work = Path(scratch)
        external = work / "external"
        external.mkdir()
        sentinel = external / "sentinel"
        sentinel.write_bytes(b"J24I06 NEVER MUTATE OUTSIDE SCRATCH\n")
        sentinel_hash = digest(sentinel)
        for name in ("plain", "safe-relative", "absolute", "parent-relative", "hardlink", "sparse"):
            root = work / (name + "-root")
            root.mkdir()
            payload = b"J24I06 exact owner bytes\n" * 5
            (root / "b-owner.bin").write_bytes(payload)
            target = None
            if name == "safe-relative":
                target = "b-owner.bin"
            elif name == "absolute":
                target = str(sentinel.resolve())
            elif name == "parent-relative":
                target = "../external/sentinel"
            if target is not None:
                (root / "link").symlink_to(target)
            if name == "hardlink":
                os.link(root / "b-owner.bin", root / "z-hard.bin")
            if name == "sparse":
                with open(root / "z-sparse.bin", "wb") as f:
                    f.write(b"START"); f.seek(1024 * 1024); f.write(b"END")
            if hasattr(os, "setxattr"):
                try: os.setxattr(root / "b-owner.bin", "user.cmpct-j24i06", b"archived attribute")
                except OSError: pass

            source = work / (name + ".cmpct")
            output = work / (name + ".compacted.cmpct")
            Builder(root, reproducible=True, workers=1).build(source)
            original = snapshot(source)
            source_sha = digest(source)
            if target is not None:
                with CMPCT(source) as reader:
                    assert reader.read("link") == os.fsencode(target)
                    if name in ("absolute", "parent-relative"):
                        blocked = work / (name + "-unsafe-dest")
                        try:
                            reader.extractall(blocked)
                        except OSError as ex:
                            assert "unsafe symlink target" in str(ex), repr(ex)
                        else:
                            raise AssertionError("ordinary safe_symlinks=True failed to reject")
            output.write_bytes(b"J24I06 EXISTING DESTINATION MUST ONLY CHANGE ON SUCCESS")
            compact_archive(source, output)
            result = snapshot(output)
            assert original == result, (name, original, result)
            assert digest(source) == source_sha, "compaction altered source"
            assert digest(sentinel) == sentinel_hash, "archive target escaped staging"
            assert all(tuple(v[3:5]) == (0, 0) for v in result["metadata"].values()), (name, result["metadata"])
            if target is not None:
                with CMPCT(output) as reader:
                    assert reader.read("link") == os.fsencode(target)
            if os.environ.get("CMPCT_J24I06_ARCHIVE_DIR"):
                out = Path(os.environ["CMPCT_J24I06_ARCHIVE_DIR"])
                out.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, out / (name + "-source.cmpct"))
                shutil.copyfile(output, out / (name + "-compacted.cmpct"))
            cases.append({
                "case": name,
                "source_bytes": source.stat().st_size,
                "output_bytes": output.stat().st_size,
                "source_sha256": source_sha,
                "output_sha256": digest(output),
                "entries": len(result["rows"]),
                "verified": result["verified"],
                "metadata_exact": True,
                "sentinel_unchanged": True,
            })

        # Archive-controlled parents may never traverse an inert literal symlink.
        bad_parent = [
            ["pivot", K_SYMLINK, 0o777, 0, 3, None, [S_BLOB, 0]],
            ["pivot/child", K_FILE, 0o644, 0, 3, None, [S_BLOB, 1]],
        ]
        bad_owner = [
            ["link", K_SYMLINK, 0o777, 0, 3, None, [S_BLOB, 0]],
            ["hard", K_HARDLINK, 0o644, 0, 3, None, ["link"]],
        ]
        guards = []
        for name, rows in (("symlink-parent", bad_parent), ("hardlink-to-symlink", bad_owner)):
            try:
                _private_compaction_guard(rows)
            except OSError as ex:
                guards.append({"name": name, "rejected": str(ex)})
            else:
                raise AssertionError("private compaction accepted hostile " + name)

        # Stage-and-publish must not touch an existing target if source payload
        # corruption makes full source verification or extraction fail.
        source = work / "plain.cmpct"
        damaged = work / "damaged.cmpct"
        bad = bytearray(source.read_bytes())
        with CMPCT(source) as ar:
            off, _, _, _, ml = ar.blobs[0]
            physical = ar.record_base + off + BHDR.size + ml
        bad[physical] ^= 0x40
        damaged.write_bytes(bad)
        destination = work / "protected-destination.cmpct"
        destination.write_bytes(b"do not overwrite on failed compact\n")
        existing_sha = digest(destination)
        try:
            compact_archive(damaged, destination)
        except (OSError, ValueError, RuntimeError) as ex:
            failure = type(ex).__name__ + ": " + str(ex)
        else:
            raise AssertionError("corrupt source was compacted")
        assert digest(destination) == existing_sha
        assert digest(sentinel) == sentinel_hash

    return {
        "schema": "j24i06-compaction-candidate-court-v1",
        "cases": cases,
        "guards": guards,
        "corrupt_source_failure": failure,
        "decision": "CANDIDATE_NARROW_EXACTNESS_PASS_NOT_RELEASE",
    }


if __name__ == "__main__":
    report = run()
    encoded = json.dumps(report, sort_keys=True, indent=2) + "\n"
    if os.environ.get("CMPCT_J24I06_RECEIPT"):
        Path(os.environ["CMPCT_J24I06_RECEIPT"]).write_text(encoded)
    print(encoded)
