"""ONE-G0.2 causal probe: two-segment exact minimizer maintenance.

Hypothesis (Referee): the frozen four-segment Builder pays avoidable block-turnover and
middle-fold bookkeeping.  For a fixed 4096-state rightmost-minimum selector, two 2048-state
segments are sufficient to partition every mature window into exactly three pieces: an old
partial suffix, one complete middle block and the current prefix.  Therefore a two-segment
implementation may preserve the exact selector while reducing maintenance work.

Disproof: any emitted-anchor trace, final Gear state or considered-position mismatch against
the independent Python oracle falsifies the representation-preserving claim immediately.
Timing and state are diagnostic in this probe; no promotion threshold is defined and no failed
four-segment threshold is altered.  A later Builder must be separately preregistered before it
can promote a maintenance policy.
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
from benchmarks.one.one_g02_minimizer_segmented_ab import (
    _bind_segmented,
    _call_segmented,
)


class _TwoSegmentResult(ctypes.Structure):
    _fields_ = [
        ("emitted", ctypes.c_uint64),
        ("final_state", ctypes.c_uint64),
        ("positions_considered", ctypes.c_uint64),
        ("reserved_state_bytes", ctypes.c_uint64),
        ("derived_state_reads", ctypes.c_uint64),
    ]


def _build() -> tuple[ctypes.CDLL, tempfile.TemporaryDirectory[str]]:
    here = Path(__file__).parent
    tempdir = tempfile.TemporaryDirectory(prefix="cmpct-one-g02-two-segment-")
    library = Path(tempdir.name) / "libone_g02_two_segment_probe.so"
    subprocess.run(
        [
            os.environ.get("CC", "cc"), "-O3", "-std=c11", "-fPIC", "-shared",
            str(here / "one_g02_minimizer_mask_kernel.c"),
            str(here / "one_g02_minimizer_segmented_kernel.c"),
            str(here / "one_g02_minimizer_two_segment_kernel.c"),
            "-o", str(library),
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return ctypes.CDLL(str(library)), tempdir


def _bind_two_segment(lib: ctypes.CDLL):
    fn = lib.one_g02_minimizer_two_segment_kernel
    fn.argtypes = [
        ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t, ctypes.POINTER(ctypes.c_uint64),
        ctypes.c_size_t, ctypes.c_size_t, ctypes.POINTER(_TwoSegmentResult),
        ctypes.POINTER(ctypes.c_uint64), ctypes.c_size_t,
    ]
    fn.restype = ctypes.c_int
    return fn


def _call_two_segment(fn, gear, data_array, length: int, trace=None, trace_capacity: int = 0):
    out = _TwoSegmentResult()
    rc = fn(
        data_array, length, gear, WINDOW, MINIMIZER_SPAN, ctypes.byref(out),
        trace if trace is not None else None, trace_capacity,
    )
    if rc != 0:
        raise RuntimeError(f"two-segment kernel failed: {rc}")
    return out


def run() -> dict[str, object]:
    lib, tempdir = _build()
    try:
        masked = _bind_masked(lib)
        four = _bind_segmented(lib)
        two = _bind_two_segment(lib)
        gear = (ctypes.c_uint64 * 256)(*_GEAR)
        rows: list[dict[str, object]] = []

        for name, data in _cases().items():
            expected_trace, expected_state, expected_considered = _python_anchor_trace(data)
            data_array = (ctypes.c_uint8 * len(data)).from_buffer_copy(data)
            masked_once = _call_masked(masked, gear, data_array, len(data))
            four_once = _call_segmented(four, gear, data_array, len(data))
            trace_storage = (ctypes.c_uint64 * max(1, len(data)))()
            two_once = _call_two_segment(
                two, gear, data_array, len(data), trace_storage, max(1, len(data))
            )
            actual_trace = [int(trace_storage[i]) for i in range(int(two_once.emitted))]
            equal = (
                actual_trace == expected_trace
                and int(two_once.final_state) == expected_state
                and int(two_once.positions_considered) == expected_considered
                and int(masked_once.emitted) == len(expected_trace)
                and int(four_once.emitted) == len(expected_trace)
            )
            if not equal:
                raise AssertionError(f"two-segment semantic mismatch for {name}")

            masked_ns = _median_ns(lambda: _call_masked(masked, gear, data_array, len(data)))
            four_ns = _median_ns(lambda: _call_segmented(four, gear, data_array, len(data)))
            two_ns = _median_ns(lambda: _call_two_segment(two, gear, data_array, len(data)))
            two_reserved = int(two_once.reserved_state_bytes) + 256 * 8
            four_reserved = int(four_once.reserved_state_bytes) + 256 * 8
            rows.append({
                "case": name,
                "input_bytes": len(data),
                "anchor_trace_equal": True,
                "masked_deque_median_ns": masked_ns,
                "four_segment_median_ns": four_ns,
                "two_segment_median_ns": two_ns,
                "two_over_masked_elapsed_ratio": two_ns / masked_ns,
                "two_over_four_elapsed_ratio": two_ns / four_ns,
                "masked_reserved_state_bytes": MASKED_RESERVED_STATE_BYTES,
                "four_segment_reserved_state_bytes": four_reserved,
                "two_segment_reserved_state_bytes": two_reserved,
                "two_over_masked_state_ratio": two_reserved / MASKED_RESERVED_STATE_BYTES if two_reserved else 0.0,
                "two_over_four_state_ratio": two_reserved / four_reserved if four_reserved else 0.0,
                "four_segment_derived_state_reads": int(four_once.derived_state_reads),
                "two_segment_derived_state_reads": int(two_once.derived_state_reads),
                "source_byte_rescans": 0,
            })

        return {
            "schema": "cmpct-one-g02-minimizer-two-segment-probe-v1",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "hypothesis": "two half-span segments preserve the exact rightmost-minimum selector and may reduce four-segment turnover/bookkeeping",
            "disproof": "any independent-oracle anchor trace, final Gear state, or considered-position mismatch falsifies the structural simplification",
            "decision_scope": "causal diagnostic only; no promotion threshold and no product/wire/reader/comparator claim",
            "rows": rows,
        }
    finally:
        tempdir.cleanup()


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True, indent=2))
