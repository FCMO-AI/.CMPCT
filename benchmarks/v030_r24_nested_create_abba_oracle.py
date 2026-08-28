from __future__ import annotations

"""Focused r24 nested/library/create worker for same-runner ABBA reproduction.

The mature r24 core/ZIP gate recently isolated a nested/library/create timing red. This worker measures only
that direct-base boundary on one immutable nested corpus so we can distinguish a reproducible indirect r24
regression from shared-runner drift without weakening the authoritative gate. Archive bytes are hashed on every
sample and base/candidate are expected to remain byte-identical.
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
        raise RuntimeError("r24 nested create was not byte-deterministic within one worker arm")
    return {
        "schema": "cmpct-v030-r24-nested-create-worker-v1",
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
    parser.add_argument("--reps", type=int, default=9)
    args = parser.parse_args()
    result = run(args.src, args.archive, reps=args.reps)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()
