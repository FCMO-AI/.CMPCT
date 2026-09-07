#!/usr/bin/env python3
"""ONE-G0.2 bounded content-relocation cache experiment.

Compare the existing positional fingerprint cache with a content-addressed relocation
candidate under identical SHA-256 current-block validation.  The candidate only earns
continuation if block-aligned movement recovers substantial feature work without turning
unaligned shifts into a large regression.  This is writer-discovery evidence only.
"""
from __future__ import annotations

import json
import os
import statistics
import time
from dataclasses import asdict

from experiments.one.cache_fingerprints import observe_fingerprints_cached
from experiments.one.cache_relocation import observe_fingerprints_relocated


SIZES = (256 << 10, 1 << 20)
REPETITIONS = 15
BLOCK_SIZE = 4096
CHUNK_SIZE = 64


def _data(size: int) -> bytes:
    # Every block has distinct deterministic content so relocation cannot win through a
    # degenerate repeated-block corpus.  The generator is separate from the Genesis 15.
    out = bytearray(size)
    for i in range(size):
        block = i // BLOCK_SIZE
        within = i % BLOCK_SIZE
        out[i] = (block * 73 + within * 131 + (within >> 4) * 17 + 29) & 0xFF
    return bytes(out)


def _timed(fn) -> tuple[int, int]:
    c0 = time.process_time_ns()
    w0 = time.perf_counter_ns()
    fn()
    return time.perf_counter_ns() - w0, time.process_time_ns() - c0


def _paired_medians(baseline_fn, candidate_fn) -> tuple[float, float, float, float]:
    base_walls = []
    base_cpus = []
    cand_walls = []
    cand_cpus = []
    for repetition in range(REPETITIONS):
        order = (
            (baseline_fn, base_walls, base_cpus),
            (candidate_fn, cand_walls, cand_cpus),
        )
        if repetition % 2:
            order = tuple(reversed(order))
        for fn, walls, cpus in order:
            wall, cpu = _timed(fn)
            walls.append(wall)
            cpus.append(cpu)
    return (
        statistics.median(base_walls),
        statistics.median(base_cpus),
        statistics.median(cand_walls),
        statistics.median(cand_cpus),
    )


def _cases(base: bytes) -> tuple[tuple[str, bytes], ...]:
    insertion = bytes(((i * 19 + 7) & 0xFF) for i in range(BLOCK_SIZE))
    half = (len(base) // 2 // BLOCK_SIZE) * BLOCK_SIZE
    block_insert = base[:half] + insertion + base[half:]

    blocks = [base[i : i + BLOCK_SIZE] for i in range(0, len(base), BLOCK_SIZE)]
    quarter = max(1, len(blocks) // 4)
    block_reorder = b"".join(blocks[quarter:] + blocks[:quarter])

    # Explicit hostile control: aligned fingerprints are not invariant to byte shifts.
    one_byte_insert = base[:half] + b"X" + base[half:]
    return (
        ("exact_repeat", base),
        ("block_insert", block_insert),
        ("block_reorder", block_reorder),
        ("one_byte_insert", one_byte_insert),
    )


def main() -> int:
    rows = []
    failed = False
    for size in SIZES:
        base = _data(size)
        positional_seed = observe_fingerprints_cached(
            base, block_size=BLOCK_SIZE, chunk_size=CHUNK_SIZE
        )
        relocation_seed = observe_fingerprints_relocated(
            base, block_size=BLOCK_SIZE, chunk_size=CHUNK_SIZE
        )
        if positional_seed.fingerprints != relocation_seed.fingerprints:
            raise AssertionError("seed semantics differ before relocation experiment")

        for case, current in _cases(base):
            baseline = observe_fingerprints_cached(
                current,
                previous=positional_seed.cache,
                block_size=BLOCK_SIZE,
                chunk_size=CHUNK_SIZE,
            )
            candidate = observe_fingerprints_relocated(
                current,
                previous=relocation_seed.cache,
                block_size=BLOCK_SIZE,
                chunk_size=CHUNK_SIZE,
            )
            if candidate.fingerprints != baseline.fingerprints:
                raise AssertionError(f"candidate/baseline divergence: {size=} {case=}")

            def baseline_call():
                return observe_fingerprints_cached(
                    current,
                    previous=positional_seed.cache,
                    block_size=BLOCK_SIZE,
                    chunk_size=CHUNK_SIZE,
                )

            def candidate_call():
                return observe_fingerprints_relocated(
                    current,
                    previous=relocation_seed.cache,
                    block_size=BLOCK_SIZE,
                    chunk_size=CHUNK_SIZE,
                )

            base_wall, base_cpu, cand_wall, cand_cpu = _paired_medians(
                baseline_call, candidate_call
            )
            wall_ratio = cand_wall / base_wall
            cpu_ratio = cand_cpu / base_cpu
            feature_ratio = candidate.stats.feature_recompute_bytes / max(
                1, baseline.stats.feature_recompute_bytes
            )
            index_payload_ratio = candidate.stats.relocation_index_payload_bytes / max(
                1, len(current)
            )
            row = {
                "size": size,
                "case": case,
                "baseline_wall_ns": base_wall,
                "candidate_wall_ns": cand_wall,
                "baseline_cpu_ns": base_cpu,
                "candidate_cpu_ns": cand_cpu,
                "wall_ratio": wall_ratio,
                "cpu_ratio": cpu_ratio,
                "feature_recompute_ratio": feature_ratio,
                "relocation_index_payload_ratio": index_payload_ratio,
                "baseline_stats": asdict(baseline.stats),
                "candidate_stats": asdict(candidate.stats),
            }
            rows.append(row)

            # Frozen disproof rules.  Aligned movement must remove at least 90% of the
            # feature recomputation that positional caching would perform and must be a
            # real CPU/wall win.  Exact repeat must not build the relocation index.  The
            # unaligned hostile control may miss, but lookup/index overhead may not exceed
            # 15% on either wall or process CPU.
            if case in {"block_insert", "block_reorder"}:
                if feature_ratio > 0.10 or wall_ratio > 0.90 or cpu_ratio > 0.90:
                    failed = True
            elif case == "exact_repeat":
                if (
                    candidate.stats.relocation_index_entries != 0
                    or candidate.stats.relocation_lookups != 0
                    or wall_ratio > 1.05
                    or cpu_ratio > 1.05
                ):
                    failed = True
            elif case == "one_byte_insert":
                if wall_ratio > 1.15 or cpu_ratio > 1.15:
                    failed = True

            # Lower-bound relocation-index payload must stay small even before Python
            # object overhead is measured independently.
            if index_payload_ratio > 0.02:
                failed = True

    result = {
        "experiment": "ONE-G0.2 bounded content-relocation fingerprint cache",
        "head": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA"),
        "github_event_sha": os.environ.get("GITHUB_SHA"),
        "repetitions": REPETITIONS,
        "timing_order": "paired alternating positional/relocation; odd repetitions reversed",
        "block_size": BLOCK_SIZE,
        "chunk_size": CHUNK_SIZE,
        "rows": rows,
        "decision": "ADVANCE_RELOCATION" if not failed else "REJECT_OR_REFORM",
        "scope": (
            "Python writer-discovery falsifier only; aligned movement only; no product/native "
            "performance authority and no claim for arbitrary byte-shift resynchronization"
        ),
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
