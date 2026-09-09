"""ONE-G0.2 reusable validated-Program selective planning falsifier.

Frozen by ONE_G02_VALIDATED_PROGRAM_SELECTIVE_PLAN_PREREG_2026-09-09.md.
"""
from __future__ import annotations

import gc
import json
import statistics
import time

from benchmarks.one.one_g02_native_law_terminal_reader import _case
from benchmarks.one.one_g02_selective_preflight_scaling import _with_unrelated_nodes
from experiments.one.native_law_range_plan import (
    compile_native_law_range_plan,
    compile_validated_native_law_range_plan,
    execute_native_law_range_plan,
)
from experiments.one.validated_program import validate_program_snapshot

ROOT_BYTES = 128 * 1024
REQUEST_START = 0
REQUEST_BYTES = 4096
DEAD_NODE_COUNTS = (0, 64, 256, 1024, 4096)
ROUNDS = 11
MAX_CANDIDATE_GROWTH = 2.0
MAX_LARGE_CANDIDATE_OVER_INCUMBENT = 0.20


def _median_cpu_ns(fn) -> tuple[object, int]:
    value = fn()
    samples = []
    was_enabled = gc.isenabled()
    try:
        if was_enabled:
            gc.disable()
        for _ in range(ROUNDS):
            c0 = time.process_time_ns()
            value = fn()
            samples.append(time.process_time_ns() - c0)
    finally:
        if was_enabled:
            gc.enable()
    return value, int(statistics.median(samples))


def run():
    rows = []
    semantic_ok = True
    candidate_zero = {}

    for family in ("add8", "xor"):
        base = _case(ROOT_BYTES, family)
        for unrelated in DEAD_NODE_COUNTS:
            program = _with_unrelated_nodes(base, unrelated)

            validated, validation_cpu_ns = _median_cpu_ns(
                lambda p=program: validate_program_snapshot(p)
            )
            incumbent_plan, incumbent_cpu_ns = _median_cpu_ns(
                lambda p=program: compile_native_law_range_plan(
                    p, "current", REQUEST_START, REQUEST_BYTES
                )
            )
            candidate_plan, candidate_cpu_ns = _median_cpu_ns(
                lambda v=validated: compile_validated_native_law_range_plan(
                    v, "current", REQUEST_START, REQUEST_BYTES
                )
            )

            incumbent_value = execute_native_law_range_plan(incumbent_plan)
            candidate_value = execute_native_law_range_plan(candidate_plan)
            exact = candidate_value == incumbent_value
            semantic_ok &= exact
            if not exact:
                raise AssertionError("validated selective plan diverged from incumbent")

            if unrelated == 0:
                candidate_zero[family] = candidate_cpu_ns
            growth = candidate_cpu_ns / max(candidate_zero[family], 1)
            ratio = candidate_cpu_ns / max(incumbent_cpu_ns, 1)
            rows.append(
                {
                    "family": family,
                    "root_bytes": ROOT_BYTES,
                    "request_bytes": REQUEST_BYTES,
                    "unrelated_nodes": unrelated,
                    "program_nodes": len(program.nodes),
                    "declared_max_nodes": program.limits.max_nodes,
                    "validation_open_cpu_ns": validation_cpu_ns,
                    "validation_preflight_entries": validated.preflight_entry_count,
                    "validation_modeled_preflight_bytes": validated.modeled_preflight_bytes,
                    "validation_python_preflight_bytes": validated.python_preflight_bytes,
                    "incumbent_per_request_compile_cpu_ns": incumbent_cpu_ns,
                    "candidate_per_request_compile_cpu_ns": candidate_cpu_ns,
                    "candidate_over_incumbent": ratio,
                    "candidate_growth_over_zero_unrelated": growth,
                    "semantic_ok": exact,
                }
            )

    growth_by_family = {
        family: max(
            r["candidate_growth_over_zero_unrelated"]
            for r in rows
            if r["family"] == family
        )
        for family in ("add8", "xor")
    }
    large_rows = [r for r in rows if r["unrelated_nodes"] in {1024, 4096}]
    gates = {
        "semantic_ok": semantic_ok,
        "candidate_growth_ok": all(v <= MAX_CANDIDATE_GROWTH for v in growth_by_family.values()),
        "large_candidate_over_incumbent_ok": all(
            r["candidate_over_incumbent"] <= MAX_LARGE_CANDIDATE_OVER_INCUMBENT
            for r in large_rows
        ),
    }
    return {
        "schema": "cmpct-one-g02-validated-program-selective-plan-v2",
        "experimental_version": "ONE-G0.2",
        "root_bytes": ROOT_BYTES,
        "request_bytes": REQUEST_BYTES,
        "rounds": ROUNDS,
        "summary": {
            "semantic_ok": semantic_ok,
            "max_candidate_growth_by_family": growth_by_family,
            "median_candidate_over_incumbent": statistics.median(
                r["candidate_over_incumbent"] for r in rows
            ),
            "median_large_candidate_over_incumbent": statistics.median(
                r["candidate_over_incumbent"] for r in large_rows
            ),
            "max_validation_modeled_preflight_bytes": max(
                r["validation_modeled_preflight_bytes"] for r in rows
            ),
            "max_validation_python_preflight_bytes": max(
                r["validation_python_preflight_bytes"] for r in rows
            ),
            "gates": gates,
            "advance": all(gates.values()),
            "interpretation": (
                "validation_open_cpu_ns and retained preflight state are deliberately disclosed separately: "
                "the candidate models repeated range requests after one complete immutable Program-open "
                "validation, never skipped validation."
            ),
        },
        "rows": rows,
    }


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, sort_keys=True))
    if not result["summary"]["advance"]:
        raise SystemExit(1)
