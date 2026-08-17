from __future__ import annotations

"""Full 15-workload production-qualification harness for canonical r25 Geometry.

This gate is intentionally separate from the three-row breakthrough gate.  It regenerates the same inherited
public frontier used by v0.29, validates every source-tree identity against the accepted historical/repair
records, builds canonical r24 and the self-locating r25 candidate from each *same live tree*, and compares the
complete artifacts.  No workload may disappear and the portfolio may never exceed r24 bytes.

The raw r25 size is retained even when the portfolio chooses r24 so the evidence cannot hide an unfavorable
format embodiment.  Geometry's current physical compiler preserves the canonical logical storage graph, so its
logical dependency/read-decode topology must remain byte-for-byte identical to r24; this gate asserts those
index sections exactly rather than estimating locality from filenames.

Footnote: creation latency from this two-pass evidence compiler is reported but is not the release latency gate.
A production writer must integrate the physical tournament into ``src/cmpct`` and eliminate the temporary r24
artifact before timing promotion.  The two-pass number is useful debt evidence, not a loophole for shipping a
slow implementation.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import statistics
import time

from benchmarks import mosaic_v029_generalization_bench as FRONTIER
from cmpct.builder import Builder
from cmpct.reader import CMPCT
from experiments import canonical_v25_geometry_recovery as V25

MIN_AGGREGATE_SAVING = 2 * 1024 * 1024
MIN_IMPROVED_WORKLOADS = 3


def _tree_hash(root: Path) -> str:
    h = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        rel = path.relative_to(root).as_posix().encode()
        data = path.read_bytes()
        h.update(len(rel).to_bytes(4, "little")); h.update(rel)
        h.update(len(data).to_bytes(8, "little")); h.update(data)
    return h.hexdigest()


def _logical_sections(index: dict) -> tuple:
    # Blob physical codec/offset rows and the format feature/version are intentionally excluded. Everything
    # that describes the logical filesystem, reconstruction graph, dictionary identity and filesystem metadata
    # must remain identical after the r25 physical compile.
    return (
        index["files"],
        index.get("recipes"),
        index.get("dict_blob"),
        index.get("fsmeta"),
    )


def _measure(suite: str, root: Path, out_root: Path, expected: dict) -> dict:
    tree = _tree_hash(root)
    if tree != expected["tree_sha256"]:
        raise RuntimeError(
            f"r25 full-qualification source identity drift for {suite}/{root.name}: "
            f"expected {expected['tree_sha256']}, got {tree}"
        )
    row_root = out_root / suite / root.name
    row_root.mkdir(parents=True, exist_ok=True)
    r24 = row_root / "canonical-r24.cmpct"
    r25 = row_root / "canonical-r25.cmpct"

    started = time.perf_counter()
    r24_stats = Builder(root, workers=1, reproducible=True).build(r24)
    r24_create_s = time.perf_counter() - started
    started = time.perf_counter()
    r25_stats = V25.compile_r24_to_r25(r24, r25)
    r25_compile_s = time.perf_counter() - started

    verify_samples = []
    with CMPCT(r24) as before, V25.CMPCTV25(r25) as after:
        if _logical_sections(before.index) != _logical_sections(after.index):
            raise RuntimeError(f"r25 changed canonical logical graph for {suite}/{root.name}")
        # Every logical member is reconstructed through both real readers. Direct blob equality alone is not
        # enough because virtual ZIP, sparse, pack, CDC, hardlink and symlink paths exercise different graphs.
        started_verify = time.perf_counter()
        for member in before.files:
            if member[1] == 1:  # K_DIR
                continue
            left = before.read(member[0]); right = after.read(member[0])
            if left != right:
                raise RuntimeError(f"r25 logical byte mismatch for {suite}/{root.name}/{member[0]}")
        verify_samples.append(time.perf_counter() - started_verify)

    r24_bytes = r24.stat().st_size
    r25_bytes = r25.stat().st_size
    portfolio_bytes = min(r24_bytes, r25_bytes)
    return {
        "suite": suite,
        "name": root.name,
        "tree_sha256": tree,
        "baseline_identity": expected["baseline_identity"],
        "logical_bytes": int(r24_stats["logical_bytes"]),
        "logical_files": int(r24_stats["logical_files"]),
        "r24_bytes": r24_bytes,
        "raw_r25_bytes": r25_bytes,
        "raw_r25_saving_vs_r24_bytes": r24_bytes - r25_bytes,
        "portfolio_bytes": portfolio_bytes,
        "portfolio_saving_vs_r24_bytes": r24_bytes - portfolio_bytes,
        "selected": "r25-geometry" if r25_bytes < r24_bytes else "r24-fallback",
        "geometry_blobs": int(r25_stats["geometry_blobs"]),
        "representation_kind_counts": r25_stats["representation_kind_counts"],
        "g5_incremental_stored_saving": int(r25_stats["g5_incremental_stored_saving"]),
        "self_locating_tail": bool(r25_stats.get("self_locating_tail")),
        "r24_create_s": r24_create_s,
        "r25_compile_s": r25_compile_s,
        "two_pass_create_s": r24_create_s + r25_compile_s,
        "semantic_verify_s": statistics.median(verify_samples),
        "logical_graph_identical": True,
    }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    preserved = FRONTIER._preserved_rows()
    neutral = FRONTIER._load(FRONTIER.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py", "cmpct_v25_full_neutral")
    hostile = FRONTIER._load(FRONTIER.ROOT / "benchmarks" / "resemblance_hostile_corpus_v1.py", "cmpct_v25_full_hostile")
    repair = FRONTIER._load(FRONTIER.REPAIR_PATH, "cmpct_v25_full_repair")
    repair.install_generation_hooks(neutral)

    rows = []
    suites = [
        ("neutral_hostile_v1", neutral, work_root / "neutral"),
        ("resemblance_hostile_v1", hostile, work_root / "resemblance"),
    ]
    for label, builder, root in suites:
        builder.build(root)
        if label == "neutral_hostile_v1":
            repair.normalize_root(root)
        for workload in sorted(path for path in root.iterdir() if path.is_dir()):
            expected = preserved[(label, workload.name)]
            row = _measure(label, workload, work_root / "archives", expected)
            rows.append(row)
            print(json.dumps({
                "suite": label,
                "name": workload.name,
                "r24": row["r24_bytes"],
                "raw_r25": row["raw_r25_bytes"],
                "portfolio": row["portfolio_bytes"],
                "selected": row["selected"],
                "saving": row["portfolio_saving_vs_r24_bytes"],
            }), flush=True)

    r24_total = sum(row["r24_bytes"] for row in rows)
    raw_r25_total = sum(row["raw_r25_bytes"] for row in rows)
    portfolio_total = sum(row["portfolio_bytes"] for row in rows)
    saving = r24_total - portfolio_total
    totals = {
        "workloads": len(rows),
        "r24_bytes": r24_total,
        "raw_r25_bytes": raw_r25_total,
        "portfolio_bytes": portfolio_total,
        "portfolio_saving_vs_r24_bytes": saving,
        "portfolio_smaller_than_r24_pct": saving / max(1, r24_total) * 100.0,
        "workloads_improved": sum(row["portfolio_bytes"] < row["r24_bytes"] for row in rows),
        "workloads_regressed": sum(row["portfolio_bytes"] > row["r24_bytes"] for row in rows),
        "raw_r25_workloads_regressed": sum(row["raw_r25_bytes"] > row["r24_bytes"] for row in rows),
        "geometry_blobs": sum(row["geometry_blobs"] for row in rows),
        "g5_incremental_stored_saving": sum(row["g5_incremental_stored_saving"] for row in rows),
        "logical_graph_drift_rows": sum(not row["logical_graph_identical"] for row in rows),
        "self_locating_tail_rows": sum(row["self_locating_tail"] for row in rows),
        "two_pass_create_s": sum(row["two_pass_create_s"] for row in rows),
        "r24_create_s": sum(row["r24_create_s"] for row in rows),
    }
    totals["mechanism_gate"] = (
        len(rows) == 15
        and totals["workloads_regressed"] == 0
        and totals["logical_graph_drift_rows"] == 0
        and totals["self_locating_tail_rows"] == 15
        and totals["workloads_improved"] >= MIN_IMPROVED_WORKLOADS
        and saving >= MIN_AGGREGATE_SAVING
    )
    return {
        "schema": "cmpct-v030-canonical-r25-full-qualification-v1",
        "status": "PRODUCTION_QUALIFICATION_NOT_RELEASE",
        "claim_boundary": (
            "Complete canonical r24-vs-r25 portfolio across the inherited 15-workload public frontier. "
            "Two-pass create time is debt evidence; native parity/performance/transaction/external-competitor "
            "gates remain separately required before release."
        ),
        "contract": {
            "expected_workloads": 15,
            "portfolio_size_regression_tolerance_bytes": 0,
            "minimum_aggregate_saving_bytes": MIN_AGGREGATE_SAVING,
            "minimum_improved_workloads": MIN_IMPROVED_WORKLOADS,
            "every_tree_identity_must_match_preserved_frontier": True,
            "canonical_logical_graph_must_be_identical": True,
            "self_locating_tail_required": True,
            "raw_r25_losses_must_be_reported": True,
            "two_pass_creation_is_not_release_latency": True,
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
    if not result["totals"]["mechanism_gate"]:
        raise SystemExit("full canonical r25 qualification failed; do not weaken thresholds")


if __name__ == "__main__":
    main()
