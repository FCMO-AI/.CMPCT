#!/usr/bin/env python3
"""J24G39: genuine installed CMPCT compaction publish-leaf adversarial court.

RESEARCH NEGATIVE: a verified file descriptor is not a guarantee that an
fd-relative rename publishes the same inode. All attack paths are created
inside one disposable TemporaryDirectory and the test grants the actor the
same UID as the compactor. The hook controls only the final publication instant.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import shutil
import sys
import tempfile
from unittest.mock import patch

from cmpct.builder import Builder
from cmpct.reader import CMPCT
import cmpct.transactions as tx


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot(path: Path) -> dict:
    with CMPCT(path) as ar:
        ar.verify()
        return {
            "rows": [(r[0], r[1], r[2], r[3], r[4]) for r in ar.files],
            "logical": {
                r[0]: ar.file_sha256(r[0]).hex()
                for r in ar.files if r[1] != 1
            },
        }


def main() -> None:
    if os.name != "posix" or not hasattr(os, "O_DIRECTORY"):
        raise RuntimeError("J24G39 is POSIX-only research; no Windows credit")
    results = []
    with tempfile.TemporaryDirectory(prefix="j24g39-physical-publication-") as tmp:
        root = Path(tmp)
        tree = root / "tree"
        tree.mkdir()
        data = (bytes(range(256)) * 64) + b"\0PHYSICAL-OWNER"
        (tree / "owner.bin").write_bytes(data)
        os.link(tree / "owner.bin", tree / "alias.bin")
        source = root / "original.cmpct"
        Builder(tree, workers=1, reproducible=True).build(source)
        source_sha = sha(source)
        expected = snapshot(source)

        target_dir = root / "dest"
        target_dir.mkdir()
        control = target_dir / "control.cmpct"
        tx.compact_archive(source, control)
        assert control.is_file() and not control.is_symlink()
        assert snapshot(control) == expected
        assert sha(source) == source_sha
        control_sha = sha(control)
        artifacts = os.environ.get("CMPCT_J24G39_ARTIFACTS")
        artifact_dir = Path(artifacts) if artifacts else None
        if artifact_dir is not None:
            artifact_dir.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, artifact_dir / "source.cmpct")
            shutil.copyfile(control, artifact_dir / "control.cmpct")

        outside = root / "outside-sentinel.bin"
        outside.write_bytes(b"FOREIGN-SENTINEL-DO-NOT-TOUCH")
        outside_sha = sha(outside)
        marker = b"J24G39-UNVERIFIED-REGULAR-REPLACEMENT"
        original_replace = os.replace

        for kind in ("symlink", "regular"):
            target = target_dir / (kind + ".cmpct")
            target.write_bytes(b"EXISTING-DESTINATION")
            observed = []
            saved_inode = None

            def interpose(src, dst, *args, **kwargs):
                nonlocal saved_inode
                if (
                    src == "payload.cmpct"
                    and dst == target.name
                    and kwargs.get("src_dir_fd") is not None
                    and kwargs.get("dst_dir_fd") is not None
                ):
                    assert not observed, "publication hook may fire exactly once"
                    candidates = [
                        p for p in target_dir.iterdir()
                        if p.name.startswith("." + target.name + ".compact-private-")
                        and p.is_dir() and not p.is_symlink()
                    ]
                    assert len(candidates) == 1, "must target actual private staging directory"
                    stage = candidates[0]
                    payload = stage / "payload.cmpct"
                    assert payload.is_file() and not payload.is_symlink()
                    assert snapshot(payload) == expected, "candidate did not verify authentic archive"
                    verified_sha = sha(payload)
                    saved_inode = stage / "already-verified.cmpct"
                    # A separate same-UID process does the namespace mutation.
                    # The owner process only schedules it at the real rename boundary.
                    actor_code = """import os,sys
from pathlib import Path
src,dst,kind,sentinel=sys.argv[1:]
os.replace(src,dst)
if kind=='symlink':os.symlink(sentinel,src)
else:Path(src).write_bytes(b'J24G39-UNVERIFIED-REGULAR-REPLACEMENT')
"""
                    actor = subprocess.run(
                        [sys.executable, "-c", actor_code, str(payload),
                         str(saved_inode), kind, str(outside)],
                        check=True, capture_output=True, text=True,
                    )
                    assert actor.returncode == 0
                    observed.append({
                        "verified_sha": verified_sha,
                        "planted_kind": kind,
                        "stage": stage.name,
                        "verified_inode_saved": saved_inode.name,
                    })
                return original_replace(src, dst, *args, **kwargs)

            error = None
            with patch.object(tx.os, "replace", interpose):
                try:
                    tx.compact_archive(source, target)
                except OSError as exc:
                    error = f"{type(exc).__name__}:{exc.errno}:{exc.strerror}"

            assert len(observed) == 1, f"{kind}: did not intercept real publication"
            assert saved_inode is not None and saved_inode.is_file()
            assert not saved_inode.is_symlink()
            assert sha(saved_inode) == observed[0]["verified_sha"]
            assert snapshot(saved_inode) == expected, f"{kind}: verified inode changed"
            assert sha(source) == source_sha
            assert sha(outside) == outside_sha
            if kind == "symlink":
                bad = target.is_symlink() and os.readlink(target) == str(outside)
            else:
                bad = target.is_file() and not target.is_symlink() and target.read_bytes() == marker
            if artifact_dir is not None:
                shutil.copyfile(saved_inode, artifact_dir / f"verified-{kind}.cmpct")
                if kind == "regular":
                    shutil.copyfile(target, artifact_dir / "published-regular.bin")
                else:
                    (artifact_dir / "published-symlink.target").write_text(
                        os.readlink(target), encoding="utf-8"
                    )
            results.append({
                "case": kind,
                "publication_intercepted": True,
                "operation_error": error,
                "published_unverified_entry": bad,
                "destination_is_symlink": target.is_symlink(),
                "destination_bytes_sha256": sha(target) if target.exists() else None,
                "verified_inode_still_valid": snapshot(saved_inode) == expected,
                "source_unchanged": sha(source) == source_sha,
                "outside_sentinel_unchanged": sha(outside) == outside_sha,
                "verified_archive_sha256": observed[0]["verified_sha"],
                "stage_name": observed[0]["stage"],
            })

        if artifact_dir is not None:
            shutil.copyfile(outside, artifact_dir / "outside-sentinel.bin")
        negative = all(r["published_unverified_entry"] and r["operation_error"] is None for r in results)
    output = {
        "schema": "J24G39-real-r24-stage-leaf-publication-v1",
        "host": platform.platform(),
        "evidence_class": "UNRELEASED_CANDIDATE_NEGATIVE_RESEARCH",
        "parent_candidate": "3e6b1c75a303ba638d420e49b658b90c7b573773",
        "source_sha256": source_sha,
        "control_compacted_sha256": control_sha,
        "control_logical_identity_exact": True,
        "decision": (
            "MUTABLE_STAGE_LEAF_PUBLISHES_UNVERIFIED_INODE"
            if negative else "HYPOTHESIS_NOT_REPRODUCED"
        ),
        "results": results,
        "unmeasured": [
            "cross-UID attack feasibility",
            "actual adversary scheduling probability",
            "secure Windows HANDLE publication",
            "whole-product timing/RSS/temp I/O",
            "power-failure crash consistency",
        ],
    }
    print(json.dumps(output, indent=2, sort_keys=True))
    assert negative, "falsifier did not reproduce predicted negative; preserve actual observations"


if __name__ == "__main__":
    main()
