"""ONE-G0.2 open-once validated authenticated selective lifecycle falsifier.

Frozen by ONE_G02_VALIDATED_AUTHENTICATED_SELECTIVE_LIFECYCLE_PREREG_2026-09-09.md.
The candidate pays full Program validation once per open and reuses the sealed authority for
repeated authenticated native cone reads. The comparator repeats raw full preflight per read.
"""
from __future__ import annotations

import gc
import json
import os
import statistics
import time

from benchmarks.one.one_g02_native_law_terminal_reader import CONTROLS, LAW_FAMILIES, _case
from experiments.one.auth_tree import build_auth_tree
from experiments.one.authenticated_native_selective_cone import (
    reconstruct_authenticated_native_range,
    reconstruct_validated_authenticated_native_range,
)
from experiments.one.ir import Node, Program
from experiments.one.validated_program import (
    validate_program_snapshot,
    validate_program_snapshot_compact,
)
from experiments.one.vm import evaluate

ROOT_BYTES = 128 * 1024
LEAF_BYTES = 4096
FAMILIES = LAW_FAMILIES + CONTROLS
TOTAL_NODE_TARGETS = (0, 64, 512, 2048, 4096)
REQUEST_COUNTS = (1, 4, 16, 64)
ROUNDS = 5

MAX_RETAINED_RATIO_AT_4096 = 0.40
MAX_MEDIAN_CPU_RATIO_GE4 = 0.75
MAX_MEDIAN_CPU_RATIO_GE16 = 0.50
MAX_WORST_ONESHOT_CPU_RATIO = 1.30


def _with_total_nodes(program: Program, target: int) -> Program:
    if target == 0 or target <= len(program.nodes):
        return program
    if target > program.limits.max_nodes:
        raise AssertionError("target exceeds declared node limit")
    extra = tuple(
        Node("fill", count=1, value=(index * 17 + 3) & 255, declared_length=1)
        for index in range(target - len(program.nodes))
    )
    return Program(program.nodes + extra, program.roots, program.limits)


