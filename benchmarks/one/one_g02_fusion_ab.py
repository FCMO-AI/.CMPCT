"""ONE-G0.2 fused-vs-separated observation A/B instrument.

This isolates the engineering claim behind ONE-03: one fused source pass should expose
run + fixed-chunk reuse opportunities with less source traffic than two mechanism-like
rescans. It is Python reference evidence only; it does not claim native/product speed.
"""
from __future__ import annotations

import json
import os
import random
import statistics
import time

from experiments.one.observe import observe

REPETITIONS = 7
SIZE = 1024 * 1024
_FNV64_OFFSET = 0xCBF29CE484222325
_FNV64_PRIME = 0x100000001B3
_U64_MASK = (1 << 64) - 1


def _separate_observe(data: bytes, *, min_run: int = 8, chunk_size: int = 64, max_index_entries: int = 1 << 14) -> dict[str, int]:
    run_candidates = 0
    run_opportunity_bytes = 0
    if data:
        run_value = data[0]
        run_length = 0
        for value in data:
            if value == run_value:
                run_length += 1
            else:
                if run_length >= min_run:
                    run_candidates += 1
                    run_opportunity_bytes += run_length
                run_value = value
                run_length = 1
        if run_length >= min_run:
            run_candidates += 1
            run_opportunity_bytes += run_length

    index: dict[int, list[int]] = {}
    index_entries = 0
    reuse_candidates = 0
    reuse_opportunity_bytes = 0
    verifications = 0
    verification_read_bytes = 0
    chunk_hash = _FNV64_OFFSET
    for position, value in enumerate(data):
        chunk_hash ^= value
        chunk_hash = (chunk_hash * _FNV64_PRIME) & _U64_MASK
        if (position + 1) % chunk_size:
            continue
        start = position + 1 - chunk_size
        fingerprint = chunk_hash
        chunk_hash = _FNV64_OFFSET
        sources = index.get(fingerprint)
        matched = False
        if sources:
            for source in sources:
                verifications += 1
                verification_read_bytes += 2 * chunk_size
                if data[source : source + chunk_size] == data[start : start + chunk_size]:
                    reuse_candidates += 1
                    reuse_opportunity_bytes += chunk_size
                    matched = True
                    break
        if not matched and index_entries < max_index_entries:
            index.setdefault(fingerprint, []).append(start)
            index_entries += 1

    return {
        "run_candidates": run_candidates,
        "run_opportunity_bytes": run_opportunity_bytes,
        "reuse_candidates": reuse_candidates,
        "reuse_opportunity_bytes": reuse_opportunity_bytes,
        "collision_verifications": verifications,
        "verification_read_bytes": verification_read_bytes,
        "source_scan_bytes": 2 * len(data),
        "total_source_read_bytes": 2 * len(data) + verification_read_bytes,
    }


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
        fused_ns, fused_obj = _median_ns(lambda: observe(data, min_run=8, chunk_size=64, max_index_entries=1 << 14))
        separate_ns, separate_obj = _median_ns(lambda: _separate_observe(data))
        assert fused_obj is not None and separate_obj is not None
        fs = fused_obj.stats
        ss = separate_obj
        # The A/B must discover the same cheap opportunities; only scan organization differs.
        assert fs.run_candidates == ss["run_candidates"]
        assert fs.run_opportunity_bytes == ss["run_opportunity_bytes"]
        assert fs.reuse_candidates == ss["reuse_candidates"]
        assert fs.reuse_opportunity_bytes == ss["reuse_opportunity_bytes"]
        assert fs.collision_verifications == ss["collision_verifications"]
        assert fs.verification_read_bytes == ss["verification_read_bytes"]
        rows.append({
            "case": name,
            "input_bytes": len(data),
            "fused_median_ns": fused_ns,
            "separate_median_ns": separate_ns,
            "python_elapsed_ratio_fused_over_separate": fused_ns / separate_ns,
            "fused_source_scan_bytes": fs.source_scan_bytes,
            "separate_source_scan_bytes": ss["source_scan_bytes"],
            "source_scan_bytes_eliminated": ss["source_scan_bytes"] - fs.source_scan_bytes,
            "fused_total_source_read_bytes": fs.total_source_read_bytes,
            "separate_total_source_read_bytes": ss["total_source_read_bytes"],
            "total_source_read_reduction_fraction": 1.0 - (fs.total_source_read_bytes / ss["total_source_read_bytes"]),
            "run_opportunity_bytes": fs.run_opportunity_bytes,
            "reuse_opportunity_bytes": fs.reuse_opportunity_bytes,
        })
    return {
        "schema": "cmpct-one-g02-fusion-ab-v1",
        "experimental_version": "ONE-G0.2",
        "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
        "repetitions": REPETITIONS,
        "claim_boundary": "Python reference A/B; source-read reduction is algorithmic, elapsed ratio is not product-speed evidence",
        "rows": rows,
    }


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True, indent=2))
