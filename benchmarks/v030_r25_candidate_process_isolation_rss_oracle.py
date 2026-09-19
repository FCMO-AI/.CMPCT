from __future__ import annotations

"""Frozen whole-process-tree RSS A/B for PrefixGraph process isolation."""

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
WORKER = ROOT / "benchmarks" / "v030_r25_candidate_process_isolation_rss_worker.py"
TARGET = ("resemblance_hostile_v1", "01_shifted_versions")
PREREG = "docs/v030-rnd/R25_CANDIDATE_PROCESS_ISOLATION_RSS_PREREG.md"
ORDER = (
    ("shipping-control", "isolated-serialized-pg"),
    ("isolated-serialized-pg", "shipping-control"),
)


def _head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def _run(mode: str, source: Path, archive: Path) -> dict:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    proc = subprocess.run(
        [sys.executable, str(WORKER), "--mode", mode, "--source", str(source), "--archive", str(archive)],
        cwd=ROOT, env=env, capture_output=True, text=True,
    )
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    if proc.returncode or not lines:
        return {"worker_failed": True, "mode": mode, "returncode": proc.returncode,
                "stdout": proc.stdout, "stderr": proc.stderr}
    try:
        data = json.loads(lines[-1])
    except Exception as exc:
        return {"worker_failed": True, "mode": mode, "returncode": 0,
                "failure": f"json:{exc}", "stdout": proc.stdout, "stderr": proc.stderr}
    data["worker_failed"] = False
    return data


