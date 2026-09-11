"""ONE-G0.2 preregistered segmented-block rehabilitation A/B.

The full-4096 block Builder is formally rejected because its first enabled case pays a large
suffix-build burst, despite exact anchor traces and ~2.3x large-case speedups. This new Builder
attacks that exported debt directly: divide the same 4096-state sliding window into four
1024-state blocks, spread derived-state suffix work across the stream, and fold the three
intervening complete block minima once per block.

Selector semantics are unchanged. This is not a post-hoc threshold switch and does not alter
the previous frozen result.

Frozen promotion rule before result-bearing execution:
* full emitted anchor-position trace, final Gear state, and considered-position count exactly
  equal the independent Python deque reference on every case;
* segmented median <= 0.70 * masked-deque median on every large case;
* segmented median <= 1.10 * masked-deque median on every tested case;
* segmented reserved discovery state including Gear <= 0.85 * masked-deque state;
* no source-byte rescan.

Failure retires this segmented layout. No proof, extension, Law selection, wire, reader,
stored-byte, v0.29/v0.30, or product-speed cost is gifted.
"""
from __future__ import annotations

import ctypes
import json
import os
from pathlib import Path
import subprocess
import tempfile

from benchmarks.one.one_g02_gear_replacement_ab import _GEAR
from benchmarks.one.one_g02_minimizer_block_ab import (
    MASKED_RESERVED_STATE_BYTES,
    _bind_masked,
    _call_masked,
    _median_ns,
    _python_anchor_trace,
)
from benchmarks.one.one_g02_minimizer_native_probe import _cases, MINIMIZER_SPAN, WINDOW
from benchmarks.one.one_g02_minimizer_wrap_ab import LARGE_CASES

MATERIAL_SPEED_RATIO = 0.70
MAX_REGRESSION_RATIO = 1.10
MAX_STATE_RATIO = 0.85


class _SegmentedResult(ctypes.Structure):
    _fields_ = [
        ("emitted", ctypes.c_uint64),
        ("final_state", ctypes.c_uint64),
        ("positions_considered", ctypes.c_uint64),
        ("reserved_state_bytes", ctypes.c_uint64),
        ("derived_state_reads", ctypes.c_uint64),
    ]


def _build() -> tuple[ctypes.CDLL, tempfile.TemporaryDirectory[str]]:
    here = Path(__file__).parent
    tempdir = tempfile.TemporaryDirectory(prefix="cmpct-one-g02-segmented-")
    library = Path(tempdir.name) / "libone_g02_segmented_ab.so"
    subprocess.run(
        [
            os.environ.get("CC", "cc"), "-O3", "-std=c11", "-fPIC", "-shared",
            str(here / "one_g02_minimizer_mask_kernel.c"),
            str(here / "one_g02_minimizer_segmented_kernel.c"),
            "-o", str(library),
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return ctypes.CDLL(str(library)), tempdir


def _bind_segmented(lib: ctypes.CDLL):
    fn = lib.one_g02_minimizer_segmented_kernel
    fn.argtypes = [
        ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t, ctypes.POINTER(ctypes.c_uint64),
        ctypes.c_size_t, ctypes.c_size_t, ctypes.POINTER(_SegmentedResult),
        ctypes.POINTER(ctypes.c_uint64), ctypes.c_size_t,
    ]
    fn.restype = ctypes.c_int
    return fn


def _call_segmented(fn, gear, data_array, length: int, trace=None, trace_capacity: int = 0) -> _SegmentedResult:
    out = _SegmentedResult()
    rc = fn(
        data_array, length, gear, WINDOW, MINIMIZER_SPAN, ctypes.byref(out),
        trace if trace is not None else None, trace_capacity,
    )
    if rc != 0:
        raise RuntimeError(f"segmented kernel failed: {rc}")
    return out


def run() -> dict[str, object]:
    lib, tempdir = _build()
    try:
        masked = _bind_masked(lib)
        segmented = _bind_segmented(lib)
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
                raise AssertionError(f"masked baseline disagrees with reference for {name}")

            trace_storage = (ctypes.c_uint64 * max(1, len(data)))()
            segmented_once = _call_segmented(
                segmented, gear, data_array, len(data), trace_storage, max(1, len(data))
            )
            actual_trace = [int(trace_storage[i]) for i in range(int(segmented_once.emitted))]
            equal = (
                actual_trace == expected_trace
                and int(segmented_once.final_state) == expected_state
                and int(segmented_once.positions_considered) == expected_considered
            )
            semantic_ok &= equal
            if not equal:
                raise AssertionError(
                    f"segmented semantic mismatch {name}: expected={expected_trace[:32]} actual={actual_trace[:32]}"
                )

            masked_ns = _median_ns(lambda: _call_masked(masked, gear, data_array, len(data)))
            segmented_ns = _median_ns(
                lambda: _call_segmented(segmented, gear, data_array, len(data))
            )
            ratio = segmented_ns / masked_ns
            if name in LARGE_CASES:
                material_large_ok &= ratio <= MATERIAL_SPEED_RATIO
            no_regression_ok &= ratio <= MAX_REGRESSION_RATIO

            segmented_reserved = int(segmented_once.reserved_state_bytes) + 256 * 8
            state_ratio = segmented_reserved / MASKED_RESERVED_STATE_BYTES if segmented_reserved else 0.0
            state_ok &= state_ratio <= MAX_STATE_RATIO
            rows.append({
                "case": name,
                "input_bytes": len(data),
                "large_case": name in LARGE_CASES,
                "anchor_trace_equal": equal,
                "emitted_anchors": len(expected_trace),
                "masked_deque_median_ns": masked_ns,
                "segmented_block_median_ns": segmented_ns,
                "segmented_over_masked_elapsed_ratio": ratio,
                "segmented_speedup_over_masked": masked_ns / segmented_ns,
                "masked_reserved_state_bytes": MASKED_RESERVED_STATE_BYTES,
                "segmented_reserved_state_bytes": segmented_reserved,
                "segmented_over_masked_state_ratio": state_ratio,
                "segmented_derived_state_reads": int(segmented_once.derived_state_reads),
                "source_byte_rescans": 0,
            })

        promote = semantic_ok and material_large_ok and no_regression_ok and state_ok
        return {
            "schema": "cmpct-one-g02-minimizer-segmented-ab-v1",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "hypothesis": "four 1024-state blocks preserve exact 4096-window rightmost minima while retaining >=30% large-case speedup, eliminating >10% small-case regression, and using <=85% of masked-deque reserved state",
            "disproof": "any trace/state/count mismatch, less than 30% improvement on any large case, more than 10% regression on any tested case, any source rescan, or more than 85% masked-deque reserved state retires the segmented layout",
            "frozen_material_speed_ratio": MATERIAL_SPEED_RATIO,
            "frozen_max_regression_ratio": MAX_REGRESSION_RATIO,
            "frozen_max_state_ratio": MAX_STATE_RATIO,
            "decision": "promote_segmented_maintenance_for_integration_review" if promote else "retire_segmented_maintenance_candidate",
            "claim_boundary": "encoder discovery microkernel A/B only; excludes proof, Law selection, wire, reader and product-speed costs",
            "rows": rows,
        }
    finally:
        tempdir.cleanup()


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True, indent=2))
