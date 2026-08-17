from __future__ import annotations

"""Focused complete-artifact gate for canonical-semantics r25 Geometry.

Unlike CMPNX13/14, this benchmark starts from the real r24 Builder/Reader contract and then compiles only
physical blob representations.  The logical index, filesystem metadata, storage graph and nested-container
recipes must remain identical.  Every workload is generated once; r24 and r25 therefore consume the same live
bytes.  Raw r25 must win all three focused workloads before it is allowed into full 15-workload production
qualification; portfolio fallback is recorded but cannot manufacture this mechanism gate.

The gate is intentionally comparable in scale to the earlier GIR survival contract: >=256 KiB on each exact
logs/analytics/ML tree and >=2 MiB aggregate, with at least one structural (delimiter/hierarchical/lane) Geometry
chunk so a high-effort direct Zstd setting alone cannot claim the representation breakthrough.
"""
import argparse
import json
from pathlib import Path
import shutil
import time

from benchmarks import neutral_hostile_corpus_v1 as neutral
from benchmarks import neutral_hostile_determinism_repair_v5 as repair
from cmpct.builder import Builder
from cmpct.reader import CMPCT
from experiments import canonical_v25_geometry as V25

EXPECTED = {
    "05_logs_and_telemetry": "7356b866d7b99bfce2dd1fc6ef86d61d09c9d8a38a2ff3fec7d9a92e46020931",
    "04_analytics_and_database": "6d0854fe058a95258588b89dca653ac8f00c61f815c6127b179e86cc58b1789d",
    "09_ml_artifacts": "efc09910fea8ef67d24cd8957d3d576df3a7cc7f10f14585e3a3ae269017901d",
}
MIN_ROW_SAVING = 256 * 1024
MIN_AGGREGATE_SAVING = 2 * 1024 * 1024


def _generate(parent: Path, name: str) -> Path:
    parent.mkdir(parents=True, exist_ok=True)
    repair.install_generation_hooks(neutral)
    if name == "05_logs_and_telemetry":
        neutral.corpus_logs(parent); repair.normalize_workload(parent / name)
    elif name == "04_analytics_and_database":
        neutral.corpus_analytics(parent)
    elif name == "09_ml_artifacts":
        neutral.corpus_ml(parent)
    else:  # pragma: no cover
        raise RuntimeError(name)
    root = parent / name
    got = neutral.tree_hash(root)
    if got != EXPECTED[name]:
        raise RuntimeError(f"canonical r25 source identity drift for {name}: expected {EXPECTED[name]}, got {got}")
    return root


def _logical_sections(index: dict) -> tuple:
    return index["files"], index.get("recipes"), index.get("dict_blob"), index.get("fsmeta")


def _measure(root: Path, out: Path) -> dict:
    r24 = out / f"{root.name}-r24.cmpct"
    r25 = out / f"{root.name}-r25.cmpct"
    started = time.perf_counter()
    base_stats = Builder(root, workers=1, reproducible=True).build(r24)
    r24_create_s = time.perf_counter() - started
    started = time.perf_counter()
    compile_stats = V25.compile_r24_to_r25(r24, r25)
    r25_compile_s = time.perf_counter() - started
    with CMPCT(r24) as before, V25.CMPCTV25(r25) as after:
        if _logical_sections(before.index) != _logical_sections(after.index):
            raise RuntimeError(f"canonical logical index changed for {root.name}")
        for row in before.files:
            if row[1] == 1:
                continue
            if before.read(row[0]) != after.read(row[0]):
                raise RuntimeError(f"canonical r25 byte mismatch: {root.name}/{row[0]}")
    r24_bytes = r24.stat().st_size
    r25_bytes = r25.stat().st_size
    saving = r24_bytes - r25_bytes
    structural = sum(
        count for kind, count in compile_stats["representation_kind_counts"].items()
        if kind in {"lane", "delimiter", "hierarchical", "lane_perm"}
    )
    return {
        "name": root.name,
        "tree_sha256": EXPECTED[root.name],
        "r24_bytes": r24_bytes,
        "r25_bytes": r25_bytes,
        "saving_vs_r24_bytes": saving,
        "smaller_than_r24_pct": saving / max(1, r24_bytes) * 100.0,
        "row_gate": saving >= MIN_ROW_SAVING,
        "geometry_blobs": compile_stats["geometry_blobs"],
        "geometry_blob_net_saving": compile_stats["geometry_blob_net_saving"],
        "representation_kind_counts": compile_stats["representation_kind_counts"],
        "structural_geometry_chunks": structural,
        "g5_incremental_stored_saving": compile_stats["g5_incremental_stored_saving"],
        "r24_create_s": r24_create_s,
        "r25_compile_s": r25_compile_s,
        "r25_total_create_s": r24_create_s + r25_compile_s,
        "base_stats": base_stats,
    }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    corpora = work_root / "corpora"; artifacts = work_root / "artifacts"; artifacts.mkdir(parents=True)
    rows = []
    for name in ("05_logs_and_telemetry", "04_analytics_and_database", "09_ml_artifacts"):
        rows.append(_measure(_generate(corpora, name), artifacts))
    r24_total = sum(row["r24_bytes"] for row in rows)
    r25_total = sum(row["r25_bytes"] for row in rows)
    saving = r24_total - r25_total
    structural = sum(row["structural_geometry_chunks"] for row in rows)
    gate = (
        all(row["row_gate"] and row["r25_bytes"] < row["r24_bytes"] for row in rows)
        and saving >= MIN_AGGREGATE_SAVING
        and structural > 0
    )
    return {
        "schema": "cmpct-v030-canonical-r25-geometry-focused-v1",
        "status": "PRODUCTION_CANDIDATE_EVIDENCE_NOT_RELEASE",
        "claim_boundary": (
            "Canonical r24 logical semantics preserved; r25 changes physical blob codec only. Three exact public "
            "workloads are a survival gate, not full release qualification or native parity."
        ),
        "contract": {
            "expected_trees": EXPECTED,
            "minimum_each_workload_saving_bytes": MIN_ROW_SAVING,
            "minimum_aggregate_saving_bytes": MIN_AGGREGATE_SAVING,
            "raw_r25_must_win_each": True,
            "logical_index_sections_must_match": True,
            "at_least_one_structural_geometry_chunk": True,
            "size_regression_tolerance_bytes": 0,
        },
        "rows": rows,
        "totals": {
            "r24_bytes": r24_total,
            "r25_bytes": r25_total,
            "saving_vs_r24_bytes": saving,
            "smaller_than_r24_pct": saving / max(1, r24_total) * 100.0,
            "geometry_blobs": sum(row["geometry_blobs"] for row in rows),
            "structural_geometry_chunks": structural,
            "g5_incremental_stored_saving": sum(row["g5_incremental_stored_saving"] for row in rows),
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
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    print(json.dumps(result["totals"], indent=2, sort_keys=True))
    if not result["totals"]["mechanism_gate"]:
        raise SystemExit("canonical r25 Geometry focused gate failed; do not weaken thresholds")


if __name__ == "__main__":
    main()
