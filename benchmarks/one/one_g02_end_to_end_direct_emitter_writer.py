"""ONE-G0.2 end-to-end temporal writer direct-emitter falsifier.

Frozen by ONE_G02_END_TO_END_DIRECT_EMITTER_WRITER_PREREG_2026-09-05.md.
Both arms use identical admission, native one-pass segmentation, bounded Program
construction and validation. Only canonical emission differs.
"""
from __future__ import annotations

import ctypes
from hashlib import sha256
import gc
import json
import os
import statistics
import subprocess
import tempfile
import time
from pathlib import Path

from benchmarks.one.one_g02_post_segment_control_cost_owner import (
    CONTROLS,
    PRODUCTIVE,
    SIZES,
    _literal_program,
    _program_from_plan,
    _segments_plus1,
)
from benchmarks.one.one_g02_shift_branch_bound_relation_transfer import Result, _relation_cases
from experiments.one.growable_wire import _encode_program_growable_prevalidated
from experiments.one.ir import Program, Ref, Root
from experiments.one.vm import evaluate
from experiments.one.wire import decode_program, encode_program

ROUNDS = 31
PRODUCTIVE_MEDIAN_MAX = 0.92
PRODUCTIVE_ROW_MAX = 0.98
MIN_PRODUCTIVE_ROWS_AT_ROW_MAX = 18
PRODUCTIVE_SIZE_MEDIAN_MAX = 1.00
MAX_PRODUCTIVE_ROW = 1.10
CONTROL_SIZE_MEDIAN_MAX = 1.03


class Segment(ctypes.Structure):
    _fields_ = [
        ("start", ctypes.c_uint32),
        ("length", ctypes.c_uint32),
        ("kind", ctypes.c_uint8),
    ]


class SegmentStats(ctypes.Structure):
    _fields_ = [
        ("compared_target_bytes", ctypes.c_uint64),
        ("segments", ctypes.c_uint64),
    ]


