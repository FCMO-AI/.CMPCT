from __future__ import annotations

"""Full-artifact benchmark for the bounded multi-root + residual-placement research campaign.

For every deterministic workload the strict-reconciled attempt-5 engine builds:

1. the complete **released strict v0.28** portfolio artifact;
2. the complete research graph, where attempt #4 placement is preserved and attempt #5 may additionally
   co-pack bounded one-base reconstruction programs;
3. an outer portfolio that copies strict v0.28 byte-for-byte whenever the research graph is not smaller.

Footnote: attempt #5 originally passed the encoded full-artifact thresholds but a post-pass audit found
that its lineage still used the pre-strict v0.28 root-pack selector, allowing ~23.68x ordinary pack
amplification on the compressed-stream workload.  This benchmark keeps every original byte/coverage
threshold and adds the already-inherited <=8x *ordinary pack* locality requirement.  A loss caused by
that repair is mechanism evidence, not a reason to weaken either locality or the frozen coverage gate.
"""

import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import statistics
import sys
import time

from mosaic_hostile_corpus_v1 import build as build_v1
from mosaic_stress_corpus_v2 import build as build_v2

ROOT = Path(__file__).resolve().parents[1]
ENGINE_PATH = ROOT / "experiments" / "entropygraph_v029_strict_reconcile.py"


