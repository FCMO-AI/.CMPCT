"""ONE-G0.2 trusted prior-root identity reuse falsifier.

Frozen by ONE_G02_TRUSTED_PRIOR_ROOT_REUSE_PREREG_2026-09-08.md.
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
TARGET_RATIO_MAX = 0.95
TARGET_ROWS_REQUIRED = 4
DECISION_ROW_MAX = 1.02
SMALL_ROW_MAX = 1.05


def _writer_charged(
    arm: str,
    admission_fn,
    segment_fn,
    source: bytes,
    target: bytes,
    trusted_previous_digest: str,
):
    """Run one lazy writer call; arms differ only in prior-root hashing."""
    n = len(source)
    src_arr = (ctypes.c_uint8 * n).from_buffer_copy(source)
    dst_arr = (ctypes.c_uint8 * n).from_buffer_copy(target)
    if arm == "rehash_both":
        previous_digest = sha256(source).hexdigest()
    elif arm == "trusted_prior":
        previous_digest = trusted_previous_digest
    else:
        raise ValueError(f"unknown arm: {arm}")
    current_digest = sha256(target).hexdigest()
    previous_root = Root(Ref(0), n, previous_digest)
    value = _writer_once(
        "lazy",
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
    decision_rows = [by_key[(DECISION_SIZE, case)] for case in CASES] if complete else []
    wall_wins = sum(row["trusted_over_rehash_wall"] <= TARGET_RATIO_MAX for row in decision_rows)
    cpu_wins = sum(row["trusted_over_rehash_cpu"] <= TARGET_RATIO_MAX for row in decision_rows)
    target_ok = (
        complete
        and wall_wins >= TARGET_ROWS_REQUIRED
        and cpu_wins >= TARGET_ROWS_REQUIRED
    )
    decision_guard_ok = complete and all(
        row["trusted_over_rehash_wall"] <= DECISION_ROW_MAX
        and row["trusted_over_rehash_cpu"] <= DECISION_ROW_MAX
        for row in decision_rows
    )
    small_ok = complete and all(
        by_key[(SIZES[0], case)]["trusted_over_rehash_wall"] <= SMALL_ROW_MAX
        and by_key[(SIZES[0], case)]["trusted_over_rehash_cpu"] <= SMALL_ROW_MAX
        for case in CASES
    )
    if not semantic_ok:
        return "INVALIDATE_TRUSTED_PRIOR_ROOT_REUSE", target_ok, decision_guard_ok, small_ok
    if target_ok and decision_guard_ok and small_ok:
        return "ADVANCE_TRUSTED_PRIOR_ROOT_REUSE", target_ok, decision_guard_ok, small_ok
    return "HOLD_TRUSTED_PRIOR_ROOT_REUSE", target_ok, decision_guard_ok, small_ok


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
                trusted_previous_digest = sha256(source).hexdigest()
                target_oracle_digest = sha256(target).hexdigest()

                control_probe, control_prev, control_cur = _writer_charged(
                    "rehash_both", admission_fn, segment_fn, source, target, trusted_previous_digest
                )
                control_sig = _semantic_signature(control_probe, source, target)
                control_probe = None
                trusted_probe, trusted_prev, trusted_cur = _writer_charged(
                    "trusted_prior", admission_fn, segment_fn, source, target, trusted_previous_digest
                )
                trusted_sig = _semantic_signature(trusted_probe, source, target)
                trusted_probe = None

                case_semantic_ok = (
                    _equivalent(control_sig, trusted_sig)
                    and control_sig["enabled"] == bool(expected_enable)
                    and (
                        not expected_enable
                        or expected_shift is None
                        or control_sig["best_shift"] == expected_shift
                    )
                    and control_prev == trusted_prev == trusted_previous_digest
                    and control_cur == trusted_cur == target_oracle_digest
                    and control_sig["previous_sha256"] == trusted_previous_digest
                    and control_sig["current_sha256"] == target_oracle_digest
                    and trusted_sig["previous_sha256"] == trusted_previous_digest
                    and trusted_sig["current_sha256"] == target_oracle_digest
                    and control_sig["segment_capacity_bytes"]
                    == trusted_sig["segment_capacity_bytes"]
                )
                semantic_ok &= case_semantic_ok

                canonical_wire_bytes = int(control_sig["wire_total_bytes"])
                surprise_bytes = int(control_sig["surprise_bytes"])
                reader_work_bytes = int(control_sig["reader_work_bytes"])
                segment_capacity_bytes = int(control_sig["segment_capacity_bytes"])
                control_sig = None
                trusted_sig = None

                wall = {"rehash_both": [], "trusted_prior": []}
                cpu = {"rehash_both": [], "trusted_prior": []}
                value = None
                for rep in range(REPETITIONS):
                    order = (
                        ("rehash_both", "trusted_prior")
                        if rep % 2 == 0
                        else ("trusted_prior", "rehash_both")
                    )
                    for arm in order:
                        value = None
                        t0_wall = time.perf_counter_ns()
                        t0_cpu = time.process_time_ns()
                        value = _writer_charged(
                            arm,
                            admission_fn,
                            segment_fn,
                            source,
                            target,
                            trusted_previous_digest,
                        )
                        t1_cpu = time.process_time_ns()
                        t1_wall = time.perf_counter_ns()
                        wall[arm].append(t1_wall - t0_wall)
                        cpu[arm].append(t1_cpu - t0_cpu)
                value = None

                control_wall = float(statistics.median(wall["rehash_both"]))
                trusted_wall = float(statistics.median(wall["trusted_prior"]))
                control_cpu = float(statistics.median(cpu["rehash_both"]))
                trusted_cpu = float(statistics.median(cpu["trusted_prior"]))
                rows.append({
                    "size": size,
                    "case": case,
                    "expected_enable": bool(expected_enable),
                    "semantic_ok": case_semantic_ok,
                    "canonical_wire_bytes": canonical_wire_bytes,
                    "surprise_bytes": surprise_bytes,
                    "reader_work_bytes": reader_work_bytes,
                    "segment_capacity_bytes": segment_capacity_bytes,
                    "rehash_both_wall_ns_median": control_wall,
                    "trusted_prior_wall_ns_median": trusted_wall,
                    "trusted_over_rehash_wall": _ratio(trusted_wall, control_wall),
                    "rehash_both_cpu_ns_median": control_cpu,
                    "trusted_prior_cpu_ns_median": trusted_cpu,
                    "trusted_over_rehash_cpu": _ratio(trusted_cpu, control_cpu),
                })
    finally:
        if was_enabled:
            gc.enable()
        td.cleanup()

    decision, target_ok, decision_guard_ok, small_ok = _adjudicate(rows, semantic_ok)
    return {
        "schema": "cmpct-one-g02-trusted-prior-root-reuse-v1",
        "experimental_version": "ONE-G0.2",
        "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
        "sizes": list(SIZES),
        "decision_size": DECISION_SIZE,
        "repetitions": REPETITIONS,
        "target_ratio_max": TARGET_RATIO_MAX,
        "target_rows_required": TARGET_ROWS_REQUIRED,
        "decision_row_max": DECISION_ROW_MAX,
        "small_row_max": SMALL_ROW_MAX,
        "semantic_gates_pass": semantic_ok,
        "target_gate_pass": target_ok,
        "decision_guard_pass": decision_guard_ok,
        "small_transfer_gate_pass": small_ok,
        "decision": decision,
        "claim_boundary": (
            "persistent adjacent-version research writer; candidate reuses an independently verified prior-root SHA-256 "
            "as trusted state while both arms charge source/target ctypes conversion, current-root SHA-256, relation "
            "admission, lazy Segment scheduling, segmentation, bounded Program construction, validation, and direct "
            "canonical emission; establishment/authentication of prior state, filesystem traversal, authenticated "
            "placement, and decode timing remain outside scope"
        ),
        "rows": rows,
    }


def main() -> int:
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["decision"] == "ADVANCE_TRUSTED_PRIOR_ROOT_REUSE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
