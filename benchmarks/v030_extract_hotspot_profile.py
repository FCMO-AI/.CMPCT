from __future__ import annotations

"""Research-only cProfile attribution for canonical v0.30 extraction.

No product mutation. The profiler answers which concrete reader/restoration functions own extraction CPU after the
single-session family was falsified, so the next intervention can target reconstruction/data movement rather than wrappers.
Absolute profiled wall time is not release evidence.
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


def _profile_one(source: Path, root: Path, label: str) -> dict:
    archive = root / f"{label}.cmpct"
    dst = root / f"{label}-extract"
    build = PRODUCT.build(source, archive)
    expected = PRODUCT.treehash(source)
    profiler = cProfile.Profile()
    started = time.perf_counter()
    profiler.enable()
    PRODUCT.extract(archive, dst)
    profiler.disable()
    wall = time.perf_counter() - started
    if PRODUCT.treehash(dst) != expected:
        raise RuntimeError(f"{label} extraction semantic-tree drift")
    stats = pstats.Stats(profiler)
    rows = []
    for (filename, lineno, function), (cc, nc, tt, ct, _callers) in stats.stats.items():
        rows.append({"file": filename, "line": lineno, "function": function, "primitive_calls": cc,
                     "calls": nc, "self_s": tt, "cumulative_s": ct})
    rows.sort(key=lambda row: (row["cumulative_s"], row["self_s"]), reverse=True)
    return {"workload": label, "archive_bytes": archive.stat().st_size, "selected": build.get("selected"),
            "profiled_wall_s": wall, "total_profile_cpu_s": stats.total_tt,
            "top_by_cumulative": rows[:40],
            "claim_boundary": "profiling/attribution only; profiler timings are not release performance evidence"}


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    roots = PERF._build_corpora(work_root / "corpora")
    wanted = (("09_ml_artifacts", roots[("neutral_hostile_v1", "09_ml_artifacts")]),
              ("05_logs", roots[("neutral_hostile_v1", "05_logs")]))
    return {"schema": "cmpct-v030-extract-hotspot-profile-v1",
            "results": [_profile_one(source, work_root, label) for label, source in wanted]}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-extract-hotspot-profile-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-extract-hotspot-profile.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    for result_row in result["results"]:
        print(result_row["workload"], result_row["profiled_wall_s"])
        for row in result_row["top_by_cumulative"][:12]:
            print(f"  {row['cumulative_s']:.6f}s cum {row['self_s']:.6f}s self {row['function']} {row['file']}:{row['line']}")


if __name__ == "__main__":
    main()
