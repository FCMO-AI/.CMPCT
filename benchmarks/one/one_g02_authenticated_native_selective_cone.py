"""ONE-G0.2 authenticated native selective-cone end-to-end falsifier.

Frozen by ONE_G02_AUTHENTICATED_NATIVE_SELECTIVE_CONE_PREREG_2026-09-09.md.
The complete open operation is charged: cone planning/source packing, native execution,
auth leaf preparation, sibling extraction, verification/root rebuild, and output.
Persistent AuthTree creation is outside open timing but its stored bytes are reported.
"""
from __future__ import annotations

import gc
import json
import os
import statistics
import time

from benchmarks.one.one_g02_native_law_terminal_reader import (
    CONTROLS,
    LAW_FAMILIES,
    _case,
)
from experiments.one.auth_tree import build_auth_tree
from experiments.one.authenticated_native_selective_cone import (
    reconstruct_authenticated_native_range,
)
from experiments.one.ir import Node, OneError, Program, Ref, Root
from experiments.one.selective_auth import reconstruct_authenticated_range
from experiments.one.vm import evaluate

SIZES = (32 * 1024, 128 * 1024, 512 * 1024)
FAMILIES = LAW_FAMILIES + CONTROLS
LEAF_BYTES = 4096
ROUNDS = 7

MAX_POSITIVE_CPU_RATIO = 1.10
MAX_MEDIAN_MOVEMENT_RATIO = 0.75


