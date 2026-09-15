from __future__ import annotations

"""Research-only ownership profile for canonical ML extraction through the real shipping front door.

Unlike the older profiler, this instrument does not hold the private revision-25 profile context around
PRODUCT.build/extract. The product owns its own internal contexts. Construction is evidence setup only;
only one post-warmup PRODUCT.extract call is cProfile-instrumented. Profiled wall time receives no
release credit. Exact G04 selection and source/destination tree identity are mandatory.
"""

import argparse
import cProfile
import json
from pathlib import Path
import pstats
import shutil
import time

from benchmarks import v030_release_performance as PERF
from experiments import entropygraph_v030_release_product as PRODUCT
from experiments import entropygraph_v030_release_reader as RR

TARGET = ("neutral_hostile_v1", "09_ml_artifacts")


def run(work: Path) -> dict:
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    roots = PERF._build_corpora(work / "corpus")
    source = roots[TARGET]
    source_tree = PRODUCT.treehash(source)
    archive = work / "ml.cmpct"

    setup_started = time.perf_counter()
    built = PRODUCT.build(source, archive)
    build_s = time.perf_counter() - setup_started
    if archive.read_bytes()[:8] != RR.G04.MAG:
        raise RuntimeError("shipping ML target did not select G04")
    verified = PRODUCT.strong_verify(archive)
    if not verified.get("ok") or verified.get("tree_sha256") != source_tree:
        raise RuntimeError("shipping archive failed exact strong verification")

    warm = work / "warm"
    PRODUCT.extract(archive, warm)
    if PRODUCT.treehash(warm) != source_tree:
        raise RuntimeError("warm extraction identity failure")

    dst = work / "profiled"
    profile = cProfile.Profile()
    started = time.perf_counter()
    profile.enable()
    PRODUCT.extract(archive, dst)
    profile.disable()
    profiled_wall_s = time.perf_counter() - started
    if PRODUCT.treehash(dst) != source_tree:
        raise RuntimeError("profiled extraction identity failure")

    stats = pstats.Stats(profile)
    total = float(stats.total_tt)
    rows = []
    for (filename, line, function), (cc, nc, tt, ct, _callers) in stats.stats.items():
        rows.append({
            "filename": str(filename), "line": int(line), "function": str(function),
            "primitive_calls": int(cc), "total_calls": int(nc),
            "self_s": float(tt), "cumulative_s": float(ct),
            "self_fraction": float(tt / total) if total else 0.0,
        })
    return {
        "schema": "cmpct-v030-g04-ml-shipping-extract-profile-v1",
        "release_credit": False,
        "target": "/".join(TARGET),
        "diagnostic_route": "shipping-product-front-door-no-external-r25-context-v1",
        "archive_bytes": archive.stat().st_size,
        "source_tree_sha256": source_tree,
        "build_elapsed_s_context_only": build_s,
        "profiled_extract_wall_s_context_only": profiled_wall_s,
        "profile_total_self_s": total,
        "shipping_build": built,
        "top_by_self": sorted(rows, key=lambda r: r["self_s"], reverse=True)[:60],
        "top_by_cumulative": sorted(rows, key=lambda r: r["cumulative_s"], reverse=True)[:60],
        "claim_boundary": "Function-ownership diagnostic only; cProfile timing is not release performance evidence.",
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-root", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "schema": result["schema"],
        "archive_bytes": result["archive_bytes"],
        "build_elapsed_s_context_only": result["build_elapsed_s_context_only"],
        "profiled_extract_wall_s_context_only": result["profiled_extract_wall_s_context_only"],
        "top_by_self": result["top_by_self"][:15],
        "release_credit": False,
    }, indent=2))


if __name__ == "__main__":
    main()
