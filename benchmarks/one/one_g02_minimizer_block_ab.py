"""ONE-G0.2 preregistered masked-deque vs block prefix/suffix maintenance A/B.

Referee lock before result-bearing execution:

The previous exact-head A/B retired ring-address arithmetic as the primary remaining owner:
power-of-two masking recovered only 5.15--8.74% on large cases and regressed a hostile small
case, while the compiled minimizer remains about 22--23x Gear-only. This Builder changes the
maintenance algorithm rather than the selector. It computes the identical rightmost minimum
over the frozen 4096-position Gear-state window using predictable block prefix/suffix work.
Its backward pass touches derived Gear states only; it never rereads source bytes.

Frozen promotion rule:
* exact emitted anchor-position sequence must equal an independent Python deque reference on
  every case (not merely equal counts);
* final Gear state and considered-position count must also match;
* block median <= 0.70 * masked-deque median on every large case (>=30% faster);
* block median <= 1.10 * masked-deque median on every tested case;
* reserved discovery state, including the shared Gear table, <= 1.25x masked-deque state.

Failure retires this block-maintenance candidate. It does not falsify rolling-minimum
opportunity semantics and does not authorize threshold tuning. No proof, extension, index,
Law, wire, stored-byte, reader or product-speed cost is gifted.
"""
from __future__ import annotations

from collections import deque
import ctypes
import json
import os
from pathlib import Path
import statistics
import subprocess
import tempfile
import time

from benchmarks.one.one_g02_gear_replacement_ab import _GEAR, _U64_MASK
from benchmarks.one.one_g02_minimizer_native_probe import (
    _KernelResult,
    _cases,
    MINIMIZER_SPAN,
    REPETITIONS,
    WINDOW,
)
from benchmarks.one.one_g02_minimizer_wrap_ab import LARGE_CASES

MATERIAL_SPEED_RATIO = 0.70
MAX_REGRESSION_RATIO = 1.10
MAX_STATE_RATIO = 1.25
MASKED_RESERVED_STATE_BYTES = MINIMIZER_SPAN * 16 + 256 * 8


class _BlockResult(ctypes.Structure):
    _fields_ = [
        ("emitted", ctypes.c_uint64),
        ("final_state", ctypes.c_uint64),
        ("positions_considered", ctypes.c_uint64),
        ("reserved_state_bytes", ctypes.c_uint64),
        ("derived_state_reads", ctypes.c_uint64),
    ]


def _python_anchor_trace(data: bytes) -> tuple[list[int], int, int]:
    minima: deque[tuple[int, int]] = deque()
    enabled = len(data) >= MINIMIZER_SPAN + WINDOW
    h = 0
    considered = 0
    last_emitted = -1
    anchors: list[int] = []
    for position, value in enumerate(data):
        h = ((h << 1) + _GEAR[value]) & _U64_MASK
        if position + 1 < WINDOW:
            continue
        considered += 1
        if not enabled:
            continue
        while minima and minima[-1][0] >= h:
            minima.pop()
        minima.append((h, position))
        first_valid = position - MINIMIZER_SPAN + 1
        while minima and minima[0][1] < first_valid:
            minima.popleft()
        if first_valid < WINDOW - 1:
            continue
        anchor = minima[0][1]
        if anchor != last_emitted:
            anchors.append(anchor)
            last_emitted = anchor
    return anchors, h, considered


