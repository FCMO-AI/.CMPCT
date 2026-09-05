"""ONE-G0.2 growable direct-emitter size-boundary diagnostic.

Diagnostic only: it cannot promote the growable emitter. Frozen by
ONE_G02_GROWABLE_EMITTER_BOUNDARY_DIAGNOSTIC_PREREG_2026-09-05.md.
"""
from __future__ import annotations

import gc
from hashlib import sha256
import json
import os
import statistics
import time

from benchmarks.one.one_g02_post_segment_control_cost_owner import _literal_program, _program_from_plan, _segments_plus1
from benchmarks.one.one_g02_shift_branch_bound_relation_transfer import _relation_cases
from experiments.one.growable_wire import _append_blob, _encode_program_growable_prevalidated
from experiments.one.ir import Program, Ref, Root
from experiments.one.vm import evaluate
from experiments.one.wire import MAGIC, _blob, decode_program, encode_program

SIZES = (98304, 131072, 163840, 196608, 229376, 245760, 253952, 258048, 262144, 266240, 270336, 294912, 327680)
ROUNDS = 101


def _timed(fn):
    t0 = time.perf_counter_ns()
    value = fn()
    return time.perf_counter_ns() - t0, value


def _paired(program: Program):
    program.validate_shape()
    a, b = [], []
    av = bv = None
    original = Program.validate_shape
    enabled = gc.isenabled()
    try:
        if enabled:
            gc.disable()
        Program.validate_shape = lambda self: None  # type: ignore[method-assign]
        for i in range(ROUNDS):
            if i & 1:
                dt, bv = _timed(lambda: _encode_program_growable_prevalidated(program)); b.append(dt)
                dt, av = _timed(lambda: encode_program(program)); a.append(dt)
            else:
                dt, av = _timed(lambda: encode_program(program)); a.append(dt)
                dt, bv = _timed(lambda: _encode_program_growable_prevalidated(program)); b.append(dt)
    finally:
        Program.validate_shape = original  # type: ignore[method-assign]
        if enabled:
            gc.enable()
    return float(statistics.median(a)), av, float(statistics.median(b)), bv


def _paired_blob(payload: bytes):
    a, b = [], []
    prefix = MAGIC + b"\x01\x02\x03\x04"
    enabled = gc.isenabled()
    try:
        if enabled:
            gc.disable()
        for i in range(ROUNDS):
            if i & 1:
                t0 = time.perf_counter_ns(); out_b = bytearray(prefix); _append_blob(out_b, payload); b.append(time.perf_counter_ns()-t0)
                t0 = time.perf_counter_ns(); out_a = bytearray(prefix); out_a += _blob(payload); a.append(time.perf_counter_ns()-t0)
            else:
                t0 = time.perf_counter_ns(); out_a = bytearray(prefix); out_a += _blob(payload); a.append(time.perf_counter_ns()-t0)
                t0 = time.perf_counter_ns(); out_b = bytearray(prefix); _append_blob(out_b, payload); b.append(time.perf_counter_ns()-t0)
        if out_a != out_b:
            raise AssertionError("blob diagnostic changed bytes")
    finally:
        if enabled:
            gc.enable()
    return float(statistics.median(a)), float(statistics.median(b))


def _program(source: bytes, target: bytes, generic: bool):
    prev = Root(Ref(0), len(source), sha256(source).hexdigest())
    digest = sha256(target).hexdigest()
    if generic:
        return _program_from_plan(source, target, _segments_plus1(source, target), prev, digest)[0]
    return _literal_program(source, target, prev, digest)[0]


def run():
    rows = []
    full_slow = []
    blob_slow = []
    all_full_le_103 = True
    for size in SIZES:
        cases = _relation_cases(size)
        for case, generic in (("shift_plus1", True), ("independent_random", False)):
            source, target, _enable, _shift = cases[case]
            program = _program(source, target, generic)
            baseline_wire, baseline_stats = encode_program(program)
            candidate_wire, candidate_stats = _encode_program_growable_prevalidated(program)
            if baseline_wire != candidate_wire or baseline_stats != candidate_stats:
                raise AssertionError("canonical mismatch")
            outputs, _ = evaluate(decode_program(candidate_wire))
            if outputs != {"previous": source, "current": target}:
                raise AssertionError("reconstruction mismatch")
            a_ns, a_value, b_ns, b_value = _paired(program)
            if a_value != b_value:
                raise AssertionError("timed output mismatch")
            ratio = b_ns / a_ns
            if generic:
                all_full_le_103 &= ratio <= 1.03
                if ratio >= 1.20:
                    full_slow.append(size)
            blob_a, blob_b = _paired_blob(source)
            blob_ratio = blob_b / blob_a
            if generic and blob_ratio >= 1.20:
                blob_slow.append(size)
            rows.append({
                "size": size,
                "case": case,
                "wire_bytes": baseline_stats.total_bytes,
                "surprise_bytes": baseline_stats.surprise_bytes,
                "baseline_emit_median_ns": a_ns,
                "direct_emit_median_ns": b_ns,
                "direct_over_baseline": ratio,
                "baseline_blob_median_ns": blob_a,
                "direct_blob_median_ns": blob_b,
                "direct_blob_over_baseline": blob_ratio,
            })

    neighboring_growth = any((a in full_slow and b in full_slow) for a, b in zip(SIZES, SIZES[1:]))
    corresponding_blob = any(size in blob_slow for size in full_slow)
    no_blob_slow = not blob_slow
    if neighboring_growth and corresponding_blob:
        decision = "confirm_growth_boundary"
    elif all_full_le_103 and no_blob_slow:
        decision = "classify_parent_outlier_nonrepeatable"
    else:
        decision = "hold_direct_emitter_instability"
    result = {
        "schema": "cmpct-one-g02-growable-emitter-boundary-diagnostic-v1",
        "experimental_version": "ONE-G0.2",
        "source_sha": os.environ.get("EVIDENCE_HEAD", "local"),
        "rounds": ROUNDS,
        "sizes": SIZES,
        "full_slow_sizes_ge_1_20": full_slow,
        "blob_slow_sizes_ge_1_20": blob_slow,
        "all_shift_full_rows_le_1_03": all_full_le_103,
        "decision": decision,
        "rows": rows,
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    run()
