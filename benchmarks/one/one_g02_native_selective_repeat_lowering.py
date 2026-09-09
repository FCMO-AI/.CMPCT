"""ONE-G0.2 native authenticated selective Repeat lowering falsifier."""
from __future__ import annotations

from hashlib import sha256
import gc
import json
import math
import os
import statistics
import time

from experiments.one.auth_tree import build_auth_tree
from experiments.one.authenticated_native_selective_cone import (
    reconstruct_validated_authenticated_native_range,
)
from experiments.one.ir import Limits, Node, Program, Ref, Root
from experiments.one.selective_auth import reconstruct_validated_authenticated_range
from experiments.one.validated_program import validate_program_snapshot_compact

BASES = (32, 64, 256, 4096)
ROOTS = (32 * 1024, 128 * 1024, 512 * 1024)
LEAF_BYTES = 4096
ROUNDS = 5
MAX_MEDIAN_CPU_RATIO = 0.75
MAX_WORST_CPU_RATIO = 1.10
MAX_MEDIAN_MOVEMENT_RATIO = 1.00


def _program(basis_bytes: int, root_bytes: int):
    basis = bytes((index * 73 + 19) & 255 for index in range(basis_bytes))
    assert root_bytes % basis_bytes == 0
    full = basis * (root_bytes // basis_bytes)
    nodes = (
        Node("surprise", surprise=basis, declared_length=basis_bytes),
        Node("repeat", refs=(Ref(0),), count=root_bytes // basis_bytes, declared_length=root_bytes),
    )
    root = Root(Ref(1), root_bytes, sha256(full).hexdigest())
    limits = Limits(max_output_bytes=root_bytes * 2, max_work_bytes=root_bytes * 8)
    return Program(nodes, {"current": root}, limits), full


def _requests(root_bytes: int, basis_bytes: int):
    return (
        ("first64", 0, 64),
        ("first4k", 0, 4096),
        ("period_cross4k", basis_bytes - 1, 4096),
        ("middle8k", root_bytes // 2 - 4096, 8192),
        ("final257", root_bytes - 257, 257),
    )


def _cpu(fn):
    c0 = time.process_time_ns()
    value = fn()
    return value, time.process_time_ns() - c0


def _paired(base_fn, cand_fn):
    base_fn()
    cand_fn()
    base_times = []
    cand_times = []
    base_value = cand_value = None
    enabled = gc.isenabled()
    try:
        if enabled:
            gc.disable()
        for i in range(ROUNDS):
            order = ("base", "cand") if i % 2 == 0 else ("cand", "base")
            for arm in order:
                if arm == "base":
                    base_value, elapsed = _cpu(base_fn)
                    base_times.append(elapsed)
                else:
                    cand_value, elapsed = _cpu(cand_fn)
                    cand_times.append(elapsed)
    finally:
        if enabled:
            gc.enable()
    return base_value, int(statistics.median(base_times)), cand_value, int(statistics.median(cand_times))


def run():
    rows = []
    cpu_ratios = []
    movement_ratios = []
    exact = True
    geometry = True
    temp_ok = True
    command_ok = True
    fixed_probe = {}

    for basis_bytes in BASES:
        for root_bytes in ROOTS:
            program, full = _program(basis_bytes, root_bytes)
            validated = validate_program_snapshot_compact(program)
            tree = build_auth_tree(full, LEAF_BYTES)
            for label, start, length in _requests(root_bytes, basis_bytes):
                base_fn = lambda s=start, l=length: reconstruct_validated_authenticated_range(
                    validated, "current", tree, tree.root, s, l
                )
                cand_fn = lambda s=start, l=length: reconstruct_validated_authenticated_native_range(
                    validated, "current", tree, tree.root, s, l
                )
                base, base_cpu, cand, cand_cpu = _paired(base_fn, cand_fn)
                base_value, base_stats = base
                cand_value, cand_stats = cand
                expected = full[start : start + length]
                semantic = base_value == cand_value == expected
                same_cone = base_stats.cone_bytes == cand_stats.cone_bytes
                exact &= semantic
                geometry &= same_cone

                cpu_ratio = cand_cpu / max(base_cpu, 1)
                base_movement = (
                    base_stats.range_work_bytes
                    + base_stats.proof_payload_bytes
                    + base_stats.proof_hash_bytes
                )
                movement_ratio = cand_stats.modeled_data_movement_bytes / max(base_movement, 1)
                cpu_ratios.append(cpu_ratio)
                movement_ratios.append(movement_ratio)

                temp_limit = 3 * cand_stats.cone_bytes + cand_stats.proof_hash_bytes
                this_temp_ok = cand_stats.peak_temporary_bytes <= temp_limit
                temp_ok &= this_temp_ok
                command_bound = math.ceil(cand_stats.cone_bytes / basis_bytes) + 2
                this_command_ok = cand_stats.plan_commands <= command_bound
                command_ok &= this_command_ok

                if label == "first4k":
                    fixed_probe.setdefault(basis_bytes, []).append(
                        (
                            root_bytes,
                            cand_stats.cone_bytes,
                            cand_stats.packed_source_bytes,
                            cand_stats.source_read_bytes,
                            cand_stats.source_plan_write_bytes,
                            cand_stats.sink_write_bytes,
                        )
                    )

                rows.append(
                    {
                        "basis_bytes": basis_bytes,
                        "root_bytes": root_bytes,
                        "request": label,
                        "start": start,
                        "length": length,
                        "semantic_ok": semantic,
                        "same_cone_geometry": same_cone,
                        "comparator_cpu_ns": base_cpu,
                        "candidate_cpu_ns": cand_cpu,
                        "candidate_over_comparator_cpu": cpu_ratio,
                        "comparator_range_work_plus_proof_bytes": base_movement,
                        "candidate_modeled_movement_bytes": cand_stats.modeled_data_movement_bytes,
                        "candidate_over_comparator_movement": movement_ratio,
                        "cone_bytes": cand_stats.cone_bytes,
                        "packed_source_bytes": cand_stats.packed_source_bytes,
                        "source_read_bytes": cand_stats.source_read_bytes,
                        "source_plan_write_bytes": cand_stats.source_plan_write_bytes,
                        "sink_write_bytes": cand_stats.sink_write_bytes,
                        "proof_hash_bytes": cand_stats.proof_hash_bytes,
                        "peak_temporary_bytes": cand_stats.peak_temporary_bytes,
                        "temporary_bound_bytes": temp_limit,
                        "plan_commands": cand_stats.plan_commands,
                        "command_bound": command_bound,
                        "temporary_ok": this_temp_ok,
                        "command_bound_ok": this_command_ok,
                    }
                )

    fixed_scale_ok = True
    for observations in fixed_probe.values():
        signatures = [obs[1:] for obs in observations]
        fixed_scale_ok &= signatures[0] == signatures[1] == signatures[2]

    median_cpu = statistics.median(cpu_ratios)
    worst_cpu = max(cpu_ratios)
    median_movement = statistics.median(movement_ratios)
    gates = {
        "semantic_exact": exact,
        "cone_geometry_exact": geometry,
        "fixed_cone_root_scaling_ok": fixed_scale_ok,
        "temporary_bound_ok": temp_ok,
        "command_bound_ok": command_ok,
        "median_cpu_ok": median_cpu <= MAX_MEDIAN_CPU_RATIO,
        "worst_cpu_ok": worst_cpu <= MAX_WORST_CPU_RATIO,
        "median_movement_ok": median_movement <= MAX_MEDIAN_MOVEMENT_RATIO,
    }
    invalid = not (exact and geometry and fixed_scale_ok and temp_ok and command_ok)
    advance = all(gates.values())
    decision = (
        "INVALIDATE_NATIVE_SELECTIVE_REPEAT_LOWERING"
        if invalid
        else (
            "ADVANCE_NATIVE_SELECTIVE_REPEAT_LOWERING"
            if advance
            else "HOLD_NATIVE_SELECTIVE_REPEAT_LOWERING"
        )
    )
    return {
        "schema": "cmpct-one-g02-native-selective-repeat-lowering-v1",
        "experimental_version": "ONE-G0.2",
        "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
        "rounds": ROUNDS,
        "frozen_gate": {
            "max_median_cpu_ratio": MAX_MEDIAN_CPU_RATIO,
            "max_worst_cpu_ratio": MAX_WORST_CPU_RATIO,
            "max_median_movement_ratio": MAX_MEDIAN_MOVEMENT_RATIO,
        },
        "summary": {
            "median_candidate_over_comparator_cpu": median_cpu,
            "worst_candidate_over_comparator_cpu": worst_cpu,
            "median_candidate_over_comparator_movement": median_movement,
            "gates": gates,
            "advance": advance,
            "decision": decision,
        },
        "fixed_probe": {str(k): v for k, v in fixed_probe.items()},
        "rows": rows,
    }


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, sort_keys=True))
    decision = result["summary"]["decision"]
    if decision.startswith("INVALIDATE"):
        raise SystemExit(2)
    if not result["summary"]["advance"]:
        raise SystemExit(1)
