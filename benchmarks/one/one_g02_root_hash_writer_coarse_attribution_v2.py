"""Exact owner-size decision wrapper for ONE-G0.2 root-hash writer attribution.

The timed experiment is unchanged from v1. This wrapper repairs only the secondary
owner-size decision map according to the immutable amendment: 16/64/256 KiB.
"""
from __future__ import annotations

import json
import statistics

from benchmarks.one.one_g02_root_hash_writer_coarse_attribution import (
    OWNER_REQUIRED_MATURE_SIZES,
    OWNER_SHARE_MIN,
    OWNER_SIZE_SHARE_MIN,
    PHASES,
    run as run_v1,
)

OWNER_SIZES = (16 * 1024, 64 * 1024, 256 * 1024)


def run():
    result = run_v1()
    owner_size_medians = {name: {} for name in PHASES}
    for name in PHASES:
        for size in OWNER_SIZES:
            values = [
                float(row["phase_share"][name])
                for row in result["rows"]
                if row["productive"] and int(row["relation_bytes"]) == size
            ]
            if not values:
                raise AssertionError(f"missing frozen owner-size rows for {name} at {size}")
            owner_size_medians[name][str(size)] = float(statistics.median(values))

    phase_medians = result["mature_productive_phase_share_medians"]
    qualifying = []
    for name in PHASES:
        sizes_at_20 = sum(
            1 for value in owner_size_medians[name].values()
            if value >= OWNER_SIZE_SHARE_MIN
        )
        if (
            float(phase_medians[name]) >= OWNER_SHARE_MIN
            and sizes_at_20 >= OWNER_REQUIRED_MATURE_SIZES
        ):
            qualifying.append(name)
    qualifying.sort(key=lambda name: float(phase_medians[name]), reverse=True)

    if (
        not result["semantic_gates_pass"]
        or not result["native_plan_oracle_pass"]
        or not result["instrumentation_overhead_gate_pass"]
    ):
        decision = "invalidate_root_hash_writer_attribution"
    elif qualifying:
        decision = "localize_root_hash_writer_owner"
    else:
        decision = "diffuse_root_hash_writer_cost"

    result["schema"] = "cmpct-one-g02-root-hash-writer-coarse-attribution-v2"
    result["owner_size_rule_bytes"] = list(OWNER_SIZES)
    result["owner_size_phase_share_medians"] = owner_size_medians
    result["qualifying_material_owners"] = qualifying
    result["primary_owner"] = qualifying[0] if qualifying else None
    result["decision"] = decision
    result["supersedes_terminal_decision_from_v1"] = True
    result["amendment"] = (
        "ONE_G02_ROOT_HASH_WRITER_COARSE_ATTRIBUTION_OWNER_SIZE_AMENDMENT_2026-09-06.md"
    )
    return result


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(
        0 if result["decision"] in {
            "localize_root_hash_writer_owner", "diffuse_root_hash_writer_cost"
        } else 1
    )
