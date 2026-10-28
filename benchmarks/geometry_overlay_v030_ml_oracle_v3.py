from __future__ import annotations

"""Frozen public-ML oracle for full G0-G4 Geometry inside the pre-fallback Mosaic graph.

V2 fixed the causal attachment point but only exercised lanes + flat delimiter Geometry.  V3 keeps the same
public ML identity, accepted-v0.29 byte floor and >=256 KiB complete-artifact hurdle while replacing the
physical audition with the full reactor ladder through Hierarchical Geometry / Prefix Planes.

Footnote: this benchmark does not borrow the standalone CMPNX14 saving.  It builds one complete transformed
Mosaic graph, pays its own metadata/recovery bytes, strong-verifies it, then tournaments it against the exact
accepted v0.29 release artifact.  Hierarchical search must actually be exercised, but it need not nominate or
select a hierarchical candidate if the content-derived screener correctly finds none.

A scientifically valid measurement is not itself a promotion.  The frozen >=256 KiB hurdle remains unchanged,
but a well-formed, exact, locality-safe experiment that measures less than that hurdle is durable negative
evidence rather than a permanently broken CI lane.  ``promotion_signal`` is therefore fail-closed and remains
false until the original breakthrough contract is actually met.
"""

import argparse
import json
from pathlib import Path
import shutil
import time

from benchmarks import neutral_hostile_corpus_v1 as neutral
from benchmarks import neutral_hostile_determinism_repair_v5 as repair
from experiments import entropygraph_v030_geometry_overlay_g04 as overlay

