from __future__ import annotations

"""Evidence-safe wrapper for the G0-G4 duplicate-metadata A/B.

A clean performance rejection is useful negative evidence and must not become permanent red CI. This wrapper keeps
v1's exact archive/tree/corruption experiment unchanged, separates experiment validity from promotion materiality,
and records the unchanged record/node cache budgets without claiming that Python bookkeeping itself consumes zero
bytes.
"""

import argparse
import json
from pathlib import Path

from benchmarks import v030_g04_metadata_copy_reuse_oracle as BASE


def run(work_root: Path) -> dict:
    result = BASE.run(work_root)
    old_gate = dict(result["gate"])
    experiment_valid = all(
        old_gate[key]
        for key in (
            "candidate_reused_identical_tail_every_verify",
            "candidate_reused_identical_tail_every_extract",
            "physical_record_reads_unchanged",
            "tail_difference_forces_full_decode_path",
            "tail_corruption_primary_recovery_same_tree",
        )
    )
    promotion_earned = experiment_valid and old_gate["verify_materially_faster"] and old_gate["extract_materially_faster"]
    result["schema"] = "cmpct-v030-g04-metadata-copy-reuse-v2"
    result["gate"] = {
        **old_gate,
        "experiment_valid": experiment_valid,
        "promotion_earned": promotion_earned,
    }
    result["contract"].pop("memory_budget_change_bytes", None)
    result["contract"].update(
        {
            "record_cache_budget_change_bytes": 0,
            "node_cache_budget_change_bytes": 0,
            "python_memo_scope": "one archive open; one validated metadata object/key for the duplicate-control A/B",
            "negative_result_policy": "valid measured rejection remains green research evidence; production promotion requires promotion_earned",
        }
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-g04-meta-reuse-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-g04-meta-reuse.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "verify_improvement_fraction": result["verify_improvement_fraction"],
        "extract_improvement_fraction": result["extract_improvement_fraction"],
        "gate": result["gate"],
    }, indent=2), flush=True)
    if not result["gate"]["experiment_valid"]:
        raise SystemExit("G0-G4 metadata-copy reuse experiment invalid")


if __name__ == "__main__":
    main()
