from __future__ import annotations

"""Fresh-process PrefixGraph low-memory compression-parameter Pareto oracle."""

import argparse
import json
import os
from pathlib import Path
import shutil
import statistics
import subprocess
import sys

from benchmarks import v030_release_performance as PERF
from experiments import entropygraph_v030_release_candidate as CAND

ROOT = Path(__file__).resolve().parents[1]
WORKER = ROOT / "benchmarks" / "v030_prefixgraph_lowmem_params_worker.py"
TARGET = ("resemblance_hostile_v1", "01_shifted_versions")
ARMS = (
    "baseline",
    "chain-m1",
    "chain-m2",
    "hash-m1",
    "chain-m1-hash-m1",
    "chain-m2-hash-m1",
)
# Reverse the second pass to damp ordinary runner/order effects without multiplying the matrix excessively.
ORDERS = (ARMS, tuple(reversed(ARMS)))


def source_commit() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def run_worker(arm: str, source: Path, archive: Path) -> dict:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    cp = subprocess.run(
        [sys.executable, str(WORKER), "--arm", arm, "--source", str(source), "--archive", str(archive)],
        cwd=ROOT, env=env, text=True, capture_output=True, check=False,
    )
    if cp.returncode != 0:
        return {"arm": arm, "worker_failed": True, "returncode": cp.returncode, "stdout": cp.stdout, "stderr": cp.stderr}
    lines = [line for line in cp.stdout.splitlines() if line.strip()]
    try:
        receipt = json.loads(lines[-1])
    except (IndexError, json.JSONDecodeError) as exc:
        return {"arm": arm, "worker_failed": True, "returncode": cp.returncode, "stdout": cp.stdout, "stderr": cp.stderr, "failure": repr(exc)}
    receipt["worker_failed"] = False
    return receipt


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    roots = PERF._build_corpora(work_root / "corpora")
    source = roots[TARGET]
    expected_tree = CAND.treehash(source)

    reps: list[dict] = []
    valid = True
    for round_index, order in enumerate(ORDERS):
        row = {"round": round_index, "execution_order": list(order), "arms": {}}
        for arm in order:
            archive = work_root / "archives" / f"r{round_index}-{arm}.cmpct"
            receipt = run_worker(arm, source, archive)
            row["arms"][arm] = receipt
            if receipt.get("worker_failed") or receipt.get("tree_sha256") != expected_tree or receipt.get("strong_verify_ok") is not True:
                valid = False
        reps.append(row)

    summaries: dict[str, dict] = {}
    if valid:
        for arm in ARMS:
            samples = [row["arms"][arm] for row in reps]
            summaries[arm] = {
                "archive_bytes": [int(s["archive_bytes"]) for s in samples],
                "archive_sha256": [s["archive_sha256"] for s in samples],
                "median_build_s": statistics.median(float(s["build_s"]) for s in samples),
                "median_incremental_build_peak_rss_kib": statistics.median(float(s["incremental_build_peak_rss_kib"]) for s in samples),
                "anchors": [s["anchor"] for s in samples],
                "prefix_records": [int(s["prefix_records"]) for s in samples],
                "params": samples[0]["params"],
            }

    pareto: list[str] = []
    if valid:
        baseline = summaries["baseline"]
        baseline_bytes = baseline["archive_bytes"][0]
        baseline_wall = baseline["median_build_s"]
        baseline_rss = baseline["median_incremental_build_peak_rss_kib"]
        for arm in ARMS[1:]:
            s = summaries[arm]
            deterministic = len(set(s["archive_bytes"])) == 1 and len(set(s["archive_sha256"])) == 1
            size_ratio = s["archive_bytes"][0] / baseline_bytes
            wall_ratio = s["median_build_s"] / baseline_wall
            rss_ratio = s["median_incremental_build_peak_rss_kib"] / baseline_rss
            s.update({
                "deterministic": deterministic,
                "size_ratio_to_baseline": size_ratio,
                "wall_ratio_to_baseline": wall_ratio,
                "rss_ratio_to_baseline": rss_ratio,
                "strict_three_axis_pareto": bool(deterministic and size_ratio <= 1.0 and wall_ratio < 1.0 and rss_ratio < 1.0),
                "bounded_tradeoff_signal": bool(deterministic and size_ratio <= 1.005 and wall_ratio <= 1.0 and rss_ratio <= 0.70),
            })
            if s["strict_three_axis_pareto"] or s["bounded_tradeoff_signal"]:
                pareto.append(arm)

    return {
        "schema": "cmpct-v030-prefixgraph-lowmem-params-v1",
        "source_commit": source_commit(),
        "target": "/".join(TARGET),
        "tree_sha256": expected_tree,
        "rounds": len(ORDERS),
        "arms": list(ARMS),
        "repetitions": reps,
        "summaries": summaries,
        "pareto_signal_arms": pareto,
        "experiment_valid": valid,
        "selector_change": False,
        "release_credit": False,
        "contract": {
            "fresh_process_per_arm": True,
            "four_anchor_workers_unchanged": True,
            "direct_zstd19_payload_floor_unchanged": True,
            "anchor_nomination_unchanged": True,
            "complete_archive_tournament_unchanged": True,
            "reader_and_integrity_law_unchanged": True,
            "candidate_prefix_bytes_may_change": True,
            "production_bytes_changed": False,
            "release_thresholds_changed": False,
            "benchmark_identity_dispatch": False,
        },
        "claim_boundary": "Research-only parameter frontier. Any positive arm requires product-wide generic admission, exact 15-workload no-regression/external authority, runtime/RSS, reader/recovery/native/Android parity before credit.",
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-prefixgraph-lowmem-params-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-prefixgraph-lowmem-params.json"))
    args = p.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"valid": result["experiment_valid"], "pareto_signal_arms": result["pareto_signal_arms"], "summaries": result["summaries"]}, indent=2), flush=True)
    if not result["experiment_valid"]:
        raise SystemExit("PrefixGraph low-memory parameter evidence invalid")


if __name__ == "__main__":
    main()
