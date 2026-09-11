"""ONE-G0.2 lazy Segment scheduling under a broader charged ingest envelope.

Frozen by ONE_G02_LAZY_SEGMENT_CHARGED_INGEST_PREREG_2026-09-08.md.
"""
from __future__ import annotations

import ctypes
import gc
from hashlib import sha256
import json
import os
import statistics
import time

from benchmarks.one.one_g02_end_to_end_direct_emitter_writer import _build_native
from benchmarks.one.one_g02_lazy_segment_timing import (
    ADMITTED,
    REJECTED,
    Segment,
    _equivalent,
    _semantic_signature,
    _writer_once,
)
from benchmarks.one.one_g02_shift_branch_bound_relation_transfer import _relation_cases
from experiments.one.ir import Ref, Root

SIZES = (64 << 10, 1 << 20)
CASES = ADMITTED + REJECTED
REPETITIONS = 15
DECISION_SIZE = 1 << 20
ADMITTED_RATIO_MAX = 1.05
REJECTED_RATIO_MAX = 0.97
SMALL_ROW_MAX = 1.08


def _charged_writer_once(arm: str, admission_fn, segment_fn, source: bytes, target: bytes):
    n = len(source)
    src_arr = (ctypes.c_uint8 * n).from_buffer_copy(source)
    dst_arr = (ctypes.c_uint8 * n).from_buffer_copy(target)
    previous_digest = sha256(source).hexdigest()
    current_digest = sha256(target).hexdigest()
    previous_root = Root(Ref(0), n, previous_digest)
    value = _writer_once(
        arm,
        admission_fn,
        segment_fn,
        source,
        target,
        src_arr,
        dst_arr,
        previous_root,
        current_digest,
    )
    return value, previous_digest, current_digest


def _ratio(candidate: float, control: float) -> float:
    return candidate / control if control else float("inf")


def _adjudicate(rows: list[dict], semantic_ok: bool) -> tuple[str, bool, bool, bool]:
    expected = {(size, case) for size in SIZES for case in CASES}
    by_key = {(row["size"], row["case"]): row for row in rows}
    complete = set(by_key) == expected
    admitted_ok = complete and all(
        by_key[(DECISION_SIZE, case)]["lazy_over_eager_wall"] <= ADMITTED_RATIO_MAX
        and by_key[(DECISION_SIZE, case)]["lazy_over_eager_cpu"] <= ADMITTED_RATIO_MAX
        and by_key[(DECISION_SIZE, case)]["lazy_segment_capacity_bytes"]
        == by_key[(DECISION_SIZE, case)]["eager_segment_capacity_bytes"]
        for case in ADMITTED
    )
    rejected_ok = complete and all(
        by_key[(DECISION_SIZE, case)]["lazy_over_eager_wall"] <= REJECTED_RATIO_MAX
        and by_key[(DECISION_SIZE, case)]["lazy_over_eager_cpu"] <= REJECTED_RATIO_MAX
        and by_key[(DECISION_SIZE, case)]["lazy_segment_capacity_bytes"] == 0
        for case in REJECTED
    )
    small_ok = complete and all(
        by_key[(SIZES[0], case)]["lazy_over_eager_wall"] <= SMALL_ROW_MAX
        and by_key[(SIZES[0], case)]["lazy_over_eager_cpu"] <= SMALL_ROW_MAX
        for case in CASES
    )
    if not semantic_ok:
        return "INVALIDATE_LAZY_SEGMENT_CHARGED_INGEST", admitted_ok, rejected_ok, small_ok
    if admitted_ok and rejected_ok and small_ok:
        return "ADVANCE_LAZY_SEGMENT_CHARGED_INGEST", admitted_ok, rejected_ok, small_ok
    return "HOLD_LAZY_SEGMENT_CHARGED_INGEST", admitted_ok, rejected_ok, small_ok


