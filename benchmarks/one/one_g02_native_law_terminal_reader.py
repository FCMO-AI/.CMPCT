"""ONE-G0.2 native Law-terminal reader integration falsifier.

Frozen by ONE_G02_NATIVE_LAW_TERMINAL_READER_PREREG_2026-09-09.md.
"""
from __future__ import annotations

import gc
from hashlib import sha256
import json
import random
import statistics
import time

from experiments.one.ir import Limits, Node, Program, Ref, Root
from experiments.one.native_law_terminal_plan import (
    compile_native_law_terminal_plan,
    execute_native_law_terminal_plan,
)
from experiments.one.vm import evaluate
from experiments.one.wire import encode_program

SIZES = (32 * 1024, 128 * 1024, 512 * 1024)
LAW_FAMILIES = ("add8", "xor", "add8_crack", "xor_crack")
CONTROLS = ("literal", "fill", "concat")
FAMILIES = LAW_FAMILIES + CONTROLS
ROUNDS = 9

MAX_MEDIAN_LAW_CPU_RATIO = 0.75
MAX_LAW_CPU_RATIO = 1.00
MAX_MEDIAN_CONTROL_CPU_RATIO = 1.10
MAX_CONTROL_CPU_RATIO = 1.25
MAX_MEDIAN_LAW_TRAFFIC_RATIO = 0.75


def _root(ref: Ref, value: bytes) -> Root:
    return Root(ref, len(value), sha256(value).hexdigest())


