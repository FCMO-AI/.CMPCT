from __future__ import annotations

"""Causal A/B for r24 release-policy visibility across encoder worker threads.

Diagnostic only. See docs/v030-rnd/R25_R24_WORKER_POLICY_PROPAGATION_V2_PREREG.md.
"""

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


def _stable_stats(stats: dict) -> dict:
    drop = {"encode_workers", "create_s"}
    return {k: v for k, v in stats.items() if k not in drop}


def build_worker(mode: str, source: Path, archive: Path) -> dict:
    from experiments import entropygraph_v030_release_product as P

    original_builder = P.C.Builder
    builder_module = P.R24_BUILDER_MODULE
    original_text_ext = builder_module.TEXT_EXT

    if mode == "single":
        class SingleWorkerBuilder(original_builder):
            def __init__(self, *args, **kwargs):
                kwargs["workers"] = 1
                super().__init__(*args, **kwargs)
        P.C.Builder = SingleWorkerBuilder
    elif mode == "propagated":
        # The parent release build already sees .bin through _ReleaseTextHints because
        # _locality_bounded_r24_build sets the release thread-local policy. Represent
        # that already-active eligibility as an immutable set in this isolated process
        # so child encoder threads see the same predicate. No codec/search parameter changes.
        base = set(builder_module._cmpct_v030_original_text_ext)
        base.add(P.R24_RELEASE_MEDIUM_BINARY_EXT)
        builder_module.TEXT_EXT = frozenset(base)
    elif mode != "inherited":
        raise ValueError(mode)

    baseline = rss_kib()
    started = time.perf_counter()
    try:
        stats = dict(P._locality_bounded_r24_build(source, archive))
    finally:
        P.C.Builder = original_builder
        builder_module.TEXT_EXT = original_text_ext
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
        "stable_build_stats": _stable_stats(stats),
        "verification": verify,
    }


def run_worker(mode: str, source: Path, archive: Path) -> dict:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    done = subprocess.run(
        [sys.executable, __file__, "--worker-mode", mode,
         "--worker-source", str(source), "--worker-archive", str(archive)],
        cwd=ROOT, env=env, check=True, capture_output=True, text=True,
    )
    lines = [line for line in done.stdout.splitlines() if line.strip()]
    if not lines:
        raise RuntimeError(f"worker emitted no JSON: {done.stderr!r}")
    return json.loads(lines[-1])


def med(rows: list[dict], key: str) -> float:
    return float(statistics.median(float(r[key]) for r in rows))


def _identity(rows: list[dict]) -> set[tuple[int, str, str]]:
    return {(int(r["archive_bytes"]), str(r["archive_sha256"]), str(r["tree_sha256"])) for r in rows}


def _stable_stats_identity(rows: list[dict]) -> set[str]:
    return {json.dumps(r["stable_build_stats"], sort_keys=True) for r in rows}


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    roots = PERF._build_corpora(work_root / "corpora")
    source = roots[TARGET]
    modes = ("inherited", "single", "propagated")
    rows: dict[str, list[dict]] = {m: [] for m in modes}
    orders = [
        ("inherited", "single", "propagated"),
        ("propagated", "single", "inherited"),
        ("single", "inherited", "propagated"),
    ]
    for rep, order in enumerate(orders):
        for mode in order:
            archive = work_root / "archives" / f"r{rep}-{mode}.cmpct"
            archive.parent.mkdir(parents=True, exist_ok=True)
            rows[mode].append(run_worker(mode, source, archive))

    verified = all(r["verification"].get("ok") is True for rs in rows.values() for r in rs)
    trees = {r["tree_sha256"] for rs in rows.values() for r in rs}
    per_mode_identity = {m: _identity(rows[m]) for m in modes}
    per_mode_stats = {m: _stable_stats_identity(rows[m]) for m in modes}
    worker_counts = {
        m: sorted({int(r["build_stats"].get("encode_workers", -1)) for r in rows[m]})
        for m in modes
    }
    dict_states = {
        m: sorted({str(r["build_stats"].get("r24_dead_dictionary_elision")) for r in rows[m]})
        for m in modes
    }

    repeatable = all(len(per_mode_identity[m]) == 1 and len(per_mode_stats[m]) == 1 for m in modes)
    single_propagated_exact = (
        per_mode_identity["single"] == per_mode_identity["propagated"]
        and per_mode_stats["single"] == per_mode_stats["propagated"]
    )
    inherited_differs = per_mode_identity["inherited"] != per_mode_identity["single"]
    propagated_parallel = worker_counts["propagated"] and min(worker_counts["propagated"]) > 1
    predicted_dict_flip = (
        dict_states["inherited"] == ["dictionary-dead"]
        and dict_states["single"] == ["dictionary-live"]
        and dict_states["propagated"] == ["dictionary-live"]
    )

    valid = verified and len(trees) == 1 and repeatable and propagated_parallel
    if not valid:
        decision = "INVALID_EXPERIMENT"
    elif single_propagated_exact and inherited_differs and predicted_dict_flip:
        decision = "THREAD_LOCAL_POLICY_LEAK_CAUSAL"
    elif per_mode_identity["inherited"] == per_mode_identity["single"] == per_mode_identity["propagated"]:
        decision = "NO_WORKER_POLICY_DRIFT"
    else:
        decision = "UNRESOLVED_POLICY_DRIFT"

    summary = {
        m: {
            "archive_bytes": next(iter(per_mode_identity[m]))[0],
            "median_peak_rss_kib": med(rows[m], "peak_rss_kib"),
            "median_incremental_peak_rss_kib": med(rows[m], "incremental_peak_rss_kib"),
            "median_wall_s": med(rows[m], "wall_s"),
            "worker_counts": worker_counts[m],
            "dictionary_states": dict_states[m],
        }
        for m in modes
    }
    summary["propagated_vs_inherited_archive_delta_bytes"] = int(summary["propagated"]["archive_bytes"] - summary["inherited"]["archive_bytes"])
    summary["propagated_vs_inherited_peak_ratio"] = float(summary["propagated"]["median_peak_rss_kib"] / summary["inherited"]["median_peak_rss_kib"])
    summary["propagated_vs_inherited_wall_ratio"] = float(summary["propagated"]["median_wall_s"] / summary["inherited"]["median_wall_s"])
    summary["decision"] = decision

    return {
        "schema": "cmpct-v030-r24-worker-policy-propagation-v2",
        "source_commit": source_commit(),
        "target": list(TARGET),
        "rounds": ROUNDS,
        "rows": rows,
        "identity": {
            "all_strong_verified": verified,
            "single_logical_tree": len(trees) == 1,
            "repeatable_per_mode": repeatable,
            "single_propagated_exact": single_propagated_exact,
            "inherited_differs": inherited_differs,
            "propagated_parallel": propagated_parallel,
            "predicted_dictionary_flip": predicted_dict_flip,
            "worker_counts": worker_counts,
            "dictionary_states": dict_states,
        },
        "summary": summary,
        "production_change": False,
        "release_credit": False,
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path)
    p.add_argument("--output", type=Path)
    p.add_argument("--worker-mode", choices=("inherited", "single", "propagated"))
    p.add_argument("--worker-source", type=Path)
    p.add_argument("--worker-archive", type=Path)
    a = p.parse_args()
    if a.worker_mode:
        print(json.dumps(build_worker(a.worker_mode, a.worker_source, a.worker_archive), sort_keys=True, default=str))
        return
    evidence = run(a.work_root)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"summary": evidence["summary"], "identity": evidence["identity"]}, indent=2))


if __name__ == "__main__":
    main()
