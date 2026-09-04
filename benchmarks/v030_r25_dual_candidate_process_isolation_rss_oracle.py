from __future__ import annotations

"""Frozen whole-process-tree RSS A/B for dual candidate process isolation."""

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
WORKER = ROOT / "benchmarks" / "v030_r25_dual_candidate_process_isolation_rss_worker.py"
TARGET = ("resemblance_hostile_v1", "01_shifted_versions")
PREREG = "docs/v030-rnd/R25_DUAL_CANDIDATE_PROCESS_ISOLATION_RSS_PREREG.md"
ORDER = (("pg-isolated-control", "dual-isolated"), ("dual-isolated", "pg-isolated-control"))


def _head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def _run(mode: str, source: Path, archive: Path) -> dict:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    proc = subprocess.run([sys.executable, str(WORKER), "--mode", mode, "--source", str(source), "--archive", str(archive)], cwd=ROOT, env=env, capture_output=True, text=True)
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    if proc.returncode or not lines:
        return {"worker_failed": True, "mode": mode, "returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr}
    try:
        data = json.loads(lines[-1])
    except Exception as exc:
        return {"worker_failed": True, "mode": mode, "failure": f"json:{exc}", "stdout": proc.stdout, "stderr": proc.stderr}
    data["worker_failed"] = False
    return data


def _median(rows: list[dict], key: str) -> float:
    return float(statistics.median(float(r[key]) for r in rows))


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    accepted = GENERAL._accepted_v029_rows()
    source = PERF._build_corpora(work_root / "corpora")[TARGET]
    expected_historical_tree = str(accepted[TARGET]["tree_sha256"])
    if str(GENERAL._historical_treehash(source)) != expected_historical_tree:
        raise RuntimeError("dual-isolation source drifted from accepted repaired Shifted authority")
    product_tree = str(PRODUCT.treehash(source))

    rows: list[dict] = []
    failures: list[dict] = []
    identities: set[tuple] = set()
    counts = {"pg-isolated-control": 0, "dual-isolated": 0}
    for round_index, modes in enumerate(ORDER):
        for position, mode in enumerate(modes):
            counts[mode] += 1
            archive = work_root / "archives" / f"r{round_index}-{position}-{mode}.cmpct"
            archive.parent.mkdir(parents=True, exist_ok=True)
            data = _run(mode, source, archive)
            data.update(round_index=round_index, position=position)
            rows.append(data)
            owners = data.get("semantic_owners") or {}
            ok = (
                not data.get("worker_failed")
                and data.get("tree_sha256") == product_tree
                and data.get("expected_verification_tree_sha256") == product_tree
                and data.get("selected") == "prefixgraph"
                and data.get("r24_product_bytes") is not None and data.get("r25_product_bytes") is not None
                and int(data.get("tree_peak_rss_kib", 0)) > 0
                and int(data.get("tree_samples", 0)) >= 100
                and data.get("tree_sampler_errors") == []
                and float(data.get("tree_sampler_interval_s", 1.0)) <= 0.01
                and data.get("prefixgraph_executor_intercepts") == 1
                and data.get("prefixgraph_submissions") == 1
                and data.get("prefixgraph_children") == 1
                and data.get("prefixgraph_returncodes") == [0]
                and data.get("executor_restored") is True
                and data.get("g04_build_restored") is True
                and owners.get("identity_exact") is True
                and owners.get("pg") == "experiments._v030_canonical_prefixgraph"
                and owners.get("g04") == "experiments._v030_canonical_shared_portfolio"
                and owners.get("reader") == "experiments._v030_canonical_release_reader_policy"
            )
            if mode == "dual-isolated":
                ok = ok and data.get("g04_children") == 1 and data.get("g04_returncodes") == [0]
            else:
                ok = ok and data.get("g04_children") == 0 and data.get("g04_returncodes") == []
            identities.add(tuple(data.get(k) for k in ("archive_bytes","archive_sha256","tree_sha256","selected","format_revision","r24_product_bytes","r25_product_bytes")))
            if not ok:
                failures.append({"round": round_index, "position": position, **data})

    valid = not failures and counts == {"pg-isolated-control": 2, "dual-isolated": 2} and len(identities) == 1
    summaries: dict[str, dict] = {}
    for mode in counts:
        rs = [r for r in rows if r.get("mode") == mode and not r.get("worker_failed")]
        if len(rs) == 2:
            summaries[mode] = {
                "median_tree_peak_rss_kib": _median(rs, "tree_peak_rss_kib"),
                "median_parent_peak_ru_maxrss_kib": _median(rs, "parent_peak_ru_maxrss_kib"),
                "median_wall_s": _median(rs, "wall_s"),
                "median_tree_samples": _median(rs, "tree_samples"),
                "max_tree_peak_processes": max(int(r["tree_peak_processes"]) for r in rs),
            }
    derived: dict[str, float] = {}
    decision = "INVALID"
    if valid and len(summaries) == 2:
        c, d = summaries["pg-isolated-control"], summaries["dual-isolated"]
        derived["incremental_tree_peak_reduction_fraction"] = max(0.0, c["median_tree_peak_rss_kib"] - d["median_tree_peak_rss_kib"]) / c["median_tree_peak_rss_kib"]
        derived["wall_ratio"] = d["median_wall_s"] / c["median_wall_s"]
        reduction = derived["incremental_tree_peak_reduction_fraction"]
        if reduction >= 0.20:
            decision = "G04_PROCESS_LIFETIME_SUPPORTED_WITH_ADDITIONAL_CREATE_DEBT" if derived["wall_ratio"] > 1.10 else "G04_PROCESS_LIFETIME_SUPPORTED"
        elif reduction < 0.10:
            decision = "G04_PROCESS_LIFETIME_RETIRED_AS_PRIMARY"
        else:
            decision = "G04_PROCESS_LIFETIME_AMBIGUOUS"
    return {
        "schema": "cmpct-v030-r25-dual-candidate-process-isolation-rss-v1",
        "source_commit": _head(),
        "preregistration": PREREG,
        "causal_predecessor": "docs/v030-rnd/R25_CANDIDATE_PROCESS_ISOLATION_RSS_V2_RESULT.md",
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
            "pg_child_exit_before_g04": True,
            "dual_g04_child_exit_before_selection": True,
            "production_source_changed": False,
            "candidate_semantics_changed": False,
            "release_thresholds_changed": False,
            "decision_thresholds": {"support": 0.20, "retire": 0.10, "additional_wall_debt": 1.10},
        },
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r25-dual-candidate-process-isolation-rss-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r25-dual-candidate-process-isolation-rss.json"))
    a = p.parse_args()
    data = run(a.work_root)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(data, indent=2) + "\n")
    print(json.dumps({k: data[k] for k in ("source_commit","experiment_valid","summaries","derived","decision")}, indent=2), flush=True)
    if not data["experiment_valid"]:
        raise SystemExit("dual candidate process-isolation evidence invalid")


if __name__ == "__main__":
    main()
