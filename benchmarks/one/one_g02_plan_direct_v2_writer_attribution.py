"""ONE-G0.2 coarse elapsed attribution for the promoted plan-direct V2 writer.

Frozen by ONE_G02_PLAN_DIRECT_V2_WRITER_ATTRIBUTION_PREREG_2026-09-06.md.
Attribution only: no ONE semantic or representation change.
"""
from __future__ import annotations

import ctypes
import gc
from hashlib import sha256
import json
import os
import statistics
import time

import benchmarks.one.one_g02_root_hash_writer_plan_direct_wire as v1
from benchmarks.one.one_g02_end_to_end_direct_emitter_writer import (
    CONTROLS,
    PRODUCTIVE,
    ROUNDS,
    SIZES,
    Segment,
    SegmentStats,
    _build_native,
    _oracle_plan,
    _plan_signature,
    _relation_cases,
)
from benchmarks.one.one_g02_root_hash_writer_plan_direct_wire_v2 import (
    _candidate_once_v2,
    _direct_wire_from_plan_v2,
)
from experiments.one.vm import evaluate
from experiments.one.wire import decode_program

MATURE_MIN = 16 * 1024
PROFILED_PRODUCTIVE_MEDIAN_MAX = 1.03
PROFILED_PRODUCTIVE_ROW_MAX = 1.08
PROFILED_CONTROL_MEDIAN_MAX = 1.05
OWNER_SHARE_MIN = 0.25
OWNER_SIZE_SHARE_MIN = 0.20
OWNER_REQUIRED_MATURE_SIZES = 2
PHASES = ("root_hash", "admission", "segment", "direct_wire")


def _writer_profiled(admission_fn, segment_fn, source, target, src_arr, dst_arr, seg_buf):
    phase_ns = {name: 0 for name in PHASES}

    t = time.perf_counter_ns()
    previous_digest = sha256(source).hexdigest()
    current_digest = sha256(target).hexdigest()
    phase_ns["root_hash"] = time.perf_counter_ns() - t

    t = time.perf_counter_ns()
    result, gate_reads, gate_used, enabled = v1._admit(
        admission_fn, src_arr, dst_arr, len(source)
    )
    phase_ns["admission"] = time.perf_counter_ns() - t

    segment_stats = SegmentStats()
    t = time.perf_counter_ns()
    if enabled:
        plan = v1._native_plan(segment_fn, src_arr, dst_arr, len(source), seg_buf, segment_stats)
    else:
        plan = ()
    phase_ns["segment"] = time.perf_counter_ns() - t

    t = time.perf_counter_ns()
    wire, stats, depth, node_count = _direct_wire_from_plan_v2(
        source, target, plan, previous_digest, current_digest, enabled
    )
    phase_ns["direct_wire"] = time.perf_counter_ns() - t

    return (
        wire, stats, result, gate_reads, gate_used, enabled, plan,
        int(segment_stats.compared_target_bytes), int(segment_stats.segments),
        depth, node_count, phase_ns,
    )


def _same_value(unprofiled, profiled) -> bool:
    if unprofiled[0] != profiled[0] or unprofiled[1] != profiled[1]:
        return False
    if unprofiled[5] != profiled[5]:
        return False
    if int(unprofiled[2].best_shift) != int(profiled[2].best_shift):
        return False
    if int(unprofiled[2].exact_proofs) != int(profiled[2].exact_proofs):
        return False
    if _plan_signature(unprofiled[6]) != _plan_signature(profiled[6]):
        return False
    return unprofiled[7:11] == profiled[7:11]


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
                value = _writer_profiled(*ctx) if do_profile else _candidate_once_v2(*ctx)
                elapsed = time.perf_counter_ns() - t0
                if do_profile:
                    profiled_samples.append(elapsed)
                    profiled_value = value
                    for name in PHASES:
                        phase_samples[name].append(int(value[-1][name]))
                else:
                    baseline_samples.append(elapsed)
                    baseline_value = value
    finally:
        if was_enabled:
            gc.enable()

    phase_medians = {
        name: float(statistics.median(phase_samples[name])) for name in PHASES
    }
    total = sum(phase_medians.values())
    phase_shares = {
        name: (phase_medians[name] / total if total else 0.0) for name in PHASES
    }
    return (
        float(statistics.median(baseline_samples)), baseline_value,
        float(statistics.median(profiled_samples)), profiled_value,
        phase_medians, phase_shares,
    )


