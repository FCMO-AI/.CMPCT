from __future__ import annotations

"""Frozen fresh-process A/B for outer genuine-r24-vs-r25 product lifetime RSS."""

import argparse
import json
import os
import shutil
import statistics
import subprocess
import sys
from pathlib import Path

from benchmarks import v030_release_generalization as GENERAL
from benchmarks import v030_release_performance as PERF
from experiments import entropygraph_v030_release_product as PRODUCT

ROOT = Path(__file__).resolve().parents[1]
WORKER = ROOT / "benchmarks" / "v030_r25_outer_product_scheduling_rss_worker.py"
ORDERS = (("concurrent", "serialized"), ("serialized", "concurrent"))
TARGET = ("resemblance_hostile_v1", "01_shifted_versions")
PREREG = "docs/v030-rnd/R25_OUTER_PRODUCT_SCHEDULING_RSS_PREREG.md"


def _head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def _run(mode: str, source: Path, archive: Path) -> dict:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    proc = subprocess.run(
        [sys.executable, str(WORKER), "--mode", mode, "--source", str(source), "--archive", str(archive)],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    if proc.returncode or not lines:
        return {
            "mode": mode,
            "worker_failed": True,
            "returncode": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
        }
    try:
        data = json.loads(lines[-1])
    except Exception as exc:
        return {
            "mode": mode,
            "worker_failed": True,
            "returncode": 0,
            "failure": f"json:{exc}",
            "stdout": proc.stdout,
            "stderr": proc.stderr,
        }
    data["worker_failed"] = False
    return data


def run(work_root: Path) -> dict:
    work_root = Path(work_root)
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)

    accepted = GENERAL._accepted_v029_rows()
    source = PERF._build_corpora(work_root / "corpora")[TARGET]
    expected_historical_tree = str(accepted[TARGET]["tree_sha256"])
    historical_tree = str(GENERAL._historical_treehash(source))
    product_tree = str(PRODUCT.treehash(source))
    if historical_tree != expected_historical_tree:
        raise RuntimeError("outer scheduling source drifted from accepted repaired Shifted authority")

    repetitions: list[dict] = []
    failures: list[dict] = []
    valid = True

    for round_index, order in enumerate(ORDERS):
        row = {"round": round_index, "execution_order": list(order)}
        for mode in order:
            archive = work_root / "archives" / f"r{round_index}-{mode}.cmpct"
            archive.parent.mkdir(parents=True, exist_ok=True)
            data = _run(mode, source, archive)
            row[mode] = data
            owners = data.get("semantic_owners") or {}
            ok = (
                not data.get("worker_failed")
                and data.get("expected_verification_tree_sha256") == product_tree
                and data.get("verified_tree_sha256", data.get("tree_sha256")) == product_tree
                and data.get("tree_sha256") == product_tree
                and data.get("verification_identity_domain") == "canonical-filesystem-user-tree-v1"
                and data.get("research_identity_domain") == "research-content-tree-v1"
                and owners.get("identity_exact") is True
                and owners.get("pg") == "experiments._v030_canonical_prefixgraph"
                and owners.get("g04") == "experiments._v030_canonical_shared_portfolio"
                and owners.get("reader") == "experiments._v030_canonical_release_reader_policy"
                and data.get("r24_product_bytes") is not None
                and data.get("r25_product_bytes") is not None
                and data.get("r25_attempted") is not False
                and data.get("r24_prebuild_executor_patched") is False
                and data.get("inner_r25_executor_patched") is False
                and data.get("canonical_executor_restored") is True
            )
            if mode == "serialized":
                ok = (
                    ok
                    and data.get("intercepted_product_executor_constructions") == 1
                    and data.get("intercepted_product_submissions") == 2
                )
            else:
                ok = (
                    ok
                    and data.get("intercepted_product_executor_constructions") == 0
                    and data.get("intercepted_product_submissions") == 0
                )
            if not ok:
                valid = False
                failures.append({"round": round_index, **data})

        concurrent = row["concurrent"]
        serialized = row["serialized"]
        if not concurrent.get("worker_failed") and not serialized.get("worker_failed"):
            identity_keys = (
                "archive_bytes",
                "archive_sha256",
                "tree_sha256",
                "selected",
                "format_revision",
                "r24_product_bytes",
                "r25_product_bytes",
            )
            if any(concurrent.get(key) != serialized.get(key) for key in identity_keys):
                valid = False
                failures.append({"round": round_index, "failure": "paired-complete-product-identity-mismatch"})
        repetitions.append(row)

    def median(mode: str, key: str) -> float:
        return statistics.median(float(row[mode][key]) for row in repetitions)

    concurrent_peak = median("concurrent", "peak_rss_kib")
    serialized_peak = median("serialized", "peak_rss_kib")
    concurrent_wall = median("concurrent", "wall_s")
    serialized_wall = median("serialized", "wall_s")
    reduction = (concurrent_peak - serialized_peak) / concurrent_peak if concurrent_peak else 0.0
    decision = (
        "supports-outer-r24-r25-lifetime-ownership"
        if reduction >= 0.20
        else "retires-outer-r24-r25-concurrency-primary-explanation"
        if reduction < 0.10
        else "ambiguous"
    )

    return {
        "schema": "cmpct-v030-r25-outer-product-scheduling-rss-v1",
        "source_commit": _head(),
        "preregistration": PREREG,
        "causal_predecessor": "docs/v030-rnd/R25_CANDIDATE_SCHEDULING_RSS_V3_RESULT.md",
        "target": list(TARGET),
        "accepted_historical_tree_sha256": expected_historical_tree,
        "product_tree_sha256": product_tree,
        "orders": [list(order) for order in ORDERS],
        "repetitions": repetitions,
        "concurrent_median_peak_rss_kib": int(concurrent_peak),
        "serialized_median_peak_rss_kib": int(serialized_peak),
        "serialized_peak_rss_reduction": reduction,
        "concurrent_median_wall_s": concurrent_wall,
        "serialized_median_wall_s": serialized_wall,
        "serialized_wall_ratio": serialized_wall / concurrent_wall if concurrent_wall else None,
        "decision": decision,
        "experiment_valid": valid,
        "worker_failures": failures,
        "release_credit": False,
        "contract": {
            "outer_product_executor_only": True,
            "r24_prebuild_overlap_unchanged": True,
            "inner_r25_scheduling_unchanged": True,
            "exact_complete_product_identity_required": True,
            "fresh_process_per_measurement": True,
            "total_peak_rss_is_causal_metric": True,
            "decision_thresholds_changed": False,
            "production_source_changed": False,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r25-outer-product-scheduling-rss-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r25-outer-product-scheduling-rss.json"))
    args = parser.parse_args()
    data = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, indent=2) + "\n")
    print(json.dumps({
        key: data[key]
        for key in (
            "source_commit",
            "experiment_valid",
            "concurrent_median_peak_rss_kib",
            "serialized_median_peak_rss_kib",
            "serialized_peak_rss_reduction",
            "concurrent_median_wall_s",
            "serialized_median_wall_s",
            "decision",
        )
    }, indent=2), flush=True)
    if not data["experiment_valid"]:
        raise SystemExit("outer product scheduling RSS evidence invalid")


if __name__ == "__main__":
    main()
