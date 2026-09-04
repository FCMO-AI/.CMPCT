from __future__ import annotations

"""Source-bound domination decision for the exact Analytics effort bracket.

This wraps the existing six-arm measurement without changing a candidate byte or timing
boundary.  It exists so a completed receipt can either promote a real crossing or retire
compression-level tuning and force representation-level work.
"""

import argparse
import json
import os
from pathlib import Path

from benchmarks import v030_analytics_v029_effort_frontier as CORE


def run(work_root: Path) -> dict:
    result = CORE.run(work_root)
    rows = list(result["rows"])
    zip_s = float(result["comparators"]["zip"]["median_create_s"])
    accepted = int(result["accepted_v029_bytes"])

    within_zip_budget = [r for r in rows if float(r["median_complete_verified_create_s"]) < zip_s]
    best_budget_row = min(within_zip_budget, key=lambda r: int(r["archive_bytes"])) if within_zip_budget else None
    size_qualifying = [r for r in rows if int(r["archive_bytes"]) <= accepted]
    fastest_size_row = min(size_qualifying, key=lambda r: float(r["median_complete_verified_create_s"])) if size_qualifying else None
    viable = [r for r in rows if r["strict"]["release_size_time_prerequisites"]]

    if viable:
        terminal = "PROMOTE_NEXT_PREREQUISITE"
        next_test = "productize the fastest viable content-agnostic level policy and run exact all-15 no-regression/external authority"
    else:
        terminal = "ESCALATE_RADICALITY"
        next_test = "replace effort tuning with a representation/execution change that crosses v0.29 inside the ZIP creation budget"

    best_budget_gap = None if best_budget_row is None else accepted - int(best_budget_row["archive_bytes"])
    size_time_gap = None if fastest_size_row is None else float(fastest_size_row["median_complete_verified_create_s"]) - zip_s
    result.update({
        "schema": "cmpct-v030-analytics-v029-effort-decision-v2",
        "source_commit": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local",
        "domination_audit": {
            "strict_target": "15/15 strictly smaller and faster than ZIP/Deflate and solid Zstd-19; ties fail",
            "diagnosis": "D2",
            "radicality": "R2",
            "required_next_radicality_if_red": "R4",
            "saturation_triggers": ["S1", "S3", "S4"],
            "research_priority_score": 95,
            "pre_mortem": "higher compression effort may buy the v0.29 bytes only after creation time has already exceeded ZIP",
            "builder": "measure level 1 plus the exact 15-19 crossing bracket with canonical filesystem tax and strong verification inside timing",
            "hostile_review": "a level that crosses v0.29 but misses either external time comparator is still a loss; no interpolation receives credit",
            "best_within_zip_budget_saving_vs_v029_bytes": best_budget_gap,
            "fastest_size_qualifying_time_gap_vs_zip_s": size_time_gap,
            "terminal_decision": terminal,
            "next_decisive_test": next_test,
        },
    })
    return result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-root", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"result": result["result"], "domination_audit": result["domination_audit"]}, indent=2), flush=True)


if __name__ == "__main__":
    main()
