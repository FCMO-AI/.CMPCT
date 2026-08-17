from __future__ import annotations

"""Frozen incremental gate for G5 adaptive lane ordering.

This probe deliberately measures G5 against the already-existing G0-G4 Representation Compiler incumbent,
not against direct Zstd.  It regenerates the exact public analytics and ML trees, verifies their tree hashes,
then prices every balanced node of ``features.npy`` and ``scales.npy`` with the same descriptor-aware stored
cost used by the production candidate.  ``model.q4.bin`` is retained as a hostile/high-entropy negative.

Passing this mechanism gate does not authorize release; it merely earns G5 a place in the consolidated
complete-artifact candidate.  Thresholds are frozen from earlier detached evidence and may not be weakened.
"""
import argparse
import json
from pathlib import Path
import shutil
import time

from benchmarks import neutral_hostile_corpus_v1 as neutral
from experiments import entropygraph_v030_representation_compiler as RC

EXPECTED = {
    "04_analytics_and_database": "6d0854fe058a95258588b89dca653ac8f00c61f815c6127b179e86cc58b1789d",
    "09_ml_artifacts": "efc09910fea8ef67d24cd8957d3d576df3a7cc7f10f14585e3a3ae269017901d",
}
MIN_SCALES_SAVING = 16 * 1024
MIN_FEATURES_SAVING = 8 * 1024
MIN_AGGREGATE_SAVING = 24 * 1024


def _generate(parent: Path, name: str) -> Path:
    if name == "04_analytics_and_database":
        neutral.corpus_analytics(parent)
    elif name == "09_ml_artifacts":
        neutral.corpus_ml(parent)
    else:  # pragma: no cover - frozen caller table.
        raise RuntimeError(name)
    root = parent / name
    got = neutral.tree_hash(root)
    if got != EXPECTED[name]:
        raise RuntimeError(f"G5 source identity drift for {name}: expected {EXPECTED[name]}, got {got}")
    return root


def _measure_file(path: Path) -> dict:
    raw = path.read_bytes()
    rows = []
    started = time.perf_counter()
    for index, part in enumerate(RC.G.L._balanced_chunks(raw)):
        logical_hash = RC.G.H(part)
        incumbent = RC._g0_g4(part)
        incumbent_cost = RC._stored_cost(incumbent, len(part), logical_hash)
        selected = RC.encode_node(part)
        selected_cost = int(selected["selected_stored_cost"])
        if selected_cost > incumbent_cost:
            raise RuntimeError("G5 compiler regressed a node despite fallback")
        restored = RC.inverse_physical(selected["kind"], selected.get("param", 0), selected["physical"], len(part))
        if restored != part:
            raise RuntimeError("G5 selected node failed exact inverse")
        rows.append({
            "node": index,
            "logical_bytes": len(part),
            "g0_g4_kind": incumbent["kind"],
            "g0_g4_stored_cost": incumbent_cost,
            "selected_kind": selected["kind"],
            "selected_stored_cost": selected_cost,
            "saving_vs_g0_g4_bytes": incumbent_cost - selected_cost,
            "g5_strategy": selected.get("g5_strategy"),
            "g5_exact_finalists": selected["g5_exact_finalists"],
        })
    return {
        "path": path.name,
        "logical_bytes": len(raw),
        "nodes": rows,
        "saving_vs_g0_g4_bytes": sum(row["saving_vs_g0_g4_bytes"] for row in rows),
        "g5_selected_nodes": sum(row["selected_kind"] == "lane_perm" for row in rows),
        "entropy_selected_nodes": sum(row.get("g5_strategy") == "entropy" for row in rows),
        "histogram_chain_selected_nodes": sum(row.get("g5_strategy") == "histogram-chain" for row in rows),
        "wall_s": time.perf_counter() - started,
    }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True, exist_ok=True)
    analytics = _generate(work_root, "04_analytics_and_database")
    ml = _generate(work_root, "09_ml_artifacts")
    features = _measure_file(analytics / "features.npy")
    scales = _measure_file(ml / "scales.npy")
    hostile = _measure_file(ml / "model.q4.bin")
    total = features["saving_vs_g0_g4_bytes"] + scales["saving_vs_g0_g4_bytes"]
    gate = (
        scales["saving_vs_g0_g4_bytes"] >= MIN_SCALES_SAVING
        and features["saving_vs_g0_g4_bytes"] >= MIN_FEATURES_SAVING
        and total >= MIN_AGGREGATE_SAVING
        and scales["g5_selected_nodes"] > 0
        and features["g5_selected_nodes"] > 0
        and all(row["saving_vs_g0_g4_bytes"] >= 0 for row in hostile["nodes"])
    )
    return {
        "schema": "cmpct-v030-g5-incremental-v1",
        "status": "RESEARCH_INCREMENTAL_GATE_NOT_RELEASE",
        "claim_boundary": "Exact public-tree node/storage-cost evidence only; complete consolidated archive still required.",
        "contract": {
            "minimum_scales_saving_bytes": MIN_SCALES_SAVING,
            "minimum_features_saving_bytes": MIN_FEATURES_SAVING,
            "minimum_aggregate_saving_bytes": MIN_AGGREGATE_SAVING,
            "node_regression_tolerance_bytes": 0,
            "exact_inverse_required": True,
        },
        "tree_sha256": dict(EXPECTED),
        "rows": [features, scales, hostile],
        "totals": {
            "target_saving_vs_g0_g4_bytes": total,
            "g5_selected_nodes": features["g5_selected_nodes"] + scales["g5_selected_nodes"],
            "hostile_g5_selected_nodes": hostile["g5_selected_nodes"],
            "mechanism_gate": gate,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["totals"], indent=2, sort_keys=True))
    if not result["totals"]["mechanism_gate"]:
        raise SystemExit("G5 incremental gate failed; do not weaken thresholds")


if __name__ == "__main__":
    main()
