from __future__ import annotations

"""Research-only bounded parallelism frontier for G0-G4 record auditions on frozen ML.

G04's authenticated physical records are independent inputs to ``_audition_record``;
shipping currently auditions them serially, then writes them in record-id order. This
oracle asks whether bounded concurrency can remove enough of the ML creation outlier to
justify a productization pass without changing any candidate, tie rule, transform, or
archive semantics.

Each 1/2/4-worker arm runs in a fresh process. Graph construction is deliberately outside
the timed/RSS audition region because this is a mechanism-causality experiment, not a
release-speed claim. The complete candidate record+transform sequence is hashed and must
be identical across every arm. Any product promotion would still have to time the complete
archive construction, pay preprocessing/verification/publication costs, preserve v0.29
bytes, locality/recovery, native/Android parity, and pass the exact 15-workload authority.
"""

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import resource
import shutil
import statistics
import subprocess
import sys
import tempfile
import time

import msgpack

from benchmarks import v030_release_performance as PERF
from experiments import entropygraph_v030_geometry_overlay_g04 as G04

ROOT = Path(__file__).resolve().parents[1]
TARGET = ("neutral_hostile_v1", "09_ml_artifacts")
WORKERS = (1, 2, 4)
ROUNDS = 2
MIN_WALL_SPEEDUP = 0.20
MAX_RSS_RATIO = 1.50


def _rss_kib() -> int:
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)


def _source_commit() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def _candidate_digest(rows: list[tuple[tuple[int, int, bytes, int, bytes], list | None, dict]]) -> str:
    semantic = []
    for record, transform, _stats in rows:
        codec, usize, payload, crc, logical_sha = record
        semantic.append([int(codec), int(usize), bytes(payload), int(crc), bytes(logical_sha), transform])
    return hashlib.sha256(msgpack.packb(semantic, use_bin_type=True)).hexdigest()


def _worker(source: Path, workers: int) -> dict:
    if workers not in WORKERS:
        raise ValueError(f"unsupported worker count {workers}")
    with tempfile.TemporaryDirectory(prefix="cmpct-v030-g04-parallel-worker-") as td:
        td = Path(td)
        graph = td / "attempt5-prefallback.cmpct"
        G04.A5.build_graph(source, graph)
        _fmt, _source, meta, records = G04.strict._read_source_records(graph)
        users = G04.O._record_member_lengths(meta, len(records))

        baseline = _rss_kib()
        started = time.perf_counter()
        if workers == 1:
            rows = [G04._audition_record(i, record, users[i]) for i, record in enumerate(records)]
        else:
            def run_one(item):
                i, record = item
                return G04._audition_record(i, record, users[i])
            with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="cmpct-g04-audition") as pool:
                rows = list(pool.map(run_one, enumerate(records)))
        wall_s = time.perf_counter() - started
        peak = _rss_kib()

        transformed = sum(transform is not None for _record, transform, _stats in rows)
        hierarchical = sum(
            isinstance(transform, list) and transform and transform[0] == "hierarchical"
            for _record, transform, _stats in rows
        )
        screened = sum(int(stats.get("hierarchical_screened_candidates", 0)) for _record, _transform, stats in rows)
        finalists = sum(int(stats.get("hierarchical_exact_finalists", 0)) for _record, _transform, stats in rows)
        incremental_saving = sum(
            int(stats.get("hierarchical_incremental_saving_bytes", 0))
            for _record, _transform, stats in rows
            if str(stats.get("selected", "")).startswith("hierarchical")
        )
        return {
            "workers": workers,
            "records": len(rows),
            "candidate_digest": _candidate_digest(rows),
            "transformed_records": transformed,
            "hierarchical_records": hierarchical,
            "hierarchical_screened_candidates": screened,
            "hierarchical_exact_finalists": finalists,
            "hierarchical_incremental_saving_bytes": incremental_saving,
            "audition_wall_s": wall_s,
            "baseline_rss_kib": baseline,
            "peak_rss_kib": peak,
            "incremental_peak_rss_kib": max(0, peak - baseline),
        }


