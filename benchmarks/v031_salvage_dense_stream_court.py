#!/usr/bin/env python3
"""Held-out physically allocated input A/B against the original salvage scanner.

Separate workload from the sparse-source court so an apparent zero-page fast path
cannot explain the memory and throughput economics. No codec recovery is claimed.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import random
import statistics
import tempfile

from cmpct.codec import BHDR, BMAGIC, CODEC_RAW
from v031_salvage_stream_product_court import _observe


def main():
    with tempfile.TemporaryDirectory(prefix="cmpct-salvage-dense-") as td:
        path = Path(td) / "dense-physical.cmpct"
        n = 16 * 1024 * 1024
        raw = bytearray(random.Random(729042).randbytes(n))
        payload = b"candidate not authenticated"
        header = BHDR.pack(BMAGIC, CODEC_RAW, 0, 0, len(payload), len(payload),
                           0, 0, bytes([0x42]) * 32) + payload
        expected_offsets = [23, 1024 * 1024 - 31, 7 * 1024 * 1024 + 5, n - len(header) - 13]
        for off in expected_offsets:
            raw[off:off + len(header)] = header
        path.write_bytes(raw)
        digest = hashlib.sha256(raw).hexdigest()
        order = ["candidate", "inherited", "inherited", "candidate"] * 2
        samples = [_observe(path, mode) for mode in order]
        sha = {x["framing_sha256"] for x in samples}
        assert len(sha) == 1, "dense-source framing parity regression"
        counts = {x["record_count"] for x in samples}
        assert counts == {len(expected_offsets)}, counts
        r = {mode: [x for x in samples if x["mode"] == mode] for mode in ("inherited", "candidate")}
        assert max(x["rss_increment_kib"] for x in r["candidate"]) < 16 * 1024
        # A previous guard required >=14 MiB *delta* in ru_maxrss for the old
        # 16 MiB allocation. That is not a valid implication: ru_maxrss is a
        # process-lifetime maximum, so imports may already have set a higher
        # high-water mark. Compare the exact same installed-product algorithms
        # in separate, heap-instrumented child runs to test source allocations
        # directly. Do not time these profiled samples or relax the heap budget.
        heap_order = ["inherited", "candidate", "candidate", "inherited"] * 2
        heap_samples = [_observe(path, mode, profile_heap=True) for mode in heap_order]
        assert {x["framing_sha256"] for x in heap_samples} == sha
        assert {x["record_count"] for x in heap_samples} == counts
        h = {mode: [x["python_peak_heap_kib"] for x in heap_samples if x["mode"] == mode]
             for mode in ("inherited", "candidate")}
        assert min(h["inherited"]) >= 15 * 1024, h
        assert max(h["candidate"]) < 4 * 1024, h
        assert min(h["inherited"]) - max(h["candidate"]) > 12 * 1024, h
        med = {
            mode: {
                "cpu_ms": statistics.median(x["cpu_ns"] / 1e6 for x in r[mode]),
                "wall_ms": statistics.median(x["wall_ns"] / 1e6 for x in r[mode]),
                "incremental_peak_rss_mib": statistics.median(x["rss_increment_kib"] / 1024 for x in r[mode]),
            }
            for mode in r
        }
        print(json.dumps({
            "decision": "DENSE_SOURCE_CANDIDATE_PARITY_AND_RSS",
            "scope": "held-out physically allocated random bytes; not authenticated CMPCT recovery",
            "source_sha256": digest,
            "logical_bytes": n,
            "physically_allocated_bytes": path.stat().st_blocks * 512,
            "candidate_offsets": expected_offsets,
            "record_count": next(iter(counts)),
            "framing_sha256": next(iter(sha)),
            "raw_repeated_measurements": samples,
            "raw_independent_python_heap_measurements": heap_samples,
            "python_heap_guard": {
                "inherited_min_peak_mib": min(h["inherited"]) / 1024,
                "candidate_max_peak_mib": max(h["candidate"]) / 1024,
                "required_margin_mib": 12,
                "profiled_runs_excluded_from_timing": True,
            },
            "medians": med,
            "limitations": [
                "single high-entropy source",
                "Linux ru_maxrss high-water delta is not a reliable lower bound on allocations",
                "tracemalloc measures Python allocations, not native heap, mapped or page-cache memory",
                "raw ru_maxrss/CPU/wall preserved separately from tracemalloc profiles",
                "CPU/wall diagnostic; not full archive product performance",
                "header claims unverified, commit ancestry unproven",
            ],
        }, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
