from __future__ import annotations

"""Frozen post-PrefixGraph reclaim attribution for the Shifted r25 RSS debt."""

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
WORKER = ROOT / "benchmarks" / "v030_r25_candidate_reclaim_rss_worker.py"
TARGET = ("resemblance_hostile_v1", "01_shifted_versions")
PREREG = "docs/v030-rnd/R25_CANDIDATE_RECLAIM_RSS_PREREG.md"
ORDER = (
    ("control", "gc", "trim"),
    ("trim", "gc", "control"),
    ("control", "trim", "gc"),
)


def _head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def _run(arm: str, source: Path, archive: Path) -> dict:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    proc = subprocess.run(
        [sys.executable, str(WORKER), "--arm", arm, "--source", str(source), "--archive", str(archive)],
        cwd=ROOT, env=env, capture_output=True, text=True,
    )
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    if proc.returncode or not lines:
        return {"worker_failed": True, "arm": arm, "returncode": proc.returncode,
                "stdout": proc.stdout, "stderr": proc.stderr}
    try:
        data = json.loads(lines[-1])
    except Exception as exc:
        return {"worker_failed": True, "arm": arm, "returncode": 0, "failure": f"json:{exc}",
                "stdout": proc.stdout, "stderr": proc.stderr}
    data["worker_failed"] = False
    return data


