from __future__ import annotations

"""Generalization benchmark for the attempt-5 CMPCT research candidate.

The campaign-specific 18-workload gate has already passed.  This harness returns to the exact 15 public
workloads that supported v0.28 and asks a different question: does the new compiler preserve every old
result and improve at least one of them, or is it specialized to the newly designed multi-root frontier?

Footnote: each attempt-5 build internally produces its own exact v0.28 portfolio baseline from the same
source tree.  The harness also checks regenerated tree hashes and v0.28 artifact bytes against the
preserved 2026-08-16 v0.28 evidence.  Baseline drift therefore fails visibly instead of being mistaken
for a new compression gain.
"""

import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import statistics
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
ENGINE_PATH = ROOT / "experiments" / "entropygraph_v029_residual_strict.py"
V028_HISTORY = ROOT / "benchmarks" / "history" / "2026-08-16-entropygraph-v028.json"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


ENGINE = _load(ENGINE_PATH, "cmpct_v029_generalization_engine")


def _tree_stats(root: Path) -> tuple[int, int]:
    files = [path for path in root.rglob("*") if path.is_file()]
    return len(files), sum(path.stat().st_size for path in files)


def _preserved_rows() -> dict[tuple[str, str], dict]:
    record = json.loads(V028_HISTORY.read_text(encoding="utf-8"))
    return {(row["suite"], row["name"]): row for row in record["rows"]}


