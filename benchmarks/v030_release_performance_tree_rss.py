from __future__ import annotations

"""Whole-process-tree RSS companion for the frozen v0.30 paired runtime authority.

The base harness still owns the exact three targets, balanced ordering, archive/tree checks and immutable
1.10/1.25 thresholds.  This binding swaps only the fresh operation worker for a companion that samples the
worker plus every live descendant during the exact pack/verify/extract operation window.  Parent RUSAGE_SELF
ru_maxrss remains a floor, so the stronger accounting can never make the inherited memory measurement smaller.
"""

import argparse
import json
from pathlib import Path

from benchmarks import v030_release_performance as B
from experiments import entropygraph_v030_release_product as PRODUCT
from tools import check_v030_release_lock as RELEASE_LOCK

SCHEMA = "cmpct-v030-release-performance-tree-rss-v1"
RSS_ACCOUNTING = "whole-process-tree-vmrss-10ms-with-parent-rumaxrss-floor"
B.WORKER = B.ROOT / "benchmarks" / "v030_perf_worker_tree_rss.py"


def _candidate_fingerprint() -> str:
    fingerprint, _ = RELEASE_LOCK.fingerprint(RELEASE_LOCK.load_manifest())
    return fingerprint


def _expected_tree(engine: str, source: Path, historical_expected: str) -> str:
    return PRODUCT.treehash(source) if engine == "v030" else historical_expected


B._expected_tree_for_engine = _expected_tree
_BASE_RUN_WORKER = B._run_worker
_RECEIPTS: list[dict] = []


def _run_worker_with_tree_receipt(*args: str) -> dict:
    result = _BASE_RUN_WORKER(*args)
    parent = int(result["parent_peak_rss_kib"])
    sampled = int(result["sampled_tree_peak_rss_kib"])
    decisive = int(result["peak_rss_kib"])
    if result.get("rss_accounting") != RSS_ACCOUNTING:
        raise RuntimeError("whole-tree worker accounting drift")
    if decisive < parent or decisive < sampled:
        raise RuntimeError("whole-tree decisive peak undercounted a measured owner")
    if int(result.get("tree_rss_samples", 0)) < 1:
        raise RuntimeError("whole-tree worker produced no RSS samples")
    if result.get("tree_sampler_errors"):
        raise RuntimeError(f"whole-tree sampler error: {result['tree_sampler_errors']!r}")
    _RECEIPTS.append(
        {
            "engine": result.get("engine"),
            "op": result.get("op"),
            "parent_peak_rss_kib": parent,
            "sampled_tree_peak_rss_kib": sampled,
            "decisive_peak_rss_kib": decisive,
            "tree_rss_samples": int(result["tree_rss_samples"]),
            "tree_peak_processes": int(result.get("tree_peak_processes", 0)),
            "sample_interval_s": float(result.get("sample_interval_s", 0.01)),
        }
    )
    return result


B._run_worker = _run_worker_with_tree_receipt


def run(work_root: Path) -> dict:
    fingerprint = _candidate_fingerprint()
    _RECEIPTS.clear()
    result = dict(B.run(work_root))
    result["schema"] = SCHEMA
    result["engine"] = "experiments/entropygraph_v030_release_product.py"
    result["release_facade"] = "cmpct-v030-release-product-v1"
    result["worker"] = "benchmarks/v030_perf_worker_tree_rss.py"
    result["identity_binding"] = "v029-historical-content-tree + v030-canonical-user-tree"
    result["candidate_fingerprint"] = fingerprint
    result["rss_accounting"] = RSS_ACCOUNTING
    result["tree_rss_contract"] = {
        "sample_interval_s": 0.01,
        "operation_window": "same pack/verify/extract timer boundary as v030_perf_worker_v2",
        "decisive_peak": "max(worker parent RUSAGE_SELF ru_maxrss, sampled live worker process-tree VmRSS)",
        "child_memory_gifted": False,
        "timing_boundary_changed": False,
        "peak_rss_threshold_changed": False,
        "release_credit": False,
    }
    result["tree_rss_receipts"] = list(_RECEIPTS)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-release-performance-tree-rss-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-release-performance-tree-rss.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"candidate_fingerprint": result["candidate_fingerprint"], "totals": result["totals"], "gate": result["gate"], "rss_accounting": result["rss_accounting"]}, indent=2), flush=True)
    if not result["gate"]["passed"]:
        raise SystemExit("v0.30 whole-process-tree RSS runtime promotion gate failed")


if __name__ == "__main__":
    main()
