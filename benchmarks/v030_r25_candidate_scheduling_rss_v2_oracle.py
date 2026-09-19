from __future__ import annotations

import argparse
import json
import os
import shutil
import statistics
import subprocess
import sys
from pathlib import Path

from benchmarks import v030_release_performance as PERF
from experiments import entropygraph_v030_canonical_final as CANONICAL

ROOT = Path(__file__).resolve().parents[1]
WORKER = ROOT / "benchmarks" / "v030_r25_candidate_scheduling_rss_v2_worker.py"
ORDERS = (("concurrent", "serialized"), ("serialized", "concurrent"))
TARGET = ("resemblance_hostile_v1", "01_shifted_versions")


def _head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def _run(mode: str, source: Path, archive: Path) -> dict:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    completed = subprocess.run(
        [sys.executable, str(WORKER), "--mode", mode, "--source", str(source), "--archive", str(archive)],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    if completed.returncode or not lines:
        return {
            "mode": mode,
            "worker_failed": True,
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        }
    try:
        data = json.loads(lines[-1])
    except Exception as exc:
        return {
            "mode": mode,
            "worker_failed": True,
            "returncode": 0,
            "failure": f"json:{exc}",
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        }
    data["worker_failed"] = False
    return data


def run(root: Path) -> dict:
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True)
    corpora = PERF._build_corpora(root / "corpora")
    source = corpora[TARGET]

    research_tree = str(CANONICAL.RC.treehash(source))
    expected_product_tree = str(CANONICAL.treehash(source))
    repetitions: list[dict] = []
    failures: list[dict] = []
    valid = True

    for round_index, order in enumerate(ORDERS):
        row: dict = {"round": round_index, "execution_order": list(order)}
        for mode in order:
            archive = root / "archives" / f"r{round_index}-{mode}.cmpct"
            archive.parent.mkdir(parents=True, exist_ok=True)
            data = _run(mode, source, archive)
            row[mode] = data
            owners = data.get("semantic_owners") or {}
            ok = (
                not data.get("worker_failed")
                and data.get("research_tree_sha256") == research_tree
                and data.get("research_identity_domain") == "research-content-tree-v1"
                and data.get("expected_verification_tree_sha256") == expected_product_tree
                and data.get("verification_identity_domain") == "canonical-filesystem-user-tree-v1"
                and data.get("verified_tree_sha256") == expected_product_tree
                and data.get("tree_sha256") == expected_product_tree
                and owners.get("identity_exact") is True
                and owners.get("pg") == "experiments._v030_canonical_prefixgraph"
                and owners.get("g04") == "experiments._v030_canonical_shared_portfolio"
                and owners.get("reader") == "experiments._v030_canonical_release_reader_policy"
                and data.get("selected") == "prefixgraph"
            )
            if mode == "serialized":
                ok = ok and data.get("inline_executor_submissions") == 2
            if not ok:
                valid = False
                failures.append({"round": round_index, **data})

        concurrent = row["concurrent"]
        serialized = row["serialized"]
        if not concurrent.get("worker_failed") and not serialized.get("worker_failed"):
            if (
                concurrent.get("archive_bytes") != serialized.get("archive_bytes")
                or concurrent.get("archive_sha256") != serialized.get("archive_sha256")
                or concurrent.get("verified_tree_sha256") != serialized.get("verified_tree_sha256")
                or concurrent.get("selected") != serialized.get("selected")
            ):
                valid = False
                failures.append({"round": round_index, "failure": "paired-product-identity-mismatch"})
        repetitions.append(row)

    def median(mode: str, key: str) -> float:
        return statistics.median(float(row[mode][key]) for row in repetitions)

    concurrent_peak = median("concurrent", "peak_rss_kib")
    serialized_peak = median("serialized", "peak_rss_kib")
    concurrent_wall = median("concurrent", "wall_s")
    serialized_wall = median("serialized", "wall_s")
    reduction = (concurrent_peak - serialized_peak) / concurrent_peak if concurrent_peak else 0.0

    if reduction >= 0.20:
        decision = "supports-concurrency-lifetime-ownership"
    elif reduction < 0.10:
        decision = "retires-concurrency-primary-explanation"
    else:
        decision = "ambiguous"

    return {
        "schema": "cmpct-v030-r25-candidate-scheduling-rss-v2",
        "source_commit": _head(),
        "preregistration": "docs/v030-rnd/R25_CANDIDATE_SCHEDULING_RSS_V2_PREREG.md",
        "supersedes": {
            "record": "docs/v030-rnd/R25_CANDIDATE_SCHEDULING_RSS_V1_INVALID_RESULT.md",
            "v1_source": "81b64517271baf4efa534ae1cadfa96d0b02c6d8",
            "v1_workflow_run": 33594786248,
            "v1_artifact_id": 9833258503,
            "reason": "v1 compared canonical filesystem/user-tree verification against research-content tree identity",
        },
        "target": list(TARGET),
        "research_tree_sha256": research_tree,
        "expected_verification_tree_sha256": expected_product_tree,
        "verification_identity_domain": "canonical-filesystem-user-tree-v1",
        "research_identity_domain": "research-content-tree-v1",
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
            "exact_product_identity_required": True,
            "dual_identity_domains_explicit": True,
            "fresh_process_per_measurement": True,
            "total_peak_rss_is_causal_metric": True,
            "baseline_subtracted_ru_maxrss_is_diagnostic_only": True,
            "production_source_changed": False,
            "selector_changed": False,
            "admission_changed": False,
            "grammar_changed": False,
            "integrity_changed": False,
            "locality_changed": False,
            "recovery_changed": False,
            "decision_thresholds_changed_from_v1": False,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--work-root",
        type=Path,
        default=Path("benchmark-artifacts/v030-r25-candidate-scheduling-rss-v2-work"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("benchmark-artifacts/v030-r25-candidate-scheduling-rss-v2.json"),
    )
    args = parser.parse_args()
    data = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, indent=2) + "\n")
    print(
        json.dumps(
            {
                key: data[key]
                for key in (
                    "source_commit",
                    "experiment_valid",
                    "research_tree_sha256",
                    "expected_verification_tree_sha256",
                    "concurrent_median_peak_rss_kib",
                    "serialized_median_peak_rss_kib",
                    "serialized_peak_rss_reduction",
                    "concurrent_median_wall_s",
                    "serialized_median_wall_s",
                    "decision",
                )
            },
            indent=2,
        )
    )
    if not data["experiment_valid"]:
        raise SystemExit("candidate scheduling RSS v2 evidence invalid")


if __name__ == "__main__":
    main()
