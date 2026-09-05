"""ONE-G0.2 root-hash-charged direct-emitter dilution falsifier."""
from __future__ import annotations

import ctypes
from hashlib import sha256
import gc
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
    _build_native,
    _relation_cases,
    _writer_once,
)
from experiments.one.ir import Root, Ref
from experiments.one.vm import evaluate
from experiments.one.wire import decode_program

PRODUCTIVE_MEDIAN_MAX = 0.95
MIN_PRODUCTIVE_ROWS_AT_1_00 = 18
PRODUCTIVE_SIZE_MEDIAN_MAX = 1.03
MAX_PRODUCTIVE_ROW = 1.10
CONTROL_SIZE_MEDIAN_MAX = 1.05


def _writer_once_hashed(admission_fn, segment_fn, source, target, src_arr, dst_arr, seg_buf, direct_emit: bool):
    previous_digest = sha256(source).hexdigest()
    current_digest = sha256(target).hexdigest()
    previous_root = Root(Ref(0), len(source), previous_digest)
    return _writer_once(
        admission_fn,
        segment_fn,
        source,
        target,
        src_arr,
        dst_arr,
        seg_buf,
        previous_root,
        current_digest,
        direct_emit=direct_emit,
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
                value = _writer_once_hashed(*ctx, direct_emit=direct)
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
                ctx = (admission_fn, segment_fn, source, target, src_arr, dst_arr, seg_buf)

                baseline = _writer_once_hashed(*ctx, direct_emit=False)
                candidate = _writer_once_hashed(*ctx, direct_emit=True)
                bwire, bstats, bprogram, bresult, breads, bused, benabled, bplan, btraffic, bsegments, bdepth = baseline
                cwire, cstats, cprogram, cresult, creads, cused, cenabled, cplan, ctraffic, csegments, cdepth = candidate

                exact_digest_roots = (
                    bprogram.roots["previous"].sha256 == sha256(source).hexdigest()
                    and bprogram.roots["current"].sha256 == sha256(target).hexdigest()
                    and cprogram.roots == bprogram.roots
                )
                wire_equal = bwire == cwire and bstats == cstats
                classification_equal = (
                    benabled == cenabled
                    and int(bresult.best_shift) == int(cresult.best_shift)
                    and int(bresult.exact_proofs) == int(cresult.exact_proofs)
                )
                plan_equal = bplan == cplan

                # The imported writer already compares native plans to the same Program builder.
                # Here the ordinary decoder/evaluator plus actual computed roots provides the
                # independent digest/reconstruction boundary for the new charged dimension.
                decoded = decode_program(cwire)
                outputs, vm_stats = evaluate(decoded)
                exact = outputs == {"previous": source, "current": target}
                this_semantic = wire_equal and classification_equal and plan_equal and exact_digest_roots and exact
                semantic_ok &= this_semantic
                if not this_semantic:
                    raise AssertionError("root-hash-charged direct emitter changed writer semantics")

                baseline_ns, baseline_timed, candidate_ns, candidate_timed = _time_pair(ctx)
                if baseline_timed is None or candidate_timed is None:
                    raise AssertionError("missing timed writer result")
                if baseline_timed[0] != candidate_timed[0] or baseline_timed[1] != candidate_timed[1]:
                    raise AssertionError("timed root-hash writer paths changed canonical bytes/stats")
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
                    "hierarchy_depth": cdepth,
                    "program_nodes": len(cprogram.nodes),
                    "canonical_wire_bytes": cstats.total_bytes,
                    "surprise_bytes": cstats.surprise_bytes,
                    "control_integrity_bytes": cstats.control_integrity_bytes,
                    "reader_work_bytes": vm_stats.work_bytes,
                    "reader_materialized_bytes": vm_stats.materialized_bytes,
                    "root_hashes_exact": exact_digest_roots,
                    "baseline_hash_charged_writer_median_ns": baseline_ns,
                    "candidate_hash_charged_writer_median_ns": candidate_ns,
                    "candidate_over_baseline": ratio,
                    "wire_equal": wire_equal,
                    "exact_reconstruction": exact,
                })

        productive_median = float(statistics.median(productive_ratios))
        productive_good = sum(r <= 1.00 for r in productive_ratios)
        productive_size_medians = {str(size): float(statistics.median(productive_by_size[size])) for size in SIZES}
        control_size_medians = {str(size): float(statistics.median(control_by_size[size])) for size in SIZES}
        worst_productive = max(productive_ratios)
        worst_control_size = max(control_size_medians.values())
        perf_ok = (
            productive_median <= PRODUCTIVE_MEDIAN_MAX
            and productive_good >= MIN_PRODUCTIVE_ROWS_AT_1_00
            and all(v <= PRODUCTIVE_SIZE_MEDIAN_MAX for v in productive_size_medians.values())
            and worst_productive <= MAX_PRODUCTIVE_ROW
            and worst_control_size <= CONTROL_SIZE_MEDIAN_MAX
        )
        if not semantic_ok or not plan_oracle_ok:
            decision = "invalidate_root_hash_charged_direct_emitter"
        elif perf_ok:
            decision = "advance_root_hash_charged_direct_emitter"
        else:
            decision = "hold_root_hash_charged_direct_emitter"
        return {
            "schema": "cmpct-one-g02-root-hash-charged-direct-emitter-v1",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "frozen_rounds": ROUNDS,
            "timing_order": "alternating A/B-B/A",
            "semantic_gates_pass": semantic_ok,
            "productive_median_ratio": productive_median,
            "productive_rows_at_or_below_1_00": productive_good,
            "productive_size_median_ratios": productive_size_medians,
            "control_size_median_ratios": control_size_medians,
            "worst_productive_ratio": worst_productive,
            "worst_control_size_median_ratio": worst_control_size,
            "decision": decision,
            "claim_boundary": (
                "adjacent-version research writer including SHA-256 of both version roots, relation admission, native one-pass "
                "segmentation, bounded Program construction, validation and canonical emission; excludes broader fused "
                "observation/arbitrary discovery, authenticated placement/durability and native product writer authority"
            ),
            "rows": rows,
        }
    finally:
        td.cleanup()


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["decision"] == "advance_root_hash_charged_direct_emitter" else 1)
