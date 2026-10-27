#!/usr/bin/env python3
"""Public seeded analogue of repeated snapshots; never copies a private tree."""
from __future__ import annotations

import argparse
import io
import os
from pathlib import Path
import random
import zipfile


def generate(root: Path, *, seed=20261027, stages=4, files=256, block_bytes=4096,
             copies_per_object=1, event_multiplier=32, files_per_dir=0, links_per_stage=0):
    if (min(stages, files, copies_per_object, event_multiplier) < 1 or block_bytes < 64
            or files_per_dir < 0 or links_per_stage < 0):
        raise ValueError("invalid public corpus dimensions")
    root.mkdir(parents=True, exist_ok=False)
    rng = random.Random(seed)
    unique_objects = (files + copies_per_object - 1) // copies_per_object
    base = [rng.randbytes(block_bytes) for _ in range(unique_objects)]
    large = rng.randbytes(3 * 1024 * 1024)
    # Fixed ZIP timestamps and bytes keep this analogue independent of wall clock.
    containers = []
    for i in range(12):
        out = io.BytesIO()
        with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_STORED) as archive:
            archive.writestr(zipfile.ZipInfo("payload.bin", (2000, 1, 1, 0, 0, 0)), base[i % unique_objects])
        containers.append(out.getvalue())
    for stage in range(stages):
        dest = root / f"snapshot-{stage:02d}"
        dest.mkdir()
        for i in range(files):
            identity = i // copies_per_object
            raw = b"record=" + str(identity).encode() + b"\n" + base[identity]
            if identity % 8 == 0:
                raw = raw[:40] + str(stage).encode() + raw[41:]
            parent = dest
            if files_per_dir:
                parent = dest / f"group-{i // files_per_dir:05d}"
                parent.mkdir(exist_ok=True)
            (parent / f"object-{i:05d}.dat").write_bytes(raw)
        for i, raw in enumerate(containers):
            (dest / f"container-{i:02d}.zip").write_bytes(raw)
        (dest / "shifted.bin").write_bytes(bytes([stage]) + large)
        (dest / "events.txt").write_bytes(
            b"".join(f"event={i} value={i % 17} stage={stage}\n".encode() for i in range(files * event_multiplier)))
        for i in range(links_per_stage):
            # Neutral, deliberately unresolved targets exercise trusted-source restoration without
            # naming a real host path or following a link while generating the corpus.
            target = "../unavailable" if i < 7 else "/unavailable/example-file"
            (dest / f"link-{i:04d}").symlink_to(target)
    # Reproducible bytes and metadata, suitable for same-tree base/candidate comparisons.
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            os.utime(path, ns=(0, 0), follow_symlinks=False)
            continue
        path.chmod(0o755 if path.is_dir() else 0o644)
        os.utime(path, ns=(0, 0))
    root.chmod(0o755)
    os.utime(root, ns=(0, 0))
    return root


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("root", type=Path)
    ap.add_argument("--seed", type=int, default=20261027)
    ap.add_argument("--stages", type=int, default=4)
    ap.add_argument("--files", type=int, default=256)
    ap.add_argument("--block-bytes", type=int, default=4096)
    ap.add_argument("--copies-per-object", type=int, default=1)
    ap.add_argument("--event-multiplier", type=int, default=32)
    ap.add_argument("--files-per-dir", type=int, default=0)
    ap.add_argument("--links-per-stage", type=int, default=0)
    args = ap.parse_args()
    generate(args.root, seed=args.seed, stages=args.stages, files=args.files,
             block_bytes=args.block_bytes, copies_per_object=args.copies_per_object,
             event_multiplier=args.event_multiplier, files_per_dir=args.files_per_dir,
             links_per_stage=args.links_per_stage)