def _build_native():
    here = Path(__file__).parent
    td = tempfile.TemporaryDirectory(prefix="cmpct-one-g02-e2e-emitter-")
    lib = Path(td.name) / "lib.so"
    subprocess.run(
        [
            os.environ.get("CC", "cc"), "-O3", "-std=c11", "-fPIC", "-shared",
            str(here / "one_g02_shift_branch_bound_relation_direct_kernel.c"),
            str(here / "one_g02_shift_branch_bound_relation_restrict_kernel.c"),
            str(here / "one_g02_shift_relation_safe_dispatch_kernel.c"),
            str(here / "one_g02_shift_relation_sparse_gate_kernel.c"),
            str(here / "one_g02_shift_relation_amortization_safe_gate_kernel.c"),
            str(here / "one_g02_native_segment_plan_fusion_kernel.c"),
            "-o", str(lib),
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    c = ctypes.CDLL(str(lib))
    admission = c.one_g02_shift_relation_amortization_safe_gate
    admission.argtypes = [
        ctypes.POINTER(ctypes.c_uint8), ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t,
        ctypes.POINTER(Result), ctypes.POINTER(ctypes.c_uint64), ctypes.POINTER(ctypes.c_int),
    ]
    admission.restype = ctypes.c_int

    segment = c.one_g02_segment_plan_one_pass
    segment.argtypes = [
        ctypes.POINTER(ctypes.c_uint8), ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t,
        ctypes.POINTER(Segment), ctypes.c_size_t, ctypes.POINTER(SegmentStats),
    ]
    segment.restype = ctypes.c_int
    return admission, segment, td


def _native_plan(segment_fn, src_arr, dst_arr, n: int, buf, stats: SegmentStats):
    rc = segment_fn(src_arr, dst_arr, n, buf, n, ctypes.byref(stats))
    if rc != 0:
        raise RuntimeError(f"native one-pass segmenter failed: {rc}")
    plan = []
    for i in range(int(stats.segments)):
        seg = buf[i]
        start = int(seg.start)
        length = int(seg.length)
        if int(seg.kind) == 0:
            plan.append(("ref", start, length, b""))
        elif int(seg.kind) == 1:
            # Native surprise start is a target offset.
            plan.append(("surprise", 0, length, bytes(dst_arr[start:start + length])))
        else:
            raise AssertionError("unknown native segment kind")
    return tuple(plan)


def _admit(fn, src_arr, dst_arr, n: int):
    result = Result()
    reads = ctypes.c_uint64()
    used = ctypes.c_int()
    rc = fn(src_arr, dst_arr, n, ctypes.byref(result), ctypes.byref(reads), ctypes.byref(used))
    if rc < 0:
        raise RuntimeError(f"amortization-safe relation gate failed: {rc}")
    enabled = int(result.exact_proofs) >= 4 and int(result.best_shift) == 1
    return result, int(reads.value), bool(used.value), enabled


def _writer_once(
    admission_fn,
    segment_fn,
    source: bytes,
    target: bytes,
    src_arr,
    dst_arr,
    seg_buf,
    previous_root: Root,
    current_digest: str,
    direct_emit: bool,
):
    result, gate_reads, gate_used, enabled = _admit(admission_fn, src_arr, dst_arr, len(source))
    segment_stats = SegmentStats()
    if enabled:
        plan = _native_plan(segment_fn, src_arr, dst_arr, len(source), seg_buf, segment_stats)
        program, hierarchy_depth = _program_from_plan(source, target, plan, previous_root, current_digest)
    else:
        plan = ()
        program, hierarchy_depth = _literal_program(source, target, previous_root, current_digest)

    # Validation remains a charged hard boundary in both arms.
    program.validate_shape()
    if direct_emit:
        wire, stats = _encode_program_growable_prevalidated(program)
    else:
        # Avoid charging duplicate validation only to the baseline. The ordinary encoder's
        # validation contract has already been paid immediately above in both arms.
        original = Program.validate_shape
        try:
            Program.validate_shape = lambda self: None  # type: ignore[method-assign]
            wire, stats = encode_program(program)
        finally:
            Program.validate_shape = original  # type: ignore[method-assign]
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


def _time_pair(ctx):
    baseline_samples = []
    candidate_samples = []
    baseline_value = None
    candidate_value = None
    was_enabled = gc.isenabled()
    try:
        if was_enabled:
            gc.disable()
        for round_index in range(ROUNDS):
            order = (False, True) if round_index % 2 == 0 else (True, False)
            for direct in order:
                t0 = time.perf_counter_ns()
                value = _writer_once(*ctx, direct_emit=direct)
                elapsed = time.perf_counter_ns() - t0
                if direct:
                    candidate_samples.append(elapsed)
                    candidate_value = value
                else:
                    baseline_samples.append(elapsed)
                    baseline_value = value
    finally:
        if was_enabled:
            gc.enable()
    return (
        float(statistics.median(baseline_samples)),
        baseline_value,
        float(statistics.median(candidate_samples)),
        candidate_value,
    )


def _oracle_plan(source: bytes, target: bytes):
    return _segments_plus1(source, target)


def _plan_signature(plan):
    return tuple((kind, offset, length, payload) for kind, offset, length, payload in plan)


def run():
    admission_fn, segment_fn, td = _build_native()
    rows = []
    productive_ratios = []
    productive_by_size = {size: [] for size in SIZES}
    control_by_size = {size: [] for size in SIZES}
    semantic_ok = True
    plan_oracle_ok = True
    try:
        for size in SIZES:
            cases = _relation_cases(size)
            for case in PRODUCTIVE + CONTROLS:
                source, target, expected_enable, expected_shift = cases[case]
                src_arr = (ctypes.c_uint8 * size).from_buffer_copy(source)
                dst_arr = (ctypes.c_uint8 * size).from_buffer_copy(target)
                seg_buf = (Segment * size)()
                previous_root = Root(Ref(0), len(source), sha256(source).hexdigest())
                current_digest = sha256(target).hexdigest()
                ctx = (
                    admission_fn,
                    segment_fn,
                    source,
                    target,
                    src_arr,
                    dst_arr,
                    seg_buf,
                    previous_root,
                    current_digest,
                )

                # Untimed authority path.
                baseline = _writer_once(*ctx, direct_emit=False)
                candidate = _writer_once(*ctx, direct_emit=True)
                bwire, bstats, bprogram, bresult, breads, bused, benabled, bplan, btraffic, bsegments, bdepth = baseline
                cwire, cstats, cprogram, cresult, creads, cused, cenabled, cplan, ctraffic, csegments, cdepth = candidate

                wire_equal = bwire == cwire and bstats == cstats
                classification_equal = (
                    benabled == cenabled
                    and int(bresult.best_shift) == int(cresult.best_shift)
                    and int(bresult.exact_proofs) == int(cresult.exact_proofs)
                )
                plan_equal = _plan_signature(bplan) == _plan_signature(cplan)
                if benabled:
                    oracle = _oracle_plan(source, target)
                    this_plan_oracle = _plan_signature(bplan) == _plan_signature(oracle)
                else:
                    this_plan_oracle = True
                plan_oracle_ok &= this_plan_oracle

                decoded = decode_program(cwire)
                outputs, vm_stats = evaluate(decoded)
                exact = outputs == {"previous": source, "current": target}
                semantics = wire_equal and classification_equal and plan_equal and exact
                semantic_ok &= semantics
                if not semantics:
                    raise AssertionError("end-to-end direct emitter changed writer semantics")

                baseline_ns, baseline_timed, candidate_ns, candidate_timed = _time_pair(ctx)
                if baseline_timed is None or candidate_timed is None:
                    raise AssertionError("missing timed writer result")
                if baseline_timed[0] != candidate_timed[0] or baseline_timed[1] != candidate_timed[1]:
                    raise AssertionError("timed writer paths changed canonical bytes/stats")
                ratio = candidate_ns / baseline_ns
                if case in PRODUCTIVE:
                    productive_ratios.append(ratio)
                    productive_by_size[size].append(ratio)
                else:
                    control_by_size[size].append(ratio)

                rows.append({
                    "relation_bytes": size,
                    "case": case,
                    "expected_enable": expected_enable,
                    "expected_shift": expected_shift,
                    "relation_enabled": cenabled,
                    "best_shift": int(cresult.best_shift),
                    "exact_proofs": int(cresult.exact_proofs),
                    "gate_compared_bytes": creads,
                    "used_sparse_gate": cused,
                    "native_segment_compared_target_bytes": ctraffic,
                    "segments": csegments,
                    "modeled_segment_plan_bytes": csegments * ctypes.sizeof(Segment),
                    "plan_matches_python_oracle": this_plan_oracle,
                    "hierarchy_depth": cdepth,
                    "program_nodes": len(cprogram.nodes),
                    "canonical_wire_bytes": cstats.total_bytes,
                    "surprise_bytes": cstats.surprise_bytes,
                    "control_integrity_bytes": cstats.control_integrity_bytes,
                    "reader_work_bytes": vm_stats.work_bytes,
                    "reader_materialized_bytes": vm_stats.materialized_bytes,
                    "baseline_full_writer_median_ns": baseline_ns,
                    "candidate_direct_emit_full_writer_median_ns": candidate_ns,
                    "candidate_over_baseline": ratio,
                    "wire_equal": wire_equal,
                    "exact_reconstruction": exact,
                })

        productive_median = float(statistics.median(productive_ratios))
        productive_good = sum(r <= PRODUCTIVE_ROW_MAX for r in productive_ratios)
        productive_size_medians = {
            str(size): float(statistics.median(productive_by_size[size])) for size in SIZES
        }
        control_size_medians = {
            str(size): float(statistics.median(control_by_size[size])) for size in SIZES
        }
        worst_productive = max(productive_ratios)
        worst_control_size = max(control_size_medians.values())
        perf_ok = (
            productive_median <= PRODUCTIVE_MEDIAN_MAX
            and productive_good >= MIN_PRODUCTIVE_ROWS_AT_ROW_MAX
            and all(v <= PRODUCTIVE_SIZE_MEDIAN_MAX for v in productive_size_medians.values())
            and worst_productive <= MAX_PRODUCTIVE_ROW
            and worst_control_size <= CONTROL_SIZE_MEDIAN_MAX
        )
        if not semantic_ok or not plan_oracle_ok:
            decision = "invalidate_end_to_end_direct_emitter_writer"
        elif perf_ok:
            decision = "advance_end_to_end_direct_emitter_writer"
        else:
            decision = "hold_end_to_end_direct_emitter_writer"
        return {
            "schema": "cmpct-one-g02-end-to-end-direct-emitter-writer-v1",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "frozen_rounds": ROUNDS,
            "timing_order": "alternating A/B-B/A",
            "semantic_gates_pass": semantic_ok,
            "native_plan_oracle_pass": plan_oracle_ok,
            "productive_median_ratio": productive_median,
            "productive_rows_at_or_below_0_98": productive_good,
            "productive_size_median_ratios": productive_size_medians,
            "control_size_median_ratios": control_size_medians,
            "worst_productive_ratio": worst_productive,
            "worst_control_size_median_ratio": worst_control_size,
            "decision": decision,
            "claim_boundary": (
                "adjacent-version research writer after root identities are available; charges relation admission, "
                "native one-pass segmentation, bounded Program construction, validation and canonical emission; "
                "does not establish arbitrary discovery, root-hash observation cost, native/product writer speed, "
                "authenticated selective access, recovery, portability or v0.29/v0.30 supremacy"
            ),
            "rows": rows,
        }
    finally:
        td.cleanup()


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["decision"] == "advance_end_to_end_direct_emitter_writer" else 1)
