from __future__ import annotations

"""Optimistic BytePlane4-margin oracle for Analytics high-effort work elimination.

Mission: docs/V030_ANALYTICS_MARGIN_CPU_ORACLE_MISSION_2026-09-12.md
Research-only. The selected pack identities are oracle evidence, never encoder policy.
"""

import argparse
import json
from pathlib import Path
import shutil

from benchmarks import v030_analytics_l19_cost_attribution_referee as COST

ACCEPTED_V029_BYTES = 6_135_172
BYTEPLANE4_STRONG_BYTES = 6_063_752
BYTE_BUDGET = ACCEPTED_V029_BYTES - BYTEPLANE4_STRONG_BYTES
EXPECTED_PACKS = 45
MIN_CPU_REMOVAL_FRACTION = 0.70


def _solve_exact_knapsack(rows: list[dict], budget: int) -> dict:
    """Maximize removable L19 CPU under exact deterministic byte giveback.

    State is sparse because only 45 items exist. The bit mask is evidence/provenance only and must
    never become a selector: this oracle deliberately receives impossible post-result knowledge.
    """
    # bytes -> (cpu_removed, mask)
    states: dict[int, tuple[float, int]] = {0: (0.0, 0)}
    for idx, row in enumerate(rows):
        weight = max(0, int(row["saving_bytes"]))
        value = max(0.0, float(row["median_l19_cpu_s"]))
        updated = dict(states)
        bit = 1 << idx
        for used, (cpu, mask) in states.items():
            new_used = used + weight
            if new_used > budget:
                continue
            new_cpu = cpu + value
            incumbent = updated.get(new_used)
            if incumbent is None or new_cpu > incumbent[0]:
                updated[new_used] = (new_cpu, mask | bit)
        states = updated

    used, (cpu_removed, mask) = max(
        states.items(), key=lambda item: (item[1][0], -item[0])
    )
    selected = [rows[i] for i in range(len(rows)) if mask & (1 << i)]
    return {
        "byte_giveback": used,
        "cpu_removed_s": cpu_removed,
        "selected_count": len(selected),
        "selected": selected,
    }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)

    attribution = COST.run(work_root / "cost-attribution")
    rows = list(attribution["packs_by_l19_cpu_desc"])
    if len(rows) != EXPECTED_PACKS:
        raise RuntimeError(f"frozen pack population drift: {len(rows)} != {EXPECTED_PACKS}")
    if attribution["fixture"]["admitted_count"] != EXPECTED_PACKS:
        raise RuntimeError("attribution fixture admission drift")
    if BYTE_BUDGET != 71_420:
        raise RuntimeError("frozen BytePlane4 archive-margin arithmetic drift")

    oracle = _solve_exact_knapsack(rows, BYTE_BUDGET)
    total_cpu = float(attribution["total_median_l19_cpu_s_sum"])
    total_saving = int(attribution["total_saving_bytes"])
    removed = float(oracle["cpu_removed_s"])
    remaining_cpu = max(0.0, total_cpu - removed)
    removal_fraction = removed / max(total_cpu, 1e-12)
    retained_reward = total_saving - int(oracle["byte_giveback"])

    verdict = (
        "MARGIN_CAN_SUPPORT_SKIP_RESEARCH"
        if removal_fraction >= MIN_CPU_REMOVAL_FRACTION
        else "MARGIN_INSUFFICIENT_RETIRE_SKIP_ONLY"
    )

    return {
        "schema": "cmpct-v030-analytics-margin-cpu-oracle-v1",
        "experiment_valid": True,
        "release_credit": False,
        "target": "neutral_hostile_v1/04_analytics_and_database",
        "frozen_bytes": {
            "accepted_v029": ACCEPTED_V029_BYTES,
            "byteplane4_strong": BYTEPLANE4_STRONG_BYTES,
            "spendable_margin": BYTE_BUDGET,
        },
        "cost_attribution": {
            "fixture": attribution["fixture"],
            "total_median_l19_cpu_s_sum": total_cpu,
            "total_median_l15_cpu_s_sum": float(attribution["total_median_l15_cpu_s_sum"]),
            "total_l15_to_l19_saving_bytes": total_saving,
            "source_verdict": attribution["verdict"],
            "source_concentration": attribution["concentration"],
        },
        "omniscient_oracle": {
            "selected_count": int(oracle["selected_count"]),
            "byte_giveback": int(oracle["byte_giveback"]),
            "unused_margin_bytes": BYTE_BUDGET - int(oracle["byte_giveback"]),
            "cpu_removed_s": removed,
            "cpu_remaining_s": remaining_cpu,
            "cpu_removal_fraction": removal_fraction,
            "retained_l15_to_l19_reward_bytes": retained_reward,
            "selected_rows": oracle["selected"],
        },
        "gate": {
            "byte_giveback_within_margin": int(oracle["byte_giveback"]) <= BYTE_BUDGET,
            "cpu_removal_fraction_at_least_0_70": removal_fraction >= MIN_CPU_REMOVAL_FRACTION,
        },
        "verdict": verdict,
        "contract": {
            "oracle_uses_post_result_knowledge": True,
            "oracle_identities_not_policy": True,
            "no_path_extension_workload_policy": True,
            "no_selector_threshold_sweep": True,
            "byteplane4_margin_frozen_from_prior_receipt": True,
            "cost_measurement_repeated_rotated": True,
            "no_archive_format_or_release_credit": True,
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--work-root",
        type=Path,
        default=Path("benchmark-artifacts/v030-analytics-margin-cpu-work"),
    )
    ap.add_argument(
        "--output",
        type=Path,
        default=Path("benchmark-artifacts/v030-analytics-margin-cpu.json"),
    )
    args = ap.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({
        "verdict": result["verdict"],
        "byte_giveback": result["omniscient_oracle"]["byte_giveback"],
        "cpu_removal_fraction": result["omniscient_oracle"]["cpu_removal_fraction"],
        "selected_count": result["omniscient_oracle"]["selected_count"],
    }, indent=2))


if __name__ == "__main__":
    main()
