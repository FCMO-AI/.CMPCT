"""ONE-G0.2 packed observer rehabilitation whole-writer falsifier.

Frozen by ONE_G02_PACKED_OBSERVER_REHABILITATION_PREREG_2026-09-08.md.
The prior arena-retaining compact view remains a preserved negative. This candidate
retains only used native records after the same observer kernel completes.
"""
from __future__ import annotations

import ctypes
import gc
from hashlib import sha256
import json
import os
import statistics
import time

from benchmarks.one.one_g02_compact_observer_handoff_writer import (
    FAMILIES,
    REPETITIONS,
    SIZES,
    Segment,
    SegmentStats,
    _admit,
    _build_native,
    _case,
    _native_plan,
    _plan_signature,
    _same_writer_result,
)
from benchmarks.one.one_g02_post_segment_control_cost_owner import _literal_program
from experiments.one.bounded_surprise_pool import program_from_plan_pooled
from experiments.one.growable_wire import _encode_program_growable_prevalidated
from experiments.one.ir import Ref, Root
from experiments.one.native_observe import _CRun, _CReuse, observe_native
from experiments.one.native_observe_view import PackedObservationView, observe_native_packed
from experiments.one.vm import evaluate
from experiments.one.wire import decode_program

GAIN_RETENTION_MAX = 0.60
NO_REGRESSION_MAX = 1.05


