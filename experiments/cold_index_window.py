#!/usr/bin/env python3
"""Research only: audition long-window compression of an r24 checkpoint index.

Payloads, logical metadata, hashes and the r24 grammar are unchanged. This is not
the default encoder policy. Full product timing/native/resource gates remain due.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

from cmpct.codec import HDR, FTR, MAGIC, FMAGIC, VERSION, zd
from cmpct.validation import preflight_archive


def recompress(source: Path, output: Path):
    if output.exists():
        raise ValueError("research output must not exist")
    preflight_archive(source)
    size = source.stat().st_size
    with source.open("rb") as stream:
        magic, version, flags, cs, us, span, ih = HDR.unpack(stream.read(HDR.size))
        if (magic, version, flags) != (MAGIC, VERSION, 0):
            raise ValueError("only ordinary r24 checkpoints are admitted")
        original = stream.read(cs)
        raw = zd(original, us)
        if hashlib.sha256(raw).digest() != ih:
            raise ValueError("primary index identity mismatch")
        stream.seek(HDR.size + cs + span)
        tail = stream.read(cs)
        footer = stream.read(FTR.size)
        if (tail != original or len(footer) != FTR.size or
                FTR.unpack(footer) != (FMAGIC, 0, 1, 0, 0, cs, us, 0, ih) or
                stream.tell() != size):
            raise ValueError("only exact checkpoints, without journals or trailing bytes, are admitted")
    trial = subprocess.run(["zstd", "-q", "-19", "--long=31", "-c"], input=raw,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True).stdout
    # Measure both redundant index copies. A losing audition preserves every original byte.
    selected = len(trial) < len(original)
    if selected:
        with source.open("rb") as src, output.open("xb") as dst:
            dst.write(HDR.pack(magic, version, flags, len(trial), us, span, ih))
            dst.write(trial)
            src.seek(HDR.size + cs)
            remaining = span
            while remaining:
                block = src.read(min(remaining, 1024 * 1024))
                if not block:
                    raise IOError("source truncated during research copy")
                dst.write(block)
                remaining -= len(block)
            dst.write(trial)
            dst.write(FTR.pack(FMAGIC, 0, 1, 0, 0, len(trial), us, 0, ih))
    else:
        # Exclusive creation avoids replacing an unrelated existing file on a losing trial.
        with source.open("rb") as src, output.open("xb") as dst:
            shutil.copyfileobj(src, dst)
    return {"research_only": True, "selected": selected, "base_bytes": size,
            "candidate_bytes": output.stat().st_size, "index_raw_bytes": us,
            "index_base_bytes": cs, "index_trial_bytes": len(trial),
            "payload_bytes_changed": 0}


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("source", type=Path)
    ap.add_argument("output", type=Path)
    args = ap.parse_args()
    print(json.dumps(recompress(args.source, args.output), indent=2))
