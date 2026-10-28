from __future__ import annotations

"""Fixed BytePlane4 transfer onto the unique non-dominated level-17 Analytics point.

Mission: docs/V030_ANALYTICS_BYTEPLANE4_LEVEL17_TRANSFER_MISSION_2026-09-12.md
Research-only. No level/width/threshold sweep.
"""

import argparse
import json
from pathlib import Path
import shutil
import statistics

from benchmarks import v030_analytics_byteplane4_strong_transfer_referee as BP
from benchmarks import v030_external_competitors as EXT
from benchmarks import v030_release_generalization as GENERAL
from experiments import entropygraph_v030_release_product as PRODUCT

TARGET = "04_analytics_and_database"
ROUNDS = 3
LEVEL17 = 17
LEVEL19 = 19
WIDTH = 4
ACCEPTED_V029_BYTES = 6_135_172
MIN_SPEEDUP_VS_L19 = 0.30
MAX_ADDED_CREATE_VS_L17_S = 0.75


def _build_at(stage: Path, root: Path, *, level: int, candidate: bool) -> dict:
    old_level = BP.LEVEL
    try:
        BP.LEVEL = int(level)
        return BP._build(stage, root, "candidate" if candidate else "baseline")
    finally:
        BP.LEVEL = old_level


def run(work_root: Path) -> dict:
    if BP.WIDTH != WIDTH:
        raise RuntimeError(f"frozen BytePlane width drift: {BP.WIDTH} != {WIDTH}")

    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    neutral = GENERAL.V029._load(
        GENERAL.V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py",
        "cmpct_v030_analytics_bp4_l17_neutral",
    )
    repair = GENERAL.V029._load(
        GENERAL.V029.REPAIR_PATH,
        "cmpct_v030_analytics_bp4_l17_repair",
    )
    repair.install_generation_hooks(neutral)
    corpus = work_root / "neutral"
    neutral.build(corpus)
    repair.normalize_root(corpus)
    stage = EXT._normalized_stage(corpus / TARGET, work_root / "normalized")
    expected_tree = PRODUCT.treehash(stage)

    specs = {
        "direct_l17": (LEVEL17, False),
        "bp4_l17": (LEVEL17, True),
        "direct_l19": (LEVEL19, False),
    }
    rows = {k: [] for k in specs}
    names = list(specs)
    for ri in range(ROUNDS):
        order = names[ri:] + names[:ri]
        for name in order:
            level, candidate = specs[name]
            root = work_root / "rounds" / f"r{ri}-{name}"
            root.mkdir(parents=True, exist_ok=True)
            result = _build_at(stage, root, level=level, candidate=candidate)
            if result["canonical_user_tree_sha256"] != expected_tree:
                raise RuntimeError(f"canonical tree drift in {name}")
            rows[name].append(result)

    summaries: dict[str, dict] = {}
    for name, rr in rows.items():
        sizes = {int(r["archive_bytes"]) for r in rr}
        trees = {r["canonical_user_tree_sha256"] for r in rr}
        if len(sizes) != 1 or len(trees) != 1:
            raise RuntimeError(f"nondeterminism in {name}")
        summaries[name] = {
            "archive_bytes": next(iter(sizes)),
            "median_complete_verified_create_s": statistics.median(float(r["complete_verified_create_s"]) for r in rr),
            "median_process_cpu_s": statistics.median(float(r["process_cpu_s"]) for r in rr),
            "median_process_wall_s": statistics.median(float(r["process_wall_s"]) for r in rr),
            "median_peak_rss_kib": statistics.median(int(r["rss_peak_kib"]) for r in rr),
            "median_incremental_rss_kib": statistics.median(int(r["rss_increment_kib"]) for r in rr),
        }

    candidate_rows = rows["bp4_l17"]
    first_stats = candidate_rows[0]["stats"]
    deterministic_keys = (
        "zc_calls", "cheap_gate_auditions", "cheap_gate_winners", "cheap_gate_raw_bytes",
        "strong_transform_auditions", "strong_transform_raw_bytes", "strong_transform_selected",
        "direct_l19_bytes_for_selected", "selected_framed_bytes", "net_payload_saving_bytes",
    )
    for key in deterministic_keys:
        values = {int(r["stats"][key]) for r in candidate_rows}
        if len(values) != 1:
            raise RuntimeError(f"candidate stat nondeterminism {key}: {values}")
    candidate_stats = {key: int(first_stats[key]) for key in deterministic_keys}
    for key in ("cheap_gate_cpu_s", "cheap_gate_wall_s", "strong_transform_cpu_s", "strong_transform_wall_s"):
        candidate_stats[f"median_{key}"] = statistics.median(float(r["stats"][key]) for r in candidate_rows)

    l17 = summaries["direct_l17"]
    cand = summaries["bp4_l17"]
    l19 = summaries["direct_l19"]
    saving_vs_l17 = int(l17["archive_bytes"]) - int(cand["archive_bytes"])
    margin_vs_v029 = ACCEPTED_V029_BYTES - int(cand["archive_bytes"])
    added_vs_l17 = float(cand["median_complete_verified_create_s"]) - float(l17["median_complete_verified_create_s"])
    speedup_vs_l19 = 1.0 - float(cand["median_complete_verified_create_s"]) / max(float(l19["median_complete_verified_create_s"]), 1e-12)

    gate = {
        "candidate_at_or_below_v029": int(cand["archive_bytes"]) <= ACCEPTED_V029_BYTES,
        "canonical_tree_exact_all_modes": True,
        "candidate_deterministic": True,
        "speedup_vs_direct_l19_at_least_30pct": speedup_vs_l19 >= MIN_SPEEDUP_VS_L19,
        "added_create_vs_direct_l17_at_most_0_75_s": added_vs_l17 <= MAX_ADDED_CREATE_VS_L17_S,
        "fixed_level17_width4_no_sweep": True,
    }
    verdict = "LEVEL17_STRUCTURAL_CROSSOVER" if all(gate.values()) else "RETIRE_LEVEL17_BYTEPLANE4_CROSSOVER"

    return {
        "schema": "cmpct-v030-analytics-byteplane4-level17-transfer-v1",
        "experiment_valid": True,
        "release_credit": False,
        "target": f"neutral_hostile_v1/{TARGET}",
        "rounds": ROUNDS,
        "accepted_v029_bytes": ACCEPTED_V029_BYTES,
        "modes": summaries,
        "candidate_stats": candidate_stats,
        "archive_saving_vs_direct_l17_bytes": saving_vs_l17,
        "candidate_margin_vs_v029_bytes": margin_vs_v029,
        "added_complete_verified_create_vs_l17_s": added_vs_l17,
        "complete_verified_create_speedup_vs_l19_fraction": speedup_vs_l19,
        "gate": gate,
        "verdict": verdict,
        "contract": {
            "level17_predeclared_unique_non_dominated_lower_effort_point": True,
            "width4_frozen": True,
            "cheap_gate_is_prior_level1_exact_framed_win": True,
            "path_extension_workload_identity_forbidden": True,
            "no_level_width_threshold_sweep": True,
            "strong_verify_inside_creation_time": True,
            "canonical_format_changed": False,
            "production_selector_changed": False,
            "reader_locality_auth_recovery_native_credit": False,
            "release_credit": False,
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-analytics-bp4-l17-work"))
    ap.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-analytics-bp4-l17.json"))
    args = ap.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({
        "verdict": result["verdict"],
        "modes": result["modes"],
        "saving_vs_l17": result["archive_saving_vs_direct_l17_bytes"],
        "margin_vs_v029": result["candidate_margin_vs_v029_bytes"],
        "speedup_vs_l19": result["complete_verified_create_speedup_vs_l19_fraction"],
        "candidate_stats": result["candidate_stats"],
        "gate": result["gate"],
    }, indent=2), flush=True)


if __name__ == "__main__":
    main()
