from __future__ import annotations

"""Research-only direct measurement of the six-row v0.30 generalization fallback cliff.

The frozen product failure showed that six rows first retain an inner v0.29 fallback and then publish a larger
canonical r24 fallback. This oracle does not change that law. It rebuilds exactly those six frozen source rows,
adds the canonical filesystem staging layer, and decomposes the complete G04 tournament into: staged v0.29 base,
Attempt-5 pre-fallback graph, and final raw G04 overlay. That decomposition distinguishes inherited graph debt from
Geometry's recovery and from later outer fallback amplification.

Workload names are used only to select frozen benchmark cases for measurement; no product dispatch observes them.
All thresholds, grammars, admission rules, source identities and product code remain unchanged. This earns zero
release credit.
"""

import argparse
import json
from pathlib import Path
import shutil
import traceback

from benchmarks import mosaic_v029_generalization_bench as V029
from benchmarks import v030_release_generalization as GEN

TARGETS = {
    ("neutral_hostile_v1", "01_developer_repository"),
    ("neutral_hostile_v1", "02_office_workspace"),
    ("neutral_hostile_v1", "04_analytics_and_database"),
    ("neutral_hostile_v1", "07_incompressible_and_encrypted_like"),
    ("neutral_hostile_v1", "08_many_tiny_files"),
    ("resemblance_hostile_v1", "04_deflate_family"),
}


