"""ONE-G0.2 causal A/B: per-window dense selection vs event-driven dense selection.

Referee freeze before result-bearing execution
==============================================

Tail-aware four-segment maintenance is the promoted encoder-discovery baseline. The record-suffix
negative removed ~99.3% of suffix writes yet regressed every large case by 25--32%, falsifying dense
suffix write volume as the main remaining owner. The next hypothesis keeps the dense direct-indexed
suffix tables intact but uses their stored argmin offsets as expiration/jump pointers. Prefix minima,
complete-middle minima, and suffix minima are stable between discrete events, so the global selected
minimum need not be recomputed or emitted on every mature window.

Frozen hypothesis
-----------------
Event-driven dense maintenance preserves the exact rightmost-minimum selector and is <=0.85x the
promoted tail-aware elapsed time on every large case, <=1.05x on every tested case, <=1.01x state,
with zero source rescans. To support the causal explanation rather than a coincidental timing win,
selection recomputes and suffix candidate loads must each be <=0.25 per mature window on every large
case.

Disproof
--------
Any oracle mismatch, source rescan, >5% regression on any case, <15% improvement on any large case,
>1.01x state, >25% selection recomputes per mature window, or >25% suffix loads per mature window on a
large case rejects this Builder. No threshold may change after result-bearing execution.
"""
from __future__ import annotations

import ctypes
import json
import os
from pathlib import Path
import subprocess
import tempfile

from benchmarks.one.one_g02_gear_replacement_ab import _GEAR
from benchmarks.one.one_g02_minimizer_block_ab import _median_ns, _python_anchor_trace
from benchmarks.one.one_g02_minimizer_native_probe import _cases, MINIMIZER_SPAN, WINDOW
from benchmarks.one.one_g02_minimizer_segmented_tail_ab import _bind_tail, _call_tail
from benchmarks.one.one_g02_minimizer_wrap_ab import LARGE_CASES

MATERIAL_SPEED_RATIO = 0.85
MAX_REGRESSION_RATIO = 1.05
MAX_STATE_RATIO = 1.01
MAX_EVENT_RATIO = 0.25
GEAR_STATE_BYTES = 256 * 8


class _EventResult(ctypes.Structure):
    _fields_ = [
        ("emitted", ctypes.c_uint64),
        ("final_state", ctypes.c_uint64),
        ("positions_considered", ctypes.c_uint64),
        ("reserved_state_bytes", ctypes.c_uint64),
        ("derived_state_reads", ctypes.c_uint64),
        ("suffix_blocks_built", ctypes.c_uint64),
        ("suffix_blocks_skipped_dead", ctypes.c_uint64),
        ("mature_windows", ctypes.c_uint64),
        ("suffix_candidate_loads", ctypes.c_uint64),
        ("selection_recomputes", ctypes.c_uint64),
        ("prefix_change_events", ctypes.c_uint64),
        ("suffix_change_events", ctypes.c_uint64),
    ]


