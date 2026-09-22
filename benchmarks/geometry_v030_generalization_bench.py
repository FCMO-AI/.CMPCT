from __future__ import annotations

"""Exact-tree full-artifact generalization gate for the CMPCT v0.30 Geometry Compiler seed.

Every workload is generated once.  ``Geometry.build`` then constructs both the accepted v0.29 release
artifact and Geometry from that same still-live tree and emits the smaller complete archive.  A transform
that looks spectacular in isolation therefore cannot create a workload regression or borrow a historical
baseline generated from different producer bytes.

Four neutral/hostile workloads use the accepted repair-v5 portable identity before either contender sees
the tree.  This keeps the v0.30 research gate aligned with the exact 15-workload substrate used by the
accepted v0.29 generalization evidence instead of silently reviving nondeterministic media-producer bytes.

Footnote: this remains a research-seed gate.  It can prove a storage mechanism and open explicit creation-
time debt; numeric promotion still requires rehabilitation and the unchanged direct-base release gate.
"""

import argparse
import json
from pathlib import Path
import shutil
import time

from benchmarks import neutral_hostile_corpus_v1 as neutral
from benchmarks import neutral_hostile_determinism_repair_v5 as repair
from benchmarks import resemblance_hostile_corpus_v1 as resemblance
from experiments import entropygraph_v030_geometry as geometry

EXPECTED_WORKLOADS = 15
MIN_AGGREGATE_SAVING = 256 * 1024
MIN_SINGLE_WORKLOAD_SAVING = 256 * 1024


def _files_and_bytes(root: Path) -> tuple[int, int]:
    files = [path for path in root.rglob("*") if path.is_file()]
    return len(files), sum(path.stat().st_size for path in files)


