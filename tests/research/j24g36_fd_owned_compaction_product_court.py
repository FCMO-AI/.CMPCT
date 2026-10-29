#!/usr/bin/env python3
"""J24G36 product-candidate source-FD stage custody court.

This imports and executes the installed CMPCT package, not an OS-only model.
The deterministic actor has write access to the selected destination parent.
No paths escape TemporaryDirectory; no release/security certification is made.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import tempfile
from unittest.mock import patch

from cmpct.builder import Builder
from cmpct.reader import CMPCT
import cmpct.transactions as t


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def effective(path: Path) -> dict:
    with CMPCT(path) as ar:
        return {
            "rows": [(r[0],r[1],r[2],r[3],r[4]) for r in ar.files],
            "digests": {
                r[0]:ar.file_sha256(r[0]).hex()
                for r in ar.files if r[1] != 1
            },
            "verified": ar.verify(),
        }


def main() -> int:
    if os.name != "posix":
        raise RuntimeError("POSIX-only prototype; do not record Windows success")
    results = []
    with tempfile.TemporaryDirectory(prefix="j24g36-") as rootname:
        root = Path(rootname)
        tree = root / "tree"
        tree.mkdir()
        payload = bytes(range(256)) * 32
        owner = tree / "owner.bin"
        owner.write_bytes(payload)
        os.link(owner, tree / "alias.bin")
        with (tree / "sparse.bin").open("wb") as f:
            f.write(b"START")
            f.seek(2 * 1024 * 1024)
            f.write(b"END")
        source = root / "input.cmpct"
        Builder(tree, workers=1, reproducible=True).build(source)
        source_sha = digest(source)
        expected = effective(source)
        destdir = root / "dest"
        destdir.mkdir()
        normal = destdir / "normal.cmpct"
        t.compact_archive(source, normal)
        assert effective(normal) == expected
        assert digest(source) == source_sha
        results.append({
            "case": "no-rebind", "source_sha": source_sha,
            "output_sha": digest(normal), "output_bytes": normal.stat().st_size,
            "regular_destination": normal.is_file() and not normal.is_symlink()
        })

        outside = root / "attacker-outside"
        outside.mkdir()
        sentinel = outside / "payload.cmpct"
        sentinel.write_bytes(b"OUTSIDE MUST REMAIN INTACT")
        sentinel_sha = digest(sentinel)
        destination = destdir / "victim.cmpct"
        destination.write_bytes(b"EXISTING TARGET")
        interventions = []
        real_build = t.Builder.build

        def rebind_parent_before_writing(self, out, *, _out_fd=None):
            assert _out_fd is not None, "candidate Builder must own source fd"
            stage = Path(out).parent
            assert stage.parent == destdir
            assert stage.is_dir() and not stage.is_symlink()
            moved = destdir / (stage.name + "-moved")
            stage.rename(moved)
            stage.symlink_to(outside, target_is_directory=True)
            interventions.append({
                "stage_name": stage.name,
                "old_dir_rebound_symlink": stage.is_symlink(),
                "old_dir_moved": moved.is_dir(),
            })
            return real_build(self, out, _out_fd=_out_fd)

        with patch.object(t.Builder, "build", rebind_parent_before_writing):
            t.compact_archive(source, destination)
        assert len(interventions) == 1
        assert digest(sentinel) == sentinel_sha, "candidate stage wrote outside"
        assert destination.is_file() and not destination.is_symlink()
        assert effective(destination) == expected
        assert digest(source) == source_sha
        results.append({
            "case": "ancestor-stage-directory-rebound",
            "interventions": interventions,
            "outside_sentinel_unchanged": digest(sentinel) == sentinel_sha,
            "destination_is_regular": destination.is_file() and not destination.is_symlink(),
            "source_sha_unchanged": digest(source) == source_sha,
            "logical_identity_exact": effective(destination) == expected,
            "output_bytes": destination.stat().st_size,
            "output_sha": digest(destination),
        })
        # Clean up adversary-created names only after all observations are taken.
        for p in destdir.iterdir():
            if p.is_symlink():p.unlink()
            elif p.is_dir():shutil.rmtree(p)
        assert not any(x.is_symlink() for x in destdir.iterdir())
    assert all(result.get("case") for result in results)
    print(json.dumps({
        "schema": "J24G36-cmpct-posix-stage-custody-v1",
        "decision": "FD_CUSTODY_SURVIVES_DETERMINISTIC_PARENT_REBIND",
        "evidence_class": "PRODUCT_CANDIDATE_NOT_RELEASE",
        "host": platform.platform(),
        "results": results,
        "unmeasured": [
            "Windows HANDLE equivalent", "same-UID in-private-stage adversary",
            "rename between stage mkdir and stage-dirfd open",
            "full product benchmark", "power-loss durability"
        ]
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
