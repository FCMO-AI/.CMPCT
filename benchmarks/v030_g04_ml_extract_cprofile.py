from __future__ import annotations

"""Research-only cProfile ownership map for shipping ML G0-G4 extraction.

The profile is diagnostic, not a performance benchmark: profiler overhead invalidates wall-time
comparison. The canonical archive is built and strongly verified before profiling; one unprofiled
warm-up extraction is performed; then exactly one shipping PRODUCT.extract() call is profiled into a
fresh destination and checked for strong tree identity. No product bytes, thresholds, or release law
are changed.
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
TOP_N = 50


def _row(key, value, total_tt: float) -> dict:
    filename, line, name = key
    cc, nc, tt, ct, _callers = value
    return {
        "filename": str(filename),
        "line": int(line),
        "function": str(name),
        "primitive_calls": int(cc),
        "total_calls": int(nc),
        "self_s": float(tt),
        "cumulative_s": float(ct),
        "self_fraction": float(tt / total_tt) if total_tt > 0 else 0.0,
    }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    roots = PERF._build_corpora(work_root / "corpus")
    source = roots[TARGET]
    source_tree = PRODUCT.treehash(source)
    archive = work_root / "ml.cmpct"

    with PRODUCT.C._revision25_profile_context():
        build_started = time.perf_counter()
        built = PRODUCT.build(source, archive)
        build_s = time.perf_counter() - build_started
        if archive.read_bytes()[:8] != RR.G04.MAG:
            raise RuntimeError("canonical ML target did not select G0-G4")
        verified = PRODUCT.strong_verify(archive)
        if not verified.get("ok") or verified.get("tree_sha256") != source_tree:
            raise RuntimeError("shipping strong verification failed before profile")

        warm = work_root / "warm"
        PRODUCT.extract(archive, warm)
        if PRODUCT.treehash(warm) != source_tree:
            raise RuntimeError("warm-up extraction identity failure")

        profiled = work_root / "profiled"
        profile = cProfile.Profile()
        wall_started = time.perf_counter()
        profile.enable()
        PRODUCT.extract(archive, profiled)
        profile.disable()
        profiled_wall_s = time.perf_counter() - wall_started
        if PRODUCT.treehash(profiled) != source_tree:
            raise RuntimeError("profiled extraction identity failure")

    stats = pstats.Stats(profile)
    total_tt = float(stats.total_tt)
    rows = [_row(key, value, total_tt) for key, value in stats.stats.items()]
    by_self = sorted(rows, key=lambda row: row["self_s"], reverse=True)[:TOP_N]
    by_cumulative = sorted(rows, key=lambda row: row["cumulative_s"], reverse=True)[:TOP_N]
    top3_self_fraction = sum(row["self_fraction"] for row in by_self[:3])
    return {
        "schema": "cmpct-v030-g04-ml-extract-cprofile-v1",
        "target": "/".join(TARGET),
        "shipping_build": built,
        "archive_bytes": archive.stat().st_size,
        "source_tree_sha256": source_tree,
        "build_elapsed_s_context_only": float(build_s),
        "profiled_extract_wall_s_context_only": float(profiled_wall_s),
        "profile_total_self_s": total_tt,
        "top_self_function_fraction": float(by_self[0]["self_fraction"] if by_self else 0.0),
        "top3_self_fraction": float(top3_self_fraction),
        "top_by_self": by_self,
        "top_by_cumulative": by_cumulative,
        "release_credit": False,
        "claim_boundary": "cProfile diagnostic ownership only. Profiled wall time includes profiler overhead and is not release-performance evidence. Function attribution may route the next experiment but cannot promote a mechanism.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-g04-ml-extract-cprofile-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-g04-ml-extract-cprofile.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "schema": result["schema"],
        "archive_bytes": result["archive_bytes"],
        "build_elapsed_s_context_only": result["build_elapsed_s_context_only"],
        "profile_total_self_s": result["profile_total_self_s"],
        "top_self_function_fraction": result["top_self_function_fraction"],
        "top3_self_fraction": result["top3_self_fraction"],
        "top_by_self": result["top_by_self"][:15],
        "release_credit": False,
    }, indent=2), flush=True)


if __name__ == "__main__":
    main()
