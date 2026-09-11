"""ONE-G0.2 corrected temporal-adjacency writer integration.

This harness preserves the original frozen corpus/timing/gates while enforcing the
compiler boundary frozen in the original preregistration: only a byte-exact +1
shift compiles to generic ONE ranged Ref + Surprise structure. Accepted damaged
relations remain literal in this experiment and are reported as compiler debt.
"""
from __future__ import annotations

import json

from benchmarks.one import one_g02_temporal_adjacency_writer_integration as base


def _is_exact_plus1(source: bytes, target: bytes) -> bool:
    return (
        len(source) == len(target)
        and bool(source)
        and all(target[i] == source[i - 1] for i in range(1, len(target)))
    )


def _frozen_compile_program(source: bytes, target: bytes, enabled: bool, best_shift: int):
    if enabled and best_shift == 1 and _is_exact_plus1(source, target):
        return base._relation_program_plus1(source, target), True
    return base._literal_program(source, target), False


def run():
    original = base._compile_program
    base._compile_program = _frozen_compile_program
    try:
        result = base.run()
    finally:
        base._compile_program = original

    result["schema"] = "cmpct-one-g02-temporal-adjacency-writer-v2"
    result["compiler_boundary"] = (
        "only byte-exact +1 shift compiles through generic ONE; accepted damaged "
        "relations remain literal Surprise in this integration gate"
    )
    data_rows = [row for row in result["rows"] if row.get("case") != "__size_timing__"]
    result["accepted_but_literal_baseline_rows"] = sum(
        1 for row in data_rows
        if row.get("baseline_enabled") and not row.get("baseline_relation_compiled")
    )
    result["accepted_but_literal_candidate_rows"] = sum(
        1 for row in data_rows
        if row.get("candidate_enabled") and not row.get("candidate_relation_compiled")
    )
    result["generic_relation_compiled_rows"] = sum(
        1 for row in data_rows if row.get("candidate_relation_compiled")
    )
    result["claim_boundary"] = (
        "research adjacent-version known-pair admission only; corrected frozen compiler "
        "boundary; Python object/wire construction is not product-speed authority; "
        "arbitrary pair discovery and damaged-relation compiler density remain outside scope"
    )
    return result


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["decision"] == "advance_temporal_adjacency_writer_gate" else 1)
