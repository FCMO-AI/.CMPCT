"""ONE-G0.2 lazy segment-arena creation-timing falsifier.

Frozen by ONE_G02_LAZY_SEGMENT_TIMING_PREREG_2026-09-08.md.
This narrow gate charges the real Segment arena allocation in both arms while
holding source/target ctypes setup and native compilation outside the interval.
"""
from __future__ import annotations

import ctypes
import gc
from hashlib import sha256
import json
import os
import statistics
import time

from benchmarks.one.one_g02_end_to_end_direct_emitter_writer import (
    Segment,
    SegmentStats,
    _admit,
    _build_native,
    _native_plan,
)
from benchmarks.one.one_g02_post_segment_control_cost_owner import _literal_program
from benchmarks.one.one_g02_shift_branch_bound_relation_transfer import _relation_cases
from experiments.one.bounded_surprise_pool import program_from_plan_pooled
from experiments.one.growable_wire import _encode_program_growable_prevalidated
from experiments.one.ir import Ref, Root
from experiments.one.vm import evaluate
from experiments.one.wire import decode_program

SIZE = 1 << 20
REPETITIONS = 21
ADMITTED = ("shift_plus1", "shift_plus1_damage_quarter", "fragmented_every96")
REJECTED = ("fragmented_every32", "independent_random")
CASES = ADMITTED + REJECTED
ADMITTED_RATIO_MAX = 1.05
REJECTED_RATIO_MAX = 0.95


def _writer_once(
    arm: str,
    admission_fn,
    segment_fn,
    source: bytes,
    target: bytes,
    src_arr,
    dst_arr,
    previous_root: Root,
    current_digest: str,
):
    n = len(source)
    seg_buf = None
    if arm == "eager":
        seg_buf = (Segment * n)()

    result, gate_reads, gate_used, enabled = _admit(admission_fn, src_arr, dst_arr, n)
    if enabled and seg_buf is None:
        seg_buf = (Segment * n)()

    segment_stats = SegmentStats()
    if enabled:
        if seg_buf is None:
            raise AssertionError("admitted relation missing segment arena")
        plan = _native_plan(segment_fn, src_arr, dst_arr, n, seg_buf, segment_stats)
        program, pool_stats = program_from_plan_pooled(
            source, target, plan, previous_root, current_digest
        )
        hierarchy_depth = pool_stats.hierarchy_depth
    else:
        plan = ()
        program, hierarchy_depth = _literal_program(
            source, target, previous_root, current_digest
        )

    program.validate_shape()
    wire, wire_stats = _encode_program_growable_prevalidated(program)
    return {
        "wire": wire,
        "wire_stats": wire_stats,
        "program": program,
        "result": result,
        "gate_reads": gate_reads,
        "gate_used": gate_used,
        "enabled": enabled,
        "plan": plan,
        "segment_capacity_bytes": n * ctypes.sizeof(Segment) if seg_buf is not None else 0,
        "segments": int(segment_stats.segments),
        "hierarchy_depth": hierarchy_depth,
    }


def _semantic_signature(value, source: bytes, target: bytes):
    outputs, vm_stats = evaluate(decode_program(value["wire"]))
    program = value["program"]
    if outputs != {"previous": source, "current": target}:
        raise AssertionError("writer failed exact two-root reconstruction")
    return {
        "enabled": bool(value["enabled"]),
        "best_shift": int(value["result"].best_shift),
        "exact_proofs": int(value["result"].exact_proofs),
        "gate_reads": int(value["gate_reads"]),
        "gate_used": bool(value["gate_used"]),
        "plan": value["plan"],
        "wire": value["wire"],
        "wire_total_bytes": int(value["wire_stats"].total_bytes),
        "surprise_bytes": int(value["wire_stats"].surprise_bytes),
        "reader_work_bytes": int(vm_stats.work_bytes),
        "previous_sha256": program.roots["previous"].sha256,
        "current_sha256": program.roots["current"].sha256,
        "segment_capacity_bytes": int(value["segment_capacity_bytes"]),
        "segments": int(value["segments"]),
        "hierarchy_depth": int(value["hierarchy_depth"]),
    }


def _equivalent(a: dict, b: dict) -> bool:
    keys = (
        "enabled", "best_shift", "exact_proofs", "gate_reads", "gate_used",
        "plan", "wire", "wire_total_bytes", "surprise_bytes", "reader_work_bytes",
        "previous_sha256", "current_sha256", "segments", "hierarchy_depth",
    )
    return all(a[key] == b[key] for key in keys)


def _ratio(candidate: float, control: float) -> float:
    return candidate / control if control else float("inf")


