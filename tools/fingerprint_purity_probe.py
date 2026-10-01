#!/usr/bin/env python3
"""Emit a stage-tagged v0.30 release-fingerprint purity ledger.

This is diagnostic evidence only. It does not alter the strict release lock.
Run it on the same exact Git head immediately after checkout, after setup/install,
and after a benchmark. Diff the JSON ledgers to identify the first live workspace
path that changes the content fingerprint.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

from tools import check_v030_release_lock as lock


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=lock.ROOT, text=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    manifest = lock.load_manifest()
    fingerprint, rels = lock.fingerprint(manifest)
    tracked = {row for row in _git("ls-files", "-z").split("\0") if row}
    status = _git("status", "--porcelain=v1", "--untracked-files=all").splitlines()

    ledger = []
    for rel in rels:
        path = lock.ROOT / rel
        ledger.append(
            {
                "path": rel,
                "bytes": path.stat().st_size,
                "sha256": _sha256(path),
                "tracked": rel in tracked,
            }
        )

    payload = {
        "schema": "cmpct-v030-fingerprint-purity-ledger-v1",
        "stage": args.stage,
        "head": _git("rev-parse", "HEAD").strip(),
        "candidate_fingerprint": fingerprint,
        "fingerprinted_files": len(ledger),
        "untracked_fingerprint_matches": sorted(
            row["path"] for row in ledger if not row["tracked"]
        ),
        "git_status": status,
        "ledger": ledger,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "stage": args.stage,
                "head": payload["head"],
                "candidate_fingerprint": fingerprint,
                "fingerprinted_files": len(ledger),
                "untracked_fingerprint_matches": payload["untracked_fingerprint_matches"],
                "dirty_entries": len(status),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
