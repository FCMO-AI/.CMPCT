from __future__ import annotations

"""Complete-artifact focused falsifier for the v0.30 Synthetic Phrase Substrate.

Every workload is generated once, normalized to the accepted portable identity, then measured in that same live
lifetime by accepted v0.29, raw CMPNX15 and monolithic solid tar+Zstd-19.  Raw CMPNX15 must therefore beat real
archive bytes after phrase tables, parses, duplicate metadata, integrity and bounded physical packs are charged.

The solid comparator is intentionally part of the frozen causal contract: if the substrate only wins because it
recreates a conventional solid stream with extra metadata, the new representation has not earned breakthrough
status even if it happens to beat CMPCT's locality-oriented baseline.
"""

import argparse
import json
from pathlib import Path
import shutil
import tempfile

from benchmarks import neutral_hostile_corpus_v1 as neutral
from benchmarks import neutral_hostile_determinism_repair_v5 as repair
from benchmarks import entropygraph_v028_bench as competitors
from experiments import entropygraph_v029_release as BASE
from experiments import entropygraph_v030_attractor_substrate as S

EXPECTED_TREES = {
    "01_developer_repository": "ddcdf1ae1b61042634aae40b1b12da629feb98cb45db23c56d1da15334b74645",
    "02_office_workspace": "aac7de772b9fae0f9791a8f2884cebb29a2ba85df9e4db21ea78482afb378a57",
    "06_incremental_backups": "a823728d98e5882542645e3ab0f777894479cfb3de4dedcec14341fedbb11a05",
}
MIN_SINGLE_V029_SAVING = 256 * 1024
MIN_PORTFOLIO_AGGREGATE_SAVING = 512 * 1024
MIN_SINGLE_SOLID_ZSTD_SAVING = 64 * 1024


def _generate(root: Path) -> dict[str, Path]:
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True)
    repair.install_generation_hooks(neutral)
    neutral.corpus_source_repo(root)
    neutral.corpus_office(root)
    repair.normalize_workload(root / "02_office_workspace")
    neutral.corpus_backups(root)
    repair.normalize_workload(root / "06_incremental_backups")
    roots = {name: root / name for name in EXPECTED_TREES}
    for name, path in roots.items():
        got = neutral.tree_hash(path)
        if got != EXPECTED_TREES[name]:
            raise RuntimeError(f"substrate source identity drift for {name}: expected {EXPECTED_TREES[name]}, got {got}")
    return roots


def _measure(name: str, root: Path, work: Path) -> dict:
    base_path = work / f"{name}-v029.cmpct"
    substrate_path = work / f"{name}-substrate.cmpct"
    solid_path = work / f"{name}.tar.zst"

    base_stats = BASE.build(root, base_path)
    substrate_stats = S.build_raw(root, substrate_path)
    base_verify = BASE.strong_verify(base_path)
    substrate_verify = S.strong_verify(substrate_path)
    tree = S.treehash(root)
    if not base_verify.get("ok") or base_verify.get("tree_sha256") != tree:
        raise RuntimeError(f"v0.29 strong verification failed for {name}")
    if not substrate_verify.get("ok") or substrate_verify.get("tree_sha256") != tree:
        raise RuntimeError(f"substrate strong verification failed for {name}")

    solid = competitors._solid_tar_zstd(root, solid_path)
    if not solid.get("available"):
        raise RuntimeError(f"solid Zstd comparator unavailable for {name}: {solid.get('reason', 'unknown')}")

    base_bytes = base_path.stat().st_size
    substrate_bytes = substrate_path.stat().st_size
    solid_bytes = int(solid["bytes"])
    raw_saving = base_bytes - substrate_bytes
    portfolio_bytes = min(base_bytes, substrate_bytes)
    return {
        "name": name,
        "tree_sha256": tree,
        "files": substrate_stats["files"],
        "logical_bytes": substrate_stats["logical_bytes"],
        "v029_bytes": base_bytes,
        "substrate_bytes": substrate_bytes,
        "solid_zstd19_bytes": solid_bytes,
        "raw_substrate_saving_vs_v029_bytes": raw_saving,
        "raw_substrate_smaller_than_v029_pct": raw_saving / max(1, base_bytes) * 100.0,
        "substrate_saving_vs_solid_zstd_bytes": solid_bytes - substrate_bytes,
        "portfolio_selected": "substrate" if substrate_bytes < base_bytes else "v029-fallback",
        "portfolio_bytes": portfolio_bytes,
        "portfolio_saving_vs_v029_bytes": base_bytes - portfolio_bytes,
        "selected_average_phrase": substrate_stats["selected_average_phrase"],
        "selected_ordering": substrate_stats["selected_ordering"],
        "phrases": substrate_stats["phrases"],
        "shared_phrase_ids": substrate_stats["shared_phrase_ids"],
        "shared_phrase_occurrences": substrate_stats["shared_phrase_occurrences"],
        "exact_phrase_dedup_saved_raw_bytes": substrate_stats["exact_phrase_dedup_saved_raw_bytes"],
        "metadata_raw_bytes": substrate_stats["metadata_raw_bytes"],
        "metadata_compressed_bytes": substrate_stats["metadata_compressed_bytes"],
        "physical_records": substrate_stats["physical_records"],
        "worst_phrase_read_amplification": substrate_stats["worst_phrase_read_amplification"],
        "locality_debt_open": substrate_stats["locality_debt_open"],
        "max_decode_unit": substrate_stats["max_decode_unit"],
        "v029_create_s": float(base_stats.get("portfolio_create_s", 0.0)),
        "substrate_create_s": float(substrate_stats.get("portfolio_create_s", 0.0)),
        "solid_zstd_create_s": float(solid.get("create_s", 0.0)),
        "v029_verify": base_verify,
        "substrate_verify": substrate_verify,
    }