def _build() -> tuple[ctypes.CDLL, tempfile.TemporaryDirectory[str]]:
    here = Path(__file__).parent
    tempdir = tempfile.TemporaryDirectory(prefix="cmpct-one-g02-block-")
    library = Path(tempdir.name) / "libone_g02_block_ab.so"
    subprocess.run(
        [
            os.environ.get("CC", "cc"), "-O3", "-std=c11", "-fPIC", "-shared",
            str(here / "one_g02_minimizer_mask_kernel.c"),
            str(here / "one_g02_minimizer_block_kernel.c"),
            "-o", str(library),
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return ctypes.CDLL(str(library)), tempdir


def _bind_masked(lib: ctypes.CDLL):
    fn = lib.one_g02_minimizer_mask_kernel
    fn.argtypes = [
        ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t, ctypes.POINTER(ctypes.c_uint64),
        ctypes.c_size_t, ctypes.c_size_t, ctypes.POINTER(_KernelResult),
    ]
    fn.restype = ctypes.c_int
    return fn


def _bind_block(lib: ctypes.CDLL):
    fn = lib.one_g02_minimizer_block_kernel
    fn.argtypes = [
        ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t, ctypes.POINTER(ctypes.c_uint64),
        ctypes.c_size_t, ctypes.c_size_t, ctypes.POINTER(_BlockResult),
        ctypes.POINTER(ctypes.c_uint64), ctypes.c_size_t,
    ]
    fn.restype = ctypes.c_int
    return fn


def _call_masked(fn, gear, data_array, length: int) -> _KernelResult:
    out = _KernelResult()
    rc = fn(data_array, length, gear, WINDOW, MINIMIZER_SPAN, ctypes.byref(out))
    if rc != 0:
        raise RuntimeError(f"masked kernel failed: {rc}")
    return out


def _call_block(fn, gear, data_array, length: int, trace=None, trace_capacity: int = 0) -> _BlockResult:
    out = _BlockResult()
    trace_ptr = trace if trace is not None else None
    rc = fn(
        data_array, length, gear, WINDOW, MINIMIZER_SPAN, ctypes.byref(out),
        trace_ptr, trace_capacity,
    )
    if rc != 0:
        raise RuntimeError(f"block kernel failed: {rc}")
    return out


def _median_ns(fn) -> int:
    samples: list[int] = []
    for _ in range(REPETITIONS):
        start = time.perf_counter_ns()
        fn()
        samples.append(time.perf_counter_ns() - start)
    return int(statistics.median(samples))


def run() -> dict[str, object]:
    lib, tempdir = _build()
    try:
        masked = _bind_masked(lib)
        block = _bind_block(lib)
        gear = (ctypes.c_uint64 * 256)(*_GEAR)
        rows: list[dict[str, object]] = []
        semantic_ok = True
        material_large_ok = True
        no_regression_ok = True
        state_ok = True

        for name, data in _cases().items():
            expected_trace, expected_state, expected_considered = _python_anchor_trace(data)
            data_array = (ctypes.c_uint8 * len(data)).from_buffer_copy(data)

            masked_once = _call_masked(masked, gear, data_array, len(data))
            if (
                int(masked_once.emitted) != len(expected_trace)
                or int(masked_once.final_state) != expected_state
                or int(masked_once.positions_considered) != expected_considered
            ):
                raise AssertionError(f"masked baseline disagrees with independent reference for {name}")

            trace_storage = (ctypes.c_uint64 * max(1, len(data)))()
            block_once = _call_block(
                block, gear, data_array, len(data), trace_storage, max(1, len(data))
            )
            actual_trace = [int(trace_storage[i]) for i in range(int(block_once.emitted))]
            equal = (
                actual_trace == expected_trace
                and int(block_once.final_state) == expected_state
                and int(block_once.positions_considered) == expected_considered
            )
            semantic_ok &= equal
            if not equal:
                raise AssertionError(
                    f"block semantic mismatch {name}: expected anchors={expected_trace[:32]}... "
                    f"actual={actual_trace[:32]}... expected_state={expected_state} "
                    f"actual_state={int(block_once.final_state)}"
                )

            masked_ns = _median_ns(lambda: _call_masked(masked, gear, data_array, len(data)))
            block_ns = _median_ns(lambda: _call_block(block, gear, data_array, len(data)))
            ratio = block_ns / masked_ns
            if name in LARGE_CASES:
                material_large_ok &= ratio <= MATERIAL_SPEED_RATIO
            no_regression_ok &= ratio <= MAX_REGRESSION_RATIO

            block_reserved = int(block_once.reserved_state_bytes) + 256 * 8
            state_ratio = block_reserved / MASKED_RESERVED_STATE_BYTES if block_reserved else 0.0
            state_ok &= state_ratio <= MAX_STATE_RATIO
            rows.append({
                "case": name,
                "input_bytes": len(data),
                "large_case": name in LARGE_CASES,
                "emitted_anchors": len(expected_trace),
                "anchor_trace_equal": equal,
                "masked_deque_median_ns": masked_ns,
                "block_minimum_median_ns": block_ns,
                "block_over_masked_elapsed_ratio": ratio,
                "block_speedup_over_masked": masked_ns / block_ns,
                "masked_reserved_state_bytes": MASKED_RESERVED_STATE_BYTES,
                "block_reserved_state_bytes": block_reserved,
                "block_over_masked_state_ratio": state_ratio,
                "block_derived_state_reads": int(block_once.derived_state_reads),
                "source_byte_rescans": 0,
            })

        promote = semantic_ok and material_large_ok and no_regression_ok and state_ok
        return {
            "schema": "cmpct-one-g02-minimizer-block-ab-v1",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "repetitions": REPETITIONS,
            "window": WINDOW,
            "minimizer_span": MINIMIZER_SPAN,
            "hypothesis": "predictable block prefix/suffix maintenance preserves the exact rightmost-minimum anchor sequence while removing at least 30% of masked-deque elapsed cost on every large case at <=1.25x reserved state",
            "disproof": "any anchor-position mismatch, less than 30% improvement on any large case, more than 10% regression on any tested case, or more than 1.25x reserved discovery state retires this block-maintenance candidate",
            "frozen_material_speed_ratio": MATERIAL_SPEED_RATIO,
            "frozen_max_regression_ratio": MAX_REGRESSION_RATIO,
            "frozen_max_state_ratio": MAX_STATE_RATIO,
            "decision": "promote_block_maintenance_for_integration_review" if promote else "retire_block_maintenance_candidate",
            "claim_boundary": "encoder discovery microkernel A/B only; backward pass reads derived Gear states, never source bytes; excludes proof, extension, index, Law, wire, reader and product-speed costs",
            "rows": rows,
        }
    finally:
        tempdir.cleanup()


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True, indent=2))