def _run_workload(suite: str, root: Path, work_root: Path) -> dict:
    out = work_root / f"{suite}-{root.name}.cmpct"
    started = time.perf_counter(); result = geometry.build(root, out); wall = time.perf_counter() - started
    verified = geometry.strong_verify(out); expected_tree = geometry.treehash(root)
    if not verified.get("ok") or verified.get("tree_sha256") != expected_tree:
        raise RuntimeError(f"Geometry portfolio verification failed for {suite}/{root.name}")
    files, logical = _files_and_bytes(root); base = int(result["v029_bytes"]); candidate = int(result["archive_bytes"])
    if candidate > base:
        raise RuntimeError(f"Geometry portfolio size regression for {suite}/{root.name}: {candidate}>{base}")
    graph = result.get("geometry") or {}
    row = {
        "suite": suite, "name": root.name, "files": files, "logical_bytes": logical,
        "tree_sha256": expected_tree, "selected": result["selected"], "v029_bytes": base,
        "candidate_bytes": candidate, "geometry_graph_bytes": int(result["geometry_graph_bytes"]),
        "saving_vs_v029_bytes": base - candidate,
        "saving_vs_v029_pct": (base - candidate) / max(1, base) * 100.0,
        "portfolio_create_s": float(result["portfolio_create_s"]), "benchmark_wall_s": wall,
        "lane_nodes": int(graph.get("lane_nodes") or 0),
        "delimiter_nodes": int(graph.get("delimiter_nodes") or 0),
        "transform_payload_saving_bytes": int(graph.get("transform_payload_saving_bytes") or 0),
        "delimiter_histogram": graph.get("delimiter_histogram") or {},
        "max_read_amplification": float(graph.get("max_read_amplification") or 0.0),
        "max_decode_unit": int(graph.get("max_decode_unit") or geometry.MAX_DECODE_UNIT),
    }
    print(json.dumps(row, sort_keys=True), flush=True)
    return row


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True); work_root.mkdir(parents=True)
    neutral_root = work_root / "corpora" / "neutral"; resemblance_root = work_root / "corpora" / "resemblance"

    # Footnote: repair-v5 hooks must be installed before generation, and normalization must finish before
    # either accepted v0.29 or Geometry is built.  Applying it to only one contender would manufacture a
    # gain; applying it here changes only benchmark identity and keeps both archives on byte-identical input.
    repair.install_generation_hooks(neutral)
    print("building neutral/hostile v1 (portable repair-v5 identity)", flush=True); neutral_manifest = neutral.build(neutral_root)
    repair.normalize_root(neutral_root)
    print("building resemblance-hostile v1", flush=True); resemblance_manifest = resemblance.build(resemblance_root)
    rows: list[dict] = []
    for root in sorted(path for path in neutral_root.iterdir() if path.is_dir()):
        rows.append(_run_workload("neutral_hostile_v1", root, work_root))
    for root in sorted(path for path in resemblance_root.iterdir() if path.is_dir()):
        rows.append(_run_workload("resemblance_hostile_v1", root, work_root))
    if len(rows) != EXPECTED_WORKLOADS:
        raise RuntimeError(f"expected {EXPECTED_WORKLOADS} workloads, got {len(rows)}")
    baseline = sum(row["v029_bytes"] for row in rows); candidate = sum(row["candidate_bytes"] for row in rows)
    saving = baseline - candidate; improved = [row for row in rows if row["candidate_bytes"] < row["v029_bytes"]]
    totals = {
        "workloads": len(rows), "v029_bytes": baseline, "candidate_bytes": candidate,
        "saving_vs_v029_bytes": saving, "smaller_than_v029_pct": saving / max(1, baseline) * 100.0,
        "workloads_improved": len(improved), "workloads_regressed": 0,
        "geometry_selected": sum(row["selected"] == "geometry" for row in rows),
        "max_single_workload_saving_bytes": max(row["saving_vs_v029_bytes"] for row in rows),
        "lane_nodes": sum(row["lane_nodes"] for row in rows),
        "delimiter_nodes": sum(row["delimiter_nodes"] for row in rows),
        "transform_payload_saving_bytes": sum(row["transform_payload_saving_bytes"] for row in rows),
        "max_read_amplification": max((row["max_read_amplification"] for row in improved), default=0.0),
        "mechanism_gate": saving >= MIN_AGGREGATE_SAVING and max(row["saving_vs_v029_bytes"] for row in rows) >= MIN_SINGLE_WORKLOAD_SAVING,
    }
    return {
        "schema": "cmpct-v030-geometry-generalization-v1",
        "claim_boundary": "Breakthrough seed only; accepted v0.29 exact workload fallback; canonical r24 unchanged.",
        "benchmark_contract": {
            "direct_base": "accepted v0.29 release engine built from the same live workload tree",
            "benchmark_identity": "accepted neutral-hostile repair-v5 plus historical resemblance-hostile v1",
            "archive_size_regression_tolerance_bytes": 0, "expected_workloads": EXPECTED_WORKLOADS,
            "minimum_aggregate_breakthrough_saving_bytes": MIN_AGGREGATE_SAVING,
            "minimum_single_workload_breakthrough_saving_bytes": MIN_SINGLE_WORKLOAD_SAVING,
            "correctness": "strong tree SHA-256 must equal the source tree on every emitted artifact",
            "timing": "diagnostic in seed stage; all confirmed debt must close before numeric promotion",
        },
        "generators": {"neutral": {"schema": neutral_manifest.get("schema"), "seed": neutral_manifest.get("seed"), "identity": "repair-v5"},
                       "resemblance": {"schema": resemblance_manifest.get("schema"), "seed": resemblance_manifest.get("seed")}},
        "rows": rows, "totals": totals,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/geometry-v030-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/geometry-v030-generalization.json"))
    args = parser.parse_args(); result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True); args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result["totals"], indent=2), flush=True)
    if not result["totals"]["mechanism_gate"]:
        raise SystemExit("Geometry failed preregistered breakthrough mechanism gate")


if __name__ == "__main__":
    main()