def _case(n: int, family: str) -> Program:
    rng = random.Random(0x1A700000 ^ n ^ sum(map(ord, family)))
    source = bytes(rng.randrange(256) for _ in range(n))

    if family in LAW_FAMILIES:
        op = "add8" if family.startswith("add8") else "xor"
        value = 37 if op == "add8" else 0xA7
        transformed = bytes(
            ((b + value) & 255) if op == "add8" else (b ^ value) for b in source
        )
        fill = Node("fill", count=n, value=value, declared_length=n)
        if not family.endswith("_crack"):
            nodes = (
                Node("surprise", surprise=source, declared_length=n),
                fill,
                Node(op, refs=(Ref(0), Ref(1)), declared_length=n),
            )
            return Program(
                nodes,
                {"previous": _root(Ref(0), source), "current": _root(Ref(2), transformed)},
                Limits(),
            )

        crack_width = 17
        crack_at = n // 2
        crack = bytes((x ^ 0x5D) for x in transformed[crack_at : crack_at + crack_width])
        current = (
            transformed[:crack_at]
            + crack
            + transformed[crack_at + crack_width :]
        )
        tail = n - crack_at - crack_width
        nodes = (
            Node("surprise", surprise=source, declared_length=n),
            fill,
            Node(
                op,
                refs=(Ref(0, 0, crack_at), Ref(1, 0, crack_at)),
                declared_length=crack_at,
            ),
            Node("surprise", surprise=crack, declared_length=crack_width),
            Node(
                op,
                refs=(
                    Ref(0, crack_at + crack_width, tail),
                    Ref(1, crack_at + crack_width, tail),
                ),
                declared_length=tail,
            ),
            Node("concat", refs=(Ref(2), Ref(3), Ref(4)), declared_length=n),
        )
        return Program(
            nodes,
            {"previous": _root(Ref(0), source), "current": _root(Ref(5), current)},
            Limits(),
        )

    if family == "literal":
        target = bytes(rng.randrange(256) for _ in range(n))
        nodes = (
            Node("surprise", surprise=source, declared_length=n),
            Node("surprise", surprise=target, declared_length=n),
        )
        return Program(
            nodes,
            {"previous": _root(Ref(0), source), "current": _root(Ref(1), target)},
            Limits(),
        )

    if family == "fill":
        target = bytes([0x6D]) * n
        nodes = (
            Node("surprise", surprise=source, declared_length=n),
            Node("fill", count=n, value=0x6D, declared_length=n),
        )
        return Program(
            nodes,
            {"previous": _root(Ref(0), source), "current": _root(Ref(1), target)},
            Limits(),
        )

    if family == "concat":
        a = bytes(rng.randrange(256) for _ in range(n // 2))
        fill_len = n - len(a)
        target = a + bytes([0x91]) * fill_len
        nodes = (
            Node("surprise", surprise=source, declared_length=n),
            Node("surprise", surprise=a, declared_length=len(a)),
            Node("fill", count=fill_len, value=0x91, declared_length=fill_len),
            Node("concat", refs=(Ref(1), Ref(2)), declared_length=n),
        )
        return Program(
            nodes,
            {"previous": _root(Ref(0), source), "current": _root(Ref(3), target)},
            Limits(),
        )

    raise ValueError(family)


def _median_time(fn):
    wall = []
    cpu = []
    value = None
    was_enabled = gc.isenabled()
    try:
        if was_enabled:
            gc.disable()
        for _ in range(ROUNDS):
            w0 = time.perf_counter_ns()
            c0 = time.process_time_ns()
            value = fn()
            cpu.append(time.process_time_ns() - c0)
            wall.append(time.perf_counter_ns() - w0)
    finally:
        if was_enabled:
            gc.enable()
    return value, int(statistics.median(wall)), int(statistics.median(cpu))


def _paired(program, plan):
    evaluate(program)
    execute_native_law_terminal_plan(plan)

    base_wall = []
    base_cpu = []
    native_wall = []
    native_cpu = []
    base_value = native_value = None
    was_enabled = gc.isenabled()
    try:
        if was_enabled:
            gc.disable()
        for i in range(ROUNDS):
            order = ("base", "native") if i % 2 == 0 else ("native", "base")
            for arm in order:
                w0 = time.perf_counter_ns()
                c0 = time.process_time_ns()
                if arm == "base":
                    value = evaluate(program)
                else:
                    value = execute_native_law_terminal_plan(plan)
                cpu = time.process_time_ns() - c0
                wall = time.perf_counter_ns() - w0
                if arm == "base":
                    base_value = value
                    base_cpu.append(cpu)
                    base_wall.append(wall)
                else:
                    native_value = value
                    native_cpu.append(cpu)
                    native_wall.append(wall)
    finally:
        if was_enabled:
            gc.enable()

    return (
        base_value,
        int(statistics.median(base_wall)),
        int(statistics.median(base_cpu)),
        native_value,
        int(statistics.median(native_wall)),
        int(statistics.median(native_cpu)),
    )


def run():
    rows = []
    law_cpu_ratios = []
    control_cpu_ratios = []
    law_traffic_ratios = []
    semantic_ok = True

    for n in SIZES:
        for family in FAMILIES:
            program = _case(n, family)
            wire, _wire_stats = encode_program(program)

            plan, prep_wall_ns, prep_cpu_ns = _median_time(
                lambda: compile_native_law_terminal_plan(program)
            )
            (
                baseline,
                baseline_wall_ns,
                baseline_cpu_ns,
                native,
                native_wall_ns,
                native_cpu_ns,
            ) = _paired(program, plan)

            baseline_outputs, baseline_stats = baseline
            native_outputs, native_stats = native
            exact = native_outputs == baseline_outputs
            semantic_ok &= exact
            if not exact:
                raise AssertionError("native Law terminal output diverged from reference VM")

            cpu_ratio = native_cpu_ns / max(baseline_cpu_ns, 1)
            wall_ratio = native_wall_ns / max(baseline_wall_ns, 1)
            traffic_ratio = (
                native_stats.modeled_memory_traffic_bytes / max(baseline_stats.work_bytes, 1)
            )
            root_bytes = sum(len(v) for v in baseline_outputs.values())
            native_mib_s = (
                root_bytes / (native_wall_ns / 1e9) / (1024 * 1024)
                if native_wall_ns
                else 1.0e99
            )

            kind = "law" if family in LAW_FAMILIES else "control"
            if kind == "law":
                law_cpu_ratios.append(cpu_ratio)
                law_traffic_ratios.append(traffic_ratio)
            else:
                control_cpu_ratios.append(cpu_ratio)

            rows.append(
                {
                    "version_bytes": n,
                    "family": family,
                    "kind": kind,
                    "semantic_ok": exact,
                    "program_nodes": len(program.nodes),
                    "wire_bytes": len(wire),
                    "root_bytes": root_bytes,
                    "prepare_wall_ns": prep_wall_ns,
                    "prepare_cpu_ns": prep_cpu_ns,
                    "baseline_wall_ns": baseline_wall_ns,
                    "baseline_cpu_ns": baseline_cpu_ns,
                    "native_wall_ns": native_wall_ns,
                    "native_cpu_ns": native_cpu_ns,
                    "native_over_baseline_wall": wall_ratio,
                    "native_over_baseline_cpu": cpu_ratio,
                    "native_mib_per_s": native_mib_s,
                    "baseline_materialized_bytes": baseline_stats.materialized_bytes,
                    "baseline_work_bytes": baseline_stats.work_bytes,
                    "baseline_depth": baseline_stats.max_depth,
                    "native_modeled_memory_traffic_bytes": native_stats.modeled_memory_traffic_bytes,
                    "native_over_baseline_work": traffic_ratio,
                    "native_peak_temporary_bytes": native_stats.peak_temporary_bytes,
                    "packed_source_plan_bytes": plan.packed_source_bytes,
                    "plan_command_count": plan.command_count,
                }
            )

    median_law_cpu = statistics.median(law_cpu_ratios)
    worst_law_cpu = max(law_cpu_ratios)
    median_control_cpu = statistics.median(control_cpu_ratios)
    worst_control_cpu = max(control_cpu_ratios)
    median_law_traffic = statistics.median(law_traffic_ratios)

    gates = {
        "semantic_ok": semantic_ok,
        "median_law_cpu_ok": median_law_cpu <= MAX_MEDIAN_LAW_CPU_RATIO,
        "worst_law_cpu_ok": worst_law_cpu <= MAX_LAW_CPU_RATIO,
        "median_control_cpu_ok": median_control_cpu <= MAX_MEDIAN_CONTROL_CPU_RATIO,
        "worst_control_cpu_ok": worst_control_cpu <= MAX_CONTROL_CPU_RATIO,
        "median_law_traffic_ok": median_law_traffic <= MAX_MEDIAN_LAW_TRAFFIC_RATIO,
        "peak_ok": all(r["native_peak_temporary_bytes"] <= r["version_bytes"] for r in rows),
    }
    summary = {
        "rows": rows,
        "summary": {
            "semantic_ok": semantic_ok,
            "median_law_native_over_baseline_cpu": median_law_cpu,
            "worst_law_native_over_baseline_cpu": worst_law_cpu,
            "median_control_native_over_baseline_cpu": median_control_cpu,
            "worst_control_native_over_baseline_cpu": worst_control_cpu,
            "median_law_native_over_baseline_work": median_law_traffic,
            "gates": gates,
            "advance": all(gates.values()),
        },
    }
    return summary


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, sort_keys=True))
    if not result["summary"]["advance"]:
        raise SystemExit(1)
