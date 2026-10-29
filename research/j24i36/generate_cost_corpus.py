#!/usr/bin/env python3
"""Create one immutable deterministic installed r24 source for same-runner A/B.

This is NOT the frozen external benchmark and carries no promotion credit.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import random
from pathlib import Path
from cmpct.builder import Builder
from cmpct.reader import CMPCT

def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(65536):
            h.update(block)
    return h.hexdigest()

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--files", type=int, default=64)
    ap.add_argument("--file-bytes", type=int, default=262144)
    args = ap.parse_args()
    assert 1 <= args.files <= 1024
    assert 4096 <= args.file_bytes <= 1024 * 1024
    args.output.mkdir(parents=True, exist_ok=True)
    root = args.output / "source"
    root.mkdir()
    for i in range(args.files):
        # Distinct seeded incompressible content; no fixture-identity path in product.
        payload = random.Random(0x24_1_36 + i).randbytes(args.file_bytes)
        (root / f"sample-{i:04d}.bin").write_bytes(payload)
    archive = args.output / "same-input.cmpct"
    Builder(root, workers=1, reproducible=True).build(archive)
    with CMPCT(archive) as reader:
        verified = reader.verify()
    assert verified == args.files, f"verified {verified}, expected {args.files}"
    summary = {
        "schema": "j24i36-direct-source-benchmark-v1",
        "generator": "python.Random(seed + file_id), input member count exact",
        "files": args.files,
        "logical_bytes": args.files * args.file_bytes,
        "archive_bytes": archive.stat().st_size,
        "archive_sha256": file_hash(archive),
        "verified": verified,
        "scope": "in-process component candidate A/B; not external release benchmark"
    }
    (args.output / "source-custody.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, sort_keys=True))

if __name__ == "__main__":
    main()
