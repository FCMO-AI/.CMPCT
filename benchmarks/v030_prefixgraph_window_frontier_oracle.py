from __future__ import annotations

"""Exact fresh-process Shifted PrefixGraph Zstd-window frontier."""

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
WORKER = ROOT / "benchmarks" / "v030_prefixgraph_window_frontier_worker.py"
TARGET = ("resemblance_hostile_v1", "01_shifted_versions")
ARMS = ("baseline", "window-m1", "window-m2", "window-m3")
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
        out = json.loads(lines[-1])
    except (IndexError, json.JSONDecodeError) as exc:
        return {"arm": arm, "worker_failed": True, "returncode": cp.returncode, "stdout": cp.stdout, "stderr": cp.stderr, "failure": repr(exc)}
    out["worker_failed"] = False
    return out


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    roots = PERF._build_corpora(work_root / "corpora")
    source = roots[TARGET]
    expected_tree = CAND.treehash(source)

    repetitions: list[dict] = []
    valid = True
    for round_index, order in enumerate(ORDERS):
        row = {"round": round_index, "execution_order": list(order), "arms": {}}
        for arm in order:
            archive = work_root / "archives" / f"r{round_index}-{arm}.cmpct"
            receipt = run_worker(arm, source, archive)
            row["arms"][arm] = receipt
            if receipt.get("worker_failed") or receipt.get("tree_sha256") != expected_tree or receipt.get("strong_verify_ok") is not True or int(receipt.get("anchor_audition_workers", 0)) != 4:
                valid = False
        repetitions.append(row)

    summaries: dict[str, dict] = {}
    signals: list[str] = []
    if valid:
        for arm in ARMS:
            samples = [r["arms"][arm] for r in repetitions]
            summaries[arm] = {
                "archive_bytes": [int(s["archive_bytes"]) for s in samples],
                "archive_sha256": [s["archive_sha256"] for s in samples],
                "effective_window_log": [int(s["params"]["effective"]["window_log"]) for s in samples],
                "median_build_s": statistics.median(float(s["build_s"]) for s in samples),
                "median_incremental_build_peak_rss_kib": statistics.median(float(s["incremental_build_peak_rss_kib"]) for s in samples),
            }
        baseline = summaries["baseline"]
        baseline_bytes = baseline["archive_bytes"][0]
        baseline_wall = baseline["median_build_s"]
        baseline_rss = baseline["median_incremental_build_peak_rss_kib"]
        for arm in ARMS[1:]:
            s = summaries[arm]
            deterministic = len(set(s["archive_bytes"])) == 1 and len(set(s["archive_sha256"])) == 1
            byte_ratio = s["archive_bytes"][0] / baseline_bytes
            wall_ratio = s["median_build_s"] / baseline_wall
            rss_ratio = s["median_incremental_build_peak_rss_kib"] / baseline_rss
            # This is deliberately harder than merely showing a lower resident peak. A useful window must not
            # give back a byte on Shifted and must materially attack RSS while preserving the frozen time envelope.
            material = bool(deterministic and byte_ratio <= 1.0 and wall_ratio <= 1.10 and rss_ratio <= 0.70)
            s.update({"deterministic": deterministic, "byte_ratio_to_baseline": byte_ratio, "wall_ratio_to_baseline": wall_ratio, "rss_ratio_to_baseline": rss_ratio, "material_window_signal": material})
            if material:
                signals.append(arm)

    return {
        "schema": "cmpct-v030-prefixgraph-window-frontier-v1",
        "source_commit": source_commit(),
        "target": "/".join(TARGET),
        "tree_sha256": expected_tree,
        "rounds": len(ORDERS),
        "arms": list(ARMS),
        "repetitions": repetitions,
        "summaries": summaries,
        "material_signal_arms": signals,
        "experiment_valid": valid,
        "release_credit": False,
        "contract": {
            "fresh_process_per_arm": True,
            "four_anchor_workers_unchanged": True,
            "anchor_nomination_unchanged": True,
            "complete_archive_tournament_unchanged": True,
            "direct_zstd19_floor_unchanged": True,
            "only_prefix_zstd_window_changes": True,
            "strong_tree_verification_required": True,
            "release_thresholds_changed": False,
            "benchmark_identity_dispatch": False
        },
        "claim_boundary": "Research-only Shifted Pareto evidence. A signal requires content-agnostic canonical policy plus exact 15-workload bytes, external ZIP/Zstd speed-size, runtime/RSS, recovery, native and Android parity before release credit."
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-prefixgraph-window-frontier-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-prefixgraph-window-frontier.json"))
    a = p.parse_args()
    result = run(a.work_root)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"valid": result["experiment_valid"], "signals": result["material_signal_arms"], "summaries": result["summaries"]}, indent=2), flush=True)
    if not result["experiment_valid"]:
        raise SystemExit("PrefixGraph window frontier evidence invalid")


if __name__ == "__main__":
    main()
