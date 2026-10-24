#!/usr/bin/env python3
"""O6b: actual CMPCT Reader signed-journal open vs final-checkpoint latency.

Research only; preserves both architectures and the authentic revision-24
archives produced by v031_signed_delta_replay_o0.make_case. Unlike the indexed
validation hot path, CMPCT._index_from_footer owns its separate journal replay.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import statistics
import sys
import tempfile
import time
from pathlib import Path

from cmpct.builder import Builder
from cmpct.reader import CMPCT

# This experiment reuses the exact authenticated case constructor and
# same-logical-index control from the already-proven O0 product instrument.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from v031_signed_delta_replay_o0 import PAYLOAD, make_case  # noqa: E402


def sample_open(path: Path, expected_files: int, sample_member: str) -> dict:
    t0 = time.perf_counter_ns()
    c0 = time.process_time_ns()
    with CMPCT(path) as archive:
        opened_wall = time.perf_counter_ns() - t0
        opened_cpu = time.process_time_ns() - c0
        assert len(archive.files) == expected_files
        # Read outside the constructor timing to prevent payload work from
        # hiding the metadata interpretation cost.
        assert archive.read(sample_member) == PAYLOAD
    return {"open_wall_ns": opened_wall, "open_cpu_ns": opened_cpu}


def measure_pair(delta: Path, checkpoint: Path, n: int, repeats: int) -> dict:
    samples = {"delta": [], "checkpoint": []}
    files = {"delta": delta, "checkpoint": checkpoint}
    # Pairwise reversal balances warm-cache/order bias without changing
    # process-start timing boundaries. All observations share this runner.
    for i in range(repeats):
        order = ("delta", "checkpoint") if i % 2 == 0 else ("checkpoint", "delta")
        for label in order:
            samples[label].append(sample_open(files[label], n, "g000000.bin"))
    def med(label: str, field: str) -> float:
        return statistics.median(x[field] for x in samples[label]) / 1e6
    d, c = med("delta", "open_wall_ns"), med("checkpoint", "open_wall_ns")
    return {
        "samples": samples,
        "median_open_wall_ms": {k: med(k, "open_wall_ns") for k in files},
        "median_open_cpu_ms": {k: med(k, "open_cpu_ns") for k in files},
        "delta_over_checkpoint_open_wall_ratio": d / c,
        "delta_minus_checkpoint_open_wall_ms": d - c,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--sizes", type=int, nargs="+", default=[512, 2048, 4096])
    ap.add_argument("--repeats", type=int, default=7)
    args = ap.parse_args()
    if args.repeats < 3 or any(n < 64 or n > 8192 for n in args.sizes):
        raise SystemExit("Invalid prospective O6b workload")
    args.out.mkdir(parents=True, exist_ok=True)
    result = {
        "experiment": "o6b-authenticated-r24-reader-open-delta-vs-checkpoint",
        "credit": "research-instrument-only; no release or Reader fix",
        "source_sha": os.environ.get("EVIDENCE_HEAD", "LOCAL_UNPINNED"),
        "host": platform.platform(),
        "python": sys.version,
        "cases": {},
    }
    with tempfile.TemporaryDirectory(prefix="cmpct-reader-o6b-") as scratch:
        root = Path(scratch)
        source_root = root / "input"
        source_root.mkdir()
        (source_root / "single.bin").write_bytes(PAYLOAD)
        source = root / "source.cmpct"
        Builder(source_root, workers=1, reproducible=True).build(source)
        for n in args.sizes:
            delta, checkpoint, identity = make_case(root, source, n)
            measures = measure_pair(delta, checkpoint, n, args.repeats)
            result["cases"][str(n)] = {
                "identity": identity,
                "measurement": measures,
                "full_archive_sha256": {
                    "delta": hashlib.sha256(delta.read_bytes()).hexdigest(),
                    "checkpoint": hashlib.sha256(checkpoint.read_bytes()).hexdigest(),
                },
            }
            print("O6B_READER_OPEN " + json.dumps({
                "n": n,
                "delta_wall_ms": measures["median_open_wall_ms"]["delta"],
                "checkpoint_wall_ms": measures["median_open_wall_ms"]["checkpoint"],
                "ratio": measures["delta_over_checkpoint_open_wall_ratio"],
                "archive_bytes_delta": identity["delta_archive_bytes"],
                "archive_bytes_checkpoint": identity["checkpoint_archive_bytes"],
                "final_index_identical": identity["result_index_equal"],
            }), flush=True)
    target = args.out / "reader-open-o6b-receipt.json"
    target.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("O6B_RECEIPT_SHA256", hashlib.sha256(target.read_bytes()).hexdigest(), flush=True)


if __name__ == "__main__":
    main()