def _load_engine():
    spec = importlib.util.spec_from_file_location("cmpct_mosaic_full_archive_bench_engine", ENGINE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load strict-reconciled attempt-5 research engine")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


ENGINE = _load_engine()


def _measure_workload(path: Path, scratch: Path) -> dict:
    # Footnote: the first full-artifact CI attempt failed here before measuring any archive because the
    # per-suite scratch directory did not yet exist. Create it explicitly rather than letting a harness
    # accident masquerade as compression evidence.
    scratch.mkdir(parents=True, exist_ok=True)
    archive = scratch / f"{path.name}.cmpct"
    t0 = time.perf_counter()
    result = ENGINE.build(path, archive)
    build_wall = time.perf_counter() - t0

    verify_samples = []
    for _ in range(2):
        started = time.perf_counter()
        verified = ENGINE.strong_verify(archive)
        verify_samples.append(time.perf_counter() - started)
        if not verified.get("ok"):
            raise RuntimeError(f"strong verification failed for {path.name}")
    if verified["tree_sha256"] != ENGINE.BASE.treehash(path):
        raise RuntimeError(f"tree hash mismatch for {path.name}")

    mosaic_stats = result["mosaic"]
    return {
        "name": path.name,
        "tree_sha256": ENGINE.BASE.treehash(path),
        "selected": result["selected"],
        "strict_v028_reconciled": bool(result.get("strict_v028_reconciled")),
        "v028_bytes": int(result["v028_bytes"]),
        "mosaic_graph_bytes": int(result["mosaic_graph_bytes"]),
        "candidate_bytes": int(result["archive_bytes"]),
        "saving_vs_v028_bytes": int(result["v028_bytes"] - result["archive_bytes"]),
        "saving_vs_v028_pct": float(result["smaller_than_v028_pct"]),
        "mosaic_nodes": int(mosaic_stats["mosaic_nodes"]),
        "single_delta_nodes": int(mosaic_stats["single_delta_nodes"]),
        "mosaic_auditions": int(mosaic_stats["mosaic_auditions"]),
        "mosaic_estimated_record_savings": int(mosaic_stats["mosaic_estimated_record_savings"]),
        "pack_read_amplification": float(mosaic_stats["pack_read_amplification"]),
        "max_mosaic_read_amplification": float(mosaic_stats["max_mosaic_read_amplification"]),
        "residual_pack_records": int(mosaic_stats.get("residual_pack_records", 0)),
        "residual_packed_delta_nodes": int(mosaic_stats.get("residual_packed_delta_nodes", 0)),
        "max_additional_recipe_read_amplification": float(
            mosaic_stats.get("max_additional_recipe_read_amplification", 0.0)
        ),
        "mosaic_graph_create_s": float(mosaic_stats["create_s"]),
        "portfolio_create_s": float(result["portfolio_create_s"]),
        "build_wall_s": build_wall,
        "strong_verify_median_s": statistics.median(verify_samples),
    }


def _measure_suite(label: str, builder, root: Path, scratch: Path) -> dict:
    manifest = builder(root)
    rows = []
    for workload in manifest["workloads"]:
        rows.append(_measure_workload(root / workload["name"], scratch / label))

    base = sum(row["v028_bytes"] for row in rows)
    candidate = sum(row["candidate_bytes"] for row in rows)
    return {
        "label": label,
        "corpus": manifest,
        "rows": rows,
        "totals": {
            "v028_bytes": base,
            "candidate_bytes": candidate,
            "smaller_than_v028_pct": (base - candidate) / base * 100.0 if base else 0.0,
            "workloads": len(rows),
            "workloads_improved": sum(row["candidate_bytes"] < row["v028_bytes"] for row in rows),
            "workloads_regressed": sum(row["candidate_bytes"] > row["v028_bytes"] for row in rows),
            "mosaic_selected": sum(row["selected"] == "mosaic" for row in rows),
            "mosaic_nodes": sum(row["mosaic_nodes"] for row in rows),
            "residual_pack_records": sum(row["residual_pack_records"] for row in rows),
            "residual_packed_delta_nodes": sum(row["residual_packed_delta_nodes"] for row in rows),
            "max_pack_read_amplification": max(
                (row["pack_read_amplification"] for row in rows), default=0.0
            ),
            "max_mosaic_read_amplification": max(
                (row["max_mosaic_read_amplification"] for row in rows), default=0.0
            ),
            "max_additional_recipe_read_amplification": max(
                (row["max_additional_recipe_read_amplification"] for row in rows), default=0.0
            ),
            "portfolio_create_s": sum(row["portfolio_create_s"] for row in rows),
        },
    }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    v1_root = work_root / "v1-corpus"
    v2_root = work_root / "v2-corpus"
    scratch = work_root / "archives"
    scratch.mkdir()

    v1 = _measure_suite("v1", build_v1, v1_root, scratch)
    v2 = _measure_suite("v2", build_v2, v2_root, scratch)
    all_rows = v1["rows"] + v2["rows"]
    base = sum(row["v028_bytes"] for row in all_rows)
    candidate = sum(row["candidate_bytes"] for row in all_rows)
    return {
        "schema": "cmpct-mosaic-v029-full-artifact-v1",
        "claim_boundary": (
            "complete strict-reconciled research artifacts versus complete released-strict v0.28 portfolio artifacts; canonical revision 24 unchanged"
        ),
        "engine": "experiments/entropygraph_v029_strict_reconcile.py",
        "suites": {"v1": v1, "v2": v2},
        "combined": {
            "v028_bytes": base,
            "candidate_bytes": candidate,
            "smaller_than_v028_pct": (base - candidate) / base * 100.0 if base else 0.0,
            "workloads": len(all_rows),
            "workloads_improved": sum(row["candidate_bytes"] < row["v028_bytes"] for row in all_rows),
            "workloads_regressed": sum(row["candidate_bytes"] > row["v028_bytes"] for row in all_rows),
            "mosaic_selected": sum(row["selected"] == "mosaic" for row in all_rows),
            "mosaic_nodes": sum(row["mosaic_nodes"] for row in all_rows),
            "residual_pack_records": sum(row["residual_pack_records"] for row in all_rows),
            "residual_packed_delta_nodes": sum(row["residual_packed_delta_nodes"] for row in all_rows),
            "max_pack_read_amplification": max(
                (row["pack_read_amplification"] for row in all_rows), default=0.0
            ),
            "max_mosaic_read_amplification": max(
                (row["max_mosaic_read_amplification"] for row in all_rows), default=0.0
            ),
            "max_additional_recipe_read_amplification": max(
                (row["max_additional_recipe_read_amplification"] for row in all_rows), default=0.0
            ),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("CMPCT_Mosaic_Full_Artifact"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run(args.work_root)
    text = json.dumps(result, indent=2)
    print(text)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
