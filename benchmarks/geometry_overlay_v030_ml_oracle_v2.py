from __future__ import annotations

"""Exact public-ML oracle for Geometry applied before the accepted v0.29 fallback tournament.

V1 proved a useful negative about *integration order*: the historical ML release artifact is an inherited
fallback, so overlaying only the already-selected artifact never reaches the Placement/Residual graph and
must report zero transforms.  V2 keeps the exact accepted release artifact as floor while applying Geometry
to the attempt-5 candidate graph before that outer fallback decision.

Footnote: the >=256 KiB composition hurdle is unchanged.  This is a repair of causal reachability, not a
threshold retry.  A red V2 therefore rejects this physical-overlay architecture on the frozen public ML tree.
"""

import argparse
import json
from pathlib import Path
import shutil
import time

from benchmarks import neutral_hostile_corpus_v1 as neutral
from benchmarks import neutral_hostile_determinism_repair_v5 as repair
from experiments import entropygraph_v030_geometry_overlay_prefallback as overlay

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

    archive = work_root / "geometry-overlay-v2.cmpct"
    started = time.perf_counter()
    stats = overlay.build(source, archive)
    wall = time.perf_counter() - started
    if int(stats["v029_bytes"]) != EXPECTED_V029_BYTES:
        raise RuntimeError(f"accepted v0.29 byte drift: {stats['v029_bytes']} != {EXPECTED_V029_BYTES}")
    verified = overlay.strong_verify(archive)
    if not verified.get("ok") or verified.get("tree_sha256") != live_tree:
        raise RuntimeError("pre-fallback Geometry overlay selected artifact failed strong verification")

    saving = int(stats["saving_vs_v029_bytes"])
    result = {
        "schema": "cmpct-v030-geometry-overlay-ml-oracle-v2",
        "claim_boundary": "single public ML pre-fallback composition oracle; canonical r24 unchanged",
        "contract": {
            "tree_sha256": EXPECTED_TREE,
            "accepted_v029_bytes": EXPECTED_V029_BYTES,
            "minimum_composition_saving_bytes": MIN_COMPOSITION_SAVING,
            "archive_size_regression_tolerance_bytes": 0,
            "maximum_selected_member_read_amplification": overlay.MAX_MEMBER_READ_AMP,
            "transform_substrate": "attempt5 best Placement-v4/Residual-v5 graph before outer v0.28 fallback",
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
            "transform_payload_saving_bytes": int(stats.get("transform_payload_saving_bytes", 0)),
            "max_selected_member_read_amplification": float(
                stats.get("max_selected_member_read_amplification", 0.0)
            ),
            "overlay_meta_raw_bytes": stats.get("overlay_meta_raw_bytes"),
            "overlay_meta_comp_bytes": stats.get("overlay_meta_comp_bytes"),
            "integration_order": stats["integration_order"],
            "portfolio_create_s": float(stats["portfolio_create_s"]),
            "benchmark_wall_s": wall,
            "strong_verify": verified,
        },
    }
    result["gate"] = {
        "no_size_regression": result["result"]["candidate_bytes"] <= EXPECTED_V029_BYTES,
        "exact_tree": verified.get("tree_sha256") == EXPECTED_TREE,
        "overlay_graph_was_eligible": stats["overlay_source_format"] in ("placement-v4", "residual-pack-v5"),
        "mechanism_selected": stats["selected"] == "geometry-overlay" and int(stats["transformed_records"]) > 0,
        "locality": float(stats.get("max_selected_member_read_amplification", 0.0)) <= overlay.MAX_MEMBER_READ_AMP,
        "composition_breakthrough": saving >= MIN_COMPOSITION_SAVING,
    }
    result["gate"]["passed"] = all(result["gate"].values())
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/geometry-overlay-v030-v2-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/geometry-overlay-v030-ml-v2.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"result": result["result"], "gate": result["gate"]}, indent=2), flush=True)
    if not result["gate"]["passed"]:
        raise SystemExit("pre-fallback Geometry overlay failed frozen >=256 KiB composition gate")


if __name__ == "__main__":
    main()