def run() -> dict:
    admission_fn, segment_fn, td = _build_native()
    rows: list[dict] = []
    semantic_ok = True
    was_enabled = gc.isenabled()
    try:
        if was_enabled:
            gc.disable()
        for size in SIZES:
            cases = _relation_cases(size)
            for case in CASES:
                source, target, expected_enable, expected_shift = cases[case]

                eager_probe, eager_prev, eager_cur = _charged_writer_once(
                    "eager", admission_fn, segment_fn, source, target
                )
                eager_sig = _semantic_signature(eager_probe, source, target)
                eager_probe = None
                lazy_probe, lazy_prev, lazy_cur = _charged_writer_once(
                    "lazy", admission_fn, segment_fn, source, target
                )
                lazy_sig = _semantic_signature(lazy_probe, source, target)
                lazy_probe = None

                case_semantic_ok = (
                    _equivalent(eager_sig, lazy_sig)
                    and eager_sig["enabled"] == bool(expected_enable)
                    and (
                        not expected_enable
                        or expected_shift is None
                        or eager_sig["best_shift"] == expected_shift
                    )
                    and eager_prev == lazy_prev == sha256(source).hexdigest()
                    and eager_cur == lazy_cur == sha256(target).hexdigest()
                    and eager_sig["previous_sha256"] == eager_prev
                    and eager_sig["current_sha256"] == eager_cur
                    and lazy_sig["segment_capacity_bytes"]
                    == (eager_sig["segment_capacity_bytes"] if expected_enable else 0)
                )
                semantic_ok &= case_semantic_ok

                eager_capacity = int(eager_sig["segment_capacity_bytes"])
                lazy_capacity = int(lazy_sig["segment_capacity_bytes"])
                canonical_wire_bytes = int(eager_sig["wire_total_bytes"])
                surprise_bytes = int(eager_sig["surprise_bytes"])
                reader_work_bytes = int(eager_sig["reader_work_bytes"])
                eager_sig = None
                lazy_sig = None

                wall = {"eager": [], "lazy": []}
                cpu = {"eager": [], "lazy": []}
                value = None
                for rep in range(REPETITIONS):
                    order = ("eager", "lazy") if rep % 2 == 0 else ("lazy", "eager")
                    for arm in order:
                        value = None
                        t0_wall = time.perf_counter_ns()
                        t0_cpu = time.process_time_ns()
                        value = _charged_writer_once(
                            arm, admission_fn, segment_fn, source, target
                        )
                        t1_cpu = time.process_time_ns()
                        t1_wall = time.perf_counter_ns()
                        wall[arm].append(t1_wall - t0_wall)
                        cpu[arm].append(t1_cpu - t0_cpu)
                value = None

                eager_wall = float(statistics.median(wall["eager"]))
                lazy_wall = float(statistics.median(wall["lazy"]))
                eager_cpu = float(statistics.median(cpu["eager"]))
                lazy_cpu = float(statistics.median(cpu["lazy"]))
                rows.append({
                    "size": size,
                    "case": case,
                    "expected_enable": bool(expected_enable),
                    "semantic_ok": case_semantic_ok,
                    "canonical_wire_bytes": canonical_wire_bytes,
                    "surprise_bytes": surprise_bytes,
                    "reader_work_bytes": reader_work_bytes,
                    "eager_segment_capacity_bytes": eager_capacity,
                    "lazy_segment_capacity_bytes": lazy_capacity,
                    "eager_wall_ns_median": eager_wall,
                    "lazy_wall_ns_median": lazy_wall,
                    "lazy_over_eager_wall": _ratio(lazy_wall, eager_wall),
                    "eager_cpu_ns_median": eager_cpu,
                    "lazy_cpu_ns_median": lazy_cpu,
                    "lazy_over_eager_cpu": _ratio(lazy_cpu, eager_cpu),
                })
    finally:
        if was_enabled:
            gc.enable()
        td.cleanup()

    decision, admitted_ok, rejected_ok, small_ok = _adjudicate(rows, semantic_ok)
    return {
        "schema": "cmpct-one-g02-lazy-segment-charged-ingest-v1",
        "experimental_version": "ONE-G0.2",
        "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
        "sizes": list(SIZES),
        "decision_size": DECISION_SIZE,
        "repetitions": REPETITIONS,
        "semantic_gates_pass": semantic_ok,
        "admitted_gate_pass": admitted_ok,
        "rejected_gate_pass": rejected_ok,
        "small_transfer_gate_pass": small_ok,
        "decision": decision,
        "claim_boundary": (
            "research writer charges source/target ctypes conversion, SHA-256 of both roots, relation admission, "
            "conditional/eager Segment allocation, segmentation, bounded Program construction, validation, and "
            "direct canonical emission; native build, filesystem/archive traversal, authenticated placement, and "
            "decode timing remain outside scope"
        ),
        "rows": rows,
    }


def main() -> int:
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["decision"] == "ADVANCE_LAZY_SEGMENT_CHARGED_INGEST" else 1


if __name__ == "__main__":
    raise SystemExit(main())