def run(work_root: Path) -> dict:
    roots = _generate(work_root / "corpora")
    measure_dir = work_root / "artifacts"
    measure_dir.mkdir(parents=True, exist_ok=True)
    rows = [_measure(name, roots[name], measure_dir) for name in EXPECTED_TREES]

    portfolio_saving = sum(row["portfolio_saving_vs_v029_bytes"] for row in rows)
    max_v029_saving = max(row["raw_substrate_saving_vs_v029_bytes"] for row in rows)
    max_solid_saving = max(row["substrate_saving_vs_solid_zstd_bytes"] for row in rows)
    totals = {
        "workloads": len(rows),
        "v029_bytes": sum(row["v029_bytes"] for row in rows),
        "substrate_raw_bytes": sum(row["substrate_bytes"] for row in rows),
        "portfolio_bytes": sum(row["portfolio_bytes"] for row in rows),
        "solid_zstd19_bytes": sum(row["solid_zstd19_bytes"] for row in rows),
        "portfolio_saving_vs_v029_bytes": portfolio_saving,
        "max_single_raw_saving_vs_v029_bytes": max_v029_saving,
        "max_single_saving_vs_solid_zstd_bytes": max_solid_saving,
        "substrate_raw_wins_vs_v029": sum(row["substrate_bytes"] < row["v029_bytes"] for row in rows),
        "substrate_raw_losses_vs_v029": sum(row["substrate_bytes"] > row["v029_bytes"] for row in rows),
        "substrate_wins_vs_solid_zstd": sum(row["substrate_bytes"] < row["solid_zstd19_bytes"] for row in rows),
        "shared_phrase_ids": sum(row["shared_phrase_ids"] for row in rows),
        "exact_phrase_dedup_saved_raw_bytes": sum(row["exact_phrase_dedup_saved_raw_bytes"] for row in rows),
        "max_decode_unit": max(row["max_decode_unit"] for row in rows),
        "max_phrase_read_amplification": max(row["worst_phrase_read_amplification"] for row in rows),
        "locality_debt_open": any(row["locality_debt_open"] for row in rows),
        "mechanism_gate": (
            portfolio_saving >= MIN_PORTFOLIO_AGGREGATE_SAVING
            and max_v029_saving >= MIN_SINGLE_V029_SAVING
            and max_solid_saving >= MIN_SINGLE_SOLID_ZSTD_SAVING
            and sum(row["substrate_bytes"] < row["v029_bytes"] for row in rows) > 0
            and sum(row["shared_phrase_ids"] for row in rows) > 0
            and max(row["max_decode_unit"] for row in rows) <= 8 * 1024 * 1024
        ),
    }
    return {
        "schema": "cmpct-v030-attractor-substrate-focused-v1",
        "status": "CHILD_RESEARCH_COMPLETE_ARTIFACT_BREAKTHROUGH_DEBT_OPEN",
        "claim_boundary": (
            "Complete self-contained CMPNX15 vs same-live-tree accepted v0.29 and solid tar+Zstd-19 on three "
            "exact public workloads. Workload portfolio falls back to v0.29; locality debt remains open."
        ),
        "contract": {
            "expected_trees": EXPECTED_TREES,
            "minimum_single_raw_saving_vs_v029_bytes": MIN_SINGLE_V029_SAVING,
            "minimum_portfolio_aggregate_saving_vs_v029_bytes": MIN_PORTFOLIO_AGGREGATE_SAVING,
            "minimum_single_saving_vs_solid_zstd_bytes": MIN_SINGLE_SOLID_ZSTD_SAVING,
            "portfolio_size_regression_tolerance_bytes": 0,
            "max_decode_unit_bytes": 8 * 1024 * 1024,
            "locality_policy": (
                "read amplification may exceed 8x only as explicitly recorded research debt; safety decode unit "
                "remains <=8 MiB. Promotion requires locality rehabilitation without erasing the size win."
            ),
            "anti_reinvention_rule": (
                "At least one exact workload must beat monolithic solid tar+Zstd-19 by >=64 KiB; otherwise do "
                "not describe the substrate as a new compression breakthrough."
            ),
        },
        "rows": rows,
        "totals": totals,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="cmpct-substrate-focused-") as td:
        # The user-provided work root remains the durable artifact location; temp is reserved for competitor
        # helpers that may need additional scratch in future revisions.
        _ = td
        result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    print(json.dumps(result["totals"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
