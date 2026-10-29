"""J24G47 bounded representation-level cost court for journal fsmeta rekey.

This is *not* a full archive create/extract or RSS product benchmark.
Rows are synthetic abstract metadata rows, not a public workload score.
Records median CPU/wall and tracemalloc peak over the same actual helper
used by the installed Reader/Writer. Raw repeated measurements retained.
"""
from __future__ import annotations

import copy
import json
import statistics
import sys
import time
import tracemalloc
from pathlib import Path

from cmpct.reader import _apply_journal_ops


def index_with_sparse_metadata(count: int) -> dict:
    rows = [[f"member-{i:06d}", 0] for i in range(count)]
    return {
        "files": rows,
        "fsmeta": {
            "owner": [501, 20],
            "owner_overrides": [[i, 1000 + i, 20] for i in range(0, count, 100)],
            "xattrs": [[i, [["user.test", b"value\x00"]]] for i in range(1, count, 137)],
        },
    }


def metric(source: dict, op: list, repeats=7) -> dict:
    wall_ns, cpu_ns, allocation_peak_bytes = [], [], []
    for _ in range(repeats):
        data = copy.deepcopy(source)
        tracemalloc.start()
        wall_start = time.perf_counter_ns()
        cpu_start = time.process_time_ns()
        _apply_journal_ops(data, [op])
        cpu_ns.append(time.process_time_ns() - cpu_start)
        wall_ns.append(time.perf_counter_ns() - wall_start)
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        allocation_peak_bytes.append(peak)
        names = [row[0] for row in data["files"]]
        if names != sorted(names) or len(names) != len(set(names)):
            raise AssertionError("invalid post-operation index")
        # Sparse owner exceptions must remain attached to original names.
        by_owner = {names[rec[0]]: rec[1:] for rec in data["fsmeta"]["owner_overrides"]}
        assert by_owner["member-000100"] == [1100, 20]
    return {
        "wall_ns_samples": wall_ns,
        "cpu_ns_samples": cpu_ns,
        "peak_allocated_bytes_samples": allocation_peak_bytes,
        "median_wall_ns": statistics.median(wall_ns),
        "median_cpu_ns": statistics.median(cpu_ns),
        "max_peak_allocated_bytes": max(allocation_peak_bytes),
    }


def main(output: Path) -> None:
    results = {
        "court": "J24G47 abstract index helper overhead only",
        "python": sys.version,
        "not_product_benchmark": True,
        "repeats": 7,
        "records": [],
    }
    for n in (1000, 10000):
        source = index_with_sparse_metadata(n)
        for scenario, op in (
            ("stable_same_member_put", ["put", ["member-000500", 1]]),
            ("lexical_insert_permutation", ["put", ["000-new-before", 1]]),
            ("rename_reorders", ["ren", f"member-{n-1:06d}", "000-new-name"]),
        ):
            result = metric(source, op)
            results["records"].append({
                "logical_rows": n,
                "sparse_owner_records": len(source["fsmeta"]["owner_overrides"]),
                "sparse_xattr_records": len(source["fsmeta"]["xattrs"]),
                "scenario": scenario,
                **result,
            })
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "court": results["court"],
        "records": [
            {"rows": v["logical_rows"], "case": v["scenario"],
             "median_ms": round(v["median_wall_ns"] / 1e6, 3),
             "peak_bytes": v["max_peak_allocated_bytes"]}
            for v in results["records"]
        ],
    }, sort_keys=True))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
