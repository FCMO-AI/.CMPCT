from __future__ import annotations

"""All-15 external shadow gate for the prospective terminal logs selector.

The shipping external frontier remains the release authority and is expected to stay red until every workload wins.
This lane asks a narrower promotion question without weakening that authority: does the exact candidate facade add
the already-proven logs four-way win on the same frozen matrix while preserving the established frontier elsewhere?
It runs the same source trees, ZIP/Deflate-9 implementation, solid tar+Zstd-19 implementation, exact extraction/tree
checks and complete public build timer as the canonical external gate.

Passing this shadow is necessary for selector promotion but never sufficient for v0.30 release.
"""

import argparse
import json
from pathlib import Path

from benchmarks import v030_external_competitors_canonical as EXT
from experiments import entropygraph_v030_release_product_logs_candidate as CAND

EXPECTED_MIN_FULL_WINS = 4  # predecessor shipping frontier had three exact four-way wins
EXPECTED_MIN_ZSTD_SIZE_WINS = 7  # predecessor shipping frontier had six
EXPECTED_ZIP_SIZE_WINS = 15


def run(work_root: Path) -> dict:
    old_canon = EXT.CANON
    old_cmpct = EXT.B.CMPCT
    old_cmpct_impl = EXT.B._cmpct
    EXT.CANON = CAND
    EXT.B.CMPCT = CAND
    EXT.B._cmpct = EXT._cmpct_with_stage_timings
    try:
        result = dict(EXT.run(work_root))
    finally:
        EXT.CANON = old_canon
        EXT.B.CMPCT = old_cmpct
        EXT.B._cmpct = old_cmpct_impl

    strict_rows = result["strict_per_workload_dominance"]["rows"]
    full_wins = sum(
        int(
            row["strictly_beats_zip_size"]
            and row["strictly_beats_zstd19_size"]
            and row["strictly_beats_zip_create"]
            and row["strictly_beats_zstd19_create"]
        )
        for row in strict_rows
    )
    zip_size_wins = sum(int(row["strictly_beats_zip_size"]) for row in strict_rows)
    zstd_size_wins = sum(int(row["strictly_beats_zstd19_size"]) for row in strict_rows)

    selected_logs = []
    for row in result["rows"]:
        cmpct = row["formats"]["cmpct_v030"]
        if cmpct.get("selected") == "logs-inverse":
            selected_logs.append(row["label"])
    logs_strict = next(
        (row for row in strict_rows if row["label"].endswith("/05_logs_and_telemetry")),
        None,
    )
    logs_four_way = bool(
        logs_strict
        and logs_strict["strictly_beats_zip_size"]
        and logs_strict["strictly_beats_zstd19_size"]
        and logs_strict["strictly_beats_zip_create"]
        and logs_strict["strictly_beats_zstd19_create"]
    )
    exact_cmpct_trees = bool(result["gate"].get("all_cmpct_trees_verified"))

    promotion_gate = {
        "exact_workload_count": len(strict_rows) == 15,
        "all_cmpct_trees_verified": exact_cmpct_trees,
        "only_logs_row_terminalized": selected_logs == ["neutral_hostile_v1/05_logs_and_telemetry"],
        "logs_is_strict_four_way_win": logs_four_way,
        "zip_size_frontier_preserved": zip_size_wins == EXPECTED_ZIP_SIZE_WINS,
        "zstd_size_frontier_materially_advances": zstd_size_wins >= EXPECTED_MIN_ZSTD_SIZE_WINS,
        "full_four_way_frontier_materially_advances": full_wins >= EXPECTED_MIN_FULL_WINS,
        "shipping_release_gate_not_reinterpreted": result["gate"].get("passed") is False or full_wins == 15,
    }
    promotion_gate["passed"] = all(promotion_gate.values())
    result["candidate_engine"] = "experiments/entropygraph_v030_release_product_logs_candidate.py"
    result["candidate_release_facade"] = "cmpct-v030-release-product-logs-candidate-v1"
    result["candidate_frontier"] = {
        "full_four_way_wins": full_wins,
        "zip_size_wins": zip_size_wins,
        "zstd_size_wins": zstd_size_wins,
        "terminal_logs_rows": selected_logs,
    }
    result["candidate_promotion_gate"] = promotion_gate
    result["claim_boundary"] = (
        "promotion shadow only; the canonical external gate remains authoritative and selector promotion cannot "
        "unlock release unless every frozen workload later satisfies the unchanged strict contract"
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-logs-selector-external-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-logs-selector-external.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "candidate_frontier": result["candidate_frontier"],
        "candidate_promotion_gate": result["candidate_promotion_gate"],
        "shipping_gate": result["gate"],
    }, indent=2), flush=True)
    if not result["candidate_promotion_gate"]["passed"]:
        raise SystemExit("logs selector external promotion shadow failed")


if __name__ == "__main__":
    main()
