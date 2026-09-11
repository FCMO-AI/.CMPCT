"""Frozen ONE-G0.2 generic execution-plan falsifier.

Decision question: can compile-once/replay remove generic graph-control overhead across
multiple existing ONE Law shapes without terminal/run-specific dispatch?
"""
from __future__ import annotations

import json
import statistics
import time
from hashlib import sha256

from experiments.one.generic_execution_plan import compile_execution_plan, execute_plan
from experiments.one.ir import Limits, Node, Program, Ref, Root
from experiments.one.vm import evaluate

REPETITIONS = 9
REPLAY_MAX = 1.05
MATERIAL_WIN_MAX = 0.95
MIN_MATERIAL_WINS = 8
SIZES = (64 * 1024, 256 * 1024, 1024 * 1024)
FAMILIES = ("terminal_mix", "repeat", "slice_concat", "xor2", "add8_3", "shared_basis")


def _program(family: str, size: int) -> Program:
    limits = Limits(max_nodes=4096, max_output_bytes=4 * 1024 * 1024, max_work_bytes=64 * 1024 * 1024, max_depth=64)
    seed = bytes((i * 29 + 17) & 0xFF for i in range(max(1, size)))

    if family == "terminal_mix":
        quarter = size // 4
        surprise = seed[:quarter]
        output = surprise + bytes([0xA5]) * (size - quarter)
        nodes = (Node("surprise", surprise=surprise), Node("fill", count=size - quarter, value=0xA5), Node("concat", refs=(Ref(0), Ref(1)), declared_length=size))
    elif family == "repeat":
        basis_len = max(64, size // 256)
        basis = seed[:basis_len]
        count = size // basis_len
        output = basis * count
        nodes = (Node("surprise", surprise=basis), Node("repeat", refs=(Ref(0),), count=count, declared_length=len(output)))
    elif family == "slice_concat":
        half = size // 2
        a = seed[:half]
        b = bytes((value ^ 0x5A) for value in seed[:half])
        output = a[half // 4 :] + b[: half // 2] + a[: half // 4]
        nodes = (Node("surprise", surprise=a), Node("surprise", surprise=b), Node("concat", refs=(Ref(0, half // 4, half - half // 4), Ref(1, 0, half // 2), Ref(0, 0, half // 4)), declared_length=len(output)))
    elif family == "xor2":
        a = seed[:size]
        b = bytes((i * 7 + 3) & 0xFF for i in range(size))
        output = bytes(x ^ y for x, y in zip(a, b))
        nodes = (Node("surprise", surprise=a), Node("surprise", surprise=b), Node("xor", refs=(Ref(0), Ref(1)), declared_length=size))
    elif family == "add8_3":
        a = seed[:size]
        b = bytes((i * 5 + 11) & 0xFF for i in range(size))
        c = bytes((i * 13 + 19) & 0xFF for i in range(size))
        output = bytes((x + y + z) & 0xFF for x, y, z in zip(a, b, c))
        nodes = (Node("surprise", surprise=a), Node("surprise", surprise=b), Node("surprise", surprise=c), Node("add8", refs=(Ref(0), Ref(1), Ref(2)), declared_length=size))
    elif family == "shared_basis":
        # Non-degenerate mixed Law: 3/4 reconstructed from one basis and 1/4 Fill.
        basis_len = size // 4
        basis = seed[:basis_len]
        repeated = basis * 3
        patch = bytes([0x33]) * (size - len(repeated))
        output = repeated + patch
        nodes = (Node("surprise", surprise=basis), Node("repeat", refs=(Ref(0),), count=3, declared_length=len(repeated)), Node("fill", count=len(patch), value=0x33), Node("concat", refs=(Ref(1), Ref(2)), declared_length=len(output)))
    else:
        raise AssertionError(family)

    return Program(nodes, {"root": Root(Ref(len(nodes) - 1), len(output), sha256(output).hexdigest())}, limits)


def _median(values):
    return statistics.median(values)


def decide(rows, semantic_ok: bool) -> str:
    expected = {(size, family) for size in SIZES for family in FAMILIES}
    observed = {(row["size"], row["family"]) for row in rows}
    exact = observed == expected and len(rows) == len(expected)
    if not semantic_ok or not exact:
        return "INVALIDATE_GENERIC_EXECUTION_PLAN"
    decisive = [row for row in rows if row["size"] == 1024 * 1024]
    all_bounded = all(row["wall_ratio"] <= REPLAY_MAX and row["cpu_ratio"] <= REPLAY_MAX for row in decisive)
    wins = sum(row["wall_ratio"] <= MATERIAL_WIN_MAX and row["cpu_ratio"] <= MATERIAL_WIN_MAX for row in rows)
    if all_bounded and wins >= MIN_MATERIAL_WINS:
        return "ADVANCE_GENERIC_EXECUTION_PLAN"
    return "HOLD_GENERIC_EXECUTION_PLAN"


def run():
    rows = []
    semantic_ok = True
    for size in SIZES:
        for family in FAMILIES:
            program = _program(family, size)
            reference, reference_stats = evaluate(program)
            t0 = time.perf_counter_ns()
            c0 = time.process_time_ns()
            plan = compile_execution_plan(program)
            compile_wall = time.perf_counter_ns() - t0
            compile_cpu = time.process_time_ns() - c0
            candidate, candidate_stats = execute_plan(plan)
            semantic_ok &= candidate == reference and candidate_stats.work_bytes == reference_stats.work_bytes

            ref_wall = []
            ref_cpu = []
            plan_wall = []
            plan_cpu = []
            for rep in range(REPETITIONS):
                order = ("plan", "ref") if rep & 1 else ("ref", "plan")
                for arm in order:
                    w0 = time.perf_counter_ns()
                    c0 = time.process_time_ns()
                    if arm == "ref":
                        out, _ = evaluate(program)
                    else:
                        out, _ = execute_plan(plan)
                    wall = time.perf_counter_ns() - w0
                    cpu = time.process_time_ns() - c0
                    if out != reference:
                        semantic_ok = False
                    (ref_wall if arm == "ref" else plan_wall).append(wall)
                    (ref_cpu if arm == "ref" else plan_cpu).append(cpu)

            rw = _median(ref_wall)
            rc = _median(ref_cpu)
            pw = _median(plan_wall)
            pc = _median(plan_cpu)
            rows.append({
                "size": size,
                "family": family,
                "reference_wall_ns": rw,
                "reference_cpu_ns": rc,
                "plan_wall_ns": pw,
                "plan_cpu_ns": pc,
                "wall_ratio": pw / rw,
                "cpu_ratio": pc / rc,
                "compile_wall_ns": compile_wall,
                "compile_cpu_ns": compile_cpu,
                "compile_break_even_replays_wall": (compile_wall / max(1, rw - pw)) if pw < rw else None,
                "compile_break_even_replays_cpu": (compile_cpu / max(1, rc - pc)) if pc < rc else None,
            })

    expected = {(size, family) for size in SIZES for family in FAMILIES}
    exact = {(row["size"], row["family"]) for row in rows} == expected and len(rows) == len(expected)
    wins = sum(row["wall_ratio"] <= MATERIAL_WIN_MAX and row["cpu_ratio"] <= MATERIAL_WIN_MAX for row in rows)
    decision = decide(rows, semantic_ok)
    payload = {"decision": decision, "semantic_ok": semantic_ok, "exact_matrix": exact, "repetitions": REPETITIONS, "replay_max": REPLAY_MAX, "material_win_max": MATERIAL_WIN_MAX, "min_material_wins": MIN_MATERIAL_WINS, "material_wins": wins, "rows": rows}
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if decision == "ADVANCE_GENERIC_EXECUTION_PLAN" else 1


if __name__ == "__main__":
    raise SystemExit(run())
