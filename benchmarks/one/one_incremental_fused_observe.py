#!/usr/bin/env python3
"""ONE-G0.2 fused observation cache resource falsifier.

Compare the canonical fused Python observer against the exact-oracle incremental observer
on repeat/update workloads. The candidate may reuse only current-SHA-validated, sealed
writer cache state. It must emit identical run and reuse opportunities and charge the
extra changed-block feature pass, cache payload, integrity hashing, and exact-verification
traffic.

Pre-registered gates:
* exact repeat: <=0.75x wall and CPU at both 256 KiB and 1 MiB;
* one-block and eight-block sparse edits: <=0.85x wall and CPU;
* candidate actual source reads (SHA validation + changed-block recompute + exact proof)
  may exceed baseline source+proof reads by at most changed bytes + one block of rounding;
* modeled persistent cache payload <=20% of source size;
* opportunity streams must be byte-for-byte/dataclass exact.

The thresholds are intentionally strong because ONE-07 is only useful if it removes a
major amount of repeated discovery work after paying cache integrity and memory traffic.
"""
from __future__ import annotations

import json
import os
import statistics
import time

from experiments.one.cache_fused_observe import observe_incremental
from experiments.one.observe import observe

SIZES = (256 << 10, 1 << 20)
REPETITIONS = 15
BLOCK_SIZE = 4096
CHUNK_SIZE = 64
MIN_RUN = 8


def _data(size: int) -> bytes:
    # Mixed deterministic structure: repeated 4 KiB motifs, numeric-ish drift, and short
    # run islands. This avoids a benchmark that wins solely because every chunk repeats.
    out = bytearray(size)
    for i in range(size):
        block = i // BLOCK_SIZE
        within = i % BLOCK_SIZE
        if 640 <= within < 720 or 2600 <= within < 2700:
            out[i] = (block * 11) & 0xFF
        else:
            motif = block % 7
            out[i] = (motif * 37 + within * 131 + (within >> 3) * 17 + block * 3) & 0xFF
    return bytes(out)


def _cases(base: bytes):
    one = bytearray(base)
    one[len(base) // 2 + 17] ^= 0x5A
    eight = bytearray(base)
    block_count = len(base) // BLOCK_SIZE
    for k in range(8):
        block = (k * max(1, block_count // 8)) % block_count
        eight[block * BLOCK_SIZE + 31 + k] ^= (0x21 + k)
    return (
        ("exact_repeat", base, 0),
        ("one_block_edit", bytes(one), BLOCK_SIZE),
        ("eight_block_edit", bytes(eight), min(len(base), 8 * BLOCK_SIZE)),
    )


def _timed(fn):
    c0 = time.process_time_ns()
    w0 = time.perf_counter_ns()
    fn()
    return time.perf_counter_ns() - w0, time.process_time_ns() - c0


def _paired_medians(baseline_fn, candidate_fn):
    bw, bc, cw, cc = [], [], [], []
    for rep in range(REPETITIONS):
        order = ((baseline_fn, bw, bc), (candidate_fn, cw, cc))
        if rep % 2:
            order = tuple(reversed(order))
        for fn, walls, cpus in order:
            wall, cpu = _timed(fn)
            walls.append(wall)
            cpus.append(cpu)
    return statistics.median(bw), statistics.median(bc), statistics.median(cw), statistics.median(cc)


def main() -> int:
    rows = []
    failed = False
    for size in SIZES:
        base = _data(size)
        seed = observe_incremental(
            base,
            min_run=MIN_RUN,
            chunk_size=CHUNK_SIZE,
            block_size=BLOCK_SIZE,
        )
        oracle_seed = observe(base, min_run=MIN_RUN, chunk_size=CHUNK_SIZE)
        assert seed.observation.runs == oracle_seed.runs
        assert seed.observation.reuse == oracle_seed.reuse

        payload_ratio = seed.stats.persistent_payload_bytes / max(1, len(base))
        if payload_ratio > 0.20:
            failed = True

        for case, current, expected_changed_bytes in _cases(base):
            def baseline_call():
                return observe(current, min_run=MIN_RUN, chunk_size=CHUNK_SIZE)

            def candidate_call():
                return observe_incremental(
                    current,
                    previous=seed.cache,
                    min_run=MIN_RUN,
                    chunk_size=CHUNK_SIZE,
                    block_size=BLOCK_SIZE,
                )

            baseline = baseline_call()
            candidate = candidate_call()
            if candidate.observation.runs != baseline.runs or candidate.observation.reuse != baseline.reuse:
                raise AssertionError(f"observation divergence: {size=} {case=}")
            bw, bc, cw, cc = _paired_medians(baseline_call, candidate_call)
            wall_ratio = cw / bw
            cpu_ratio = cc / bc
            actual_read_limit = baseline.stats.total_source_read_bytes + expected_changed_bytes + BLOCK_SIZE
            rows.append({
                "size": size,
                "case": case,
                "baseline_wall_ns": bw,
                "candidate_wall_ns": cw,
                "baseline_cpu_ns": bc,
                "candidate_cpu_ns": cc,
                "wall_ratio": wall_ratio,
                "cpu_ratio": cpu_ratio,
                "candidate_validation_read_bytes": candidate.stats.validation_read_bytes,
                "candidate_feature_recompute_bytes": candidate.stats.feature_recompute_bytes,
                "candidate_feature_reuse_bytes": candidate.stats.feature_reuse_bytes,
                "candidate_cache_integrity_hash_bytes": candidate.stats.cache_integrity_hash_bytes,
                "candidate_cache_feature_payload_read_bytes": candidate.stats.cache_feature_payload_read_bytes,
                "baseline_total_source_read_bytes": baseline.stats.total_source_read_bytes,
                "candidate_total_source_read_bytes": candidate.stats.total_source_read_bytes,
                "persistent_payload_bytes": candidate.stats.persistent_payload_bytes,
                "persistent_payload_ratio": candidate.stats.persistent_payload_bytes / max(1, len(current)),
            })

            limit = 0.75 if case == "exact_repeat" else 0.85
            if wall_ratio > limit or cpu_ratio > limit:
                failed = True
            if candidate.stats.total_source_read_bytes > actual_read_limit:
                failed = True
            if candidate.stats.persistent_payload_bytes / max(1, len(current)) > 0.20:
                failed = True

    result = {
        "experiment": "ONE-G0.2 exact fused-observation cache",
        "head": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA"),
        "github_event_sha": os.environ.get("GITHUB_SHA"),
        "repetitions": REPETITIONS,
        "block_size": BLOCK_SIZE,
        "chunk_size": CHUNK_SIZE,
        "min_run": MIN_RUN,
        "rows": rows,
        "decision": "ADVANCE_FUSED_OBSERVATION_CACHE" if not failed else "REJECT_OR_REFORM",
        "scope": "Python writer-discovery cache only; positional updates only; no ONE-byte, reader, native, density, or arbitrary-shift claim",
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
