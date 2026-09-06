"""Memory-only falsifier for the ONE-G0.2 plan-direct writer.

Frozen by ONE_G02_ROOT_HASH_WRITER_PLAN_DIRECT_MEMORY_PREREG_2026-09-06.md.
Measures Python traced peak allocation only; no timing claims.
"""
from __future__ import annotations

import ctypes
import gc
import json
import statistics
import tracemalloc

import benchmarks.one.one_g02_root_hash_writer_plan_direct_wire as v1
from benchmarks.one.one_g02_end_to_end_direct_emitter_writer import (
    CONTROLS,
    PRODUCTIVE,
    SIZES,
    Segment,
    _build_native,
    _oracle_plan,
    _plan_signature,
    _relation_cases,
)
from benchmarks.one.one_g02_root_hash_writer_coarse_attribution import _writer_once_direct_unprofiled
from benchmarks.one.one_g02_root_hash_writer_plan_direct_wire_v2 import _candidate_once_v2
from experiments.one.vm import evaluate
from experiments.one.wire import decode_program

SAMPLES = 9
MATURE_MIN = 64 * 1024
PRODUCTIVE_MEDIAN_MAX = 0.80
PRODUCTIVE_ROW_MAX = 1.03
PRODUCTIVE_ABS_SAVING_MIN = 32 * 1024
CONTROL_MEDIAN_MAX = 1.03
CONTROL_ROW_MAX = 1.08


def _semantic_audit(baseline, candidate, source, target):
    bwire, bstats, bprogram, bresult, _br, _bu, benabled, bplan, btraffic, bsegments, bdepth = baseline
    cwire, cstats, cresult, _cr, _cu, cenabled, cplan, ctraffic, csegments, cdepth, cnode_count = candidate
    out, _ = evaluate(decode_program(cwire))
    oracle_ok = (not benabled) or (_plan_signature(bplan) == _plan_signature(_oracle_plan(source, target)))
    return (
        bwire == cwire
        and bstats == cstats
        and benabled == cenabled
        and int(bresult.best_shift) == int(cresult.best_shift)
        and int(bresult.exact_proofs) == int(cresult.exact_proofs)
        and _plan_signature(bplan) == _plan_signature(cplan)
        and btraffic == ctraffic
        and bsegments == csegments
        and bdepth == cdepth
        and len(bprogram.nodes) == cnode_count
        and oracle_ok
        and out == {"previous": source, "current": target}
    )


def _peak_once(fn, ctx):
    gc.collect()
    tracemalloc.start()
    try:
        value = fn(*ctx)
        _current, peak = tracemalloc.get_traced_memory()
        return int(peak), value
    finally:
        tracemalloc.stop()


def _measure_pair(ctx):
    baseline_peaks = []
    candidate_peaks = []
    for i in range(SAMPLES):
        order = (False, True) if i % 2 == 0 else (True, False)
        for candidate in order:
            fn = _candidate_once_v2 if candidate else _writer_once_direct_unprofiled
            peak, value = _peak_once(fn, ctx)
            if candidate:
                candidate_peaks.append(peak)
            else:
                baseline_peaks.append(peak)
            del value
    return int(statistics.median(baseline_peaks)), int(statistics.median(candidate_peaks))


def run():
    admission_fn, segment_fn, td = _build_native()
    rows = []
    semantic_failures = 0
    mature_productive_ratios = []
    mature_productive_savings = []
    mature_control_ratios = []
    try:
        for size in SIZES:
            cases = _relation_cases(size)
            for case in PRODUCTIVE + CONTROLS:
                source, target, _expected_enable, _expected_shift = cases[case]
                src_arr = (ctypes.c_uint8 * size).from_buffer_copy(source)
                dst_arr = (ctypes.c_uint8 * size).from_buffer_copy(target)
                seg_buf = (Segment * size)()
                ctx = (admission_fn, segment_fn, source, target, src_arr, dst_arr, seg_buf)

                baseline = _writer_once_direct_unprofiled(*ctx)
                candidate = _candidate_once_v2(*ctx)
                semantic_ok = _semantic_audit(baseline, candidate, source, target)
                if not semantic_ok:
                    semantic_failures += 1
                    rows.append({"relation_bytes": size, "case": case, "semantic_ok": False})
                    continue
                del baseline, candidate

                baseline_peak, candidate_peak = _measure_pair(ctx)
                ratio = candidate_peak / baseline_peak if baseline_peak else 1.0
                saving = baseline_peak - candidate_peak
                row = {
                    "relation_bytes": size,
                    "case": case,
                    "semantic_ok": True,
                    "baseline_traced_peak_bytes": baseline_peak,
                    "candidate_traced_peak_bytes": candidate_peak,
                    "candidate_over_baseline": ratio,
                    "absolute_saving_bytes": saving,
                }
                rows.append(row)
                if size >= MATURE_MIN:
                    if case in PRODUCTIVE:
                        mature_productive_ratios.append(ratio)
                        mature_productive_savings.append(saving)
                    else:
                        mature_control_ratios.append(ratio)
    finally:
        td.cleanup()

    productive_median = float(statistics.median(mature_productive_ratios)) if mature_productive_ratios else 1.0
    productive_saving_median = float(statistics.median(mature_productive_savings)) if mature_productive_savings else 0.0
    control_median = float(statistics.median(mature_control_ratios)) if mature_control_ratios else 1.0
    productive_worst = max(mature_productive_ratios, default=1.0)
    control_worst = max(mature_control_ratios, default=1.0)

    if semantic_failures:
        decision = "invalidate_plan_direct_creator_memory_claim"
    elif (
        productive_median <= PRODUCTIVE_MEDIAN_MAX
        and productive_worst <= PRODUCTIVE_ROW_MAX
        and productive_saving_median >= PRODUCTIVE_ABS_SAVING_MIN
        and control_median <= CONTROL_MEDIAN_MAX
        and control_worst <= CONTROL_ROW_MAX
    ):
        decision = "advance_plan_direct_creator_memory_claim"
    else:
        decision = "reject_plan_direct_creator_memory_claim"

    return {
        "schema": "cmpct-one-g02-root-hash-writer-plan-direct-memory",
        "decision": decision,
        "measurement_scope": "creator-side Python traced peak allocation only",
        "samples_per_arm": SAMPLES,
        "semantic_failures": semantic_failures,
        "mature_productive_median_ratio": productive_median,
        "mature_productive_worst_ratio": productive_worst,
        "mature_productive_median_absolute_saving_bytes": productive_saving_median,
        "mature_control_median_ratio": control_median,
        "mature_control_worst_ratio": control_worst,
        "gates": {
            "productive_median_max": PRODUCTIVE_MEDIAN_MAX,
            "productive_row_max": PRODUCTIVE_ROW_MAX,
            "productive_median_absolute_saving_min_bytes": PRODUCTIVE_ABS_SAVING_MIN,
            "control_median_max": CONTROL_MEDIAN_MAX,
            "control_row_max": CONTROL_ROW_MAX,
        },
        "rows": rows,
    }


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["decision"] == "advance_plan_direct_creator_memory_claim" else 1)
