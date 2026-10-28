from __future__ import annotations

"""Frozen Shifted A/B for r24 process-lifetime ownership inside the v0.30 product."""

import argparse
import json
import os
from pathlib import Path
import shutil
import statistics
import subprocess
import sys

from benchmarks import v030_release_generalization as GENERAL
from benchmarks import v030_release_performance as PERF
from experiments import entropygraph_v030_release_product as PRODUCT

ROOT = Path(__file__).resolve().parents[1]
WORKER = ROOT / "benchmarks" / "v030_r25_r24_process_lifetime_rss_worker.py"
TARGET = ("resemblance_hostile_v1", "01_shifted_versions")
PREREG = "docs/v030-rnd/R25_R24_PROCESS_LIFETIME_RSS_PREREG.md"
REPETITIONS = 2
MODES = ("inherited", "same-parent-serialized", "r24-child-serialized")
MIN_TOTAL_SUPPORT = 0.20
MIN_PROCESS_LIFETIME_DELTA = 0.10
RETIRE_TOTAL = 0.10
RETIRE_PROCESS_DELTA = 0.05


def _head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def _worker(source: Path, archive: Path, mode: str) -> dict:
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
        return {"worker_failed": True, "returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr}
    try:
        row = json.loads(lines[-1])
    except Exception as exc:
        return {"worker_failed": True, "failure": f"json:{exc}", "stdout": proc.stdout, "stderr": proc.stderr}
    row["worker_failed"] = False
    return row


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    accepted = GENERAL._accepted_v029_rows()
    source = PERF._build_corpora(work_root / "corpora")[TARGET]
    expected_historical_tree = str(accepted[TARGET]["tree_sha256"])
    if str(GENERAL._historical_treehash(source)) != expected_historical_tree:
        raise RuntimeError("process-lifetime source drifted from accepted repaired Shifted authority")
    product_tree = str(PRODUCT.treehash(source))

    rows: list[dict] = []
    failures: list[dict] = []
    identities: set[tuple] = set()
    order = [MODES, tuple(reversed(MODES))]
    for rep in range(REPETITIONS):
        for mode in order[rep]:
            archive = work_root / "archives" / f"rep-{rep}-{mode}.cmpct"
            archive.parent.mkdir(parents=True, exist_ok=True)
            row = _worker(source, archive, mode)
            row["repetition"] = rep
            rows.append(row)
            owners = row.get("semantic_owners") or {}
            expected_child = 1 if mode == "r24-child-serialized" else 0
            expected_outer = 0 if mode == "inherited" else 1
            ok = (
                not row.get("worker_failed")
                and row.get("mode") == mode
                and row.get("tree_sha256") == product_tree
                and row.get("expected_verification_tree_sha256") == product_tree
                and row.get("selected") == "prefixgraph"
                and row.get("format_revision") == 25
                and row.get("r24_product_bytes") is not None
                and row.get("r25_product_bytes") is not None
                and int(row.get("tree_peak_rss_kib", 0)) > 0
                and int(row.get("tree_samples", 0)) >= 100
                and row.get("tree_sampler_errors") == []
                and float(row.get("tree_sampler_interval_s", 1.0)) <= 0.01
                and int(row.get("outer_executor_intercepts", -1)) == expected_outer
                and int(row.get("r24_child_launches", -1)) == expected_child
                and row.get("r24_child_returncodes") == ([0] if expected_child else [])
                and row.get("all_wrappers_restored") is True
                and owners.get("identity_exact") is True
                and owners.get("pg") == "experiments._v030_canonical_prefixgraph"
                and owners.get("g04") == "experiments._v030_canonical_shared_portfolio"
                and owners.get("reader") == "experiments._v030_canonical_release_reader_policy"
            )
            if mode != "inherited":
                ok = ok and row.get("outer_submissions") == 2
            identities.add(tuple(row.get(k) for k in (
                "archive_bytes", "archive_sha256", "tree_sha256", "selected",
                "format_revision", "r24_product_bytes", "r25_product_bytes"
            )))
            if not ok:
                failures.append({"repetition": rep, "mode": mode, **row})

    valid = not failures and len(rows) == REPETITIONS * len(MODES) and len(identities) == 1
    summary: dict[str, object] = {}
    decision = "INVALID"
    if valid:
        by_mode = {mode: [r for r in rows if r["mode"] == mode] for mode in MODES}
        med_peak = {
            mode: float(statistics.median(float(r["tree_peak_rss_kib"]) for r in by_mode[mode]))
            for mode in MODES
        }
        med_wall = {
            mode: float(statistics.median(float(r["wall_s"]) for r in by_mode[mode]))
            for mode in MODES
        }
        inherited = med_peak["inherited"]
        same = med_peak["same-parent-serialized"]
        child = med_peak["r24-child-serialized"]
        total_reduction = 1.0 - child / inherited
        process_delta = 1.0 - child / same
        same_reduction = 1.0 - same / inherited
        wall_ratio = med_wall["r24-child-serialized"] / med_wall["inherited"]
        if total_reduction >= MIN_TOTAL_SUPPORT and process_delta >= MIN_PROCESS_LIFETIME_DELTA:
            decision = "R24_PROCESS_LIFETIME_SUPPORTED"
        elif total_reduction < RETIRE_TOTAL or process_delta < RETIRE_PROCESS_DELTA:
            decision = "R24_PROCESS_LIFETIME_RETIRED_AS_PRIMARY"
        else:
            decision = "R24_PROCESS_LIFETIME_AMBIGUOUS"
        summary = {
            "median_tree_peak_rss_kib": med_peak,
            "median_wall_s": med_wall,
            "same_parent_serial_reduction_fraction": same_reduction,
            "child_serial_total_reduction_fraction": total_reduction,
            "child_vs_same_parent_process_lifetime_delta_fraction": process_delta,
            "child_serial_wall_ratio": wall_ratio,
        }

    return {
        "schema": "cmpct-v030-r25-r24-process-lifetime-rss-v1",
        "source_commit": _head(),
        "preregistration": PREREG,
        "causal_predecessor": "docs/v030-rnd/R25_PG_ISOLATED_R24_PREBUILD_BARRIER_RSS_RESULT.md",
        "target": list(TARGET),
        "accepted_historical_tree_sha256": expected_historical_tree,
        "product_tree_sha256": product_tree,
        "repetitions": REPETITIONS,
        "rows": rows,
        "summary": summary,
        "decision": decision,
        "experiment_valid": valid,
        "worker_failures": failures,
        "release_credit": False,
        "contract": {
            "whole_process_tree_rss_decisive": True,
            "parent_ru_maxrss_diagnostic_only": True,
            "sampler_interval_s_max": 0.01,
            "min_samples_per_row": 100,
            "same_source_and_exact_product_identity_required": True,
            "same_parent_serial_is_causal_control": True,
            "r24_child_must_exit_before_r25_starts": True,
            "minimum_total_support_fraction": MIN_TOTAL_SUPPORT,
            "minimum_process_lifetime_delta_fraction": MIN_PROCESS_LIFETIME_DELTA,
            "retire_total_below_fraction": RETIRE_TOTAL,
            "retire_process_delta_below_fraction": RETIRE_PROCESS_DELTA,
            "production_source_changed": False,
            "candidate_semantics_changed": False,
            "release_thresholds_changed": False,
        },
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r25-r24-process-lifetime-rss-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r25-r24-process-lifetime-rss.json"))
    a = p.parse_args()
    data = run(a.work_root)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(data, indent=2) + "\n")
    print(json.dumps({k: data[k] for k in ("source_commit", "experiment_valid", "summary", "decision")}, indent=2), flush=True)
    if not data["experiment_valid"]:
        raise SystemExit("r24 process-lifetime RSS evidence invalid")


if __name__ == "__main__":
    main()