def _median(rows: list[dict], key: str) -> float:
    return float(statistics.median(float(row[key]) for row in rows))


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
        raise RuntimeError("process-isolation source drifted from accepted repaired Shifted authority")

    rows: list[dict] = []
    failures: list[dict] = []
    identities: set[tuple] = set()
    counts = {"shipping-control": 0, "isolated-serialized-pg": 0}

    for round_index, modes in enumerate(ORDER):
        for position, mode in enumerate(modes):
            counts[mode] += 1
            archive = work_root / "archives" / f"round{round_index}-{position}-{mode}.cmpct"
            archive.parent.mkdir(parents=True, exist_ok=True)
            data = _run(mode, source, archive)
            data["round_index"] = round_index
            data["position"] = position
            rows.append(data)
            owners = data.get("semantic_owners") or {}
            ok = (
                not data.get("worker_failed")
                and data.get("mode") == mode
                and data.get("expected_verification_tree_sha256") == product_tree
                and data.get("tree_sha256") == product_tree
                and data.get("verification_identity_domain") == "canonical-filesystem-user-tree-v1"
                and data.get("research_identity_domain") == "research-content-tree-v1"
                and owners.get("identity_exact") is True
                and owners.get("pg") == "experiments._v030_canonical_prefixgraph"
                and owners.get("g04") == "experiments._v030_canonical_shared_portfolio"
                and owners.get("reader") == "experiments._v030_canonical_release_reader_policy"
                and data.get("executor_restored") is True
                and data.get("r24_product_bytes") is not None
                and data.get("r25_product_bytes") is not None
                and data.get("selected") == "prefixgraph"
                and int(data.get("tree_peak_rss_kib", 0)) > 0
                and int(data.get("tree_samples", 0)) >= 100
                and data.get("tree_sampler_errors") == []
                and float(data.get("tree_sampler_interval_s", 1.0)) <= 0.01
            )
            if mode == "shipping-control":
                ok = ok and (
                    data.get("intercepted_prefixgraph_executor_constructions") == 0
                    and data.get("intercepted_prefixgraph_submissions") == 0
                    and data.get("isolated_children_launched") == 0
                    and data.get("isolated_child_returncodes") == []
                )
            else:
                ok = ok and (
                    data.get("intercepted_prefixgraph_executor_constructions") == 1
                    and data.get("intercepted_prefixgraph_submissions") == 1
                    and data.get("isolated_children_launched") == 1
                    and data.get("isolated_child_returncodes") == [0]
                    and len(data.get("isolated_child_archive_bytes") or []) == 1
                    and len(data.get("isolated_child_archive_sha256") or []) == 1
                )
            identity = tuple(data.get(key) for key in (
                "archive_bytes", "archive_sha256", "tree_sha256", "selected", "format_revision",
                "r24_product_bytes", "r25_product_bytes",
            ))
            identities.add(identity)
            if not ok:
                failures.append({"round": round_index, "position": position, **data})

    valid = not failures and counts == {"shipping-control": 2, "isolated-serialized-pg": 2} and len(identities) == 1
    summaries: dict[str, dict] = {}
    for mode in counts:
        mode_rows = [row for row in rows if row.get("mode") == mode and not row.get("worker_failed")]
        if len(mode_rows) != 2:
            continue
        summaries[mode] = {
            "median_tree_peak_rss_kib": _median(mode_rows, "tree_peak_rss_kib"),
            "median_parent_peak_ru_maxrss_kib": _median(mode_rows, "parent_peak_ru_maxrss_kib"),
            "median_wall_s": _median(mode_rows, "wall_s"),
            "median_tree_samples": _median(mode_rows, "tree_samples"),
            "max_tree_peak_processes": max(int(row["tree_peak_processes"]) for row in mode_rows),
        }

    derived: dict[str, float] = {}
    decision = "INVALID"
    if valid and set(summaries) == set(counts):
        control = summaries["shipping-control"]
        isolated = summaries["isolated-serialized-pg"]
        control_peak = control["median_tree_peak_rss_kib"]
        isolated_peak = isolated["median_tree_peak_rss_kib"]
        derived["tree_peak_reduction_fraction"] = max(0.0, control_peak - isolated_peak) / control_peak
        derived["wall_ratio"] = isolated["median_wall_s"] / control["median_wall_s"]
        if derived["tree_peak_reduction_fraction"] >= 0.20:
            decision = "PROCESS_LIFETIME_BOUNDARY_SUPPORTED"
            if derived["wall_ratio"] > 1.15:
                decision = "PROCESS_LIFETIME_BOUNDARY_SUPPORTED_WITH_MAJOR_CREATE_DEBT"
        elif derived["tree_peak_reduction_fraction"] < 0.10:
            decision = "PROCESS_ISOLATION_RETIRED_AS_PRIMARY"
        else:
            decision = "PROCESS_ISOLATION_AMBIGUOUS"

    return {
        "schema": "cmpct-v030-r25-candidate-process-isolation-rss-v1",
        "source_commit": _head(),
        "preregistration": PREREG,
        "causal_predecessors": [
            "docs/v030-rnd/R25_CANDIDATE_SCHEDULING_RSS_V3_RESULT.md",
            "docs/v030-rnd/R25_PRODUCT_LIFETIME_RSS_PHASE_RESULT.md",
            "docs/v030-rnd/R25_CANDIDATE_RECLAIM_RSS_RESULT.md",
        ],
        "target": list(TARGET),
        "accepted_historical_tree_sha256": expected_historical_tree,
        "product_tree_sha256": product_tree,
        "run_order": [list(x) for x in ORDER],
        "rows": rows,
        "arm_counts": counts,
        "summaries": summaries,
        "derived": derived,
        "decision": decision,
        "experiment_valid": valid,
        "worker_failures": failures,
        "release_credit": False,
        "contract": {
            "whole_process_tree_rss_decisive": True,
            "parent_ru_maxrss_diagnostic_only": True,
            "sampler_interval_s_max": 0.01,
            "min_samples_per_row": 100,
            "exact_product_identity_required": True,
            "prefixgraph_process_exit_before_g04": True,
            "production_source_changed": False,
            "candidate_semantics_changed": False,
            "release_thresholds_changed": False,
            "decision_thresholds": {"support": 0.20, "retire": 0.10, "major_wall_debt": 1.15},
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r25-candidate-process-isolation-rss-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r25-candidate-process-isolation-rss.json"))
    args = parser.parse_args()
    data = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, indent=2) + "\n")
    print(json.dumps({key: data[key] for key in (
        "source_commit", "experiment_valid", "summaries", "derived", "decision")}, indent=2), flush=True)
    if not data["experiment_valid"]:
        raise SystemExit("candidate process-isolation RSS evidence invalid")


if __name__ == "__main__":
    main()