def run():
    admission_fn, segment_fn, td = _build_native()
    rows = []
    semantic_failures = 0
    oracle_failures = 0
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

                baseline = _candidate_once_v2(*ctx)
                profiled = _writer_profiled(*ctx)
                semantic_ok = _same_value(baseline, profiled)
                oracle_ok = (not baseline[5]) or (
                    _plan_signature(baseline[6]) == _plan_signature(_oracle_plan(source, target))
                )
                out, vm_stats = evaluate(decode_program(baseline[0]))
                semantic_ok = semantic_ok and out == {"previous": source, "current": target}
                if not semantic_ok:
                    semantic_failures += 1
                if not oracle_ok:
                    oracle_failures += 1
                if not semantic_ok or not oracle_ok:
                    raise AssertionError("V2 attribution changed semantics or failed plan oracle")

                baseline_ns, bt, profiled_ns, pt, phase_medians, phase_shares = _time_pair(ctx)
                if bt is None or pt is None or not _same_value(bt, pt):
                    raise AssertionError("timed V2 attribution changed semantics")
                overhead = profiled_ns / baseline_ns
                if abs(sum(phase_shares.values()) - 1.0) > 1e-9:
                    raise AssertionError("phase shares do not sum to one")

                productive = case in PRODUCTIVE
                if size >= MATURE_MIN:
                    if productive:
                        mature_productive_overhead.append(overhead)
                        for name in PHASES:
                            phase_mature_productive[name].append(phase_shares[name])
                            phase_by_mature_size[name][size].append(phase_shares[name])
                    else:
                        mature_control_overhead.append(overhead)

                rows.append({
                    "relation_bytes": size,
                    "case": case,
                    "productive": productive,
                    "expected_enable": expected_enable,
                    "expected_shift": expected_shift,
                    "relation_enabled": bool(baseline[5]),
                    "best_shift": int(baseline[2].best_shift),
                    "exact_proofs": int(baseline[2].exact_proofs),
                    "gate_compared_bytes": int(baseline[3]),
                    "used_sparse_gate": bool(baseline[4]),
                    "native_segment_compared_target_bytes": int(baseline[7]),
                    "segments": int(baseline[8]),
                    "hierarchy_depth": int(baseline[9]),
                    "node_count": int(baseline[10]),
                    "canonical_wire_bytes": int(baseline[1].total_bytes),
                    "reader_work_bytes": int(vm_stats.work_bytes),
                    "reader_materialized_bytes": int(vm_stats.materialized_bytes),
                    "unprofiled_v2_median_ns": baseline_ns,
                    "profiled_v2_median_ns": profiled_ns,
                    "profiled_over_unprofiled": overhead,
                    "phase_median_ns": phase_medians,
                    "phase_share": phase_shares,
                })

        productive_overhead_median = float(statistics.median(mature_productive_overhead))
        productive_overhead_worst = max(mature_productive_overhead)
        control_overhead_median = float(statistics.median(mature_control_overhead))
        overhead_ok = (
            productive_overhead_median <= PROFILED_PRODUCTIVE_MEDIAN_MAX
            and productive_overhead_worst <= PROFILED_PRODUCTIVE_ROW_MAX
            and control_overhead_median <= PROFILED_CONTROL_MEDIAN_MAX
        )

        phase_medians = {
            name: float(statistics.median(values))
            for name, values in phase_mature_productive.items()
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
            sizes_at_20 = sum(
                1 for value in phase_size_medians[name].values()
                if value >= OWNER_SIZE_SHARE_MIN
            )
            if phase_medians[name] >= OWNER_SHARE_MIN and sizes_at_20 >= OWNER_REQUIRED_MATURE_SIZES:
                qualifying.append(name)
        qualifying.sort(key=lambda name: phase_medians[name], reverse=True)

        if semantic_failures or oracle_failures or not overhead_ok:
            decision = "invalidate_plan_direct_v2_writer_attribution"
        elif qualifying:
            decision = "localize_plan_direct_v2_writer_owner"
        else:
            decision = "diffuse_plan_direct_v2_writer_cost"

        return {
            "schema": "cmpct-one-g02-plan-direct-v2-writer-attribution-v1",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "frozen_rounds": ROUNDS,
            "mature_min_bytes": MATURE_MIN,
            "semantic_failures": semantic_failures,
            "oracle_failures": oracle_failures,
            "mature_productive_profiled_over_unprofiled_median": productive_overhead_median,
            "mature_productive_profiled_over_unprofiled_worst": productive_overhead_worst,
            "mature_control_profiled_over_unprofiled_median": control_overhead_median,
            "instrumentation_overhead_gate_pass": overhead_ok,
            "mature_productive_phase_share_medians": phase_medians,
            "mature_productive_phase_share_size_medians": phase_size_medians,
            "qualifying_material_owners": qualifying,
            "primary_owner": qualifying[0] if qualifying else None,
            "decision": decision,
            "claim_boundary": "elapsed attribution only inside adjacent-version root-hash-charged plan-direct V2 writer; excludes arbitrary/fused discovery and product-native authority",
            "rows": rows,
        }
    finally:
        td.cleanup()


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["decision"] in {
        "localize_plan_direct_v2_writer_owner", "diffuse_plan_direct_v2_writer_cost"
    } else 1)
