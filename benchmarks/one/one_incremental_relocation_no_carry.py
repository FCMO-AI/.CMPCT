#!/usr/bin/env python3
"""ONE-G0.2 opportunity-gated relocation without carried directory.

This reruns the original positional-vs-relocation resource contract after removing the
ordinary-path cost that caused the persistent-directory candidate to fail. The candidate
emits no next-generation relocation directory. It may build a bounded prior-cache index
only after two consecutive positional misses provide movement evidence.

Frozen success rules are intentionally the original resource rules: aligned insertion and
reorder must cut feature recomputation to <=0.10x and wall/CPU to <=0.90x positional;
exact repeat <=1.05x; sparse mutation <=1.08x; hostile one-byte insertion <=1.15x; index
payload <=2%. The only semantic change in accounting is that movement is allowed to scan
at most the prior block count, while non-movement controls must scan zero prior blocks.
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
REPETITIONS = 21
BLOCK_SIZE = 4096
CHUNK_SIZE = 64


def _data(size: int) -> bytes:
    out = bytearray(size)
    for i in range(size):
        block = i // BLOCK_SIZE
        within = i % BLOCK_SIZE
        out[i] = (block * 73 + within * 131 + (within >> 4) * 17 + 29) & 0xFF
    return bytes(out)


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


def _cases(base: bytes):
    insertion = bytes(((i * 19 + 7) & 0xFF) for i in range(BLOCK_SIZE))
    half = (len(base) // 2 // BLOCK_SIZE) * BLOCK_SIZE
    block_insert = base[:half] + insertion + base[half:]
    blocks = [base[i:i + BLOCK_SIZE] for i in range(0, len(base), BLOCK_SIZE)]
    quarter = max(1, len(blocks) // 4)
    block_reorder = b"".join(blocks[quarter:] + blocks[:quarter])
    sparse = bytearray(base)
    sparse[half + 17] ^= 0x5A
    one_byte_insert = base[:half] + b"X" + base[half:]
    return (
        ("exact_repeat", base),
        ("sparse_mutation", bytes(sparse)),
        ("block_insert", block_insert),
        ("block_reorder", block_reorder),
        ("one_byte_insert", one_byte_insert),
    )


def main() -> int:
    rows = []
    failed = False
    for size in SIZES:
        base = _data(size)
        pseed = observe_fingerprints_cached(base, block_size=BLOCK_SIZE, chunk_size=CHUNK_SIZE)
        rseed = observe_fingerprints_relocated(
            base,
            block_size=BLOCK_SIZE,
            chunk_size=CHUNK_SIZE,
            persist_directory=False,
        )
        assert pseed.fingerprints == rseed.fingerprints
        assert rseed.directory.entries == ()
        prior_block_count = len(rseed.cache.blocks)

        for case, current in _cases(base):
            def baseline_call():
                return observe_fingerprints_cached(
                    current,
                    previous=pseed.cache,
                    block_size=BLOCK_SIZE,
                    chunk_size=CHUNK_SIZE,
                )

            def candidate_call():
                return observe_fingerprints_relocated(
                    current,
                    previous=rseed.cache,
                    block_size=BLOCK_SIZE,
                    chunk_size=CHUNK_SIZE,
                    persist_directory=False,
                )

            baseline = baseline_call()
            candidate = candidate_call()
            if candidate.fingerprints != baseline.fingerprints:
                raise AssertionError(f"candidate/baseline divergence: {size=} {case=}")
            if candidate.directory.entries != ():
                raise AssertionError("no-carry candidate emitted relocation directory state")

            bw, bc, cw, cc = _paired_medians(baseline_call, candidate_call)
            wall_ratio = cw / bw
            cpu_ratio = cc / bc
            feature_ratio = candidate.stats.feature_recompute_bytes / max(1, baseline.stats.feature_recompute_bytes)
            index_payload_ratio = candidate.stats.relocation_index_payload_bytes / max(1, len(current))
            rows.append({
                "size": size,
                "case": case,
                "baseline_wall_ns": bw,
                "candidate_wall_ns": cw,
                "baseline_cpu_ns": bc,
                "candidate_cpu_ns": cc,
                "wall_ratio": wall_ratio,
                "cpu_ratio": cpu_ratio,
                "feature_recompute_ratio": feature_ratio,
                "relocation_index_payload_ratio": index_payload_ratio,
                "baseline_stats": asdict(baseline.stats),
                "candidate_stats": asdict(candidate.stats),
            })

            if candidate.stats.directory_output_entries != 0 or candidate.stats.directory_output_payload_bytes != 0:
                failed = True
            if candidate.stats.prior_cache_index_scan_blocks > prior_block_count:
                failed = True

            if case in {"block_insert", "block_reorder"}:
                if candidate.stats.prior_cache_index_scan_blocks != prior_block_count:
                    failed = True
                if feature_ratio > 0.10 or wall_ratio > 0.90 or cpu_ratio > 0.90:
                    failed = True
            elif case == "exact_repeat":
                if candidate.stats.prior_cache_index_scan_blocks != 0:
                    failed = True
                if candidate.stats.relocation_index_entries != 0 or candidate.stats.relocation_lookups != 0:
                    failed = True
                if wall_ratio > 1.05 or cpu_ratio > 1.05:
                    failed = True
            elif case == "sparse_mutation":
                if candidate.stats.prior_cache_index_scan_blocks != 0:
                    failed = True
                if candidate.stats.relocation_index_entries != 0 or candidate.stats.relocation_lookups != 0:
                    failed = True
                if candidate.stats.relocation_gate_activations != 0:
                    failed = True
                if wall_ratio > 1.08 or cpu_ratio > 1.08:
                    failed = True
            elif case == "one_byte_insert":
                if wall_ratio > 1.15 or cpu_ratio > 1.15:
                    failed = True
            if index_payload_ratio > 0.02:
                failed = True

    result = {
        "experiment": "ONE-G0.2 no-carry opportunity-gated relocation cache",
        "head": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA"),
        "github_event_sha": os.environ.get("GITHUB_SHA"),
        "repetitions": REPETITIONS,
        "timing_order": "paired alternating positional/no-carry relocation; odd repetitions reversed",
        "block_size": BLOCK_SIZE,
        "chunk_size": CHUNK_SIZE,
        "rows": rows,
        "decision": "ADVANCE_NO_CARRY_RELOCATION" if not failed else "REJECT_OR_REFORM",
        "scope": "Python writer-discovery falsifier only; aligned movement only; no native/product authority; no arbitrary byte-shift resynchronization claim",
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