def _measure_workload(suite: str, path: Path, archive_dir: Path, preserved: dict) -> dict:
    archive_dir.mkdir(parents=True, exist_ok=True)
    archive = archive_dir / f"{path.name}.cmpct"
    files, logical = _tree_stats(path)
    expected = preserved[(suite, path.name)]
    tree = ENGINE.BASE.treehash(path)
    baseline_tree_match = tree == expected["tree_sha256"]

    started = time.perf_counter()
    result = ENGINE.build(path, archive)
    wall = time.perf_counter() - started
    verified = ENGINE.strong_verify(archive)
    if not verified.get("ok") or verified["tree_sha256"] != tree:
        raise RuntimeError(f"attempt-5 strong verification failed for {suite}/{path.name}")

    stats = result["mosaic"]
    embedded_v028_create = float(result["v028"].get("portfolio_create_s", 0.0))
    baseline_bytes_match = int(result["v028_bytes"]) == int(expected["candidate_bytes"])
    return {
        "suite": suite,
        "name": path.name,
        "files": files,
        "logical_bytes": logical,
        "tree_sha256": tree,
        "preserved_tree_sha256": expected["tree_sha256"],
        "baseline_tree_match": baseline_tree_match,
        "preserved_v028_bytes": int(expected["candidate_bytes"]),
        "v028_bytes": int(result["v028_bytes"]),
        "baseline_bytes_match": baseline_bytes_match,
        "candidate_bytes": int(result["archive_bytes"]),
        "research_graph_bytes": int(result["mosaic_graph_bytes"]),
        "selected": result["selected"],
        "saving_vs_v028_bytes": int(result["v028_bytes"] - result["archive_bytes"]),
        "saving_vs_v028_pct": (
            (result["v028_bytes"] - result["archive_bytes"]) / max(1, result["v028_bytes"]) * 100.0
        ),
        "mosaic_nodes": int(stats.get("mosaic_nodes", 0)),
        "residual_pack_records": int(stats.get("residual_pack_records", 0)),
        "residual_packed_delta_nodes": int(stats.get("residual_packed_delta_nodes", 0)),
        "max_mosaic_read_amplification": float(stats.get("max_mosaic_read_amplification", 0.0)),
        "max_additional_recipe_read_amplification": float(
            stats.get("max_additional_recipe_read_amplification", 0.0)
        ),
        "attempt5_portfolio_create_s": float(result["portfolio_create_s"]),
        "embedded_v028_portfolio_create_s": embedded_v028_create,
        "create_ratio_vs_v028": (
            float(result["portfolio_create_s"]) / embedded_v028_create if embedded_v028_create > 0 else None
        ),
        "build_wall_s": wall,
        "strong_verify_s": None,
    }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    preserved = _preserved_rows()
    neutral = _load(ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py", "cmpct_v029_general_neutral")
    hostile = _load(ROOT / "benchmarks" / "resemblance_hostile_corpus_v1.py", "cmpct_v029_general_hostile")

    rows = []
    suites = [
        ("neutral_hostile_v1", neutral, work_root / "neutral"),
        ("resemblance_hostile_v1", hostile, work_root / "resemblance"),
    ]
    for label, builder, root in suites:
        builder.build(root)
        for workload in sorted(path for path in root.iterdir() if path.is_dir()):
            row = _measure_workload(label, workload, work_root / "archives" / label, preserved)
            rows.append(row)
            print(json.dumps({
                "suite": label,
                "name": workload.name,
                "v028": row["v028_bytes"],
                "candidate": row["candidate_bytes"],
                "selected": row["selected"],
                "baseline_tree_match": row["baseline_tree_match"],
                "baseline_bytes_match": row["baseline_bytes_match"],
                "create_ratio": row["create_ratio_vs_v028"],
            }), flush=True)

    v028_total = sum(row["v028_bytes"] for row in rows)
    candidate_total = sum(row["candidate_bytes"] for row in rows)
    attempt5_create = sum(row["attempt5_portfolio_create_s"] for row in rows)
    v028_create = sum(row["embedded_v028_portfolio_create_s"] for row in rows)
    totals = {
        "workloads": len(rows),
        "v028_bytes": v028_total,
        "candidate_bytes": candidate_total,
        "smaller_than_v028_pct": (
            (v028_total - candidate_total) / v028_total * 100.0 if v028_total else 0.0
        ),
        "workloads_improved": sum(row["candidate_bytes"] < row["v028_bytes"] for row in rows),
        "workloads_regressed": sum(row["candidate_bytes"] > row["v028_bytes"] for row in rows),
        "research_selected": sum(row["selected"] == "mosaic" for row in rows),
        "baseline_tree_drift_rows": sum(not row["baseline_tree_match"] for row in rows),
        "baseline_byte_drift_rows": sum(not row["baseline_bytes_match"] for row in rows),
        "mosaic_nodes": sum(row["mosaic_nodes"] for row in rows),
        "residual_pack_records": sum(row["residual_pack_records"] for row in rows),
        "residual_packed_delta_nodes": sum(row["residual_packed_delta_nodes"] for row in rows),
        "max_mosaic_read_amplification": max(
            (row["max_mosaic_read_amplification"] for row in rows), default=0.0
        ),
        "max_additional_recipe_read_amplification": max(
            (row["max_additional_recipe_read_amplification"] for row in rows), default=0.0
        ),
        "attempt5_portfolio_create_s": attempt5_create,
        "embedded_v028_portfolio_create_s": v028_create,
        "creation_ratio_vs_v028": attempt5_create / v028_create if v028_create else None,
        "median_workload_creation_ratio_vs_v028": statistics.median(
            row["create_ratio_vs_v028"] for row in rows if row["create_ratio_vs_v028"] is not None
        ),
    }
    return {
        "schema": "cmpct-v029-generalization-v1",
        "claim_boundary": (
            "attempt-5 generalization versus exact embedded v0.28 portfolio on the preserved 15-workload frontier"
        ),
        "engine": "experiments/entropygraph_v029_residual_strict.py",
        "preserved_baseline": "benchmarks/history/2026-08-16-entropygraph-v028.json",
        "rows": rows,
        "totals": totals,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("CMPCT_V029_Generalization"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run(args.work_root)
    text = json.dumps(result, indent=2)
    print(json.dumps(result["totals"], indent=2))
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
