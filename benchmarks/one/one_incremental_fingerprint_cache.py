#!/usr/bin/env python3
"""ONE-G0.2 incremental fingerprint-cache resource experiment.

This benchmark is intentionally writer-only and Python-level. It answers one narrow
question before native work: can an authenticated content-identity cache skip a real
fused-observation feature family by enough margin to survive its own verification and
persistent-state costs? It does not establish product/native creation speed.
"""
from __future__ import annotations

import json
import os
import statistics
import time
from dataclasses import asdict

from experiments.one.cache_fingerprints import observe_fingerprints_cached


SIZES = (64 << 10, 256 << 10, 1 << 20)
REPETITIONS = 15
BLOCK_SIZE = 4096
CHUNK_SIZE = 64


def _data(size: int) -> bytes:
    # Deterministic non-run-heavy content with repeated local structure; benchmark bytes
    # are identical for baseline and candidate and are not selected from the 15-workload
    # Genesis matrix.
    return bytes(((i * 131 + (i >> 5) * 17 + 29) & 0xFF) for i in range(size))


def _median_call(fn) -> tuple[float, float]:
    walls = []
    cpus = []
    for _ in range(REPETITIONS):
        c0 = time.process_time_ns()
        w0 = time.perf_counter_ns()
        fn()
        walls.append(time.perf_counter_ns() - w0)
        cpus.append(time.process_time_ns() - c0)
    return statistics.median(walls), statistics.median(cpus)


def main() -> int:
    rows = []
    failed = False
    for size in SIZES:
        base = _data(size)
        seed = observe_fingerprints_cached(base, block_size=BLOCK_SIZE, chunk_size=CHUNK_SIZE)
        edited = bytearray(base)
        edited[(size // 2) + 17] ^= 0x5A
        edited = bytes(edited)

        for case, current in (("repeat", base), ("one_block_edit", edited)):
            fresh = observe_fingerprints_cached(current, block_size=BLOCK_SIZE, chunk_size=CHUNK_SIZE)
            incremental = observe_fingerprints_cached(
                current,
                previous=seed.cache,
                block_size=BLOCK_SIZE,
                chunk_size=CHUNK_SIZE,
            )
            if incremental.fingerprints != fresh.fingerprints:
                raise AssertionError(f"fresh/incremental fingerprint divergence: {size=} {case=}")

            fresh_wall, fresh_cpu = _median_call(
                lambda: observe_fingerprints_cached(
                    current, block_size=BLOCK_SIZE, chunk_size=CHUNK_SIZE
                )
            )
            cached_wall, cached_cpu = _median_call(
                lambda: observe_fingerprints_cached(
                    current,
                    previous=seed.cache,
                    block_size=BLOCK_SIZE,
                    chunk_size=CHUNK_SIZE,
                )
            )
            wall_ratio = cached_wall / fresh_wall
            cpu_ratio = cached_cpu / fresh_cpu
            row = {
                "size": size,
                "case": case,
                "fresh_wall_ns": fresh_wall,
                "cached_wall_ns": cached_wall,
                "fresh_cpu_ns": fresh_cpu,
                "cached_cpu_ns": cached_cpu,
                "wall_ratio": wall_ratio,
                "cpu_ratio": cpu_ratio,
                "stats": asdict(incremental.stats),
            }
            rows.append(row)

            # Preregistered viability gate, not promotion authority. At >=256 KiB the
            # cache must retain a very large margin in this slow Python feature kernel:
            # <=0.50x wall and CPU. Anything weaker is unlikely to justify native work
            # once the feature implementation becomes much cheaper.
            if size >= (256 << 10) and (wall_ratio > 0.50 or cpu_ratio > 0.50):
                failed = True

    evidence_head = os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA")
    result = {
        "experiment": "ONE-G0.2 incremental aligned-fingerprint cache",
        "head": evidence_head,
        "github_event_sha": os.environ.get("GITHUB_SHA"),
        "repetitions": REPETITIONS,
        "block_size": BLOCK_SIZE,
        "chunk_size": CHUNK_SIZE,
        "rows": rows,
        "decision": "ADVANCE_TO_NATIVE_FALSIFIER" if not failed else "REJECT_OR_REFORM",
        "scope": "Python writer-discovery viability only; not product/native performance authority",
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