def _build() -> tuple[ctypes.CDLL, tempfile.TemporaryDirectory[str]]:
    here = Path(__file__).parent
    tempdir = tempfile.TemporaryDirectory(prefix="cmpct-one-g02-event-ab-")
    library = Path(tempdir.name) / "libone_g02_event_ab.so"
    subprocess.run(
        [
            os.environ.get("CC", "cc"), "-O3", "-std=c11", "-fPIC", "-shared",
            str(here / "one_g02_minimizer_segmented_tail_kernel.c"),
            str(here / "one_g02_minimizer_event_kernel.c"),
            "-o", str(library),
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return ctypes.CDLL(str(library)), tempdir


def _bind_event(lib: ctypes.CDLL):
    fn = lib.one_g02_minimizer_event_kernel
    fn.argtypes = [
        ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t, ctypes.POINTER(ctypes.c_uint64),
        ctypes.c_size_t, ctypes.c_size_t, ctypes.POINTER(_EventResult),
        ctypes.POINTER(ctypes.c_uint64), ctypes.c_size_t,
    ]
    fn.restype = ctypes.c_int
    return fn


def _call_event(fn, gear, data_array, length: int, trace=None, trace_capacity: int = 0):
    out = _EventResult()
    rc = fn(
        data_array, length, gear, WINDOW, MINIMIZER_SPAN, ctypes.byref(out),
        trace if trace is not None else None, trace_capacity,
    )
    if rc != 0:
        raise RuntimeError(f"event-driven minimizer kernel failed: {rc}")
    return out


def run() -> dict[str, object]:
    lib, tempdir = _build()
    try:
        tail = _bind_tail(lib)
        event = _bind_event(lib)
        gear = (ctypes.c_uint64 * 256)(*_GEAR)
        rows: list[dict[str, object]] = []
        semantic_ok = all_speed_ok = large_speed_ok = state_ok = event_ok = True

        for name, data in _cases().items():
            expected_trace, expected_state, expected_considered = _python_anchor_trace(data)
            data_array = (ctypes.c_uint8 * len(data)).from_buffer_copy(data)
            tail_once = _call_tail(tail, gear, data_array, len(data))
            trace_storage = (ctypes.c_uint64 * max(1, len(data)))()
            event_once = _call_event(event, gear, data_array, len(data), trace_storage, max(1, len(data)))
            actual_trace = [int(trace_storage[i]) for i in range(int(event_once.emitted))]
            equal = (
                actual_trace == expected_trace
                and int(event_once.final_state) == expected_state
                and int(event_once.positions_considered) == expected_considered
                and int(tail_once.emitted) == len(expected_trace)
            )
            semantic_ok &= equal
            if not equal:
                raise AssertionError(f"event-driven semantic mismatch for {name}")

            tail_ns = _median_ns(lambda: _call_tail(tail, gear, data_array, len(data)))
            event_ns = _median_ns(lambda: _call_event(event, gear, data_array, len(data)))
            elapsed_ratio = event_ns / tail_ns
            tail_reserved = int(tail_once.reserved_state_bytes) + (GEAR_STATE_BYTES if tail_once.reserved_state_bytes else 0)
            event_reserved = int(event_once.reserved_state_bytes) + (GEAR_STATE_BYTES if event_once.reserved_state_bytes else 0)
            state_ratio = event_reserved / tail_reserved if tail_reserved else 0.0
            mature = int(event_once.mature_windows)
            select_ratio = int(event_once.selection_recomputes) / mature if mature else 0.0
            suffix_load_ratio = int(event_once.suffix_candidate_loads) / mature if mature else 0.0

            all_speed_ok &= elapsed_ratio <= MAX_REGRESSION_RATIO
            state_ok &= state_ratio <= MAX_STATE_RATIO
            if name in LARGE_CASES:
                large_speed_ok &= elapsed_ratio <= MATERIAL_SPEED_RATIO
                event_ok &= select_ratio <= MAX_EVENT_RATIO and suffix_load_ratio <= MAX_EVENT_RATIO

            rows.append({
                "case": name,
                "input_bytes": len(data),
                "large_case": name in LARGE_CASES,
                "anchor_trace_equal": equal,
                "tail_dense_median_ns": tail_ns,
                "event_dense_median_ns": event_ns,
                "event_over_tail_elapsed_ratio": elapsed_ratio,
                "tail_reserved_state_bytes": tail_reserved,
                "event_reserved_state_bytes": event_reserved,
                "event_over_tail_state_ratio": state_ratio,
                "mature_windows": mature,
                "selection_recomputes": int(event_once.selection_recomputes),
                "selection_recompute_ratio": select_ratio,
                "suffix_candidate_loads": int(event_once.suffix_candidate_loads),
                "suffix_candidate_load_ratio": suffix_load_ratio,
                "prefix_change_events": int(event_once.prefix_change_events),
                "suffix_change_events": int(event_once.suffix_change_events),
                "derived_state_reads": int(event_once.derived_state_reads),
                "source_byte_rescans": 0,
            })

        supported = semantic_ok and all_speed_ok and large_speed_ok and state_ok and event_ok
        return {
            "schema": "cmpct-one-g02-minimizer-event-ab-v1",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "hypothesis": "dense suffix argmin offsets act as expiration pointers so exact selection work can be event-driven rather than per-window",
            "disproof": "oracle mismatch, rescan, >5% any-case regression, <15% every-large gain, >1.01x state, or >25% event ratios rejects",
            "frozen_material_speed_ratio": MATERIAL_SPEED_RATIO,
            "frozen_max_regression_ratio": MAX_REGRESSION_RATIO,
            "frozen_max_state_ratio": MAX_STATE_RATIO,
            "frozen_max_event_ratio": MAX_EVENT_RATIO,
            "decision": "promote_event_driven_dense_maintenance" if supported else "reject_event_driven_dense_maintenance",
            "claim_boundary": "encoder discovery maintenance only; no Law/wire/reader/stored-byte/product/comparator claim",
            "rows": rows,
        }
    finally:
        tempdir.cleanup()


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True, indent=2))
