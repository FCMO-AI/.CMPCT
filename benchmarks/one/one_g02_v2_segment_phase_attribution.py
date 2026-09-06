"""ONE-G0.2 sub-attribution of native-kernel vs Python plan marshalling."""
from __future__ import annotations

import ctypes
import gc
import json
import os
import statistics
import time

from benchmarks.one.one_g02_end_to_end_direct_emitter_writer import (
    PRODUCTIVE, SIZES, Segment, SegmentStats, _build_native, _native_plan,
    _oracle_plan, _plan_signature,
)
from benchmarks.one.one_g02_shift_branch_bound_relation_transfer import _relation_cases

ROUNDS = 31
MATURE_MIN = 16 * 1024
PROFILE_MEDIAN_MAX = 1.03
PROFILE_WORST_MAX = 1.08
PRIMARY_SHARE = 0.50
PRIMARY_SIZE_COUNT = 3
MATERIAL_SHARE = 0.25
MATERIAL_SIZE_SHARE = 0.20
MATERIAL_SIZE_COUNT = 3
PHASES = ("native_kernel", "plan_marshalling")


def _native_plan_profiled(segment_fn, src_arr, dst_arr, n, buf):
    stats = SegmentStats()
    t0 = time.perf_counter_ns()
    rc = segment_fn(src_arr, dst_arr, n, buf, n, ctypes.byref(stats))
    native_ns = time.perf_counter_ns() - t0
    if rc != 0:
        raise RuntimeError(f"native one-pass segmenter failed: {rc}")

    t1 = time.perf_counter_ns()
    plan = []
    for i in range(int(stats.segments)):
        seg = buf[i]
        start = int(seg.start)
        length = int(seg.length)
        if int(seg.kind) == 0:
            plan.append(("ref", start, length, b""))
        elif int(seg.kind) == 1:
            plan.append(("surprise", 0, length, bytes(dst_arr[start:start + length])))
        else:
            raise AssertionError("unknown native segment kind")
    marshaling_ns = time.perf_counter_ns() - t1
    return tuple(plan), int(stats.compared_target_bytes), int(stats.segments), {
        "native_kernel": native_ns,
        "plan_marshalling": marshaling_ns,
    }


def _ordinary(segment_fn, src_arr, dst_arr, n, buf):
    stats = SegmentStats()
    plan = _native_plan(segment_fn, src_arr, dst_arr, n, buf, stats)
    return plan, int(stats.compared_target_bytes), int(stats.segments)


def _time_pair(segment_fn, src_arr, dst_arr, n, buf):
    ordinary_samples = []
    profiled_samples = []
    phase_samples = {name: [] for name in PHASES}
    ordinary_value = None
    profiled_value = None
    was_enabled = gc.isenabled()
    try:
        if was_enabled:
            gc.disable()
        for r in range(ROUNDS):
            order = (False, True) if r % 2 == 0 else (True, False)
            for profiled in order:
                t0 = time.perf_counter_ns()
                value = _native_plan_profiled(segment_fn, src_arr, dst_arr, n, buf) if profiled else _ordinary(segment_fn, src_arr, dst_arr, n, buf)
                elapsed = time.perf_counter_ns() - t0
                if profiled:
                    profiled_samples.append(elapsed)
                    profiled_value = value
                    for name in PHASES:
                        phase_samples[name].append(int(value[3][name]))
                else:
                    ordinary_samples.append(elapsed)
                    ordinary_value = value
    finally:
        if was_enabled:
            gc.enable()
    return (
        float(statistics.median(ordinary_samples)), ordinary_value,
        float(statistics.median(profiled_samples)), profiled_value,
        {name: float(statistics.median(values)) for name, values in phase_samples.items()},
    )


