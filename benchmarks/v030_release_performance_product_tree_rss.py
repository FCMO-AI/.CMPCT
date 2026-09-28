from __future__ import annotations

"""Whole-process-tree RSS companion for the promoted v0.30 product runtime gate.

The canonical release runtime harness owns corpus generation, balanced execution order,
candidate fingerprinting, source-tree validation, product verification, and the frozen
1.25x RSS ceiling. Its normal worker records only RUSAGE_SELF, which cannot see short-lived
descendant-process peaks in the current v0.30 architecture.

This companion changes exactly one evidence boundary: it reruns the same paired product harness
with v030_perf_worker_tree_rss.py so pack/extract memory is charged to the live worker plus all
descendants. Timing produced under the 10 ms sampler is diagnostic only and is deliberately not
emitted as release timing evidence. The ordinary uninstrumented runtime court remains the sole
timing authority.

A green result therefore means only: on the same candidate fingerprint and frozen target set,
whole-process-tree pack/extract peak RSS remains within the inherited 1.25x ratio ceiling.
"""

import argparse
import json
from pathlib import Path

from benchmarks import v030_release_performance as B
from benchmarks import v030_release_performance_product as PRODUCT


TREE_WORKER = B.ROOT / "benchmarks" / "v030_perf_worker_tree_rss.py"
RSS_ACCOUNTING = "whole-process-tree-vmrss-10ms-with-parent-rumaxrss-floor"
SCHEMA = "cmpct-v030-release-product-tree-rss-v1"


def _ratio(new: float, old: float) -> float:
    return float(new) / max(float(old), 1e-9)


def run(work_root: Path) -> dict:
    original_worker = B.WORKER
    try:
        B.WORKER = TREE_WORKER
        paired = PRODUCT.run(work_root)
    finally:
        B.WORKER = original_worker

    rows: list[dict] = []
    for row in paired["rows"]:
        repetitions = []
        for rep in row["repetitions"]:
            v029 = rep["v029"]
            v030 = rep["v030"]
            repetitions.append(
                {
                    "rep": int(rep["rep"]),
                    "execution_order": list(rep["execution_order"]),
                    "v029": {
                        "pack_peak_rss_kib": int(v029["pack_peak_rss_kib"]),
                        "extract_peak_rss_kib": int(v029["extract_peak_rss_kib"]),
                    },
                    "v030": {
                        "pack_peak_rss_kib": int(v030["pack_peak_rss_kib"]),
                        "extract_peak_rss_kib": int(v030["extract_peak_rss_kib"]),
                    },
                    "pack_rss_ratio": _ratio(
                        v030["pack_peak_rss_kib"], v029["pack_peak_rss_kib"]
                    ),
                    "extract_rss_ratio": _ratio(
                        v030["extract_peak_rss_kib"], v029["extract_peak_rss_kib"]
                    ),
                }
            )

        rows.append(
            {
                "suite": row["suite"],
                "name": row["name"],
                "historical_tree_sha256": row["historical_tree_sha256"],
                "product_tree_sha256": row["product_tree_sha256"],
                "repetitions": repetitions,
                "max_pack_rss_ratio": max(rep["pack_rss_ratio"] for rep in repetitions),
                "max_extract_rss_ratio": max(
                    rep["extract_rss_ratio"] for rep in repetitions
                ),
            }
        )

    max_rss_ratio = max(
        max(row["max_pack_rss_ratio"], row["max_extract_rss_ratio"]) for row in rows
    )
    gate = {
        "exact_target_count": len(rows) == len(B.TARGETS),
        "stable_historical_baseline_identity": all(
            len(row["historical_tree_sha256"]) == 64 for row in rows
        ),
        "stable_product_identity": all(
            len(row["product_tree_sha256"]) == 64 for row in rows
        ),
        "peak_rss_ratio": max_rss_ratio <= B.MAX_PEAK_RSS_RATIO,
    }
    gate["passed"] = all(gate.values())

    return {
        "schema": SCHEMA,
        "candidate_fingerprint": paired["candidate_fingerprint"],
        "engine": paired["engine"],
        "release_facade": paired["release_facade"],
        "contract": {
            "targets": [list(item) for item in B.TARGETS],
            "repetition_order": [list(item) for item in B.REPETITION_ORDER],
            "maximum_peak_rss_ratio": B.MAX_PEAK_RSS_RATIO,
            "rss_accounting": RSS_ACCOUNTING,
            "worker": str(TREE_WORKER.relative_to(B.ROOT)),
            "timing_credit": False,
            "timing_authority": "benchmarks/v030_release_performance_product.py with its canonical uninstrumented worker",
            "identity_rule": paired["contract"]["identity_rule"],
        },
        "rows": rows,
        "totals": {"max_peak_rss_ratio": max_rss_ratio},
        "gate": gate,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--work-root",
        type=Path,
        default=Path("benchmark-artifacts/v030-product-tree-rss-work"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("benchmark-artifacts/v030-product-tree-rss.json"),
    )
    args = parser.parse_args()

    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "candidate_fingerprint": result["candidate_fingerprint"],
                "totals": result["totals"],
                "gate": result["gate"],
            },
            indent=2,
        ),
        flush=True,
    )
    if not result["gate"]["passed"]:
        raise SystemExit("v0.30 whole-process-tree RSS companion gate failed")


if __name__ == "__main__":
    main()
