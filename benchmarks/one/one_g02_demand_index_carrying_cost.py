"""ONE-G0.2 demand-grown nomination-index carrying-cost gate.

Reuses the frozen native paired timing machinery from the fixed-index experiment,
but evaluates the current demand-grown fused kernel under the demand-index decision law.
"""
from __future__ import annotations

import json

from benchmarks.one.one_g02_fused_native_nomination_carrying_cost import run as _run_paired


def run() -> dict[str, object]:
    result = _run_paired()
    cross = float(result["cross_large_median_fused_over_two_stage"])
    worst = float(result["worst_fused_over_two_stage"])
    worst_negative = float(result["worst_negative_fused_over_two_stage"])
    selector_premium = float(result["median_fused_over_selector_only"])

    if cross >= 1.0 or worst_negative > 1.05:
        decision = "retire_demand_index_carrying_shape"
    elif cross <= 0.92 and worst <= 1.05 and worst_negative <= 1.0 and selector_premium <= 1.35:
        decision = "advance_demand_index_carrying_shape"
    else:
        decision = "hold_demand_index_carrying_shape"

    result["schema"] = "cmpct-one-g02-demand-index-carrying-cost-v1"
    result["decision"] = decision
    result.pop("fixed_research_event_index_storage_bytes", None)
    result["claim_boundary"] = (
        "hosted native carrying-cost evidence for the demand-grown fused research shape; "
        "semantic/resource gate is independent prerequisite and selector-only premium remains debt"
    )
    return result


if __name__ == "__main__":
    value = run()
    print(json.dumps(value, indent=2, sort_keys=True))
    raise SystemExit(0 if value["decision"] != "retire_demand_index_carrying_shape" else 1)
