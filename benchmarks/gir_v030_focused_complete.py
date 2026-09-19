from __future__ import annotations

"""Focused complete-artifact gate for the self-contained CMPNX14 Geometry IR research grammar.

The detached G3/G4 payload oracles are only mechanism evidence.  This harness forces GIR to pay complete
archive framing on three exact public workloads chosen *before* the run because they exercise different
structured-byte regimes: logs/telemetry, analytics/database, and ML artifacts.

Every row rebuilds accepted v0.29 from the same still-live source tree, builds a complete CMPNX14 artifact,
strong-verifies both, and compares file sizes.  GIR itself (not workload fallback) must win all three rows.
The frozen gate is deliberately larger than the complete v0.29 portable gain: >=256 KiB per row and >=2 MiB
aggregate.  Failure does not license lowering the threshold; it sends the representation back to research.
"""

import argparse
import json
from pathlib import Path
import shutil
import time

from benchmarks import neutral_hostile_corpus_v1 as neutral
from benchmarks import neutral_hostile_determinism_repair_v5 as repair
from experiments import entropygraph_v030_gir_safe as GIR

EXPECTED = {
    "05_logs_and_telemetry": "7356b866d7b99bfce2dd1fc6ef86d61d09c9d8a38a2ff3fec7d9a92e46020931",
    "04_analytics_and_database": "6d0854fe058a95258588b89dca653ac8f00c61f815c6127b179e86cc58b1789d",
    "09_ml_artifacts": "efc09910fea8ef67d24cd8957d3d576df3a7cc7f10f14585e3a3ae269017901d",
}
MIN_ROW_SAVING = 256 * 1024
MIN_AGGREGATE_SAVING = 2 * 1024 * 1024


def _generate(parent: Path, name: str) -> Path:
    parent.mkdir(parents=True, exist_ok=True)
    if name == "05_logs_and_telemetry":
        neutral.corpus_logs(parent)
        target = parent / name
        repair.normalize_workload(target)
    elif name == "04_analytics_and_database":
        neutral.corpus_analytics(parent)
        target = parent / name
    elif name == "09_ml_artifacts":
        neutral.corpus_ml(parent)
        target = parent / name
    else:  # pragma: no cover - frozen table controls callers.
        raise RuntimeError(f"unsupported focused GIR workload: {name}")
    got = neutral.tree_hash(target)
    if got != EXPECTED[name]:
        raise RuntimeError(f"focused GIR source identity drift for {name}: expected {EXPECTED[name]}, got {got}")
    return target


def _run_row(root: Path, out_root: Path) -> dict:
    row_root = out_root / root.name
    row_root.mkdir(parents=True, exist_ok=True)
    base_archive = row_root / "accepted-v029.cmpct"
    gir_archive = row_root / "geometry-ir.cmpct"

    base_started = time.perf_counter()
    base_stats = GIR.BASE.build(root, base_archive)
    base_create_s = time.perf_counter() - base_started
    gir_started = time.perf_counter()
    gir_stats = GIR._build_gir(root, gir_archive)
    gir_create_s = time.perf_counter() - gir_started

    source_tree = GIR.treehash(root)
    if source_tree != EXPECTED[root.name]:
        raise RuntimeError(f"GIR treehash disagrees with frozen source identity for {root.name}")
    base_verified = GIR.BASE.strong_verify(base_archive)
    if not base_verified.get("ok") or base_verified.get("tree_sha256") != source_tree:
        raise RuntimeError(f"accepted v0.29 strong verification failed for {root.name}: {base_verified}")
    gir_verified = GIR.strong_verify(gir_archive)
    if not gir_verified.get("ok") or gir_verified.get("tree_sha256") != source_tree:
        raise RuntimeError(f"CMPNX14 strong verification failed for {root.name}: {gir_verified}")

    base_bytes = base_archive.stat().st_size
    gir_bytes = gir_archive.stat().st_size
    saving = base_bytes - gir_bytes
    return {
        "name": root.name,
        "tree_sha256": source_tree,
        "logical_bytes": sum(path.stat().st_size for path in root.rglob("*") if path.is_file()),
        "files": sum(1 for path in root.rglob("*") if path.is_file()),
        "v029_bytes": base_bytes,
        "gir_bytes": gir_bytes,
        "saving_vs_v029_bytes": saving,
        "smaller_than_v029_pct": saving / max(1, base_bytes) * 100.0,
        "gir_smaller_than_v029": gir_bytes < base_bytes,
        "row_gate": saving >= MIN_ROW_SAVING,
        "base_create_s": base_create_s,
        "gir_create_s": gir_create_s,
        "create_ratio_vs_v029": gir_create_s / max(base_create_s, 1e-9),
        "gir_stats": gir_stats,
        "accepted_v029_selected": base_stats.get("selected"),
        "strong_verify": {"v029": base_verified, "gir": gir_verified},
    }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    corpus_parent = work_root / "corpora"
    archive_root = work_root / "archives"
    rows = []
    for name in ("05_logs_and_telemetry", "04_analytics_and_database", "09_ml_artifacts"):
        root = _generate(corpus_parent, name)
        rows.append(_run_row(root, archive_root))

    v029_total = sum(row["v029_bytes"] for row in rows)
    gir_total = sum(row["gir_bytes"] for row in rows)
    saving = v029_total - gir_total
    totals = {
        "workloads": len(rows),
        "v029_bytes": v029_total,
        "gir_bytes": gir_total,
        "saving_vs_v029_bytes": saving,
        "smaller_than_v029_pct": saving / max(1, v029_total) * 100.0,
        "workloads_improved": sum(row["gir_smaller_than_v029"] for row in rows),
        "workloads_regressed": sum(row["gir_bytes"] > row["v029_bytes"] for row in rows),
        "rows_passing_minimum": sum(row["row_gate"] for row in rows),
        "hierarchical_nodes": sum(row["gir_stats"]["node_kind_counts"]["hierarchical"] for row in rows),
        "prefix_plane_nodes": sum(row["gir_stats"]["hierarchical_prefix_nodes"] for row in rows),
        "mechanism_gate": (
            all(row["row_gate"] and row["gir_smaller_than_v029"] for row in rows)
            and saving >= MIN_AGGREGATE_SAVING
        ),
    }
    return {
        "schema": "cmpct-v030-gir-focused-complete-v1",
        "status": "RESEARCH_COMPLETE_ARTIFACT_GATE_NOT_RELEASE",
        "claim_boundary": (
            "Three exact public workloads only. CMPNX14 is research-only; canonical r24 and project v0.29 "
            "remain unchanged. Passing this gate retains GIR for 15-workload research but does not authorize release."
        ),
        "direct_base": "accepted CMPCT v0.29 release engine built from each same live source tree",
        "contract": {
            "workloads": list(EXPECTED),
            "minimum_each_workload_saving_bytes": MIN_ROW_SAVING,
            "minimum_aggregate_saving_bytes": MIN_AGGREGATE_SAVING,
            "size_regression_tolerance_bytes": 0,
            "gir_must_win_without_workload_fallback": True,
            "strong_verify_both_artifacts": True,
        },
        "rows": rows,
        "totals": totals,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    print(json.dumps(result["totals"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
