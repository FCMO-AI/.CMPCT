"""ONE-G0.2 sized single-buffer canonical emitter falsifier.

Frozen by ONE_G02_BULK_CANONICAL_EMITTER_PREREG_2026-09-05.md and its
pre-result timing-method amendment. Segment discovery and Program construction
are outside the timed region. Both timing paths receive the same already-valid
Program so this experiment isolates canonical byte emission only.
"""
from __future__ import annotations

import gc
from hashlib import sha256
import json
import os
import statistics
import time

from benchmarks.one.one_g02_post_segment_control_cost_owner import (
    CONTROLS,
    PRODUCTIVE,
    SIZES,
    _literal_program,
    _program_from_plan,
    _segments_plus1,
)
from benchmarks.one.one_g02_shift_branch_bound_relation_transfer import _relation_cases
from experiments.one.bulk_wire import _encode_program_bulk_prevalidated
from experiments.one.ir import Program, Ref, Root
from experiments.one.vm import evaluate
from experiments.one.wire import decode_program, encode_program

ROUNDS = 51
PRODUCTIVE_MEDIAN_MAX = 0.80
PRODUCTIVE_ROW_MAX = 0.90
MIN_PRODUCTIVE_ROWS_AT_ROW_MAX = 18
SIZE_MEDIAN_MAX = 0.90
NO_REGRESSION_MAX = 1.03


def _timed_call(fn):
    t0 = time.perf_counter_ns()
    value = fn()
    return time.perf_counter_ns() - t0, value


def _measure_pair(program: Program):
    """Measure baseline/candidate in alternating A/B-B/A order.

    Validation is performed before the timed region. The baseline encoder's
    internal duplicate validation is suppressed for the complete paired run,
    exactly matching the parent cost-owner experiment's prevalidated-emission
    boundary. Alternating order prevents warm-cache/frequency drift from being
    assigned systematically to either implementation.
    """
    program.validate_shape()
    baseline_samples = []
    candidate_samples = []
    baseline_value = None
    candidate_value = None
    enabled = gc.isenabled()
    original = Program.validate_shape
    try:
        if enabled:
            gc.disable()
        Program.validate_shape = lambda self: None  # type: ignore[method-assign]
        for round_index in range(ROUNDS):
            if round_index % 2 == 0:
                elapsed, baseline_value = _timed_call(lambda: encode_program(program))
                baseline_samples.append(elapsed)
                elapsed, candidate_value = _timed_call(lambda: _encode_program_bulk_prevalidated(program))
                candidate_samples.append(elapsed)
            else:
                elapsed, candidate_value = _timed_call(lambda: _encode_program_bulk_prevalidated(program))
                candidate_samples.append(elapsed)
                elapsed, baseline_value = _timed_call(lambda: encode_program(program))
                baseline_samples.append(elapsed)
    finally:
        Program.validate_shape = original  # type: ignore[method-assign]
        if enabled:
            gc.enable()
    return (
        float(statistics.median(baseline_samples)),
        baseline_value,
        float(statistics.median(candidate_samples)),
        candidate_value,
    )


def _program_for_case(source: bytes, target: bytes, generic: bool):
    # Keep construction identical to the parent profiler while leaving it untimed.
    prev = Root(Ref(0), len(source), sha256(source).hexdigest())
    digest = sha256(target).hexdigest()
    if generic:
        return _program_from_plan(source, target, _segments_plus1(source, target), prev, digest)[0]
    return _literal_program(source, target, prev, digest)[0]


def run():
    rows = []
    semantic_ok = True
    productive_ratios = []
    control_ratios = []
    productive_by_size = {size: [] for size in SIZES}
    control_by_size = {size: [] for size in SIZES}

    for size in SIZES:
        cases = _relation_cases(size)
        for case in PRODUCTIVE + CONTROLS:
            source, target, expected_enable, expected_shift = cases[case]
            generic = case in PRODUCTIVE
            program = _program_for_case(source, target, generic)
            program.validate_shape()

            canonical_wire, canonical_stats = encode_program(program)
            candidate_wire, candidate_stats = _encode_program_bulk_prevalidated(program)
            if candidate_wire != canonical_wire or candidate_stats != canonical_stats:
                raise AssertionError("bulk emitter changed canonical ONE bytes or stats")
            decoded = decode_program(candidate_wire)
            outputs, vm_stats = evaluate(decoded)
            exact = outputs == {"previous": source, "current": target}
            if not exact:
                raise AssertionError("bulk emitter canonical reconstruction mismatch")

            baseline_ns, baseline_value, candidate_ns, candidate_value = _measure_pair(program)
            if baseline_value != candidate_value:
                raise AssertionError("timed bulk emitter output differs from canonical baseline")
            ratio = candidate_ns / baseline_ns
            row = {
                "relation_bytes": size,
                "case": case,
                "generic_relation_program": generic,
                "expected_relation_enable": expected_enable,
                "expected_shift": expected_shift,
                "baseline_prevalidated_emit_median_ns": baseline_ns,
                "candidate_bulk_emit_median_ns": candidate_ns,
                "candidate_over_baseline": ratio,
                "canonical_wire_bytes": canonical_stats.total_bytes,
                "surprise_bytes": canonical_stats.surprise_bytes,
                "control_integrity_bytes": canonical_stats.control_integrity_bytes,
                "program_nodes": len(program.nodes),
                "reader_work_bytes": vm_stats.work_bytes,
                "reader_materialized_bytes": vm_stats.materialized_bytes,
                "exact_reconstruction": exact,
            }
            rows.append(row)
            semantic_ok &= exact
            if generic:
                productive_ratios.append(ratio)
                productive_by_size[size].append(ratio)
            else:
                control_ratios.append(ratio)
                control_by_size[size].append(ratio)

    productive_median = float(statistics.median(productive_ratios))
    productive_rows_good = sum(r <= PRODUCTIVE_ROW_MAX for r in productive_ratios)
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
        and productive_rows_good >= MIN_PRODUCTIVE_ROWS_AT_ROW_MAX
        and all(v <= SIZE_MEDIAN_MAX for v in productive_size_medians.values())
        and worst_productive <= NO_REGRESSION_MAX
        and worst_control_size <= NO_REGRESSION_MAX
    )
    decision = "advance_bulk_canonical_emitter" if semantic_ok and perf_ok else "retire_bulk_canonical_emitter"
    result = {
        "schema": "cmpct-one-g02-bulk-canonical-emitter-v2-paired-order",
        "experimental_version": "ONE-G0.2",
        "source_sha": os.environ.get("EVIDENCE_HEAD", "local"),
        "claim_boundary": "Python research-harness canonical-emission evidence only; Program construction and discovery untimed; no native/product, auth/recovery or comparator authority",
        "frozen_rounds": ROUNDS,
        "timing_order": "alternating A/B-B/A",
        "semantic_gates_pass": semantic_ok,
        "productive_median_ratio": productive_median,
        "productive_rows_at_or_below_0_90": productive_rows_good,
        "productive_size_median_ratios": productive_size_medians,
        "control_size_median_ratios": control_size_medians,
        "worst_productive_ratio": worst_productive,
        "worst_control_size_median_ratio": worst_control_size,
        "decision": decision,
        "rows": rows,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    if not semantic_ok or not perf_ok:
        raise SystemExit(1)


if __name__ == "__main__":
    run()