def _writer_once(admission_fn, segment_fn, source: bytes, target: bytes, src_arr, dst_arr, seg_buf, packed: bool):
    previous_digest = sha256(source).hexdigest()
    current_digest = sha256(target).hexdigest()
    previous_root = Root(Ref(0), len(source), previous_digest)

    observer = observe_native_packed(target) if packed else observe_native(target)

    result, gate_reads, gate_used, enabled = _admit(admission_fn, src_arr, dst_arr, len(source))
    segment_stats = SegmentStats()
    if enabled:
        plan = _native_plan(segment_fn, src_arr, dst_arr, len(source), seg_buf, segment_stats)
        program, pool_stats = program_from_plan_pooled(source, target, plan, previous_root, current_digest)
        hierarchy_depth = pool_stats.hierarchy_depth
    else:
        plan = ()
        program, hierarchy_depth = _literal_program(source, target, previous_root, current_digest)
        pool_stats = None
    program.validate_shape()
    wire, wire_stats = _encode_program_growable_prevalidated(program)

    run_width = ctypes.sizeof(_CRun)
    reuse_width = ctypes.sizeof(_CReuse)
    if packed:
        assert isinstance(observer, PackedObservationView)
        observer_counts = (observer.run_count, observer.reuse_count)
        output_capacity_bytes = observer.native_output_capacity_bytes
        output_used_bytes = observer.native_output_used_bytes
        retained_output_bytes = observer.retained_output_bytes
    else:
        observer_counts = (len(observer.runs), len(observer.reuse))
        run_capacity = max(1, len(target) // 8 + 2)
        reuse_capacity = max(1, len(target) // 64 + 2)
        output_capacity_bytes = run_capacity * run_width + reuse_capacity * reuse_width
        output_used_bytes = observer_counts[0] * run_width + observer_counts[1] * reuse_width
        # Eager Python opportunities replace native scratch; retain this as a native-state
        # accounting value only rather than pretending Python object size is zero.
        retained_output_bytes = 0

    return {
        "wire": wire,
        "wire_stats": wire_stats,
        "program": program,
        "relation_signature": (
            bool(enabled), int(result.best_shift), int(result.exact_proofs), bool(gate_used), int(gate_reads)
        ),
        "plan_signature": _plan_signature(plan),
        "hierarchy_depth": hierarchy_depth,
        "segments": int(segment_stats.segments),
        "segment_compared_target_bytes": int(segment_stats.compared_target_bytes),
        "observer_counts": observer_counts,
        "observer_output_capacity_bytes": output_capacity_bytes,
        "observer_output_used_bytes": output_used_bytes,
        "observer_retained_output_bytes": retained_output_bytes,
        "pooled_groups": pool_stats.groups if pool_stats is not None else 0,
    }


def _same(a, b) -> bool:
    return _same_writer_result(a, b)


def _time_pair(ctx):
    eager_wall: list[int] = []
    eager_cpu: list[int] = []
    packed_wall: list[int] = []
    packed_cpu: list[int] = []
    eager_value = None
    packed_value = None
    was_enabled = gc.isenabled()
    try:
        if was_enabled:
            gc.disable()
        for round_index in range(REPETITIONS):
            order = (False, True) if round_index % 2 == 0 else (True, False)
            for packed in order:
                if packed:
                    packed_value = None
                else:
                    eager_value = None
                c0 = time.process_time_ns()
                w0 = time.perf_counter_ns()
                value = _writer_once(*ctx, packed=packed)
                w1 = time.perf_counter_ns()
                c1 = time.process_time_ns()
                if packed:
                    packed_value = value
                    packed_wall.append(w1 - w0)
                    packed_cpu.append(c1 - c0)
                else:
                    eager_value = value
                    eager_wall.append(w1 - w0)
                    eager_cpu.append(c1 - c0)
    finally:
        if was_enabled:
            gc.enable()
    if eager_value is None or packed_value is None:
        raise AssertionError("missing paired writer result")
    return (
        float(statistics.median(eager_wall)),
        float(statistics.median(eager_cpu)),
        eager_value,
        float(statistics.median(packed_wall)),
        float(statistics.median(packed_cpu)),
        packed_value,
    )


def run():
    observe_native(b"warmup" * 32)
    observe_native_packed(b"warmup" * 32)
    admission_fn, segment_fn, td = _build_native()
    rows = []
    semantic_ok = True
    try:
        for size in SIZES:
            for family in FAMILIES:
                source, target = _case(family, size)
                src_arr = (ctypes.c_uint8 * size).from_buffer_copy(source)
                dst_arr = (ctypes.c_uint8 * size).from_buffer_copy(target)
                seg_buf = (Segment * size)()

                eager_observation = observe_native(target)
                packed_authority = observe_native_packed(target)
                observer_exact = packed_authority.materialize() == eager_observation
                resource_exact = (
                    packed_authority.retained_output_bytes == packed_authority.native_output_used_bytes
                    and packed_authority.retained_output_bytes <= packed_authority.native_output_capacity_bytes
                )

                eager_authority = _writer_once(
                    admission_fn, segment_fn, source, target, src_arr, dst_arr, seg_buf, False
                )
                packed_authority_writer = _writer_once(
                    admission_fn, segment_fn, source, target, src_arr, dst_arr, seg_buf, True
                )
                writer_exact = _same(eager_authority, packed_authority_writer)
                decoded = decode_program(packed_authority_writer["wire"])
                outputs, vm_stats = evaluate(decoded)
                reconstruction_exact = outputs == {"previous": source, "current": target}
                roots_exact = (
                    packed_authority_writer["program"].roots["previous"].sha256 == sha256(source).hexdigest()
                    and packed_authority_writer["program"].roots["current"].sha256 == sha256(target).hexdigest()
                )
                row_semantic = observer_exact and resource_exact and writer_exact and reconstruction_exact and roots_exact
                semantic_ok &= row_semantic
                if not row_semantic:
                    raise AssertionError(f"packed observer rehabilitation changed semantics: {size=} {family=}")

                ctx = (admission_fn, segment_fn, source, target, src_arr, dst_arr, seg_buf)
                ew, ec, ev, pw, pc, pv = _time_pair(ctx)
                timed_exact = _same(ev, pv)
                if not timed_exact:
                    raise AssertionError(f"timed packed observer handoff changed writer: {size=} {family=}")

                capacity = int(pv["observer_output_capacity_bytes"])
                retained = int(pv["observer_retained_output_bytes"])
                rows.append({
                    "bytes": size,
                    "family": family,
                    "observer_exact": observer_exact,
                    "writer_exact": writer_exact,
                    "timed_writer_exact": timed_exact,
                    "root_hashes_exact": roots_exact,
                    "exact_reconstruction": reconstruction_exact,
                    "resource_exact": resource_exact,
                    "relation_enabled": pv["relation_signature"][0],
                    "best_shift": pv["relation_signature"][1],
                    "exact_proofs": pv["relation_signature"][2],
                    "segments": pv["segments"],
                    "segment_compared_target_bytes": pv["segment_compared_target_bytes"],
                    "program_nodes": len(pv["program"].nodes),
                    "canonical_wire_bytes": pv["wire_stats"].total_bytes,
                    "surprise_bytes": pv["wire_stats"].surprise_bytes,
                    "reader_work_bytes": vm_stats.work_bytes,
                    "reader_materialized_bytes": vm_stats.materialized_bytes,
                    "observer_run_count": pv["observer_counts"][0],
                    "observer_reuse_count": pv["observer_counts"][1],
                    "observer_native_scratch_capacity_bytes": capacity,
                    "observer_native_output_used_bytes": int(pv["observer_output_used_bytes"]),
                    "observer_packed_retained_bytes": retained,
                    "observer_retained_over_scratch": retained / capacity if capacity else 0.0,
                    "eager_writer_wall_median_ns": ew,
                    "eager_writer_cpu_median_ns": ec,
                    "packed_writer_wall_median_ns": pw,
                    "packed_writer_cpu_median_ns": pc,
                    "packed_over_eager_wall": pw / ew,
                    "packed_over_eager_cpu": pc / ec,
                })

        million = [row for row in rows if row["bytes"] == (1 << 20)]
        structured = next(row for row in million if row["family"] == "structured")
        gain_retained = (
            structured["packed_over_eager_wall"] <= GAIN_RETENTION_MAX
            and structured["packed_over_eager_cpu"] <= GAIN_RETENTION_MAX
        )
        no_regression = all(
            row["packed_over_eager_wall"] <= NO_REGRESSION_MAX
            and row["packed_over_eager_cpu"] <= NO_REGRESSION_MAX
            for row in million
        )
        if not semantic_ok:
            decision = "INVALIDATE_PACKED_OBSERVER_REHABILITATION"
        elif gain_retained and no_regression:
            decision = "ADVANCE_PACKED_OBSERVER_REHABILITATION"
        else:
            decision = "HOLD_PACKED_OBSERVER_REHABILITATION"
        return {
            "schema": "cmpct-one-g02-packed-observer-rehabilitation-v1",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "repetitions": REPETITIONS,
            "sizes": list(SIZES),
            "families": list(FAMILIES),
            "gain_retention_max": GAIN_RETENTION_MAX,
            "no_regression_max": NO_REGRESSION_MAX,
            "semantic_gates_pass": semantic_ok,
            "structured_gain_retained_1m": gain_retained,
            "all_rows_no_regression_1m": no_regression,
            "decision": decision,
            "claim_boundary": (
                "writer-internal rehabilitation only; same native observer kernel/input copy/scratch capacities, "
                "candidate packs only used native records then releases worst-case arenas; downstream admission/"
                "segmentation still consume source/target directly; no stored-format, reader, RSS/product, arbitrary "
                "discovery, durability, recovery, portability, or v0.29/v0.30 authority"
            ),
            "rows": rows,
        }
    finally:
        td.cleanup()


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["decision"] == "ADVANCE_PACKED_OBSERVER_REHABILITATION" else 1)
