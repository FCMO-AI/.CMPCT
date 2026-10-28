"""J24K09b fully charged immutable-snapshot session ownership oracle.

This is NOT a safe concurrent-mutation product cache. Every cached size is
proven from the actual physical BHDR through the unchanged Reader witness.
All preprocessing is included in the timing, and extra list bytes are charged.
"""
from __future__ import annotations

import json
import statistics
import sys
import time
import zipfile

from cmpct.codec import range_vzip
from j24k09_physical_witness_economics import fixture


def run_session(reader, contents, recipe, q, strategy):
    n = len(recipe[2])
    offset = n*64+6
    def get_content(idx):
        return contents[idx]
    def get_stream(*args):
        raise AssertionError("STORED stream cannot require Deflate")
    t0 = time.perf_counter_ns()
    cpu0 = time.process_time_ns()
    cache_bytes = 0
    if strategy == "per_session_verified":
        # Fully charge every physical size proof before the first query.
        physical = [reader._vzip_physical_stream_size(zipfile.ZIP_STORED, 0, i, i)
                    for i in range(1, n+1)]
        assert all(size == 64 for size in physical)
        cache_bytes = sys.getsizeof(physical) + sum(sys.getsizeof(v) for v in physical)
        def physical_size(method, mode, rawref, streamref):
            assert method == zipfile.ZIP_STORED and mode == 0
            return physical[rawref-1]
    elif strategy == "per_query_physical":
        physical_size = reader._vzip_physical_stream_size
    elif strategy == "unsafe_no_witness":
        physical_size = None
    else:
        raise ValueError(strategy)
    for _ in range(q):
        assert range_vzip(recipe, get_content, get_stream,
                          offset, 1, physical_size) == b"G"
    wall_ns = time.perf_counter_ns() - t0
    cpu_ns = time.process_time_ns() - cpu0
    return {"wall_ns": wall_ns, "cpu_ns": cpu_ns,
            "extra_cache_bytes": cache_bytes}


def main():
    strategies = ("per_query_physical", "per_session_verified", "unsafe_no_witness")
    for n in (64, 512, 4096):
        reader, contents, recipe = fixture(n)
        for q in (1, 8, 64):
            raw = {strategy: [] for strategy in strategies}
            for cycle in range(5):
                # ABBA per safe pair, followed by unsafe isolated lower bound.
                order = ("per_query_physical", "per_session_verified",
                         "per_session_verified", "per_query_physical",
                         "unsafe_no_witness")
                if cycle % 2:
                    order = ("per_session_verified", "per_query_physical",
                             "per_query_physical", "per_session_verified",
                             "unsafe_no_witness")
                for strategy in order:
                    raw[strategy].append(run_session(
                        reader, contents, recipe, q, strategy))
            med = {
                strategy: {
                    key: statistics.median(row[key] for row in raw[strategy])
                    for key in ("wall_ns", "cpu_ns", "extra_cache_bytes")
                } for strategy in strategies
            }
            print("J24K09B_SESSION=" + json.dumps({
                "class": "immovable_source_snapshot_oracle_not_product",
                "streams": n, "queries": q,
                "physically_charged_prevalidation": True,
                "unsafe_control_no_product_credit": True,
                "concurrent_same_inode_cache_invalidity_unresolved": True,
                "medians": med, "raw": raw
            }, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