def _request_cycle(n: int):
    return (
        (0, 64),
        (LEAF_BYTES, 1024),
        (n // 2 - 512, 1024),
        (n - 257, 257),
    )


def _requests(n: int, count: int):
    cycle = _request_cycle(n)
    return tuple(cycle[index % len(cycle)] for index in range(count))


def _clock_cpu(fn):
    c0 = time.process_time_ns()
    value = fn()
    return value, time.process_time_ns() - c0


def _paired(base_fn, cand_fn):
    base_fn()
    cand_fn()
    base_cpu = []
    cand_cpu = []
    base_value = cand_value = None
    was_enabled = gc.isenabled()
    try:
        if was_enabled:
            gc.disable()
        for index in range(ROUNDS):
            order = ("base", "cand") if index % 2 == 0 else ("cand", "base")
            for arm in order:
                if arm == "base":
                    base_value, elapsed = _clock_cpu(base_fn)
                    base_cpu.append(elapsed)
                else:
                    cand_value, elapsed = _clock_cpu(cand_fn)
                    cand_cpu.append(elapsed)
    finally:
        if was_enabled:
            gc.enable()
    return (
        base_value,
        int(statistics.median(base_cpu)),
        cand_value,
        int(statistics.median(cand_cpu)),
    )


def _median_open_cpu(program: Program) -> int:
    samples = []
    for _ in range(ROUNDS):
        _, elapsed = _clock_cpu(lambda: validate_program_snapshot_compact(program))
        samples.append(elapsed)
    return int(statistics.median(samples))


def _run_raw(program, tree, requests):
    values = []
    movement = []
    cones = []
    for start, length in requests:
        value, stats = reconstruct_authenticated_native_range(
            program, "current", tree, tree.root, start, length
        )
        values.append(value)
        movement.append(stats.modeled_data_movement_bytes)
        cones.append(stats.cone_bytes)
    return tuple(values), tuple(movement), tuple(cones)


def _run_validated(program, tree, requests):
    validated = validate_program_snapshot_compact(program)
    values = []
    movement = []
    cones = []
    for start, length in requests:
        value, stats = reconstruct_validated_authenticated_native_range(
            validated, "current", tree, tree.root, start, length
        )
        values.append(value)
        movement.append(stats.modeled_data_movement_bytes)
        cones.append(stats.cone_bytes)
    return (
        tuple(values),
        tuple(movement),
        tuple(cones),
        validated.uses_compact_lengths,
        validated.python_preflight_bytes,
    )


def run():
    rows = []
    exact_ok = True
    movement_ok = True
    ge4 = []
    ge16 = []
    one_shot = []
    large_ge4 = []
    retained_ratios_4096 = []

    for family in FAMILIES:
        base_program = _case(ROOT_BYTES, family)
        full_outputs, _ = evaluate(base_program)
        full = full_outputs["current"]
        tree = build_auth_tree(full, LEAF_BYTES)

        for target in TOTAL_NODE_TARGETS:
            program = _with_total_nodes(base_program, target)
            ordinary = validate_program_snapshot(program)
            compact = validate_program_snapshot_compact(program)
            retained_ratio = compact.python_preflight_bytes / max(
                ordinary.python_preflight_bytes, 1
            )
            if len(program.nodes) == 4096:
                retained_ratios_4096.append(retained_ratio)

            open_cpu = _median_open_cpu(program)

            for request_count in REQUEST_COUNTS:
                requests = _requests(ROOT_BYTES, request_count)
                raw_fn = lambda p=program, t=tree, r=requests: _run_raw(p, t, r)
                cand_fn = lambda p=program, t=tree, r=requests: _run_validated(p, t, r)
                raw, raw_cpu, candidate, cand_cpu = _paired(raw_fn, cand_fn)

                raw_values, raw_movement, raw_cones = raw
                cand_values, cand_movement, cand_cones, uses_compact, retained_bytes = candidate
                expected = tuple(full[s : s + l] for s, l in requests)
                semantic = raw_values == cand_values == expected
                same_movement = raw_movement == cand_movement and raw_cones == cand_cones
                exact_ok &= semantic
                movement_ok &= same_movement

                ratio = cand_cpu / max(raw_cpu, 1)
                if request_count >= 4:
                    ge4.append(ratio)
                if request_count >= 16:
                    ge16.append(ratio)
                if request_count == 1:
                    one_shot.append(ratio)
                if len(program.nodes) == 4096 and request_count >= 4:
                    large_ge4.append(ratio)

                rows.append(
                    {
                        "family": family,
                        "kind": "law" if family in LAW_FAMILIES else "control",
                        "root_bytes": ROOT_BYTES,
                        "program_nodes": len(program.nodes),
                        "request_count": request_count,
                        "semantic_ok": semantic,
                        "movement_identical": same_movement,
                        "raw_lifecycle_cpu_ns": raw_cpu,
                        "validated_lifecycle_cpu_ns": cand_cpu,
                        "validated_over_raw_cpu": ratio,
                        "standalone_compact_open_cpu_ns": open_cpu,
                        "ordinary_preflight_python_bytes": ordinary.python_preflight_bytes,
                        "candidate_preflight_python_bytes": retained_bytes,
                        "candidate_retained_over_ordinary": retained_ratio,
                        "candidate_uses_compact_lengths": uses_compact,
                        "auth_index_bytes": tree.stored_index_bytes,
                        "per_request_modeled_movement_bytes": list(cand_movement),
                        "per_request_cone_bytes": list(cand_cones),
                    }
                )

    median_ge4 = statistics.median(ge4)
    median_ge16 = statistics.median(ge16)
    worst_one_shot = max(one_shot)
    worst_large_ge4 = max(large_ge4)
    worst_retained_4096 = max(retained_ratios_4096)

    gates = {
        "semantic_ok": exact_ok,
        "movement_identical": movement_ok,
        "retained_4096_ok": worst_retained_4096 <= MAX_RETAINED_RATIO_AT_4096,
        "median_cpu_ge4_ok": median_ge4 <= MAX_MEDIAN_CPU_RATIO_GE4,
        "median_cpu_ge16_ok": median_ge16 <= MAX_MEDIAN_CPU_RATIO_GE16,
        "worst_oneshot_ok": worst_one_shot <= MAX_WORST_ONESHOT_CPU_RATIO,
        "every_4096_ge4_faster": worst_large_ge4 < 1.0,
    }
    semantic_failure = not exact_ok or not movement_ok
    advance = all(gates.values())
    decision = (
        "ADVANCE_VALIDATED_AUTHENTICATED_LIFECYCLE"
        if advance
        else (
            "INVALIDATE_VALIDATED_AUTHENTICATED_LIFECYCLE"
            if semantic_failure
            else "HOLD_VALIDATED_AUTHENTICATED_LIFECYCLE"
        )
    )
    return {
        "schema": "cmpct-one-g02-validated-authenticated-selective-lifecycle-v1",
        "experimental_version": "ONE-G0.2",
        "source_sha": os.environ.get("EVIDENCE_HEAD")
        or os.environ.get("GITHUB_SHA")
        or "local-unbound",
        "root_bytes": ROOT_BYTES,
        "leaf_bytes": LEAF_BYTES,
        "rounds": ROUNDS,
        "frozen_gate": {
            "max_retained_ratio_at_4096": MAX_RETAINED_RATIO_AT_4096,
            "max_median_cpu_ratio_ge4": MAX_MEDIAN_CPU_RATIO_GE4,
            "max_median_cpu_ratio_ge16": MAX_MEDIAN_CPU_RATIO_GE16,
            "max_worst_oneshot_cpu_ratio": MAX_WORST_ONESHOT_CPU_RATIO,
        },
        "summary": {
            "median_validated_over_raw_cpu_ge4": median_ge4,
            "median_validated_over_raw_cpu_ge16": median_ge16,
            "worst_oneshot_validated_over_raw_cpu": worst_one_shot,
            "worst_4096_ge4_validated_over_raw_cpu": worst_large_ge4,
            "worst_4096_retained_over_ordinary": worst_retained_4096,
            "gates": gates,
            "advance": advance,
            "decision": decision,
        },
        "rows": rows,
    }


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, sort_keys=True))
    if result["summary"]["decision"].startswith("INVALIDATE"):
        raise SystemExit(2)
    if not result["summary"]["advance"]:
        raise SystemExit(1)
