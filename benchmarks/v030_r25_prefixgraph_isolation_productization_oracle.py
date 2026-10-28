from __future__ import annotations

"""Frozen S6 Hostile Reviewer for the integrated PrefixGraph isolation Builder seam."""

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
from experiments import entropygraph_v030_canonical_final as CANONICAL

ROOT = Path(__file__).resolve().parents[1]
WORKER = ROOT / "benchmarks" / "v030_r25_prefixgraph_isolation_productization_worker.py"
TARGET = ("resemblance_hostile_v1", "01_shifted_versions")
PREREG = "docs/v030-rnd/R25_PREFIXGRAPH_ISOLATION_PRODUCTIZATION_PREREG.md"
ORDER = (("control", "candidate"), ("candidate", "control"))
R24_BYTES = 29_883_732


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
            "worker_failed": True,
            "mode": mode,
            "returncode": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
        }
    try:
        row = json.loads(lines[-1])
    except Exception as exc:
        return {
            "worker_failed": True,
            "mode": mode,
            "returncode": 0,
            "failure": f"json:{exc}",
            "stdout": proc.stdout,
            "stderr": proc.stderr,
        }
    row["worker_failed"] = False
    return row


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
    product_tree = str(CANONICAL.treehash(source))
    if historical_tree != expected_historical_tree:
        raise RuntimeError("S6 source drifted from accepted repaired Shifted authority")

    rows: list[dict] = []
    failures: list[dict] = []
    counts = {"control": 0, "candidate": 0}
    for round_index, modes in enumerate(ORDER):
        for position, mode in enumerate(modes):
            counts[mode] += 1
            archive = work_root / "archives" / f"round{round_index}-{position}-{mode}.cmpct"
            archive.parent.mkdir(parents=True, exist_ok=True)
            row = _run(mode, source, archive)
            row["round_index"] = round_index
            row["position"] = position
            rows.append(row)
            receipt = row.get("prefixgraph_process_receipt") or {}
            common_ok = (
                not row.get("worker_failed")
                and row.get("mode") == mode
                and row.get("expected_tree_sha256") == product_tree
                and row.get("tree_sha256") == product_tree
                and row.get("r25_selected") == "prefixgraph"
                and int(row.get("r24_product_bytes", -1)) == R24_BYTES
                and row.get("selected") == "prefixgraph"
                and int(row.get("format_revision", -1)) == 25
                and int(row.get("tree_peak_rss_kib", 0)) > 0
                and int(row.get("tree_samples", 0)) >= 100
                and row.get("tree_sampler_errors") == []
                and float(row.get("tree_sampler_interval_s", 1.0)) <= 0.01
                and row.get("canonical_r25_build_restored") is True
                and row.get("executor_restored") is True
            )
            if mode == "candidate":
                common_ok = common_ok and (
                    row.get("r25_candidate_scheduler") == "prefixgraph-process-level15-then-g04-main-v1"
                    and row.get("audited_executor_constructions") == 1
                    and row.get("audited_executor_submissions") == 1
                    and row.get("audited_child_dead_on_submit_return") == [True]
                    and receipt.get("schema") == "cmpct-v030-prefixgraph-process-executor-v1"
                    and receipt.get("semantic_owner") == "experiments._v030_canonical_prefixgraph"
                    and int(receipt.get("prefix_level", -1)) == 15
                    and int(receipt.get("archive_bytes", -1)) > 0
                    and isinstance(receipt.get("archive_sha256"), str)
                    and len(receipt.get("archive_sha256", "")) == 64
                )
            else:
                common_ok = common_ok and (
                    row.get("r25_candidate_scheduler") == "g04-main-plus-one-prefixgraph-worker-v2"
                    and row.get("prefixgraph_process_receipt") is None
                )
            if not common_ok:
                failures.append({"round": round_index, "position": position, **row})

    hostile_rows = []
    for index, mode in enumerate(("missing-helper", "malformed-receipt")):
        archive = work_root / "hostile" / f"{index}-{mode}.cmpct"
        archive.parent.mkdir(parents=True, exist_ok=True)
        row = _run(mode, source, archive)
        hostile_rows.append(row)
        if row.get("worker_failed") or row.get("mode") != mode or row.get("failed_closed") is not True:
            failures.append({"hostile": mode, **row})

    summaries: dict[str, dict] = {}
    deterministic: dict[str, bool] = {}
    for mode in ("control", "candidate"):
        mode_rows = [row for row in rows if row.get("mode") == mode and not row.get("worker_failed")]
        identities = {
            tuple(row.get(key) for key in (
                "archive_bytes", "archive_sha256", "tree_sha256", "selected", "format_revision",
                "r24_product_bytes", "r25_product_bytes", "r25_selected",
            ))
            for row in mode_rows
        }
        deterministic[mode] = len(mode_rows) == 2 and len(identities) == 1
        if len(mode_rows) == 2:
            summaries[mode] = {
                "archive_bytes": int(mode_rows[0]["archive_bytes"]),
                "archive_sha256": mode_rows[0]["archive_sha256"],
                "r24_product_bytes": int(mode_rows[0]["r24_product_bytes"]),
                "r25_product_bytes": int(mode_rows[0]["r25_product_bytes"]),
                "median_tree_peak_rss_kib": _median(mode_rows, "tree_peak_rss_kib"),
                "median_parent_peak_ru_maxrss_kib": _median(mode_rows, "parent_peak_ru_maxrss_kib"),
                "median_wall_s": _median(mode_rows, "wall_s"),
                "median_tree_samples": _median(mode_rows, "tree_samples"),
                "deterministic": deterministic[mode],
            }

    valid = (
        not failures
        and counts == {"control": 2, "candidate": 2}
        and set(summaries) == {"control", "candidate"}
        and all(deterministic.values())
        and all(row.get("failed_closed") is True for row in hostile_rows)
    )

    derived: dict[str, float | int | bool] = {}
    decision = "INVALID_PRODUCTIZATION_RECEIPT"
    if valid:
        control = summaries["control"]
        candidate = summaries["candidate"]
        control_peak = float(control["median_tree_peak_rss_kib"])
        candidate_peak = float(candidate["median_tree_peak_rss_kib"])
        control_wall = float(control["median_wall_s"])
        candidate_wall = float(candidate["median_wall_s"])
        size_penalty = int(candidate["archive_bytes"]) - int(control["archive_bytes"])
        size_ratio = size_penalty / max(1, int(control["archive_bytes"]))
        rss_reduction = 1.0 - candidate_peak / control_peak
        wall_ratio = candidate_wall / control_wall
        byte_budget_ok = size_penalty <= 8192 and size_ratio <= 0.005
        derived = {
            "candidate_tree_peak_reduction_fraction_vs_control": rss_reduction,
            "candidate_wall_ratio_vs_control": wall_ratio,
            "candidate_archive_size_penalty_bytes_vs_control": size_penalty,
            "candidate_archive_size_penalty_ratio_vs_control": size_ratio,
            "byte_budget_ok": byte_budget_ok,
            "hostile_fail_closed": all(row.get("failed_closed") is True for row in hostile_rows),
        }
        if rss_reduction < 0.20:
            decision = "PREFIXGRAPH_ISOLATION_PRODUCTIZATION_DID_NOT_TRANSFER"
        elif wall_ratio > 1.10 or not byte_budget_ok:
            decision = "PREFIXGRAPH_ISOLATION_EXPORTED_DEBT_REMAINS"
        else:
            decision = "PREFIXGRAPH_ISOLATION_BUILDER_SUPPORTED"

    return {
        "schema": "cmpct-v030-prefixgraph-isolation-productization-v1",
        "source_commit": _head(),
        "preregistration": PREREG,
        "target": list(TARGET),
        "accepted_historical_tree_sha256": expected_historical_tree,
        "product_tree_sha256": product_tree,
        "run_order": [list(order) for order in ORDER],
        "rows": rows,
        "hostile_rows": hostile_rows,
        "arm_counts": counts,
        "deterministic": deterministic,
        "summaries": summaries,
        "derived": derived,
        "decision": decision,
        "experiment_valid": valid,
        "worker_failures": failures,
        "release_credit": False,
        "contract": {
            "whole_process_tree_rss_decisive": True,
            "parent_ru_maxrss_diagnostic_only": True,
            "minimum_rss_reduction": 0.20,
            "maximum_wall_ratio": 1.10,
            "maximum_size_penalty_bytes": 8192,
            "maximum_size_penalty_ratio": 0.005,
            "r24_exact_bytes": R24_BYTES,
            "prefixgraph_selected_required": True,
            "exactly_one_level15_child_required": True,
            "child_dead_before_g04_required": True,
            "hostile_helper_fail_closed_required": True,
            "release_thresholds_changed": False,
            "release_credit": False,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-prefixgraph-isolation-productization-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-prefixgraph-isolation-productization.json"))
    args = parser.parse_args()
    data = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    print(json.dumps({key: data[key] for key in (
        "source_commit", "experiment_valid", "summaries", "derived", "decision")}, indent=2), flush=True)
    if not data["experiment_valid"]:
        raise SystemExit("PrefixGraph isolation Builder productization evidence invalid")


if __name__ == "__main__":
    main()
