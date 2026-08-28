from __future__ import annotations

"""Measure the PrefixGraph worker-count memory/time frontier on frozen Shifted.

The candidate-phase RSS receipt established PrefixGraph as the dominant r25 RSS
owner on Shifted. This oracle asks the next causal question without changing
production policy: how much of that peak is parallel-audition working set versus
single-audition working set? Each arm runs in a fresh process, strong-verifies the
same source tree and must emit byte-identical archives. No release credit.
"""

import argparse
import json
import os
from pathlib import Path
import shutil
import statistics
import subprocess
import sys

from benchmarks import v030_release_performance as PERF

ROOT = Path(__file__).resolve().parents[1]
WORKER = ROOT / "benchmarks" / "v030_prefixgraph_worker_count_rss_worker.py"
WORKER_COUNTS = (1, 2, 4)
ROUNDS = 2
TARGET = ("resemblance_hostile_v1", "01_shifted_versions")


def _source_commit() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def _run(source: Path, archive: Path, workers: int) -> dict:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    completed = subprocess.run(
        [sys.executable, str(WORKER), "--source", str(source), "--archive", str(archive), "--workers", str(workers)],
        cwd=ROOT, env=env, check=False, capture_output=True, text=True,
    )
    if completed.returncode != 0:
        return {"workers": workers, "worker_failed": True, "returncode": completed.returncode,
                "stdout": completed.stdout, "stderr": completed.stderr}
    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    if not lines:
        return {"workers": workers, "worker_failed": True, "returncode": 0,
                "stdout": completed.stdout, "stderr": completed.stderr,
                "failure": "worker emitted no JSON"}
    try:
        row = json.loads(lines[-1])
    except json.JSONDecodeError as exc:
        return {"workers": workers, "worker_failed": True, "returncode": 0,
                "stdout": completed.stdout, "stderr": completed.stderr,
                "failure": f"invalid JSON: {exc}"}
    row["worker_failed"] = False
    return row


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    roots = PERF._build_corpora(work_root / "corpora")
    source = roots[TARGET]
    rows = []
    valid = True
    for round_index in range(ROUNDS):
        order = WORKER_COUNTS if round_index == 0 else tuple(reversed(WORKER_COUNTS))
        measured = []
        for workers in order:
            archive = work_root / "archives" / f"r{round_index}-w{workers}.cmpct"
            row = _run(source, archive, workers)
            measured.append(row)
            if row.get("worker_failed"):
                valid = False
        rows.append({"round": round_index, "order": list(order), "measurements": measured})

    flat = [m for r in rows for m in r["measurements"] if not m.get("worker_failed")]
    if len(flat) != ROUNDS * len(WORKER_COUNTS):
        valid = False
    archive_ids = {(m.get("archive_bytes"), m.get("archive_sha256"), m.get("tree_sha256")) for m in flat}
    exact_identity = len(archive_ids) == 1 and len(flat) == ROUNDS * len(WORKER_COUNTS)
    valid = valid and exact_identity and all(
        m.get("candidate_set_unchanged") is True
        and m.get("complete_byte_tournament_unchanged") is True
        and m.get("full_candidate_list_retained") is False
        for m in flat
    )

    summary = {}
    for workers in WORKER_COUNTS:
        arm = [m for m in flat if m["workers"] == workers]
        if len(arm) != ROUNDS:
            continue
        summary[str(workers)] = {
            "median_incremental_peak_rss_kib": int(statistics.median(m["incremental_peak_rss_kib"] for m in arm)),
            "median_wall_s": float(statistics.median(m["wall_s"] for m in arm)),
            "archive_bytes": int(arm[0]["archive_bytes"]),
            "archive_sha256": arm[0]["archive_sha256"],
        }

    w4 = summary.get("4")
    best_memory = min(summary.items(), key=lambda kv: kv[1]["median_incremental_peak_rss_kib"])[0] if summary else None
    for workers, item in summary.items():
        if w4:
            item["rss_ratio_vs_w4"] = item["median_incremental_peak_rss_kib"] / w4["median_incremental_peak_rss_kib"]
            item["wall_ratio_vs_w4"] = item["median_wall_s"] / w4["median_wall_s"]

    return {
        "schema": "cmpct-v030-prefixgraph-worker-count-rss-v1",
        "source_commit": _source_commit(),
        "target": list(TARGET),
        "rounds": rows,
        "summary": summary,
        "best_memory_arm": best_memory,
        "exact_archive_identity_all_arms": exact_identity,
        "experiment_valid": bool(valid),
        "promotion_signal": False,
        "release_credit": False,
        "contract": {
            "fresh_process_per_measurement": True,
            "candidate_set_changed": False,
            "serializer_changed": False,
            "tie_law_changed": False,
            "strong_verification_preserved": True,
            "production_worker_policy_changed": False,
            "threshold_changed": False,
        },
        "claim_boundary": "Diagnostic worker-count frontier only. It may identify a safer production scheduling target, but cannot change shipping policy or claim release credit without exact all-authority validation."
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-prefixgraph-worker-count-rss-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-prefixgraph-worker-count-rss.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"source_commit": result["source_commit"], "summary": result["summary"],
                      "experiment_valid": result["experiment_valid"]}, indent=2), flush=True)
    if not result["experiment_valid"]:
        raise SystemExit("PrefixGraph worker-count RSS evidence invalid")


if __name__ == "__main__":
    main()