def run() -> dict:
    admission_fn, segment_fn, td = _build_native()
    rows = []
    semantic_ok = True
    was_enabled = gc.isenabled()
    try:
        if was_enabled:
            gc.disable()
        for case in CASES:
            source, target, expected_enable, expected_shift = _relation_cases(SIZE)[case]
            # Shared conversion and root material are deliberately outside both timed arms.
            src_arr = (ctypes.c_uint8 * SIZE).from_buffer_copy(source)
            dst_arr = (ctypes.c_uint8 * SIZE).from_buffer_copy(target)
            previous_digest = sha256(source).hexdigest()
            current_digest = sha256(target).hexdigest()
            previous_root = Root(Ref(0), SIZE, previous_digest)
            ctx = (
                admission_fn, segment_fn, source, target, src_arr, dst_arr,
                previous_root, current_digest,
            )

            eager_probe = _writer_once("eager", *ctx)
            eager_sig = _semantic_signature(eager_probe, source, target)
            eager_probe = None
            lazy_probe = _writer_once("lazy", *ctx)
            lazy_sig = _semantic_signature(lazy_probe, source, target)
            lazy_probe = None

            case_semantic_ok = (
                _equivalent(eager_sig, lazy_sig)
                and eager_sig["enabled"] == bool(expected_enable)
                and (not expected_enable or expected_shift is None or eager_sig["best_shift"] == expected_shift)
                and eager_sig["previous_sha256"] == previous_digest
                and eager_sig["current_sha256"] == current_digest
                and lazy_sig["segment_capacity_bytes"] == (
                    eager_sig["segment_capacity_bytes"] if expected_enable else 0
                )
            )
            semantic_ok &= case_semantic_ok

            wall = {"eager": [], "lazy": []}
            cpu = {"eager": [], "lazy": []}
            last_value = None
            for rep in range(REPETITIONS):
                order = ("eager", "lazy") if rep % 2 == 0 else ("lazy", "eager")
                for arm in order:
                    # Release the preceding arm before starting either clock. This keeps
                    # Python/ctypes result teardown out of the next arm's sample.
                    last_value = None
                    t0_wall = time.perf_counter_ns()
                    t0_cpu = time.process_time_ns()
                    value = _writer_once(arm, *ctx)
                    t1_cpu = time.process_time_ns()
                    t1_wall = time.perf_counter_ns()
                    wall[arm].append(t1_wall - t0_wall)
                    cpu[arm].append(t1_cpu - t0_cpu)
                    # Keep the current arm alive until after both clocks stop.
                    last_value = value
            last_value = None

            eager_wall = float(statistics.median(wall["eager"]))
            lazy_wall = float(statistics.median(wall["lazy"]))
            eager_cpu = float(statistics.median(cpu["eager"]))
            lazy_cpu = float(statistics.median(cpu["lazy"]))
            rows.append({
                "case": case,
                "expected_enable": bool(expected_enable),
                "semantic_ok": case_semantic_ok,
                "segments": eager_sig["segments"],
                "canonical_wire_bytes": eager_sig["wire_total_bytes"],
                "surprise_bytes": eager_sig["surprise_bytes"],
                "reader_work_bytes": eager_sig["reader_work_bytes"],
                "eager_segment_capacity_bytes": eager_sig["segment_capacity_bytes"],
                "lazy_segment_capacity_bytes": lazy_sig["segment_capacity_bytes"],
                "eager_wall_ns_median": eager_wall,
                "lazy_wall_ns_median": lazy_wall,
                "lazy_over_eager_wall": _ratio(lazy_wall, eager_wall),
                "eager_cpu_ns_median": eager_cpu,
                "lazy_cpu_ns_median": lazy_cpu,
                "lazy_over_eager_cpu": _ratio(lazy_cpu, eager_cpu),
            })
    finally:
        if was_enabled:
            gc.enable()
        td.cleanup()

    admitted_ok = all(
        row["lazy_over_eager_wall"] <= ADMITTED_RATIO_MAX
        and row["lazy_over_eager_cpu"] <= ADMITTED_RATIO_MAX
        and row["lazy_segment_capacity_bytes"] == row["eager_segment_capacity_bytes"]
        for row in rows if row["case"] in ADMITTED
    )
    rejected_ok = all(
        row["lazy_over_eager_wall"] <= REJECTED_RATIO_MAX
        and row["lazy_over_eager_cpu"] <= REJECTED_RATIO_MAX
        and row["lazy_segment_capacity_bytes"] == 0
        for row in rows if row["case"] in REJECTED
    )
    if not semantic_ok:
        decision = "INVALIDATE_LAZY_SEGMENT_TIMING"
    elif admitted_ok and rejected_ok:
        decision = "ADVANCE_LAZY_SEGMENT_TIMING"
    else:
        decision = "HOLD_LAZY_SEGMENT_TIMING"

    return {
        "schema": "cmpct-one-g02-lazy-segment-timing-v1",
        "experimental_version": "ONE-G0.2",
        "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
        "size": SIZE,
        "repetitions": REPETITIONS,
        "admitted_ratio_max": ADMITTED_RATIO_MAX,
        "rejected_ratio_max": REJECTED_RATIO_MAX,
        "semantic_gates_pass": semantic_ok,
        "admitted_timing_gate_pass": admitted_ok,
        "rejected_timing_gate_pass": rejected_ok,
        "decision": decision,
        "claim_boundary": (
            "native writer segment-allocation scheduling only; source/target ctypes conversion, native build, and root "
            "digest preparation are common and outside the paired interval; relation admission, conditional Segment "
            "allocation, segmentation, bounded Program construction, validation, and canonical emission are charged; "
            "decode is semantic verification outside timing; no format/reader/v0.29/v0.30 authority"
        ),
        "rows": rows,
    }


def main() -> int:
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["decision"] == "ADVANCE_LAZY_SEGMENT_TIMING" else 1


if __name__ == "__main__":
    raise SystemExit(main())
