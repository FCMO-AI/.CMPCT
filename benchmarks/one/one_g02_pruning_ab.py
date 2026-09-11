"""ONE-G0.2 same-pass pruning/coalescing A/B.

The baseline freezes the pre-pruning fused observer: one source pass, run detection and
fixed-chunk fingerprints, but every fingerprint reuse candidate is immediately verified
as a separate chunk. The candidate is current `observe()`. The comparison asks whether
content-derived run dominance and contiguous proof coalescing reduce discovery work
without reducing the union of source bytes for which a cheap Law opportunity was found.

Python timings are research evidence only, not product-speed claims.
"""
from __future__ import annotations

import json
import os
import random
import statistics
import time
from dataclasses import dataclass

from experiments.one.observe import Observation, observe

REPETITIONS = 7
SIZE = 1024 * 1024
CHUNK_SIZE = 64
MIN_RUN = 8
MAX_INDEX_ENTRIES = 1 << 14
_FNV64_OFFSET = 0xCBF29CE484222325
_FNV64_PRIME = 0x100000001B3
_U64_MASK = (1 << 64) - 1


@dataclass(frozen=True)
class _NaiveStats:
    run_intervals: tuple[tuple[int, int], ...]
    reuse_intervals: tuple[tuple[int, int], ...]
    reuse_candidates: int
    verification_operations: int
    verification_read_bytes: int
    total_source_read_bytes: int


def _naive_fused(data: bytes) -> _NaiveStats:
    """Pre-pruning one-pass observer frozen as a benchmark-only causal baseline."""
    runs: list[tuple[int, int]] = []
    reuse: list[tuple[int, int]] = []
    index: dict[int, list[int]] = {}
    index_entries = 0
    verifications = 0
    verification_read_bytes = 0

    run_start = 0
    run_value = data[0] if data else 0
    run_length = 0
    chunk_hash = _FNV64_OFFSET

    for position, value in enumerate(data):
        if run_length == 0:
            run_start = position
            run_value = value
            run_length = 1
        elif value == run_value:
            run_length += 1
        else:
            if run_length >= MIN_RUN:
                runs.append((run_start, run_start + run_length))
            run_start = position
            run_value = value
            run_length = 1

        chunk_hash ^= value
        chunk_hash = (chunk_hash * _FNV64_PRIME) & _U64_MASK
        if (position + 1) % CHUNK_SIZE:
            continue

        start = position + 1 - CHUNK_SIZE
        fingerprint = chunk_hash
        chunk_hash = _FNV64_OFFSET
        sources = index.get(fingerprint)
        matched = False
        if sources:
            for source in sources:
                verifications += 1
                verification_read_bytes += 2 * CHUNK_SIZE
                if data[source : source + CHUNK_SIZE] == data[start : start + CHUNK_SIZE]:
                    reuse.append((start, start + CHUNK_SIZE))
                    matched = True
                    break
        if not matched and index_entries < MAX_INDEX_ENTRIES:
            index.setdefault(fingerprint, []).append(start)
            index_entries += 1

    if run_length >= MIN_RUN:
        runs.append((run_start, run_start + run_length))

    return _NaiveStats(
        run_intervals=tuple(runs),
        reuse_intervals=tuple(reuse),
        reuse_candidates=len(reuse),
        verification_operations=verifications,
        verification_read_bytes=verification_read_bytes,
        total_source_read_bytes=len(data) + verification_read_bytes,
    )


def _candidate_intervals(result: Observation) -> tuple[tuple[int, int], ...]:
    return tuple((item.start, item.start + item.length) for item in result.runs) + tuple(
        (item.target, item.target + item.length) for item in result.reuse
    )


def _covered_bytes(intervals: tuple[tuple[int, int], ...]) -> int:
    if not intervals:
        return 0
    merged: list[list[int]] = []
    for start, end in sorted(intervals):
        if not merged or start > merged[-1][1]:
            merged.append([start, end])
        else:
            merged[-1][1] = max(merged[-1][1], end)
    return sum(end - start for start, end in merged)


def _cases() -> dict[str, bytes]:
    source = random.Random(12).randbytes(64 * 1024)
    return {
        "random_1mib": random.Random(11).randbytes(SIZE),
        "zeros_1mib": b"\0" * SIZE,
        "repeated_64k_1mib": source * (SIZE // len(source)),
    }


def _median_ns(fn) -> tuple[int, object]:
    samples: list[int] = []
    last = None
    for _ in range(REPETITIONS):
        start = time.perf_counter_ns()
        last = fn()
        samples.append(time.perf_counter_ns() - start)
    return int(statistics.median(samples)), last


def run() -> dict[str, object]:
    rows: list[dict[str, object]] = []
    for name, data in _cases().items():
        naive_ns, naive_obj = _median_ns(lambda: _naive_fused(data))
        candidate_ns, candidate_obj = _median_ns(
            lambda: observe(
                data,
                min_run=MIN_RUN,
                chunk_size=CHUNK_SIZE,
                max_index_entries=MAX_INDEX_ENTRIES,
            )
        )
        assert isinstance(naive_obj, _NaiveStats)
        assert isinstance(candidate_obj, Observation)

        naive_covered = _covered_bytes(naive_obj.run_intervals + naive_obj.reuse_intervals)
        candidate_covered = _covered_bytes(_candidate_intervals(candidate_obj))
        # Suppressing a redundant opportunity is acceptable only when the remaining
        # cheap Law surface still covers exactly the same source region in this test.
        assert candidate_covered == naive_covered

        cs = candidate_obj.stats
        rows.append(
            {
                "case": name,
                "input_bytes": len(data),
                "naive_median_ns": naive_ns,
                "candidate_median_ns": candidate_ns,
                "candidate_elapsed_ratio_over_naive": candidate_ns / naive_ns,
                "naive_covered_opportunity_bytes": naive_covered,
                "candidate_covered_opportunity_bytes": candidate_covered,
                "naive_reuse_candidates": naive_obj.reuse_candidates,
                "candidate_reuse_candidates": cs.reuse_candidates,
                "naive_verification_operations": naive_obj.verification_operations,
                "candidate_verification_operations": cs.collision_verifications,
                "naive_verification_read_bytes": naive_obj.verification_read_bytes,
                "candidate_verification_read_bytes": cs.verification_read_bytes,
                "naive_total_source_read_bytes": naive_obj.total_source_read_bytes,
                "candidate_total_source_read_bytes": cs.total_source_read_bytes,
                "total_source_read_reduction_fraction": 1.0
                - (cs.total_source_read_bytes / naive_obj.total_source_read_bytes),
            }
        )
    return {
        "schema": "cmpct-one-g02-pruning-ab-v1",
        "experimental_version": "ONE-G0.2",
        "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
        "repetitions": REPETITIONS,
        "claim_boundary": "same-pass Python causal A/B; opportunity coverage is test-regime evidence, not stored-byte savings",
        "rows": rows,
    }


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True, indent=2))
