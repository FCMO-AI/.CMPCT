from __future__ import annotations

"""Fresh-process PrefixGraph allocator-arena RSS frontier.

Research only.  The compression algorithm, four-worker scheduler, anchor nomination, complete byte tournament,
serializer, reader and integrity law are untouched.  Each arm starts a fresh Python process with a different
glibc malloc arena ceiling so we can falsify or confirm the observed thread-count/RSS relationship without
changing a candidate byte or hiding child-process memory.
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
from experiments import entropygraph_v030_release_candidate as CAND

ROOT = Path(__file__).resolve().parents[1]
WORKER = ROOT / "benchmarks" / "v030_prefixgraph_lowmem_params_worker.py"
TARGET = ("resemblance_hostile_v1", "01_shifted_versions")
ARMS: dict[str, str | None] = {
    "allocator-default": None,
    "arena-4": "4",
    "arena-2": "2",
    "arena-1": "1",
}
ORDERS = (tuple(ARMS), tuple(reversed(tuple(ARMS))))


def source_commit() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def run_worker(arm: str, source: Path, archive: Path) -> dict:
    arena = ARMS[arm]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    # The variable is consumed by glibc before Python starts allocating.  Do not use malloc_trim or child
    # processes: ru_maxrss remains the real high-water mark of the exact four-thread builder process.
    if arena is None:
        env.pop("MALLOC_ARENA_MAX", None)
    else:
        env["MALLOC_ARENA_MAX"] = arena
    cp = subprocess.run(
        [sys.executable, str(WORKER), "--arm", "baseline", "--source", str(source), "--archive", str(archive)],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    if cp.returncode != 0:
        return {
            "arm": arm,
            "malloc_arena_max": arena,
            "worker_failed": True,
            "returncode": cp.returncode,
            "stdout": cp.stdout,
            "stderr": cp.stderr,
        }
    lines = [line for line in cp.stdout.splitlines() if line.strip()]
    try:
        receipt = json.loads(lines[-1])
    except (IndexError, json.JSONDecodeError) as exc:
        return {
            "arm": arm,
            "malloc_arena_max": arena,
            "worker_failed": True,
            "returncode": cp.returncode,
            "stdout": cp.stdout,
            "stderr": cp.stderr,
            "failure": repr(exc),
        }
    receipt["arm"] = arm
    receipt["malloc_arena_max"] = arena
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
            if (
                receipt.get("worker_failed")
                or receipt.get("tree_sha256") != expected_tree
                or receipt.get("strong_verify_ok") is not True
                or int(receipt.get("anchor_audition_workers", 0)) != 4
            ):
                valid = False
        reps.append(row)

    summaries: dict[str, dict] = {}
    if valid:
        for arm in ARMS:
            samples = [row["arms"][arm] for row in reps]
            summaries[arm] = {
                "malloc_arena_max": ARMS[arm],
                "archive_bytes": [int(s["archive_bytes"]) for s in samples],
                "archive_sha256": [s["archive_sha256"] for s in samples],
                "median_build_s": statistics.median(float(s["build_s"]) for s in samples),
                "median_incremental_build_peak_rss_kib": statistics.median(
                    float(s["incremental_build_peak_rss_kib"]) for s in samples
                ),
                "anchor_audition_workers": [int(s["anchor_audition_workers"]) for s in samples],
            }

    signals: list[str] = []
    if valid:
        baseline = summaries["allocator-default"]
        baseline_bytes = baseline["archive_bytes"][0]
        baseline_sha = baseline["archive_sha256"][0]
        baseline_wall = baseline["median_build_s"]
        baseline_rss = baseline["median_incremental_build_peak_rss_kib"]
        for arm in tuple(ARMS)[1:]:
            s = summaries[arm]
            deterministic = len(set(s["archive_bytes"])) == 1 and len(set(s["archive_sha256"])) == 1
            exact_identity = deterministic and s["archive_bytes"][0] == baseline_bytes and s["archive_sha256"][0] == baseline_sha
            wall_ratio = s["median_build_s"] / baseline_wall
            rss_ratio = s["median_incremental_build_peak_rss_kib"] / baseline_rss
            s.update({
                "deterministic": deterministic,
                "exact_archive_identity": exact_identity,
                "wall_ratio_to_baseline": wall_ratio,
                "rss_ratio_to_baseline": rss_ratio,
                # A useful arena result must attack the actual blocker, not merely shave noise, and must stay
                # inside the frozen runtime envelope before any product-wide validation is even considered.
                "material_allocator_signal": bool(exact_identity and wall_ratio <= 1.10 and rss_ratio <= 0.70),
            })
            if s["material_allocator_signal"]:
                signals.append(arm)

    return {
        "schema": "cmpct-v030-prefixgraph-allocator-arena-v1",
        "source_commit": source_commit(),
        "target": "/".join(TARGET),
        "tree_sha256": expected_tree,
        "rounds": len(ORDERS),
        "arms": list(ARMS),
        "repetitions": reps,
        "summaries": summaries,
        "material_signal_arms": signals,
        "experiment_valid": valid,
        "selector_change": False,
        "release_credit": False,
        "contract": {
            "fresh_process_per_arm": True,
            "four_anchor_workers_unchanged": True,
            "compression_parameters_unchanged": True,
            "direct_zstd19_payload_floor_unchanged": True,
            "anchor_nomination_unchanged": True,
            "complete_archive_tournament_unchanged": True,
            "reader_and_integrity_law_unchanged": True,
            "child_process_memory_hidden": False,
            "production_bytes_changed": False,
            "release_thresholds_changed": False,
            "benchmark_identity_dispatch": False,
        },
        "claim_boundary": "Research-only allocator frontier. A positive arm still requires generic launch/runtime integration plus exact 15-workload byte/runtime/RSS, recovery, native and Android authorities before release credit.",
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-prefixgraph-allocator-arena-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-prefixgraph-allocator-arena.json"))
    args = p.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "valid": result["experiment_valid"],
        "material_signal_arms": result["material_signal_arms"],
        "summaries": result["summaries"],
    }, indent=2), flush=True)
    if not result["experiment_valid"]:
        raise SystemExit("PrefixGraph allocator-arena evidence invalid")


if __name__ == "__main__":
    main()
