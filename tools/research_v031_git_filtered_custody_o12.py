#!/usr/bin/env python3
"""O12 research-only: Git-clean-filtered *working-tree* source identity.

This does not replace the raw-worktree SHA-256 v0.31 candidate fingerprint.
Git object IDs inherit the repository object format and filters, so this is a
Git-equivalence diagnostic, NOT independent SHA-256 authentication of bytes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time

from tools import check_v031_candidate_fingerprint as raw

SCHEMA = "cmpct-v031-git-filtered-worktree-o12-v1"
_OID = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")


def compute(manifest: dict, *, root: Path = raw.ROOT, batch_size: int = 96) -> dict:
    if not 1 <= batch_size <= 128:
        raise ValueError("invalid bounded Git hash-object batch size")
    root = root.resolve()
    # O11 remains the byte-exact physical witness and source-roster authority.
    t0 = time.perf_counter_ns()
    raw_digest, rows = raw.fingerprint(manifest, root=root)
    raw_ns = time.perf_counter_ns() - t0
    digest = hashlib.sha256()
    oids: dict[str, str] = {}
    binary_digest: dict[str, str] = {}
    # Git selects path-specific clean filters when file paths are positional
    # arguments to hash-object (WITHOUT --no-filters). -- prevents option paths.
    # Never hash HEAD:index blobs here: that silently hides unstaged source edits.
    t1 = time.perf_counter_ns()
    for start in range(0, len(rows), batch_size):
        batch = rows[start:start + batch_size]
        proc = subprocess.run(
            ["git", "hash-object", "--", *batch], cwd=root,
            capture_output=True, text=True, check=False, encoding="utf-8",
        )
        if proc.returncode:
            raise ValueError(f"Git clean-filter hashing failed: {proc.stderr[:300]}")
        values = proc.stdout.splitlines()
        if len(values) != len(batch) or any(not _OID.fullmatch(v) for v in values):
            raise ValueError("Git returned incomplete or invalid clean-filter object IDs")
        for path, oid in zip(batch, values):
            encoded = path.encode("utf-8")
            digest.update(len(encoded).to_bytes(4, "little"))
            digest.update(encoded)
            digest.update(bytes.fromhex(oid))
            oids[path] = oid
            binary_digest[path] = hashlib.sha256((root / path).read_bytes()).hexdigest()
    filtered_ns = time.perf_counter_ns() - t1
    return {
        "schema": SCHEMA,
        "raw_worktree_sha256": raw_digest,
        "git_filtered_roster_sha256": digest.hexdigest(),
        "source_count": len(rows),
        "paths": rows,
        "git_filtered_object_ids": oids,
        "raw_file_sha256": binary_digest,
        "git_object_id_algorithm": "sha256" if len(next(iter(oids.values()))) == 64 else "sha1",
        "cost_ns": {"raw_roster_and_hash": raw_ns, "git_clean_filter_and_raw_file": filtered_ns},
        "scope": "research; Git-clean equivalence, NOT bytes-exact identity or release credit",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = raw.ROOT
    expected = os.environ.get("EVIDENCE_HEAD")
    sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True,
                         text=True, check=True).stdout.strip()
    if expected and expected != sha:
        raise SystemExit(f"O12 exact-source drift: {sha} != {expected}")
    result = compute(raw.load_manifest(), root=root)
    result["source_sha"] = sha
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in
                      ("source_sha", "source_count", "raw_worktree_sha256",
                       "git_filtered_roster_sha256", "git_object_id_algorithm", "cost_ns")}))


if __name__ == "__main__":
    main()