def _median(rows: list[dict], path: tuple[str, ...]) -> float:
    values = []
    for row in rows:
        value = row
        for key in path:
            value = value[key]
        values.append(float(value))
    return float(statistics.median(values))


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
        raise RuntimeError("candidate reclaim source drifted from accepted repaired Shifted authority")

    rows: list[dict] = []
    failures: list[dict] = []
    identities: set[tuple] = set()
    arm_counts = {"control": 0, "gc": 0, "trim": 0}

    for round_index, arms in enumerate(ORDER):
        for position, arm in enumerate(arms):
            arm_counts[arm] += 1
            archive = work_root / "archives" / f"round{round_index}-{position}-{arm}.cmpct"
            archive.parent.mkdir(parents=True, exist_ok=True)
            data = _run(arm, source, archive)
            data["round_index"] = round_index
            data["position"] = position
            rows.append(data)
            owners = data.get("semantic_owners") or {}
            obs = data.get("reclaim_observation") or {}
            ok = (
                not data.get("worker_failed")
                and data.get("arm") == arm
                and data.get("expected_verification_tree_sha256") == product_tree
                and data.get("tree_sha256") == product_tree
                and data.get("verification_identity_domain") == "canonical-filesystem-user-tree-v1"
                and data.get("research_identity_domain") == "research-content-tree-v1"
                and owners.get("identity_exact") is True
                and owners.get("pg") == "experiments._v030_canonical_prefixgraph"
                and owners.get("g04") == "experiments._v030_canonical_shared_portfolio"
                and owners.get("reader") == "experiments._v030_canonical_release_reader_policy"
                and data.get("executor_restored") is True
                and data.get("intercepted_prefixgraph_executor_constructions") == 1
                and data.get("intercepted_prefixgraph_submissions") == 1
                and data.get("r24_product_bytes") is not None
                and data.get("r25_product_bytes") is not None
                and int(obs.get("pre_action_vmrss_kib", 0)) > 0
                and int(obs.get("post_action_vmrss_kib", 0)) > 0
                and int(obs.get("retained_result_deep_bytes", 0)) > 0
            )
            if arm == "control":
                ok = ok and obs.get("gc_collected") is None and obs.get("malloc_trim_return") is None
            elif arm == "gc":
                ok = ok and isinstance(obs.get("gc_collected"), int) and obs.get("malloc_trim_return") is None
            else:
                ok = ok and isinstance(obs.get("gc_collected"), int) and obs.get("malloc_trim_return") in (0, 1)
            identity = tuple(data.get(key) for key in (
                "archive_bytes", "archive_sha256", "tree_sha256", "selected", "format_revision",
                "r24_product_bytes", "r25_product_bytes",
            ))
            identities.add(identity)
            if not ok:
                failures.append({"round": round_index, "position": position, **data})

    valid = not failures and arm_counts == {"control": 3, "gc": 3, "trim": 3} and len(identities) == 1
    by_arm = {arm: [row for row in rows if row.get("arm") == arm and not row.get("worker_failed")]
              for arm in ("control", "gc", "trim")}
    summaries: dict[str, dict] = {}
    for arm, arm_rows in by_arm.items():
        if len(arm_rows) != 3:
            continue
        summaries[arm] = {
            "median_peak_ru_maxrss_kib": _median(arm_rows, ("peak_ru_maxrss_kib",)),
            "median_wall_s": _median(arm_rows, ("wall_s",)),
            "median_pre_action_vmrss_kib": _median(arm_rows, ("reclaim_observation", "pre_action_vmrss_kib")),
            "median_post_action_vmrss_kib": _median(arm_rows, ("reclaim_observation", "post_action_vmrss_kib")),
            "median_vmrss_drop_kib": _median(arm_rows, ("reclaim_observation", "vmrss_drop_kib")),
            "median_retained_result_deep_bytes": _median(arm_rows, ("reclaim_observation", "retained_result_deep_bytes")),
        }

    derived = {}
    decision = "INVALID"
    if valid and set(summaries) == {"control", "gc", "trim"}:
        control_peak = summaries["control"]["median_peak_ru_maxrss_kib"]
        for arm in ("gc", "trim"):
            peak = summaries[arm]["median_peak_ru_maxrss_kib"]
            derived[f"{arm}_peak_reduction_fraction"] = max(0.0, control_peak - peak) / control_peak
            derived[f"{arm}_entry_reclaim_fraction"] = max(
                0.0,
                summaries[arm]["median_pre_action_vmrss_kib"] - summaries[arm]["median_post_action_vmrss_kib"],
            ) / control_peak
        derived["retained_result_fraction"] = (
            summaries["control"]["median_retained_result_deep_bytes"] / (control_peak * 1024.0)
        )
        if derived["gc_peak_reduction_fraction"] >= 0.20:
            decision = "PYTHON_GC_RECLAIMABLE_OWNER_SUPPORTED"
        elif derived["trim_peak_reduction_fraction"] >= 0.20:
            decision = "ALLOCATOR_TEMPORARY_RETENTION_SUPPORTED"
        elif derived["gc_peak_reduction_fraction"] < 0.10 and derived["trim_peak_reduction_fraction"] < 0.10:
            decision = "GENERIC_RECLAIM_RETIRED_AS_PRIMARY"
        else:
            decision = "AMBIGUOUS_RECLAIM_OWNERSHIP"

    return {
        "schema": "cmpct-v030-r25-candidate-reclaim-rss-v1",
        "source_commit": _head(),
        "preregistration": PREREG,
        "causal_predecessors": [
            "docs/v030-rnd/R25_CANDIDATE_SCHEDULING_RSS_V3_RESULT.md",
            "docs/v030-rnd/R25_PRODUCT_LIFETIME_RSS_PHASE_RESULT.md",
        ],
        "target": list(TARGET),
        "accepted_historical_tree_sha256": expected_historical_tree,
        "product_tree_sha256": product_tree,
        "run_order": [list(x) for x in ORDER],
        "rows": rows,
        "arm_counts": arm_counts,
        "summaries": summaries,
        "derived": derived,
        "decision": decision,
        "experiment_valid": valid,
        "worker_failures": failures,
        "release_credit": False,
        "contract": {
            "serialized_seam_diagnostic_only": True,
            "prefixgraph_result_retained_exactly": True,
            "deep_size_diagnostic_only": True,
            "live_vmrss_diagnostic_only": True,
            "ru_maxrss_decisive": True,
            "trim_linux_glibc_diagnostic_only": True,
            "exact_product_identity_required": True,
            "production_source_changed": False,
            "candidate_semantics_changed": False,
            "release_thresholds_changed": False,
            "decision_thresholds": {"support": 0.20, "retire": 0.10},
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r25-candidate-reclaim-rss-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r25-candidate-reclaim-rss.json"))
    args = parser.parse_args()
    data = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, indent=2) + "\n")
    print(json.dumps({key: data[key] for key in (
        "source_commit", "experiment_valid", "summaries", "derived", "decision")}, indent=2), flush=True)
    if not data["experiment_valid"]:
        raise SystemExit("candidate reclaim RSS evidence invalid")


if __name__ == "__main__":
    main()