EXPECTED_TREE = "efc09910fea8ef67d24cd8957d3d576df3a7cc7f10f14585e3a3ae269017901d"
EXPECTED_V029_BYTES = 13_836_439
MIN_COMPOSITION_SAVING = 256 * 1024


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    corpus_root = work_root / "corpus"
    repair.install_generation_hooks(neutral)
    neutral.corpus_ml(corpus_root)
    repair.normalize_root(corpus_root)
    source = corpus_root / "09_ml_artifacts"
    live_tree = overlay.treehash(source)
    if live_tree != EXPECTED_TREE:
        raise RuntimeError(f"public ML tree drift: {live_tree} != {EXPECTED_TREE}")

    archive = work_root / "geometry-overlay-g04-v3.cmpct"

    # Candidate/finalist counts are outputs of the hierarchical screener, not proof
    # that the G3/G4 reactor was invoked. Count the actual call boundary so a valid
    # zero-candidate result remains scientifically useful negative evidence.
    hierarchy_attempts = 0
    original_hierarchy_audition = overlay.HG.audition

    def counted_hierarchy_audition(raw: bytes) -> dict:
        nonlocal hierarchy_attempts
        hierarchy_attempts += 1
        return original_hierarchy_audition(raw)

    overlay.HG.audition = counted_hierarchy_audition
    started = time.perf_counter()
    try:
        stats = overlay.build(source, archive)
    finally:
        overlay.HG.audition = original_hierarchy_audition
    wall = time.perf_counter() - started

    if int(stats["v029_bytes"]) != EXPECTED_V029_BYTES:
        raise RuntimeError(f"accepted v0.29 byte drift: {stats['v029_bytes']} != {EXPECTED_V029_BYTES}")
    verified = overlay.strong_verify(archive)
    if not verified.get("ok") or verified.get("tree_sha256") != live_tree:
        raise RuntimeError("G0-G4 pre-fallback overlay selected artifact failed strong verification")

    saving = int(stats["saving_vs_v029_bytes"])
    hierarchy_screened = sum(int(row.get("hierarchical_screened_candidates", 0)) for row in stats["auditions"])
    hierarchy_finalists = sum(int(row.get("hierarchical_exact_finalists", 0)) for row in stats["auditions"])
    result = {
        "schema": "cmpct-v030-geometry-overlay-ml-oracle-v3",
        "claim_boundary": "single public ML full-G0-G4 pre-fallback composition oracle; canonical release unchanged",
        "contract": {
            "tree_sha256": EXPECTED_TREE,
            "accepted_v029_bytes": EXPECTED_V029_BYTES,
            "minimum_composition_saving_bytes": MIN_COMPOSITION_SAVING,
            "archive_size_regression_tolerance_bytes": 0,
            "maximum_selected_member_read_amplification": overlay.MAX_MEMBER_READ_AMP,
            "transform_substrate": "attempt5 best Placement-v4/Residual-v5 graph before outer fallback",
            "geometry_ladder": ["G0-direct", "G1-lanes", "G2-delimiter", "G3-hierarchical", "G4-prefix-planes"],
            "final_floor": "accepted v0.29 complete artifact",
        },
        "result": {
            "selected": stats["selected"],
            "overlay_source_format": stats["overlay_source_format"],
            "logical_tree_sha256": live_tree,
            "v029_bytes": int(stats["v029_bytes"]),
            "pre_overlay_graph_bytes": int(stats["pre_overlay_graph_bytes"]),
            "pre_overlay_graph_delta_vs_v029_bytes": int(stats["pre_overlay_graph_delta_vs_v029_bytes"]),
            "overlay_bytes": int(stats["overlay_bytes"]),
            "candidate_bytes": int(stats["archive_bytes"]),
            "saving_vs_v029_bytes": saving,
            "saving_vs_v029_pct": saving / EXPECTED_V029_BYTES * 100.0,
            "overlay_improvement_vs_prefallback_graph_bytes": int(
                stats["overlay_improvement_vs_prefallback_graph_bytes"]
            ),
            "transformed_records": int(stats["transformed_records"]),
            "lane_records": int(stats.get("lane_records", 0)),
            "delimiter_records": int(stats.get("delimiter_records", 0)),
            "hierarchical_records": int(stats.get("hierarchical_records", 0)),
            "prefix_plane_records": int(stats.get("prefix_plane_records", 0)),
            "hierarchical_total_records": int(stats.get("hierarchical_total_records", 0)),
            "hierarchical_audition_attempts": hierarchy_attempts,
            "hierarchical_screened_candidates": hierarchy_screened,
            "hierarchical_exact_finalists": hierarchy_finalists,
            "hierarchical_incremental_saving_bytes": int(stats.get("hierarchical_incremental_saving_bytes", 0)),
            "transform_payload_saving_bytes": int(stats.get("transform_payload_saving_bytes", 0)),
            "max_selected_member_read_amplification": float(
                stats.get("max_selected_member_read_amplification", 0.0)
            ),
            "overlay_meta_raw_bytes": stats.get("overlay_meta_raw_bytes"),
            "overlay_meta_comp_bytes": stats.get("overlay_meta_comp_bytes"),
            "integration_order": stats["integration_order"],
            "selection_materialization": stats["selection_materialization"],
            "selection_extra_payload_write_bytes": int(stats["selection_extra_payload_write_bytes"]),
            "portfolio_create_s": float(stats["portfolio_create_s"]),
            "benchmark_wall_s": wall,
            "strong_verify": verified,
        },
    }
    validity = {
        "no_size_regression": result["result"]["candidate_bytes"] <= EXPECTED_V029_BYTES,
        "exact_tree": verified.get("tree_sha256") == EXPECTED_TREE,
        "overlay_graph_was_eligible": stats["overlay_source_format"] in ("placement-v4", "residual-pack-v5"),
        "mechanism_selected": stats["selected"] == "geometry-overlay-g04" and int(stats["transformed_records"]) > 0,
        "hierarchical_search_exercised": hierarchy_attempts > 0,
        "locality": float(stats.get("max_selected_member_read_amplification", 0.0)) <= overlay.MAX_MEMBER_READ_AMP,
        "zero_copy_publication": stats["selection_materialization"] == "same-filesystem-atomic-move"
        and int(stats["selection_extra_payload_write_bytes"]) == 0,
    }
    composition_breakthrough = saving >= MIN_COMPOSITION_SAVING
    result["gate"] = {
        **validity,
        "composition_breakthrough": composition_breakthrough,
        "experiment_valid": all(validity.values()),
        "promotion_signal": all(validity.values()) and composition_breakthrough,
    }
    # ``passed`` means the research experiment produced trustworthy evidence.  Promotion remains separately
    # fail-closed through ``promotion_signal`` and the unchanged >=256 KiB contract.
    result["gate"]["passed"] = result["gate"]["experiment_valid"]
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/geometry-overlay-v030-v3-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/geometry-overlay-v030-ml-v3.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"result": result["result"], "gate": result["gate"]}, indent=2), flush=True)
    if not result["gate"]["experiment_valid"]:
        raise SystemExit("full G0-G4 pre-fallback overlay experiment was invalid")


if __name__ == "__main__":
    main()
