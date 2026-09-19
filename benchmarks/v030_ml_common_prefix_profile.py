from __future__ import annotations

"""Research-only profile of work duplicated by the co-critical v0.28 and attempt-5 ML children."""
import argparse, cProfile, json, pstats, shutil, time
from pathlib import Path
from benchmarks import v030_release_performance as PERF
from experiments import entropygraph_v028 as V028
from experiments import entropygraph_v029_residual_fast as A5

COMMON_NAMES = {
    "fastcdc", "similarity_sketch", "lsh_candidates", "delta_encode", "_compress_record",
    "_direct_cost", "_preflate_pack", "_choose_pack_plan", "read_bytes", "_merkle_root",
}


def _profile(label: str, fn, out: Path) -> dict:
    profiler = cProfile.Profile()
    started = time.perf_counter()
    profiler.enable()
    stats = fn(out)
    profiler.disable()
    wall = time.perf_counter() - started
    ps = pstats.Stats(profiler)
    rows = []
    common = []
    for (filename, line, name), values in ps.stats.items():
        cc, nc, tt, ct, _callers = values
        row = {"name": name, "file": Path(filename).name, "line": line, "calls": nc,
               "self_s": tt, "cumulative_s": ct}
        rows.append(row)
        if name in COMMON_NAMES:
            common.append(row)
    rows.sort(key=lambda row: row["self_s"], reverse=True)
    common.sort(key=lambda row: row["self_s"], reverse=True)
    return {"label": label, "wall_s": wall, "archive_bytes": out.stat().st_size,
            "selected": stats.get("selected") if isinstance(stats, dict) else None,
            "top_self": rows[:80], "common_named": common,
            "common_named_self_s": sum(row["self_s"] for row in common)}


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    corpora = PERF._build_corpora(work_root / "corpus")
    source = corpora[("neutral_hostile_v1", "09_ml_artifacts")]
    tree = A5.treehash(source)

    v028 = _profile("v028", lambda out: V028.build(source, out), work_root / "v028.cmpct")

    owner = A5.BASE.P
    original = owner._position_independent_candidates
    owner._position_independent_candidates = lambda _sketches, _nodes: []
    try:
        attempt5 = _profile("attempt5-neutral", lambda out: A5.build_graph(source, out), work_root / "attempt5.cmpct")
    finally:
        owner._position_independent_candidates = original

    for path in (work_root / "v028.cmpct", work_root / "attempt5.cmpct"):
        verified = A5.strong_verify(path) if path.name.startswith("attempt5") else V028.strong_verify(path)
        if not verified.get("ok") or verified.get("tree_sha256") != tree:
            raise RuntimeError(f"profiled child failed exact verification: {path.name}")

    shared_names = sorted(set(row["name"] for row in v028["common_named"]) &
                          set(row["name"] for row in attempt5["common_named"]))
    return {
        "schema": "cmpct-v030-ml-common-prefix-profile-v1",
        "release_credit": False,
        "source_tree_sha256": tree,
        "v028": v028,
        "attempt5": attempt5,
        "shared_common_names": shared_names,
        "claim_boundary": "cProfile attribution only. It may establish duplicated hot work and a lower-bound opportunity, but cannot grant product or release credit. Times are perturbed and are not fresh-process authority.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