def _run_worker(source: Path, workers: int) -> dict:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    completed = subprocess.run(
        [sys.executable, __file__, "--worker-source", str(source), "--workers", str(workers)],
        cwd=ROOT,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    if not lines:
        raise RuntimeError(f"G04 record-audition worker {workers} emitted no JSON")
    return json.loads(lines[-1])


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    source = PERF._build_corpora(work_root / "corpora")[TARGET]

    rounds = []
    for round_index in range(ROUNDS):
        order = WORKERS if round_index == 0 else tuple(reversed(WORKERS))
        measured = [_run_worker(source, workers) for workers in order]
        rounds.append({"round": round_index, "order": list(order), "measurements": measured})

    flat = [row for rnd in rounds for row in rnd["measurements"]]
    digests = {row["candidate_digest"] for row in flat}
    structural = {
        (
            row["records"], row["transformed_records"], row["hierarchical_records"],
            row["hierarchical_screened_candidates"], row["hierarchical_exact_finalists"],
            row["hierarchical_incremental_saving_bytes"],
        )
        for row in flat
    }
    exact_identity = len(digests) == 1 and len(structural) == 1 and len(flat) == ROUNDS * len(WORKERS)

    summary = {}
    for workers in WORKERS:
        arm = [row for row in flat if row["workers"] == workers]
        summary[str(workers)] = {
            "median_audition_wall_s": float(statistics.median(row["audition_wall_s"] for row in arm)),
            "median_incremental_peak_rss_kib": float(statistics.median(row["incremental_peak_rss_kib"] for row in arm)),
            "candidate_digest": arm[0]["candidate_digest"],
        }
    baseline = summary["1"]
    for key, item in summary.items():
        item["wall_ratio_vs_w1"] = item["median_audition_wall_s"] / max(1e-12, baseline["median_audition_wall_s"])
        item["rss_ratio_vs_w1"] = item["median_incremental_peak_rss_kib"] / max(1.0, baseline["median_incremental_peak_rss_kib"])
        item["speedup_fraction_vs_w1"] = 1.0 - item["wall_ratio_vs_w1"]

    eligible = [
        int(key) for key, item in summary.items()
        if int(key) > 1
        and item["speedup_fraction_vs_w1"] >= MIN_WALL_SPEEDUP
        and item["rss_ratio_vs_w1"] <= MAX_RSS_RATIO
    ]
    best = min(eligible, key=lambda workers: summary[str(workers)]["median_audition_wall_s"]) if eligible else None

    exemplar = flat[0]
    return {
        "schema": "cmpct-v030-g04-record-audition-parallel-v1",
        "source_commit": _source_commit(),
        "target": list(TARGET),
        "rounds": rounds,
        "summary": summary,
        "exact_candidate_identity_all_arms": exact_identity,
        "structural_counts": {
            "records": exemplar["records"],
            "transformed_records": exemplar["transformed_records"],
            "hierarchical_records": exemplar["hierarchical_records"],
            "hierarchical_screened_candidates": exemplar["hierarchical_screened_candidates"],
            "hierarchical_exact_finalists": exemplar["hierarchical_exact_finalists"],
            "hierarchical_incremental_saving_bytes": exemplar["hierarchical_incremental_saving_bytes"],
        },
        "best_bounded_parallel_arm": best,
        "promotion_signal": bool(exact_identity and best is not None),
        "release_credit": False,
        "experiment_valid": bool(exact_identity),
        "contract": {
            "fresh_process_per_arm": True,
            "graph_construction_timed": False,
            "research_mechanism_only": True,
            "record_audition_function_changed": False,
            "candidate_set_changed": False,
            "tie_law_changed": False,
            "result_order_preserved": True,
            "minimum_audition_wall_speedup_fraction": MIN_WALL_SPEEDUP,
            "maximum_incremental_rss_ratio_vs_serial": MAX_RSS_RATIO,
            "complete_product_authority_required_before_promotion": True,
        },
        "claim_boundary": (
            "This isolates only authenticated-record audition. A positive signal authorizes a complete-product "
            "bounded-parallel candidate; it does not hide graph construction, verification, metadata, publication, "
            "recovery, or platform cost from any release benchmark."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-g04-record-audition-parallel-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-g04-record-audition-parallel.json"))
    parser.add_argument("--worker-source", type=Path)
    parser.add_argument("--workers", type=int, choices=WORKERS)
    args = parser.parse_args()
    if args.worker_source is not None:
        if args.workers is None:
            raise SystemExit("--workers is required with --worker-source")
        print(json.dumps(_worker(args.worker_source, args.workers), sort_keys=True), flush=True)
        return
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"summary": result["summary"], "promotion_signal": result["promotion_signal"]}, indent=2), flush=True)
    if not result["experiment_valid"]:
        raise SystemExit("G04 bounded-parallel audition changed exact candidate sequence")


if __name__ == "__main__":
    main()
