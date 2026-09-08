"""ONE-G0.2 one-slot small-vector observer whole-writer falsifier."""
from __future__ import annotations

import argparse
import ctypes
import gc
from hashlib import sha256
import json
import os
import statistics
import subprocess
import sys
import time

from benchmarks.one.one_g02_compact_observer_handoff_writer import (
    FAMILIES,
    Segment,
    SegmentStats,
    _admit,
    _build_native,
    _case,
    _native_plan,
    _plan_signature,
)
from benchmarks.one.one_g02_post_segment_control_cost_owner import _literal_program
from experiments.one.bounded_surprise_pool import program_from_plan_pooled
from experiments.one.growable_wire import _encode_program_growable_prevalidated
from experiments.one.ir import Ref, Root
from experiments.one.native_observe import _CRun, _CReuse, observe_native
from experiments.one.native_observe_small_vector import SmallVectorObservationView, observe_native_small_vector
from experiments.one.vm import evaluate
from experiments.one.wire import decode_program

SIZES = (256 << 10, 384 << 10, 512 << 10, 768 << 10, 1 << 20)
REPETITIONS = 21
NO_REGRESSION_MAX = 1.05
STRUCTURED_GAIN_MAX = 0.60


def _writer_once(admission_fn, segment_fn, source, target, src_arr, dst_arr, seg_buf, hybrid: bool):
    previous_digest = sha256(source).hexdigest()
    current_digest = sha256(target).hexdigest()
    previous_root = Root(Ref(0), len(source), previous_digest)

    observer = observe_native_small_vector(target) if hybrid else observe_native(target)
    result, gate_reads, gate_used, enabled = _admit(admission_fn, src_arr, dst_arr, len(source))
    segment_stats = SegmentStats()
    if enabled:
        plan = _native_plan(segment_fn, src_arr, dst_arr, len(source), seg_buf, segment_stats)
        program, pool_stats = program_from_plan_pooled(source, target, plan, previous_root, current_digest)
        hierarchy_depth = pool_stats.hierarchy_depth
    else:
        plan = ()
        program, hierarchy_depth = _literal_program(source, target, previous_root, current_digest)
    program.validate_shape()
    wire, wire_stats = _encode_program_growable_prevalidated(program)

    if hybrid:
        assert isinstance(observer, SmallVectorObservationView)
        counts = (observer.run_count, observer.reuse_count)
        capacity = observer.native_output_capacity_bytes
        used = observer.native_output_used_bytes
        retained = observer.retained_output_bytes
        inline = observer.uses_inline_slot
        bulk = observer.uses_bulk_bytes
    else:
        counts = (len(observer.runs), len(observer.reuse))
        run_capacity = max(1, len(target) // 8 + 2)
        reuse_capacity = max(1, len(target) // 64 + 2)
        capacity = run_capacity * ctypes.sizeof(_CRun) + reuse_capacity * ctypes.sizeof(_CReuse)
        used = counts[0] * ctypes.sizeof(_CRun) + counts[1] * ctypes.sizeof(_CReuse)
        retained = 0
        inline = False
        bulk = False
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
        "observer_counts": counts,
        "observer_capacity_bytes": capacity,
        "observer_used_bytes": used,
        "observer_retained_bytes": retained,
        "observer_inline": inline,
        "observer_bulk": bulk,
    }


def _same(a, b) -> bool:
    return (
        a["wire"] == b["wire"]
        and a["wire_stats"] == b["wire_stats"]
        and a["program"] == b["program"]
        and a["relation_signature"] == b["relation_signature"]
        and a["plan_signature"] == b["plan_signature"]
        and a["hierarchy_depth"] == b["hierarchy_depth"]
        and a["segments"] == b["segments"]
        and a["observer_counts"] == b["observer_counts"]
    )


def _child(size: int, family: str) -> dict:
    source, target = _case(family, size)
    admission_fn, segment_fn, td = _build_native()
    try:
        src_arr = (ctypes.c_uint8 * size).from_buffer_copy(source)
        dst_arr = (ctypes.c_uint8 * size).from_buffer_copy(target)
        seg_buf = (Segment * size)()
        reference_observation = observe_native(target)
        hybrid_authority = observe_native_small_vector(target)
        observer_exact = hybrid_authority.materialize() == reference_observation
        total_count = len(reference_observation.runs) + len(reference_observation.reuse)
        storage_exact = (
            hybrid_authority.uses_inline_slot == (total_count == 1)
            and hybrid_authority.uses_bulk_bytes == (total_count > 1)
        )
        eager_authority = _writer_once(admission_fn, segment_fn, source, target, src_arr, dst_arr, seg_buf, False)
        hybrid_result = _writer_once(admission_fn, segment_fn, source, target, src_arr, dst_arr, seg_buf, True)
        writer_exact = _same(eager_authority, hybrid_result)
        outputs, vm_stats = evaluate(decode_program(hybrid_result["wire"]))
        reconstruction_exact = outputs == {"previous": source, "current": target}
        roots_exact = (
            hybrid_result["program"].roots["previous"].sha256 == sha256(source).hexdigest()
            and hybrid_result["program"].roots["current"].sha256 == sha256(target).hexdigest()
        )
        semantic_ok = observer_exact and storage_exact and writer_exact and reconstruction_exact and roots_exact
        if not semantic_ok:
            raise AssertionError(f"small-vector semantic mismatch: {size=} {family=}")

        eager_wall = []
        eager_cpu = []
        hybrid_wall = []
        hybrid_cpu = []
        last_eager = last_hybrid = None
        was_enabled = gc.isenabled()
        try:
            if was_enabled:
                gc.disable()
            for rep in range(REPETITIONS):
                order = (False, True) if rep % 2 == 0 else (True, False)
                for hybrid in order:
                    if hybrid:
                        last_hybrid = None
                    else:
                        last_eager = None
                    c0 = time.process_time_ns()
                    w0 = time.perf_counter_ns()
                    value = _writer_once(admission_fn, segment_fn, source, target, src_arr, dst_arr, seg_buf, hybrid)
                    w1 = time.perf_counter_ns()
                    c1 = time.process_time_ns()
                    if hybrid:
                        last_hybrid = value
                        hybrid_wall.append(w1 - w0)
                        hybrid_cpu.append(c1 - c0)
                    else:
                        last_eager = value
                        eager_wall.append(w1 - w0)
                        eager_cpu.append(c1 - c0)
        finally:
            if was_enabled:
                gc.enable()
        if last_eager is None or last_hybrid is None or not _same(last_eager, last_hybrid):
            raise AssertionError("small-vector timed writer mismatch")
        ew = float(statistics.median(eager_wall))
        ec = float(statistics.median(eager_cpu))
        hw = float(statistics.median(hybrid_wall))
        hc = float(statistics.median(hybrid_cpu))
        return {
            "bytes": size,
            "family": family,
            "semantic_ok": semantic_ok,
            "observer_run_count": hybrid_result["observer_counts"][0],
            "observer_reuse_count": hybrid_result["observer_counts"][1],
            "observer_total_count": total_count,
            "observer_inline": hybrid_result["observer_inline"],
            "observer_bulk": hybrid_result["observer_bulk"],
            "observer_capacity_bytes": hybrid_result["observer_capacity_bytes"],
            "observer_used_bytes": hybrid_result["observer_used_bytes"],
            "observer_retained_bytes": hybrid_result["observer_retained_bytes"],
            "canonical_wire_bytes": hybrid_result["wire_stats"].total_bytes,
            "surprise_bytes": hybrid_result["wire_stats"].surprise_bytes,
            "reader_work_bytes": vm_stats.work_bytes,
            "eager_wall_median_ns": ew,
            "eager_cpu_median_ns": ec,
            "hybrid_wall_median_ns": hw,
            "hybrid_cpu_median_ns": hc,
            "hybrid_over_eager_wall": hw / ew,
            "hybrid_over_eager_cpu": hc / ec,
        }
    finally:
        td.cleanup()


def _invoke(size: int, family: str) -> dict:
    proc = subprocess.run(
        [sys.executable, "-m", "benchmarks.one.one_g02_small_vector_observer", "--child", str(size), family],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    if not lines:
        raise RuntimeError("small-vector child produced no JSON")
    return json.loads(lines[-1])


def run() -> dict:
    rows = [_invoke(size, family) for size in SIZES for family in FAMILIES]
    semantic_ok = all(row["semantic_ok"] for row in rows)
    all_no_regression = all(
        row["hybrid_over_eager_wall"] <= NO_REGRESSION_MAX
        and row["hybrid_over_eager_cpu"] <= NO_REGRESSION_MAX
        for row in rows
    )
    near_no_regression = all(
        row["hybrid_over_eager_wall"] <= NO_REGRESSION_MAX
        and row["hybrid_over_eager_cpu"] <= NO_REGRESSION_MAX
        for row in rows if row["family"] == "near_repeats"
    )
    structured_1m = next(row for row in rows if row["family"] == "structured" and row["bytes"] == (1 << 20))
    structured_gain = (
        structured_1m["hybrid_over_eager_wall"] <= STRUCTURED_GAIN_MAX
        and structured_1m["hybrid_over_eager_cpu"] <= STRUCTURED_GAIN_MAX
    )
    if not semantic_ok:
        decision = "INVALIDATE_SMALL_VECTOR_OBSERVER"
    elif all_no_regression and near_no_regression and structured_gain:
        decision = "ADVANCE_SMALL_VECTOR_OBSERVER"
    else:
        decision = "HOLD_SMALL_VECTOR_OBSERVER"
    return {
        "schema": "cmpct-one-g02-small-vector-observer-v1",
        "experimental_version": "ONE-G0.2",
        "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
        "sizes": list(SIZES),
        "families": list(FAMILIES),
        "repetitions_per_fresh_row": REPETITIONS,
        "no_regression_max": NO_REGRESSION_MAX,
        "structured_gain_max": STRUCTURED_GAIN_MAX,
        "semantic_gates_pass": semantic_ok,
        "all_rows_no_regression": all_no_regression,
        "near_repeats_no_regression": near_no_regression,
        "structured_gain_retained_1m": structured_gain,
        "decision": decision,
        "claim_boundary": (
            "writer-internal one-slot small-vector handoff only; row-isolated subprocess timing; same native scan/"
            "writer semantics; no source-size selector, stored-format, reader, RSS, durability, recovery, portability, "
            "or v0.29/v0.30 authority"
        ),
        "rows": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--child", nargs=2, metavar=("SIZE", "FAMILY"))
    args = parser.parse_args()
    if args.child:
        size_s, family = args.child
        size = int(size_s)
        if size not in SIZES or family not in FAMILIES:
            return 2
        print(json.dumps(_child(size, family), sort_keys=True))
        return 0
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["decision"] == "ADVANCE_SMALL_VECTOR_OBSERVER" else 1


if __name__ == "__main__":
    raise SystemExit(main())
