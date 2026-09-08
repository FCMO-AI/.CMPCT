"""Frozen ONE-G0.2 native bulk data-plane falsifier."""
from __future__ import annotations

import json
import statistics
import time

from benchmarks.one.one_g02_generic_execution_plan import FAMILIES, SIZES, _program
from experiments.one.generic_execution_plan import compile_execution_plan, execute_plan
from experiments.one.native_plan_bulk import execute_native_bulk_plan
from experiments.one.vm import evaluate

REPETITIONS = 9
ARITHMETIC_FAMILIES = ("xor2", "add8_3")
NON_ARITHMETIC_FAMILIES = tuple(f for f in FAMILIES if f not in ARITHMETIC_FAMILIES)
ARITHMETIC_MAX = 0.35
NON_ARITHMETIC_MAX = 1.05


def median(values):
    return statistics.median(values)


def decide(rows, semantic_ok: bool) -> str:
    expected = {(size, family) for size in SIZES for family in FAMILIES}
    observed = {(row["size"], row["family"]) for row in rows}
    if not semantic_ok or observed != expected or len(rows) != len(expected):
        return "INVALIDATE_NATIVE_PLAN_BULK"
    for row in rows:
        limit = ARITHMETIC_MAX if row["family"] in ARITHMETIC_FAMILIES else NON_ARITHMETIC_MAX
        if row["wall_ratio"] > limit or row["cpu_ratio"] > limit:
            return "HOLD_NATIVE_PLAN_BULK"
    return "ADVANCE_NATIVE_PLAN_BULK"


def run():
    rows = []
    semantic_ok = True
    # Warm the research shared library outside timed replay; product/native startup is not
    # claimed by this hot-path falsifier and the C source would ordinarily be prebuilt.
    warm = compile_execution_plan(_program("xor2", 64 * 1024))
    execute_native_bulk_plan(warm)

    for size in SIZES:
        for family in FAMILIES:
            program = _program(family, size)
            reference, reference_stats = evaluate(program)
            plan = compile_execution_plan(program)
            generic, generic_stats = execute_plan(plan)
            native, native_stats = execute_native_bulk_plan(plan)
            semantic_ok &= native == generic == reference and native_stats == generic_stats and native_stats.work_bytes == reference_stats.work_bytes

            generic_wall = []
            generic_cpu = []
            native_wall = []
            native_cpu = []
            for rep in range(REPETITIONS):
                order = ("native", "generic") if rep & 1 else ("generic", "native")
                for arm in order:
                    w0 = time.perf_counter_ns()
                    c0 = time.process_time_ns()
                    if arm == "generic":
                        out, _ = execute_plan(plan)
                    else:
                        out, _ = execute_native_bulk_plan(plan)
                    wall = time.perf_counter_ns() - w0
                    cpu = time.process_time_ns() - c0
                    if out != reference:
                        semantic_ok = False
                    (generic_wall if arm == "generic" else native_wall).append(wall)
                    (generic_cpu if arm == "generic" else native_cpu).append(cpu)

            gw, gc = median(generic_wall), median(generic_cpu)
            nw, nc = median(native_wall), median(native_cpu)
            rows.append({"size": size, "family": family, "generic_wall_ns": gw, "generic_cpu_ns": gc, "native_wall_ns": nw, "native_cpu_ns": nc, "wall_ratio": nw / gw, "cpu_ratio": nc / gc})

    decision = decide(rows, semantic_ok)
    payload = {"decision": decision, "semantic_ok": semantic_ok, "exact_matrix": len(rows) == len(SIZES) * len(FAMILIES), "repetitions": REPETITIONS, "arithmetic_max": ARITHMETIC_MAX, "non_arithmetic_max": NON_ARITHMETIC_MAX, "rows": rows}
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if decision == "ADVANCE_NATIVE_PLAN_BULK" else 1


if __name__ == "__main__":
    raise SystemExit(run())
