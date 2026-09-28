from __future__ import annotations

"""Whole-process-tree RSS companion for the promoted v0.30 product runtime gate.

This companion preserves ``benchmarks.v030_release_performance_product`` as the owner of
corpus generation, balanced v0.29/v0.30 execution order, identity checks, release-product
fingerprinting, and the frozen 1.25x RSS ceiling. It changes exactly one evidence boundary:
fresh operation workers are charged for the live worker plus every descendant process.

The 10 ms RSS sampler executes inside the operation window. Consequently timing values emitted
by this companion are diagnostic only. Release timing remains owned by the ordinary
uninstrumented product runtime court.
"""

import argparse
from collections import Counter
import json
from pathlib import Path

from benchmarks import v030_release_performance as BASE
from benchmarks import v030_release_performance_product as PRODUCT


TREE_WORKER = BASE.ROOT / "benchmarks" / "v030_perf_worker_tree_rss.py"
RSS_ACCOUNTING = "whole-process-tree-vmrss-10ms-with-parent-rumaxrss-floor"
SCHEMA = "cmpct-v030-release-product-tree-rss-v2"
SAMPLE_INTERVAL_S = 0.01


def _ratio(new: float, old: float) -> float:
    return float(new) / max(float(old), 1e-9)


def run(work_root: Path) -> dict:
    receipts: list[dict] = []
    original_worker = BASE.WORKER
    original_run_worker = BASE._run_worker

    def run_worker_with_tree_custody(*args: str) -> dict:
        result = dict(original_run_worker(*args))
        if result.get("rss_accounting") != RSS_ACCOUNTING:
            raise RuntimeError(
                f"whole-tree worker accounting drift: {result.get('rss_accounting')!r}"
            )

        samples = int(result.get("tree_rss_samples", 0))
        errors = list(result.get("tree_sampler_errors") or [])
        parent = int(result.get("parent_peak_rss_kib", -1))
        sampled = int(result.get("sampled_tree_peak_rss_kib", -1))
        decisive = int(result.get("peak_rss_kib", -1))
        peak_processes = int(result.get("tree_peak_processes", 0))
        sample_interval = float(result.get("sample_interval_s", -1.0))

        if samples < 1:
            raise RuntimeError("whole-tree worker produced no RSS samples")
        if errors:
            raise RuntimeError(f"whole-tree sampler errors: {errors!r}")
        if parent < 0 or sampled < 0 or decisive < 0:
            raise RuntimeError("whole-tree worker omitted RSS accounting fields")
        if decisive < parent or decisive < sampled:
            raise RuntimeError(
                "whole-tree decisive peak undercounted a measured owner: "
                f"decisive={decisive} parent={parent} sampled={sampled}"
            )
        if peak_processes < 1:
            raise RuntimeError("whole-tree sampler never observed the root process")
        if abs(sample_interval - SAMPLE_INTERVAL_S) > 1e-12:
            raise RuntimeError(
                f"whole-tree sampler interval drift: {sample_interval} != {SAMPLE_INTERVAL_S}"
            )

        receipts.append(
            {
                "engine": result.get("engine"),
                "op": result.get("op"),
                "parent_peak_rss_kib": parent,
                "sampled_tree_peak_rss_kib": sampled,
                "decisive_peak_rss_kib": decisive,
                "tree_rss_samples": samples,
                "tree_peak_processes": peak_processes,
                "sample_interval_s": sample_interval,
            }
        )
        return result

    try:
        BASE.WORKER = TREE_WORKER
        BASE._run_worker = run_worker_with_tree_custody
        paired = dict(PRODUCT.run(Path(work_root)))
    finally:
        BASE._run_worker = original_run_worker
        BASE.WORKER = original_worker

    expected_receipts = (
        len(BASE.TARGETS)
        * len(BASE.REPETITION_ORDER)
        * 2
        * 3
    )
    if len(receipts) != expected_receipts:
        raise RuntimeError(
            f"whole-tree receipt count drift: {len(receipts)} != {expected_receipts}"
        )

    counts = Counter((item["engine"], item["op"]) for item in receipts)
    expected_per_engine_op = len(BASE.TARGETS) * len(BASE.REPETITION_ORDER)
    for engine in ("v029", "v030"):
        for op in ("pack", "verify", "extract"):
            if counts[(engine, op)] != expected_per_engine_op:
                raise RuntimeError(
                    "whole-tree operation custody drift: "
                    f"{engine}/{op}={counts[(engine, op)]} != {expected_per_engine_op}"
                )

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
    inherited_contract = dict(paired["contract"])
    if float(inherited_contract["maximum_peak_rss_ratio"]) != BASE.MAX_PEAK_RSS_RATIO:
        raise RuntimeError("inherited product RSS ceiling drift")

    rss_gate = {
        "exact_target_count": len(rows) == len(BASE.TARGETS),
        "stable_historical_baseline_identity": all(
            len(row["historical_tree_sha256"]) == 64 for row in rows
        ),
        "stable_product_identity": all(
            len(row["product_tree_sha256"]) == 64 for row in rows
        ),
        "complete_operation_custody": len(receipts) == expected_receipts,
        "peak_rss_ratio": max_rss_ratio <= BASE.MAX_PEAK_RSS_RATIO,
    }
    rss_gate["passed"] = all(rss_gate.values())

    return {
        "schema": SCHEMA,
        "candidate_fingerprint": paired["candidate_fingerprint"],
        "engine": paired["engine"],
        "release_facade": paired["release_facade"],
        "contract": {
            "targets": [list(item) for item in BASE.TARGETS],
            "repetition_order": [list(item) for item in BASE.REPETITION_ORDER],
            "maximum_peak_rss_ratio": BASE.MAX_PEAK_RSS_RATIO,
            "rss_accounting": RSS_ACCOUNTING,
            "sample_interval_s": SAMPLE_INTERVAL_S,
            "worker": str(TREE_WORKER.relative_to(BASE.ROOT)),
            "timing_credit": False,
            "timing_authority": (
                "benchmarks/v030_release_performance_product.py with its "
                "canonical uninstrumented worker"
            ),
            "identity_rule": inherited_contract["identity_rule"],
        },
        "rows": rows,
        "totals": {"max_peak_rss_ratio": max_rss_ratio},
        "tree_rss_receipts": receipts,
        "rss_gate": rss_gate,
        "diagnostic_timing_gate": paired["gate"],
        "claim_boundary": (
            "same product-runtime target/order/identity/fingerprint with stronger "
            "whole-process-tree RSS custody; timing is diagnostic only"
        ),
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
                "rss_gate": result["rss_gate"],
            },
            indent=2,
        ),
        flush=True,
    )
    if not result["rss_gate"]["passed"]:
        raise SystemExit("v0.30 whole-process-tree RSS companion gate failed")


if __name__ == "__main__":
    main()