def run(work_root: Path) -> dict:
    from experiments import entropygraph_v030_release_product as PRODUCT

    C = PRODUCT.C
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    accepted = GEN._accepted_v029_rows()

    neutral = V029._load(V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py", "cmpct_v030_cliff_neutral")
    hostile = V029._load(V029.ROOT / "benchmarks" / "resemblance_hostile_corpus_v1.py", "cmpct_v030_cliff_hostile")
    repair = V029._load(V029.REPAIR_PATH, "cmpct_v030_cliff_repair_v6")
    repair.install_generation_hooks(neutral)

    rows: list[dict] = []
    for suite, builder, root in (
        ("neutral_hostile_v1", neutral, work_root / "neutral"),
        ("resemblance_hostile_v1", hostile, work_root / "resemblance"),
    ):
        builder.build(root)
        if suite == "neutral_hostile_v1":
            repair.normalize_root(root)
        for source in sorted(path for path in root.iterdir() if path.is_dir()):
            key = (suite, source.name)
            if key not in TARGETS:
                continue
            expected = accepted[key]
            historical_tree = GEN._historical_treehash(source)
            if historical_tree != expected["tree_sha256"]:
                raise RuntimeError(f"frozen source identity drift: {suite}/{source.name}")

            case_root = work_root / "cases" / suite / source.name
            staged = case_root / "staged-profile-tree"
            out = case_root / "inner-g04-tournament.cmpct"
            case_root.mkdir(parents=True, exist_ok=True)
            prepared = C._prepare_profile_tree(source, staged)
            with C._revision25_profile_context():
                active_g04_magic = bytes(C.RC.G04.MAG)
                stats = dict(C.RC.G04.build(staged, out))
            staged_base = int(stats["v029_bytes"])
            pre_graph = int(stats["pre_overlay_graph_bytes"])
            raw_overlay = int(stats["overlay_bytes"])
            selected_bytes = int(stats["archive_bytes"])
            bridge = max(0, raw_overlay - staged_base + 1)
            expected_floor = int(expected["accepted_v029_bytes"])
            selected_revision, selected_profile = C._profile_for_archive(out)
            row = {
                "suite": suite,
                "name": source.name,
                "historical_tree_sha256": historical_tree,
                "accepted_v029_bytes": expected_floor,
                "filesystem_manifest_bytes": int(prepared["manifest_bytes"]),
                "filesystem_manifest_entries": int(prepared["entries"]),
                "staged_v029_base_bytes": staged_base,
                "staging_exported_cost_vs_original_v029_bytes": staged_base - expected_floor,
                "pre_overlay_graph_bytes": pre_graph,
                "pre_overlay_graph_delta_vs_staged_base_bytes": pre_graph - staged_base,
                "raw_g04_overlay_bytes": raw_overlay,
                "raw_overlay_delta_vs_staged_base_bytes": raw_overlay - staged_base,
                "overlay_improvement_vs_prefallback_graph_bytes": pre_graph - raw_overlay,
                "strict_inner_win_bridge_bytes": bridge,
                "inner_selected": stats["selected"],
                "inner_selected_bytes": selected_bytes,
                "inner_selected_revision_after_context": selected_revision,
                "inner_selected_profile_after_context": selected_profile,
                "active_g04_magic_hex": active_g04_magic.hex(),
                "transformed_records": int(stats.get("transformed_records", 0)),
                "delimiter_records": int(stats.get("delimiter_records", 0)),
                "hierarchical_total_records": int(stats.get("hierarchical_total_records", 0)),
                "transform_payload_saving_bytes": int(stats.get("transform_payload_saving_bytes", 0)),
                "hierarchical_incremental_saving_bytes": int(stats.get("hierarchical_incremental_saving_bytes", 0)),
                "max_selected_member_read_amplification": float(stats.get("max_selected_member_read_amplification", 0.0)),
                "overlay_meta_raw_bytes": int(stats.get("overlay_meta_raw_bytes", 0)),
                "overlay_meta_comp_bytes": int(stats.get("overlay_meta_comp_bytes", 0)),
            }
            rows.append(row)
            print(json.dumps(row), flush=True)

    if {(row["suite"], row["name"]) for row in rows} != TARGETS:
        raise RuntimeError(f"target coverage drift: got {[(r['suite'], r['name']) for r in rows]}")

    return {
        "schema": "cmpct-v030-generalization-fallback-cliff-oracle-v2",
        "status": "PASS",
        "evidence_class": "research-oracle-direct-current-substrate",
        "product_release_credit": False,
        "contract": {
            "target_rows": 6,
            "frozen_source_identity_required": True,
            "product_dispatch_changed": False,
            "release_thresholds_changed": False,
            "benchmark_identity_used_only_for_oracle_selection": True,
        },
        "rows": rows,
        "totals": {
            "accepted_v029_bytes": sum(r["accepted_v029_bytes"] for r in rows),
            "staged_v029_base_bytes": sum(r["staged_v029_base_bytes"] for r in rows),
            "pre_overlay_graph_bytes": sum(r["pre_overlay_graph_bytes"] for r in rows),
            "raw_g04_overlay_bytes": sum(r["raw_g04_overlay_bytes"] for r in rows),
            "staging_exported_cost_vs_original_v029_bytes": sum(r["staging_exported_cost_vs_original_v029_bytes"] for r in rows),
            "pre_overlay_graph_delta_vs_staged_base_bytes": sum(r["pre_overlay_graph_delta_vs_staged_base_bytes"] for r in rows),
            "overlay_improvement_vs_prefallback_graph_bytes": sum(r["overlay_improvement_vs_prefallback_graph_bytes"] for r in rows),
            "raw_overlay_delta_vs_staged_base_bytes": sum(r["raw_overlay_delta_vs_staged_base_bytes"] for r in rows),
            "strict_inner_win_bridge_bytes": sum(r["strict_inner_win_bridge_bytes"] for r in rows),
            "transform_payload_saving_bytes": sum(r["transform_payload_saving_bytes"] for r in rows),
            "hierarchical_incremental_saving_bytes": sum(r["hierarchical_incremental_saving_bytes"] for r in rows),
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-fallback-cliff-work"))
    ap.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-fallback-cliff.json"))
    args = ap.parse_args()
    try:
        payload = run(args.work_root)
    except BaseException as exc:
        payload = {
            "schema": "cmpct-v030-generalization-fallback-cliff-oracle-v2",
            "status": "HARNESS_FAILURE",
            "evidence_class": "research-oracle-direct-current-substrate",
            "product_release_credit": False,
            "error": {"type": type(exc).__name__, "message": str(exc), "traceback": traceback.format_exc(limit=32)},
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(payload, indent=2) + "\n")
        raise
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps({"totals": payload["totals"]}, indent=2), flush=True)


if __name__ == "__main__":
    main()