def _requests(n: int):
    return (
        ("begin_tiny", 0, 64),
        ("leaf_boundary", LEAF_BYTES, min(1024, n - LEAF_BYTES)),
        ("middle_cross", max(0, n // 2 - 512), min(1024, n)),
        ("end_tiny", n - 257, 257),
    )


def _clock(fn):
    w0 = time.perf_counter_ns()
    c0 = time.process_time_ns()
    value = fn()
    return value, time.perf_counter_ns() - w0, time.process_time_ns() - c0


def _paired(base_fn, cand_fn):
    base_fn()
    cand_fn()
    bw = []
    bc = []
    cw = []
    cc = []
    base = cand = None
    was_enabled = gc.isenabled()
    try:
        if was_enabled:
            gc.disable()
        for i in range(ROUNDS):
            order = ("base", "cand") if i % 2 == 0 else ("cand", "base")
            for arm in order:
                if arm == "base":
                    value, wall, cpu = _clock(base_fn)
                    base = value
                    bw.append(wall)
                    bc.append(cpu)
                else:
                    value, wall, cpu = _clock(cand_fn)
                    cand = value
                    cw.append(wall)
                    cc.append(cpu)
    finally:
        if was_enabled:
            gc.enable()
    return (
        base,
        int(statistics.median(bw)),
        int(statistics.median(bc)),
        cand,
        int(statistics.median(cw)),
        int(statistics.median(cc)),
    )


def _hostile_controls():
    data = bytes((i * 17 + 3) & 255 for i in range(32 * 1024))
    program = _case(len(data), "xor")
    outputs, _ = evaluate(program)
    current = outputs["current"]
    tree = build_auth_tree(current, LEAF_BYTES)
    failures = []

    bad_root = bytes([tree.root[0] ^ 1]) + tree.root[1:]
    try:
        reconstruct_authenticated_native_range(
            program, "current", tree, bad_root, 4096, 64
        )
        failures.append("wrong_expected_root_accepted")
    except ValueError:
        pass

    nodes = list(program.nodes)
    src = bytearray(nodes[0].surprise)
    src[5000] ^= 1
    nodes[0] = Node(
        "surprise",
        surprise=bytes(src),
        declared_length=nodes[0].declared_length,
    )
    mutated = Program(tuple(nodes), program.roots, program.limits)
    try:
        reconstruct_authenticated_native_range(
            mutated, "current", tree, tree.root, 4992, 64
        )
        failures.append("mutated_payload_accepted")
    except ValueError:
        pass

    repeat_program = Program(
        nodes=(
            Node("surprise", surprise=b"abcd", declared_length=4),
            Node("repeat", refs=(Ref(0),), count=8192, declared_length=32768),
        ),
        roots={"root": Root(Ref(1), 32768, "0" * 64)},
    )
    repeat_tree = build_auth_tree(b"abcd" * 8192, LEAF_BYTES)
    try:
        reconstruct_authenticated_native_range(
            repeat_program, "root", repeat_tree, repeat_tree.root, 0, 64
        )
        failures.append("unsupported_repeat_silently_accepted")
    except OneError:
        pass

    return {"failures": failures, "passed": not failures}


def run():
    rows = []
    positive_cpu_ratios = []
    positive_movement_ratios = []
    exact_ok = True

    for n in SIZES:
        for family in FAMILIES:
            program = _case(n, family)
            outputs, _ = evaluate(program)
            full = outputs["current"]
            tree = build_auth_tree(full, LEAF_BYTES)

            for request_name, start, length in _requests(n):
                base_fn = lambda p=program, t=tree, s=start, l=length: (
                    reconstruct_authenticated_range(p, "current", t, t.root, s, l)
                )
                cand_fn = lambda p=program, t=tree, s=start, l=length: (
                    reconstruct_authenticated_native_range(p, "current", t, t.root, s, l)
                )
                base, bw, bc, cand, cw, cc = _paired(base_fn, cand_fn)
                base_value, base_stats = base
                cand_value, cand_stats = cand
                expected = full[start:start+length]
                exact = base_value == cand_value == expected
                if not exact:
                    raise AssertionError("authenticated selective output mismatch")
                exact_ok &= exact

                cpu_ratio = cc / max(bc, 1)
                wall_ratio = cw / max(bw, 1)
                base_movement = (
                    base_stats.range_work_bytes
                    + base_stats.proof_payload_bytes
                    + base_stats.proof_hash_bytes
                )
                cand_movement = cand_stats.modeled_data_movement_bytes
                movement_ratio = cand_movement / max(base_movement, 1)
                is_positive = family in LAW_FAMILIES
                if is_positive:
                    positive_cpu_ratios.append(cpu_ratio)
                    positive_movement_ratios.append(movement_ratio)

                rows.append(
                    {
                        "root_bytes": n,
                        "family": family,
                        "kind": "law" if is_positive else "control",
                        "request": request_name,
                        "start": start,
                        "length": length,
                        "semantic_ok": exact,
                        "leaf_bytes": LEAF_BYTES,
                        "cone_start": cand_stats.cone_start,
                        "cone_bytes": cand_stats.cone_bytes,
                        "full_root_bytes_avoided": n - cand_stats.cone_bytes,
                        "incumbent_wall_ns": bw,
                        "incumbent_cpu_ns": bc,
                        "candidate_wall_ns": cw,
                        "candidate_cpu_ns": cc,
                        "candidate_over_incumbent_wall": wall_ratio,
                        "candidate_over_incumbent_cpu": cpu_ratio,
                        "incumbent_modeled_data_movement_bytes": base_movement,
                        "candidate_modeled_data_movement_bytes": cand_movement,
                        "candidate_over_incumbent_data_movement": movement_ratio,
                        "candidate_packed_source_bytes": cand_stats.packed_source_bytes,
                        "candidate_source_read_bytes": cand_stats.source_read_bytes,
                        "candidate_sink_write_bytes": cand_stats.sink_write_bytes,
                        "authenticated_leaf_payload_bytes": cand_stats.proof_payload_bytes,
                        "sibling_hash_bytes": cand_stats.proof_hash_bytes,
                        "sibling_hash_count": cand_stats.proof_hash_bytes // 32,
                        "stored_auth_index_bytes": cand_stats.auth_index_bytes,
                        "candidate_peak_temporary_bytes": cand_stats.peak_temporary_bytes,
                        "plan_commands": cand_stats.plan_commands,
                        "stage_prepare_cpu_ns": cand_stats.prepare_cpu_ns,
                        "stage_execute_cpu_ns": cand_stats.execute_cpu_ns,
                        "stage_proof_prepare_cpu_ns": cand_stats.proof_prepare_cpu_ns,
                        "stage_verify_cpu_ns": cand_stats.verify_cpu_ns,
                        "fallback": cand_stats.fallback,
                        "fallback_reason": cand_stats.fallback_reason,
                    }
                )

    hostile = _hostile_controls()
    median_cpu = statistics.median(positive_cpu_ratios)
    worst_cpu = max(positive_cpu_ratios)
    median_movement = statistics.median(positive_movement_ratios)

    fixed = [r for r in rows if r["kind"] == "law" and r["request"] == "begin_tiny"]
    locality_groups = {}
    for family in LAW_FAMILIES:
        group = [r for r in fixed if r["family"] == family]
        locality_groups[family] = {
            "cone_bytes": sorted(set(r["cone_bytes"] for r in group)),
            "source_read_bytes": sorted(set(r["candidate_source_read_bytes"] for r in group)),
            "auth_payload_bytes": sorted(set(r["authenticated_leaf_payload_bytes"] for r in group)),
            "sibling_hash_counts": [r["sibling_hash_count"] for r in group],
        }
    fixed_cone_ok = all(
        len(v["cone_bytes"]) == 1
        and len(v["source_read_bytes"]) == 1
        and len(v["auth_payload_bytes"]) == 1
        for v in locality_groups.values()
    )

    gates = {
        "semantic_ok": exact_ok,
        "hostile_rejection_ok": hostile["passed"],
        "no_whole_root_positive": all(
            r["cone_bytes"] < r["root_bytes"]
            for r in rows
            if r["kind"] == "law"
        ),
        "fixed_cone_non_scaling_ok": fixed_cone_ok,
        "median_positive_cpu_below_incumbent": median_cpu < 1.0,
        "worst_positive_cpu_ok": worst_cpu <= MAX_POSITIVE_CPU_RATIO,
        "median_positive_movement_ok": median_movement <= MAX_MEDIAN_MOVEMENT_RATIO,
        "temporary_state_cone_bounded": all(
            r["candidate_peak_temporary_bytes"]
            <= 3 * r["cone_bytes"] + r["sibling_hash_bytes"]
            for r in rows
            if r["kind"] == "law"
        ),
        "no_hidden_fallback": all(not r["fallback"] for r in rows),
    }
    advance = all(gates.values())
    return {
        "schema": "cmpct-one-g02-authenticated-native-selective-cone-v1",
        "experimental_version": "ONE-G0.2",
        "source_sha": os.environ.get("EVIDENCE_HEAD")
        or os.environ.get("GITHUB_SHA")
        or "local-unbound",
        "leaf_bytes": LEAF_BYTES,
        "rounds": ROUNDS,
        "frozen_gate": {
            "max_positive_cpu_ratio": MAX_POSITIVE_CPU_RATIO,
            "max_median_movement_ratio": MAX_MEDIAN_MOVEMENT_RATIO,
        },
        "summary": {
            "median_positive_candidate_over_incumbent_cpu": median_cpu,
            "worst_positive_candidate_over_incumbent_cpu": worst_cpu,
            "median_positive_candidate_over_incumbent_data_movement": median_movement,
            "hostile": hostile,
            "fixed_cone": locality_groups,
            "gates": gates,
            "advance": advance,
            "decision": (
                "ADVANCE_AUTHENTICATED_NATIVE_SELECTIVE_CONE"
                if advance
                else (
                    "INVALIDATE_AUTHENTICATED_NATIVE_SELECTIVE_CONE"
                    if not exact_ok or not hostile["passed"]
                    else "HOLD_AUTHENTICATED_NATIVE_SELECTIVE_CONE"
                )
            ),
        },
        "rows": rows,
    }


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, sort_keys=True))
    if not result["summary"]["advance"]:
        raise SystemExit(1)