def run():
    _admission, segment_fn, td = _build_native()
    rows = []
    overheads = []
    shares = {name: [] for name in PHASES}
    by_size = {name: {size: [] for size in SIZES if size >= MATURE_MIN} for name in PHASES}
    semantic_failures = 0
    try:
        for size in SIZES:
            cases = _relation_cases(size)
            for case in PRODUCTIVE:
                source, target, expected_enable, _expected_shift = cases[case]
                if not expected_enable:
                    raise AssertionError("frozen productive case unexpectedly disabled")
                src_arr = (ctypes.c_uint8 * size).from_buffer_copy(source)
                dst_arr = (ctypes.c_uint8 * size).from_buffer_copy(target)
                buf = (Segment * size)()

                ordinary = _ordinary(segment_fn, src_arr, dst_arr, size, buf)
                profiled = _native_plan_profiled(segment_fn, src_arr, dst_arr, size, buf)
                oracle = _oracle_plan(source, target)
                semantic_ok = (
                    _plan_signature(ordinary[0]) == _plan_signature(profiled[0]) == _plan_signature(oracle)
                    and ordinary[1] == profiled[1] == size
                    and ordinary[2] == profiled[2]
                )
                if not semantic_ok:
                    semantic_failures += 1
                    raise AssertionError(f"segment sub-attribution changed plan: {case}/{size}")

                ordinary_ns, ot, profiled_ns, pt, phase_ns = _time_pair(segment_fn, src_arr, dst_arr, size, buf)
                if ot is None or pt is None or _plan_signature(ot[0]) != _plan_signature(pt[0]):
                    raise AssertionError("timed segment sub-attribution changed plan")
                ratio = profiled_ns / ordinary_ns
                total_phase = sum(phase_ns.values())
                phase_share = {name: (phase_ns[name] / total_phase if total_phase else 0.0) for name in PHASES}
                if size >= MATURE_MIN:
                    overheads.append(ratio)
                    for name in PHASES:
                        shares[name].append(phase_share[name])
                        by_size[name][size].append(phase_share[name])
                rows.append({
                    "relation_bytes": size,
                    "case": case,
                    "segments": ordinary[2],
                    "semantic_ok": semantic_ok,
                    "ordinary_segment_phase_median_ns": ordinary_ns,
                    "profiled_segment_phase_median_ns": profiled_ns,
                    "profiled_over_ordinary": ratio,
                    "phase_median_ns": phase_ns,
                    "phase_share": phase_share,
                })

        overhead_median = float(statistics.median(overheads))
        overhead_worst = max(overheads)
        overhead_ok = overhead_median <= PROFILE_MEDIAN_MAX and overhead_worst <= PROFILE_WORST_MAX
        share_medians = {name: float(statistics.median(values)) for name, values in shares.items()}
        size_medians = {
            name: {str(size): float(statistics.median(values)) for size, values in sizes.items()}
            for name, sizes in by_size.items()
        }
        primary = []
        material = []
        for name in PHASES:
            primary_sizes = sum(v >= PRIMARY_SHARE for v in size_medians[name].values())
            material_sizes = sum(v >= MATERIAL_SIZE_SHARE for v in size_medians[name].values())
            if share_medians[name] >= PRIMARY_SHARE and primary_sizes >= PRIMARY_SIZE_COUNT:
                primary.append(name)
            if share_medians[name] >= MATERIAL_SHARE and material_sizes >= MATERIAL_SIZE_COUNT:
                material.append(name)
        primary.sort(key=lambda n: share_medians[n], reverse=True)
        material.sort(key=lambda n: share_medians[n], reverse=True)

        if semantic_failures or not overhead_ok:
            decision = "invalidate_v2_segment_phase_attribution"
        elif primary:
            decision = "localize_v2_segment_phase_primary_owner"
        elif material:
            decision = "localize_v2_segment_phase_material_owner"
        else:
            decision = "diffuse_v2_segment_phase_cost"

        return {
            "schema": "cmpct-one-g02-v2-segment-phase-attribution-v1",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "rounds": ROUNDS,
            "semantic_failures": semantic_failures,
            "profiled_over_ordinary_mature_median": overhead_median,
            "profiled_over_ordinary_mature_worst": overhead_worst,
            "instrumentation_overhead_gate_pass": overhead_ok,
            "mature_phase_share_medians": share_medians,
            "mature_phase_share_size_medians": size_medians,
            "primary_owners": primary,
            "material_owners": material,
            "decision": decision,
            "claim_boundary": "attribution only inside V2 _native_plan; no representation, wire, reader, product or comparator claim",
            "rows": rows,
        }
    finally:
        td.cleanup()


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["decision"] != "invalidate_v2_segment_phase_attribution" else 1)
