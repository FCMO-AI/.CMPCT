from __future__ import annotations

"""Research-only causal counterfactual for the v0.30 ML extraction bottleneck.

The exact-head shipping profile identifies DGO1 delimiter inversion as the dominant extraction owner on
neutral_hostile_v1/09_ml_artifacts. This instrument changes no archive grammar or release threshold: it builds the
ordinary shipping product, then rebuilds the same source with delimiter auditions disabled while leaving lane and
all other G0-G4 mechanisms intact. It measures complete archive bytes, build wall time, and warm extraction wall
time for both, with exact user-tree identity checked after every timed extraction. Results are research evidence
only; build timings are same-process causal diagnostics rather than release-performance credit.
"""

import argparse
import json
from pathlib import Path
import shutil
import statistics
import time

from benchmarks import v030_release_performance as PERF
from experiments import entropygraph_v030_geometry_overlay as G04
from experiments import entropygraph_v030_release_product as PRODUCT

TARGET = ("neutral_hostile_v1", "09_ml_artifacts")
ROUNDS = 7


def _selected_transforms(build_stats: dict) -> list[str]:
    auditions = build_stats.get("r25", {}).get("g04", {}).get("auditions", [])
    return [str(row.get("selected")) for row in auditions if row.get("selected") not in (None, "none")]


def _timed_extracts(archive: Path, source_tree: str, root: Path, label: str) -> list[float]:
    warm = root / f"{label}-warm"
    PRODUCT.extract(archive, warm)
    if PRODUCT.treehash(warm) != source_tree:
        raise RuntimeError(f"{label} warm extraction identity failure")
    samples: list[float] = []
    for index in range(ROUNDS):
        dst = root / f"{label}-{index}"
        started = time.perf_counter()
        PRODUCT.extract(archive, dst)
        elapsed = time.perf_counter() - started
        if PRODUCT.treehash(dst) != source_tree:
            raise RuntimeError(f"{label} timed extraction identity failure")
        samples.append(elapsed)
    return samples


def run(work: Path) -> dict:
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    source = PERF._build_corpora(work / "corpus")[TARGET]
    source_tree = PRODUCT.treehash(source)

    baseline_archive = work / "shipping.cmpct"
    started = time.perf_counter()
    baseline_build = PRODUCT.build(source, baseline_archive)
    baseline_build_s = time.perf_counter() - started
    baseline_verify = PRODUCT.strong_verify(baseline_archive)
    if not baseline_verify.get("ok") or baseline_verify.get("tree_sha256") != source_tree:
        raise RuntimeError("baseline shipping archive failed exact verification")
    baseline_transforms = _selected_transforms(baseline_build)
    if "delimiter" not in baseline_transforms:
        raise RuntimeError("exact-head ML shipping route no longer selects DGO1; counterfactual is stale")

    original_rank = G04._delimiter_rank
    candidate_archive = work / "no-delimiter.cmpct"
    try:
        G04._delimiter_rank = lambda _raw: []
        started = time.perf_counter()
        candidate_build = PRODUCT.build(source, candidate_archive)
        candidate_build_s = time.perf_counter() - started
    finally:
        G04._delimiter_rank = original_rank
    candidate_verify = PRODUCT.strong_verify(candidate_archive)
    if not candidate_verify.get("ok") or candidate_verify.get("tree_sha256") != source_tree:
        raise RuntimeError("no-delimiter candidate failed exact verification")
    candidate_transforms = _selected_transforms(candidate_build)
    if "delimiter" in candidate_transforms:
        raise RuntimeError("delimiter transform survived disabled delimiter audition")

    baseline_samples = _timed_extracts(baseline_archive, source_tree, work, "baseline")
    candidate_samples = _timed_extracts(candidate_archive, source_tree, work, "candidate")
    baseline_bytes = baseline_archive.stat().st_size
    candidate_bytes = candidate_archive.stat().st_size
    baseline_median = float(statistics.median(baseline_samples))
    candidate_median = float(statistics.median(candidate_samples))
    return {
        "schema": "cmpct-v030-g04-delimiter-cost-counterfactual-v1",
        "release_credit": False,
        "target": "/".join(TARGET),
        "source_tree_sha256": source_tree,
        "rounds": ROUNDS,
        "baseline": {
            "archive_bytes": baseline_bytes,
            "build_wall_s_context_only": baseline_build_s,
            "selected_transforms": baseline_transforms,
            "extract_s": baseline_samples,
            "median_extract_s": baseline_median,
        },
        "no_delimiter": {
            "archive_bytes": candidate_bytes,
            "build_wall_s_context_only": candidate_build_s,
            "selected_transforms": candidate_transforms,
            "extract_s": candidate_samples,
            "median_extract_s": candidate_median,
        },
        "delta": {
            "archive_bytes": candidate_bytes - baseline_bytes,
            "archive_pct": (candidate_bytes / baseline_bytes - 1.0) * 100.0,
            "build_wall_s_context_only": candidate_build_s - baseline_build_s,
            "build_ratio_context_only": candidate_build_s / baseline_build_s,
            "median_extract_s": candidate_median - baseline_median,
            "median_extract_ratio": candidate_median / baseline_median,
            "median_extract_speedup": baseline_median / candidate_median,
        },
        "claim_boundary": "Causal research counterfactual only: same source and shipping product with DGO1 auditions removed; no release threshold, evaluator, grammar, or comparator is changed. Build wall is diagnostic context, not release credit.",
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-root", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"baseline": result["baseline"], "no_delimiter": result["no_delimiter"], "delta": result["delta"], "release_credit": False}, indent=2))


if __name__ == "__main__":
    main()
