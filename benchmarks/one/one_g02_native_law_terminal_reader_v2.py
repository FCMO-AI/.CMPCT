"""ONE-G0.2 native Law terminal reader V2 rehabilitation falsifier."""
from __future__ import annotations

import gc
import json
import statistics
import time

from benchmarks.one.one_g02_native_law_terminal_reader import (
    CONTROLS,
    FAMILIES,
    LAW_FAMILIES,
    ROUNDS,
    SIZES,
    _case,
)
from experiments.one.native_law_terminal_plan import (
    compile_native_law_terminal_plan,
    execute_native_law_terminal_plan,
    has_native_law_op,
)
from experiments.one.vm import evaluate

MAX_MEDIAN_LAW_CPU_RATIO = 0.75
MAX_LAW_CPU_RATIO = 1.00
MAX_MEDIAN_CONTROL_CPU_RATIO = 1.10
MAX_CONTROL_CPU_RATIO = 1.25
MAX_MEDIAN_LAW_TRAFFIC_RATIO = 0.75


def _prepare(program):
    if not has_native_law_op(program):
        return None
    return compile_native_law_terminal_plan(program)


def _candidate(program, plan):
    # Eligibility is deliberately rechecked inside every hot call so fallback is not free.
    if not has_native_law_op(program):
        return evaluate(program), True
    if plan is None:
        raise AssertionError("eligible Program missing native plan")
    return execute_native_law_terminal_plan(plan), False


def _median_prepare(program):
    wall = []
    cpu = []
    value = None
    for _ in range(ROUNDS):
        w0 = time.perf_counter_ns()
        c0 = time.process_time_ns()
        value = _prepare(program)
        cpu.append(time.process_time_ns() - c0)
        wall.append(time.perf_counter_ns() - w0)
    return value, int(statistics.median(wall)), int(statistics.median(cpu))


def _paired(program, plan):
    evaluate(program)
    _candidate(program, plan)
    bw = []; bc = []; cw = []; cc = []
    base = cand = None
    fallback = None
    enabled = gc.isenabled()
    try:
        if enabled:
            gc.disable()
        for i in range(ROUNDS):
            order = ("base", "cand") if i % 2 == 0 else ("cand", "base")
            for arm in order:
                w0 = time.perf_counter_ns(); c0 = time.process_time_ns()
                if arm == "base":
                    value = evaluate(program)
                else:
                    value, fb = _candidate(program, plan)
                cpu = time.process_time_ns() - c0; wall = time.perf_counter_ns() - w0
                if arm == "base":
                    base = value; bc.append(cpu); bw.append(wall)
                else:
                    cand = value; fallback = fb; cc.append(cpu); cw.append(wall)
    finally:
        if enabled:
            gc.enable()
    return base, int(statistics.median(bw)), int(statistics.median(bc)), cand, int(statistics.median(cw)), int(statistics.median(cc)), fallback


def run():
    rows = []
    law_cpu = []; control_cpu = []; law_traffic = []
    semantic_ok = True
    for n in SIZES:
        for family in FAMILIES:
            program = _case(n, family)
            plan, prep_wall, prep_cpu = _median_prepare(program)
            base, bw, bc, cand, cw, cc, fallback = _paired(program, plan)
            base_outputs, base_stats = base
            cand_outputs, cand_stats = cand
            exact = cand_outputs == base_outputs
            if not exact:
                raise AssertionError("V2 candidate diverged from reference VM")
            semantic_ok &= exact
            cpu_ratio = cc / max(bc, 1)
            wall_ratio = cw / max(bw, 1)
            kind = "law" if family in LAW_FAMILIES else "control"
            traffic_ratio = None
            modeled = None
            peak = None
            packed = 0 if plan is None else plan.packed_source_bytes
            commands = 0 if plan is None else plan.command_count
            if kind == "law":
                law_cpu.append(cpu_ratio)
                modeled = cand_stats.modeled_memory_traffic_bytes
                peak = cand_stats.peak_temporary_bytes
                traffic_ratio = modeled / max(base_stats.work_bytes, 1)
                law_traffic.append(traffic_ratio)
                if fallback:
                    raise AssertionError("eligible Law row unexpectedly fell back")
            else:
                control_cpu.append(cpu_ratio)
                if not fallback:
                    raise AssertionError("no-Law control unexpectedly used native Law plan")
            rows.append({
                "version_bytes": n,
                "family": family,
                "kind": kind,
                "semantic_ok": exact,
                "fallback": fallback,
                "prepare_wall_ns": prep_wall,
                "prepare_cpu_ns": prep_cpu,
                "baseline_wall_ns": bw,
                "baseline_cpu_ns": bc,
                "candidate_wall_ns": cw,
                "candidate_cpu_ns": cc,
                "candidate_over_baseline_wall": wall_ratio,
                "candidate_over_baseline_cpu": cpu_ratio,
                "baseline_materialized_bytes": base_stats.materialized_bytes,
                "baseline_work_bytes": base_stats.work_bytes,
                "candidate_modeled_memory_traffic_bytes": modeled,
                "candidate_over_baseline_work": traffic_ratio,
                "candidate_peak_temporary_bytes": peak,
                "packed_source_plan_bytes": packed,
                "plan_command_count": commands,
                "root_bytes": sum(len(v) for v in base_outputs.values()),
            })
    med_law = statistics.median(law_cpu); worst_law = max(law_cpu)
    med_control = statistics.median(control_cpu); worst_control = max(control_cpu)
    med_traffic = statistics.median(law_traffic)
    gates = {
        "semantic_ok": semantic_ok,
        "median_law_cpu_ok": med_law <= MAX_MEDIAN_LAW_CPU_RATIO,
        "worst_law_cpu_ok": worst_law <= MAX_LAW_CPU_RATIO,
        "median_control_cpu_ok": med_control <= MAX_MEDIAN_CONTROL_CPU_RATIO,
        "worst_control_cpu_ok": worst_control <= MAX_CONTROL_CPU_RATIO,
        "median_law_traffic_ok": med_traffic <= MAX_MEDIAN_LAW_TRAFFIC_RATIO,
        "peak_ok": all(r["candidate_peak_temporary_bytes"] is None or r["candidate_peak_temporary_bytes"] <= r["version_bytes"] for r in rows),
    }
    return {"rows": rows, "summary": {
        "semantic_ok": semantic_ok,
        "median_law_candidate_over_baseline_cpu": med_law,
        "worst_law_candidate_over_baseline_cpu": worst_law,
        "median_control_candidate_over_baseline_cpu": med_control,
        "worst_control_candidate_over_baseline_cpu": worst_control,
        "median_law_candidate_over_baseline_work": med_traffic,
        "gates": gates,
        "advance": all(gates.values()),
    }}


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, sort_keys=True))
    if not result["summary"]["advance"]:
        raise SystemExit(1)
