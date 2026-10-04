from __future__ import annotations

"""Frozen PrefixGraph-isolated r24-prebuild overlap A/B on deterministic Shifted."""

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
WORKER = ROOT / "benchmarks" / "v030_r25_pg_isolated_r24_prebuild_barrier_rss_worker.py"
TARGET = ("resemblance_hostile_v1", "01_shifted_versions")
PREREG = "docs/v030-rnd/R25_PG_ISOLATED_R24_PREBUILD_BARRIER_RSS_PREREG.md"
PAIR_ORDERS = (("overlap", "r24-barrier"), ("r24-barrier", "overlap"), ("overlap", "r24-barrier"))


def _head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def _run(mode: str, source: Path, archive: Path) -> dict:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    proc = subprocess.run(
        [sys.executable, str(WORKER), "--mode", mode, "--source", str(source), "--archive", str(archive)],
        cwd=ROOT, env=env, capture_output=True, text=True
    )
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    if proc.returncode or not lines:
        return {"worker_failed": True, "returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr}
    try:
        data = json.loads(lines[-1])
    except Exception as exc:
        return {"worker_failed": True, "failure": f"json:{exc}", "stdout": proc.stdout, "stderr": proc.stderr}
    data["worker_failed"] = False
    return data


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    accepted = GENERAL._accepted_v029_rows()
    source = PERF._build_corpora(work_root / "corpora")[TARGET]
    expected_historical_tree = str(accepted[TARGET]["tree_sha256"])
    if str(GENERAL._historical_treehash(source)) != expected_historical_tree:
        raise RuntimeError("prebuild-barrier source drifted from accepted repaired Shifted authority")
    product_tree = str(PRODUCT.treehash(source))

    rows: list[dict] = []
    failures: list[dict] = []
    identities: set[tuple] = set()
    for pair_index, order in enumerate(PAIR_ORDERS):
        for position, mode in enumerate(order):
            archive = work_root / "archives" / f"pair-{pair_index}-{position}-{mode}.cmpct"
            archive.parent.mkdir(parents=True, exist_ok=True)
            row = _run(mode, source, archive)
            row.update({"pair_index": pair_index, "position": position})
            rows.append(row)
            owners = row.get("semantic_owners") or {}
            common_ok = (
                not row.get("worker_failed")
                and row.get("tree_sha256") == product_tree
                and row.get("expected_verification_tree_sha256") == product_tree
                and row.get("selected") == "prefixgraph"
                and row.get("r24_product_bytes") is not None
                and row.get("r25_product_bytes") is not None
                and int(row.get("tree_peak_rss_kib", 0)) > 0
                and int(row.get("tree_samples", 0)) >= 100
                and row.get("tree_sampler_errors") == []
                and float(row.get("tree_sampler_interval_s", 1.0)) <= 0.01
                and row.get("prefixgraph_executor_intercepts") == 1
                and row.get("prefixgraph_submissions") == 1
                and row.get("prefixgraph_children") == 1
                and row.get("prefixgraph_returncodes") == [0]
                and row.get("g04_children") == 0
                and row.get("r24_prebuild_reused_by_canonical_consumer") is True
                and row.get("bindings_restored") is True
                and owners.get("identity_exact") is True
                and owners.get("pg") == "experiments._v030_canonical_prefixgraph"
                and owners.get("g04") == "experiments._v030_canonical_shared_portfolio"
                and owners.get("reader") == "experiments._v030_canonical_release_reader_policy"
            )
            mode_ok = (
                (mode == "overlap" and row.get("r24_prebuild_barrier_waits") == 0)
                or (
                    mode == "r24-barrier"
                    and row.get("r24_prebuild_barrier_waits") == 1
                    and row.get("r24_prebuild_future_done_after_wait") is True
                    and row.get("r24_prebuilt_artifact_exists_after_wait") is True
                )
            )
            identities.add(tuple(row.get(k) for k in (
                "archive_bytes", "archive_sha256", "tree_sha256", "selected",
                "format_revision", "r24_product_bytes", "r25_product_bytes"
            )))
            if not (common_ok and mode_ok):
                failures.append({"mode": mode, "pair_index": pair_index, **row})

    valid = not failures and len(rows) == 6 and len(identities) == 1
    summary = {}
    decision = "INVALID"
    if valid:
        by_mode = {m: [r for r in rows if r["mode"] == m] for m in ("overlap", "r24-barrier")}
        o_rss = float(statistics.median(float(r["tree_peak_rss_kib"]) for r in by_mode["overlap"]))
        b_rss = float(statistics.median(float(r["tree_peak_rss_kib"]) for r in by_mode["r24-barrier"]))
        o_wall = float(statistics.median(float(r["wall_s"]) for r in by_mode["overlap"]))
        b_wall = float(statistics.median(float(r["wall_s"]) for r in by_mode["r24-barrier"]))
        reduction = (o_rss - b_rss) / o_rss
        wall_ratio = b_wall / o_wall
        if reduction >= 0.20:
            decision = "R24_PREBUILD_OVERLAP_SUPPORTED"
        elif reduction < 0.10:
            decision = "R24_PREBUILD_OVERLAP_RETIRED"
        else:
            decision = "R24_PREBUILD_OVERLAP_AMBIGUOUS"
        summary = {
            "overlap_median_tree_peak_rss_kib": o_rss,
            "barrier_median_tree_peak_rss_kib": b_rss,
            "rss_reduction_fraction": reduction,
            "rss_reduction_kib": o_rss - b_rss,
            "overlap_median_wall_s": o_wall,
            "barrier_median_wall_s": b_wall,
            "barrier_wall_ratio": wall_ratio,
            "barrier_wall_change_fraction": wall_ratio - 1.0,
            "overlap_peaks_kib": [int(r["tree_peak_rss_kib"]) for r in by_mode["overlap"]],
            "barrier_peaks_kib": [int(r["tree_peak_rss_kib"]) for r in by_mode["r24-barrier"]],
        }

    return {
        "schema": "cmpct-v030-r25-pg-isolated-r24-prebuild-barrier-rss-v1",
        "source_commit": _head(),
        "preregistration": PREREG,
        "causal_predecessor": "docs/v030-rnd/R25_PARENT_PHASE_RSS_RESULT.md",
        "target": list(TARGET),
        "accepted_historical_tree_sha256": expected_historical_tree,
        "product_tree_sha256": product_tree,
        "pair_orders": [list(x) for x in PAIR_ORDERS],
        "rows": rows,
        "summary": summary,
        "decision": decision,
        "experiment_valid": valid,
        "worker_failures": failures,
        "release_credit": False,
        "contract": {
            "whole_process_tree_rss_decisive": True,
            "sampler_interval_s_max": 0.01,
            "min_samples_per_row": 100,
            "prefixgraph_process_boundary_preserved": True,
            "g04_parent_execution_required": True,
            "exact_r24_prebuild_required": True,
            "same_prebuild_consumed_by_canonical_r24": True,
            "support_threshold": 0.20,
            "retire_threshold": 0.10,
            "exact_product_identity_required": True,
            "production_source_changed": False,
            "candidate_semantics_changed": False,
            "release_thresholds_changed": False,
        },
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r25-pg-isolated-r24-prebuild-barrier-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r25-pg-isolated-r24-prebuild-barrier.json"))
    a = p.parse_args()
    data = run(a.work_root)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(data, indent=2) + "\n")
    print(json.dumps({k: data[k] for k in ("source_commit", "experiment_valid", "summary", "decision")}, indent=2), flush=True)
    if not data["experiment_valid"]:
        raise SystemExit("r24-prebuild barrier RSS evidence invalid")


if __name__ == "__main__":
    main()
