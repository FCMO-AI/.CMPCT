"""ONE-G0.2 coarse cost attribution for the root-hash-charged direct writer.

Frozen by ONE_G02_ROOT_HASH_WRITER_COARSE_ATTRIBUTION_PREREG_2026-09-06.md.
This measures ownership only. It does not change ONE semantics or promote an optimization.
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
    CONTROLS,
    PRODUCTIVE,
    ROUNDS,
    SIZES,
    Segment,
    SegmentStats,
    _admit,
    _build_native,
    _literal_program,
    _native_plan,
    _oracle_plan,
    _plan_signature,
    _program_from_plan,
    _relation_cases,
)
from experiments.one.growable_wire import _encode_program_growable_prevalidated
from experiments.one.ir import Ref, Root
from experiments.one.vm import evaluate
from experiments.one.wire import decode_program

MATURE_MIN = 16 * 1024
PROFILED_PRODUCTIVE_MEDIAN_MAX = 1.03
PROFILED_PRODUCTIVE_ROW_MAX = 1.08
PROFILED_CONTROL_MEDIAN_MAX = 1.05
OWNER_SHARE_MIN = 0.25
OWNER_SIZE_SHARE_MIN = 0.20
OWNER_REQUIRED_MATURE_SIZES = 2
PHASES = ("root_hash", "admission", "segment", "program", "validation", "emission")


def _writer_once_direct_unprofiled(admission_fn, segment_fn, source, target, src_arr, dst_arr, seg_buf):
    previous_digest = sha256(source).hexdigest()
    current_digest = sha256(target).hexdigest()
    previous_root = Root(Ref(0), len(source), previous_digest)

    result, gate_reads, gate_used, enabled = _admit(admission_fn, src_arr, dst_arr, len(source))
    segment_stats = SegmentStats()
    if enabled:
        plan = _native_plan(segment_fn, src_arr, dst_arr, len(source), seg_buf, segment_stats)
        program, hierarchy_depth = _program_from_plan(
            source, target, plan, previous_root, current_digest
        )
    else:
        plan = ()
        program, hierarchy_depth = _literal_program(
            source, target, previous_root, current_digest
        )
    program.validate_shape()
    wire, stats = _encode_program_growable_prevalidated(program)
    return (
        wire,
        stats,
        program,
        result,
        gate_reads,
        gate_used,
        enabled,
        plan,
        int(segment_stats.compared_target_bytes),
        int(segment_stats.segments),
        hierarchy_depth,
    )


def _writer_once_profiled(admission_fn, segment_fn, source, target, src_arr, dst_arr, seg_buf):
    phase_ns = {name: 0 for name in PHASES}

    t = time.perf_counter_ns()
    previous_digest = sha256(source).hexdigest()
    current_digest = sha256(target).hexdigest()
    previous_root = Root(Ref(0), len(source), previous_digest)
    phase_ns["root_hash"] = time.perf_counter_ns() - t

    t = time.perf_counter_ns()
    result, gate_reads, gate_used, enabled = _admit(admission_fn, src_arr, dst_arr, len(source))
    phase_ns["admission"] = time.perf_counter_ns() - t

    segment_stats = SegmentStats()
    plan = ()
    t = time.perf_counter_ns()
    if enabled:
        plan = _native_plan(segment_fn, src_arr, dst_arr, len(source), seg_buf, segment_stats)
    phase_ns["segment"] = time.perf_counter_ns() - t

    t = time.perf_counter_ns()
    if enabled:
        program, hierarchy_depth = _program_from_plan(
            source, target, plan, previous_root, current_digest
        )
    else:
        program, hierarchy_depth = _literal_program(
            source, target, previous_root, current_digest
        )
    phase_ns["program"] = time.perf_counter_ns() - t

    t = time.perf_counter_ns()
    program.validate_shape()
    phase_ns["validation"] = time.perf_counter_ns() - t

    t = time.perf_counter_ns()
    wire, stats = _encode_program_growable_prevalidated(program)
    phase_ns["emission"] = time.perf_counter_ns() - t

    return (
        wire,
        stats,
        program,
        result,
        gate_reads,
        gate_used,
        enabled,
        plan,
        int(segment_stats.compared_target_bytes),
        int(segment_stats.segments),
        hierarchy_depth,
        phase_ns,
    )


def _same_writer_value(unprofiled, profiled):
    if unprofiled[0] != profiled[0] or unprofiled[1] != profiled[1]:
        return False
    if unprofiled[6] != profiled[6] or unprofiled[7] != profiled[7]:
        return False
    if int(unprofiled[3].best_shift) != int(profiled[3].best_shift):
        return False
    if int(unprofiled[3].exact_proofs) != int(profiled[3].exact_proofs):
        return False
    if _plan_signature(unprofiled[7]) != _plan_signature(profiled[7]):
        return False
    return unprofiled[8:11] == profiled[8:11]


def _time_pair(ctx):
    baseline_samples = []
    profiled_samples = []
    phase_samples = {name: [] for name in PHASES}
    baseline_value = None
    profiled_value = None
    was_enabled = gc.isenabled()
    try:
        if was_enabled:
            gc.disable()
        for round_index in range(ROUNDS):
            order = (False, True) if round_index % 2 == 0 else (True, False)
            for do_profile in order:
                t0 = time.perf_counter_ns()
                if do_profile:
                    value = _writer_once_profiled(*ctx)
                else:
                    value = _writer_once_direct_unprofiled(*ctx)
                elapsed = time.perf_counter_ns() - t0
                if do_profile:
                    profiled_samples.append(elapsed)
                    profiled_value = value
                    phases = value[-1]
                    for name in PHASES:
                        phase_samples[name].append(int(phases[name]))
                else:
                    baseline_samples.append(elapsed)
                    baseline_value = value
    finally:
        if was_enabled:
            gc.enable()

    phase_medians = {
        name: float(statistics.median(phase_samples[name])) for name in PHASES
    }
    phase_total = sum(phase_medians.values())
    phase_shares = {
        name: (phase_medians[name] / phase_total if phase_total else 0.0) for name in PHASES
    }
    return (
        float(statistics.median(baseline_samples)),
        baseline_value,
        float(statistics.median(profiled_samples)),
        profiled_value,
        phase_medians,
        phase_shares,
    )


def run():
    admission_fn, segment_fn, td = _build_native()
    rows = []
    semantics_ok = True
    oracle_ok = True
    mature_productive_overhead = []
    mature_control_overhead = []
    phase_mature_productive = {name: [] for name in PHASES}
    phase_by_mature_size = {
        name: {size: [] for size in SIZES if size >= MATURE_MIN} for name in PHASES
    }
    try:
        for size in SIZES:
            cases = _relation_cases(size)
            for case in PRODUCTIVE + CONTROLS:
                source, target, expected_enable, expected_shift = cases[case]
                src_arr = (ctypes.c_uint8 * size).from_buffer_copy(source)
                dst_arr = (ctypes.c_uint8 * size).from_buffer_copy(target)
                seg_buf = (Segment * size)()
                ctx = (admission_fn, segment_fn, source, target, src_arr, dst_arr, seg_buf)

                baseline = _writer_once_direct_unprofiled(*ctx)
                profiled = _writer_once_profiled(*ctx)
                this_semantic = _same_writer_value(baseline, profiled)

                wire, stats, program, result, gate_reads, gate_used, enabled, plan, traffic, segments, depth = baseline
                expected_roots = (
                    program.roots["previous"].sha256 == sha256(source).hexdigest()
                    and program.roots["current"].sha256 == sha256(target).hexdigest()
                )
                if enabled:
                    this_oracle = _plan_signature(plan) == _plan_signature(_oracle_plan(source, target))
                else:
                    this_oracle = True
                decoded = decode_program(wire)
                outputs, vm_stats = evaluate(decoded)
                exact = outputs == {"previous": source, "current": target}
                this_semantic = this_semantic and expected_roots and exact
                semantics_ok &= this_semantic
                oracle_ok &= this_oracle
                if not this_semantic or not this_oracle:
                    raise AssertionError("coarse attribution changed or failed writer semantics/oracle")

                baseline_ns, baseline_timed, profiled_ns, profiled_timed, phase_medians, phase_shares = _time_pair(ctx)
                if baseline_timed is None or profiled_timed is None or not _same_writer_value(baseline_timed, profiled_timed):
                    raise AssertionError("timed profiled writer changed canonical semantics")
                overhead = profiled_ns / baseline_ns
                phase_share_sum = sum(phase_shares.values())
                if abs(phase_share_sum - 1.0) > 1e-9:
                    raise AssertionError("phase shares do not sum to one")

                is_productive = case in PRODUCTIVE
                if size >= MATURE_MIN:
                    if is_productive:
                        mature_productive_overhead.append(overhead)
                        for name in PHASES:
                            phase_mature_productive[name].append(phase_shares[name])
                            phase_by_mature_size[name][size].append(phase_shares[name])
                    else:
                        mature_control_overhead.append(overhead)

                rows.append({
                    "relation_bytes": size,
                    "case": case,
                    "productive": is_productive,
                    "expected_enable": expected_enable,
                    "expected_shift": expected_shift,
                    "relation_enabled": enabled,
                    "best_shift": int(result.best_shift),
                    "exact_proofs": int(result.exact_proofs),
                    "gate_compared_bytes": gate_reads,
                    "used_sparse_gate": gate_used,
                    "native_segment_compared_target_bytes": traffic,
                    "segments": segments,
                    "modeled_segment_plan_bytes": segments * ctypes.sizeof(Segment),
                    "native_plan_matches_python_oracle": this_oracle,
                    "hierarchy_depth": depth,
                    "program_nodes": len(program.nodes),
                    "canonical_wire_bytes": stats.total_bytes,
                    "reader_work_bytes": vm_stats.work_bytes,
                    "reader_materialized_bytes": vm_stats.materialized_bytes,
                    "unprofiled_direct_writer_median_ns": baseline_ns,
                    "profiled_direct_writer_median_ns": profiled_ns,
                    "profiled_over_unprofiled": overhead,
                    "phase_median_ns": phase_medians,
                    "phase_share": phase_shares,
                    "phase_share_sum": phase_share_sum,
                    "wire_exact": baseline[0] == profiled[0],
                    "exact_reconstruction": exact,
                })

        productive_overhead_median = float(statistics.median(mature_productive_overhead))
        control_overhead_median = float(statistics.median(mature_control_overhead))
        worst_productive_overhead = max(mature_productive_overhead)
        overhead_ok = (
            productive_overhead_median <= PROFILED_PRODUCTIVE_MEDIAN_MAX
            and worst_productive_overhead <= PROFILED_PRODUCTIVE_ROW_MAX
            and control_overhead_median <= PROFILED_CONTROL_MEDIAN_MAX
        )

        phase_medians = {
            name: float(statistics.median(values)) for name, values in phase_mature_productive.items()
        }
        phase_size_medians = {
            name: {
                str(size): float(statistics.median(values))
                for size, values in by_size.items()
            }
            for name, by_size in phase_by_mature_size.items()
        }
        qualifying = []
        for name in PHASES:
            mature_sizes_at_20 = sum(
                1 for value in phase_size_medians[name].values() if value >= OWNER_SIZE_SHARE_MIN
            )
            if phase_medians[name] >= OWNER_SHARE_MIN and mature_sizes_at_20 >= OWNER_REQUIRED_MATURE_SIZES:
                qualifying.append(name)
        qualifying.sort(key=lambda name: phase_medians[name], reverse=True)

        if not semantics_ok or not oracle_ok or not overhead_ok:
            decision = "invalidate_root_hash_writer_attribution"
        elif qualifying:
            decision = "localize_root_hash_writer_owner"
        else:
            decision = "diffuse_root_hash_writer_cost"

        return {
            "schema": "cmpct-one-g02-root-hash-writer-coarse-attribution-v1",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "frozen_rounds": ROUNDS,
            "timing_order": "alternating unprofiled/profiled-profiled/unprofiled",
            "mature_min_bytes": MATURE_MIN,
            "semantic_gates_pass": semantics_ok,
            "native_plan_oracle_pass": oracle_ok,
            "mature_productive_profiled_over_unprofiled_median": productive_overhead_median,
            "mature_productive_profiled_over_unprofiled_worst": worst_productive_overhead,
            "mature_control_profiled_over_unprofiled_median": control_overhead_median,
            "instrumentation_overhead_gate_pass": overhead_ok,
            "mature_productive_phase_share_medians": phase_medians,
            "mature_productive_phase_share_size_medians": phase_size_medians,
            "qualifying_material_owners": qualifying,
            "primary_owner": qualifying[0] if qualifying else None,
            "decision": decision,
            "claim_boundary": (
                "cost attribution only inside the existing adjacent-version root-hash-charged direct-emitter "
                "research writer: hashes, relation admission, native one-pass segmentation, generic Program "
                "construction, validation and direct canonical emission; excludes arbitrary/fused discovery, "
                "authenticated placement/durability, filesystem semantics and product-native authority"
            ),
            "rows": rows,
        }
    finally:
        td.cleanup()


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["decision"] in {"localize_root_hash_writer_owner", "diffuse_root_hash_writer_cost"} else 1)
