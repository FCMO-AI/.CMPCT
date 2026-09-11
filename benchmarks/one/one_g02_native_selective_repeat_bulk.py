"""ONE-G0.2 direct periodic Repeat bulk rehabilitation falsifier.

Reuses the frozen V1 matrix/economic thresholds and adds the V2 physical-stage gates
preregistered before the result-bearing implementation.
"""
from __future__ import annotations

import json

from benchmarks.one.one_g02_native_selective_repeat_lowering import run as run_v1


def run():
    result = run_v1()
    rows = result["rows"]
    zero_source_plan = all(row["packed_source_bytes"] == 0 and row["source_plan_write_bytes"] == 0 for row in rows)
    one_descriptor = all(row["plan_commands"] == 1 for row in rows)
    tighter_temp = all(
        row["peak_temporary_bytes"] <= 2 * row["cone_bytes"] + row["proof_hash_bytes"]
        for row in rows
    )

    inherited = dict(result["summary"]["gates"])
    gates = {
        **inherited,
        "zero_full_cone_source_plan": zero_source_plan,
        "one_bulk_periodic_descriptor": one_descriptor,
        "tightened_temporary_bound_ok": tighter_temp,
    }
    semantic_hard = all(
        gates[name]
        for name in (
            "semantic_exact",
            "cone_geometry_exact",
            "fixed_cone_root_scaling_ok",
            "temporary_bound_ok",
            "command_bound_ok",
            "zero_full_cone_source_plan",
            "one_bulk_periodic_descriptor",
            "tightened_temporary_bound_ok",
        )
    )
    advance = all(gates.values())
    decision = (
        "INVALIDATE_NATIVE_SELECTIVE_REPEAT_BULK"
        if not semantic_hard
        else (
            "ADVANCE_NATIVE_SELECTIVE_REPEAT_BULK"
            if advance
            else "HOLD_NATIVE_SELECTIVE_REPEAT_BULK"
        )
    )
    result["schema"] = "cmpct-one-g02-native-selective-repeat-bulk-v1"
    result["summary"] = {
        **result["summary"],
        "gates": gates,
        "advance": advance,
        "decision": decision,
    }
    return result


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, sort_keys=True))
    decision = result["summary"]["decision"]
    if decision.startswith("INVALIDATE"):
        raise SystemExit(2)
    if not result["summary"]["advance"]:
        raise SystemExit(1)
