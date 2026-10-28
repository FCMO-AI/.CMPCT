from __future__ import annotations

"""Focused r24 tiny/library/create worker for same-runner ABBA reproduction.

The release parity gate has intermittently reported a single >10% and >3 ms regression on tiny/library/create even
though the canonical src/cmpct hot path is unchanged relative to main. This worker is intentionally tiny: a
workflow invokes the exact same file under base/src and candidate/src on one immutable corpus in A-B-B-A order.
It records individual build samples plus archive identity so runner noise can be distinguished from an indirect
import/dependency/call-path regression without weakening the release gate.
"""

import argparse
import hashlib
import json
from pathlib import Path
import statistics
import time

from cmpct.builder import Builder
import cmpct.builder as builder_module


def run(src: Path, archive: Path, *, reps: int) -> dict:
    if reps < 3:
        raise ValueError("at least three repetitions are required")
    samples: list[float] = []
    identities: list[tuple[int, str]] = []
    for _ in range(reps):
        archive.unlink(missing_ok=True)
        t0 = time.perf_counter_ns()
        Builder(src).build(archive)
        samples.append((time.perf_counter_ns() - t0) / 1_000_000_000)
        raw = archive.read_bytes()
        identities.append((len(raw), hashlib.sha256(raw).hexdigest()))
    if len(set(identities)) != 1:
        raise RuntimeError("r24 tiny create was not byte-deterministic within one worker arm")
    return {
        "schema": "cmpct-v030-r24-tiny-create-worker-v1",
        "repetitions": reps,
        "samples_s": samples,
        "median_s": statistics.median(samples),
        "archive_bytes": identities[0][0],
        "archive_sha256": identities[0][1],
        "builder_module": str(Path(builder_module.__file__).resolve()),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--src", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--reps", type=int, default=7)
    args = parser.parse_args()
    result = run(args.src, args.archive, reps=args.reps)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()
