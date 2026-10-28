from __future__ import annotations

"""Shipping-r24 inherited-vs-single-worker fresh-process RSS A/B."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import shutil
import statistics
import subprocess
import sys
import time

from benchmarks import v030_release_performance as PERF

ROOT = Path(__file__).resolve().parents[1]
TARGET = ("resemblance_hostile_v1", "01_shifted_versions")
ROUNDS = 3


def rss_kib() -> int:
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)


def source_commit() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def build_worker(mode: str, source: Path, archive: Path) -> dict:
    from experiments import entropygraph_v030_release_product as P

    original_builder = P.C.Builder
    if mode == "single":
        class SingleWorkerBuilder(original_builder):
            def __init__(self, *args, **kwargs):
                kwargs["workers"] = 1
                super().__init__(*args, **kwargs)
        P.C.Builder = SingleWorkerBuilder
    elif mode != "inherited":
        raise ValueError(mode)

    baseline = rss_kib()
    started = time.perf_counter()
    try:
        stats = dict(P._locality_bounded_r24_build(source, archive))
    finally:
        P.C.Builder = original_builder
    wall_s = time.perf_counter() - started
    peak = rss_kib()
    verify = P.strong_verify(archive)
    if verify.get("ok") is not True:
        raise RuntimeError(f"r24 strong verification failed: {verify!r}")
    payload = archive.read_bytes()
    return {
        "mode": mode,
        "archive_bytes": len(payload),
        "archive_sha256": hashlib.sha256(payload).hexdigest(),
        "tree_sha256": verify.get("tree_sha256"),
        "baseline_rss_kib": baseline,
        "peak_rss_kib": peak,
        "incremental_peak_rss_kib": peak - baseline,
        "wall_s": wall_s,
        "build_stats": stats,
        "verification": verify,
    }


def run_worker(mode: str, source: Path, archive: Path) -> dict:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    done = subprocess.run(
        [sys.executable, __file__, "--worker-mode", mode, "--worker-source", str(source), "--worker-archive", str(archive)],
        cwd=ROOT, env=env, check=True, capture_output=True, text=True,
    )
    lines = [line for line in done.stdout.splitlines() if line.strip()]
    if not lines:
        raise RuntimeError(f"worker emitted no JSON: {done.stderr!r}")
    return json.loads(lines[-1])


def med(rows: list[dict], key: str) -> float:
    return float(statistics.median(float(r[key]) for r in rows))


def stable_stats(stats: dict) -> dict:
    drop = {"encode_workers", "create_s"}
    return {k: v for k, v in stats.items() if k not in drop}


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    roots = PERF._build_corpora(work_root / "corpora")
    source = roots[TARGET]
    rows: dict[str, list[dict]] = {"inherited": [], "single": []}
    for rep in range(ROUNDS):
        order = ["inherited", "single"] if rep % 2 == 0 else ["single", "inherited"]
        for mode in order:
            archive = work_root / "archives" / f"r{rep}-{mode}.cmpct"
            archive.parent.mkdir(parents=True, exist_ok=True)
            rows[mode].append(run_worker(mode, source, archive))

    identities = {
        (r["archive_bytes"], r["archive_sha256"], r["tree_sha256"])
        for mode_rows in rows.values() for r in mode_rows
    }
    invariant_stats = {json.dumps(stable_stats(r["build_stats"]), sort_keys=True) for mode_rows in rows.values() for r in mode_rows}
    worker_counts = {
        mode: sorted({int(r["build_stats"].get("encode_workers", -1)) for r in mode_rows})
        for mode, mode_rows in rows.items()
    }
    identity_ok = len(identities) == 1 and len(invariant_stats) == 1 and worker_counts["single"] == [1]
    inherited_peak = med(rows["inherited"], "peak_rss_kib")
    single_peak = med(rows["single"], "peak_rss_kib")
    inherited_wall = med(rows["inherited"], "wall_s")
    single_wall = med(rows["single"], "wall_s")
    rss_reduction = 1.0 - single_peak / inherited_peak if inherited_peak > 0 else 0.0
    wall_ratio = single_wall / inherited_wall if inherited_wall > 0 else float("inf")
    if not identity_ok:
        decision = "INVALID_EXACT_OUTPUT_IDENTITY"
    elif rss_reduction >= 0.20 and wall_ratio <= 1.25:
        decision = "R24_SINGLE_WORKER_REHAB_SUPPORTED"
    elif rss_reduction < 0.05:
        decision = "R24_WORKER_PARALLELISM_RETIRED"
    else:
        decision = "R24_SINGLE_WORKER_AMBIGUOUS"
    return {
        "schema": "cmpct-v030-r24-worker-count-rss-ab-v1",
        "source_commit": source_commit(),
        "target": list(TARGET),
        "rounds": ROUNDS,
        "rows": rows,
        "identity": {"exact_output_and_stats": identity_ok, "worker_counts": worker_counts},
        "summary": {
            "inherited_median_peak_rss_kib": inherited_peak,
            "single_median_peak_rss_kib": single_peak,
            "inherited_median_incremental_peak_rss_kib": med(rows["inherited"], "incremental_peak_rss_kib"),
            "single_median_incremental_peak_rss_kib": med(rows["single"], "incremental_peak_rss_kib"),
            "inherited_median_wall_s": inherited_wall,
            "single_median_wall_s": single_wall,
            "rss_reduction": rss_reduction,
            "wall_ratio": wall_ratio,
            "decision": decision,
        },
        "contract": {"support_threshold": 0.20, "retire_threshold": 0.05, "max_supported_wall_ratio": 1.25, "production_change": False, "release_credit": False},
        "release_credit": False,
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path)
    p.add_argument("--output", type=Path)
    p.add_argument("--worker-mode", choices=("inherited", "single"))
    p.add_argument("--worker-source", type=Path)
    p.add_argument("--worker-archive", type=Path)
    a = p.parse_args()
    if a.worker_mode:
        print(json.dumps(build_worker(a.worker_mode, a.worker_source, a.worker_archive), sort_keys=True, default=str))
        return
    if a.work_root is None or a.output is None:
        raise SystemExit("--work-root and --output required")
    result = run(a.work_root)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"summary": result["summary"], "identity": result["identity"]}, indent=2))


if __name__ == "__main__":
    main()
