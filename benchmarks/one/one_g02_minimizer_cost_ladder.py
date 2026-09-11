"""ONE-G0.2 diagnostic: attribute promoted minimizer residual by maintenance layer.

This is an ablation/profiling instrument, not a selector proposal or promotion gate. The middle
arms intentionally do not emit anchors; they preserve the exact Gear recurrence and charge the
specified derived-state memory work so same-run elapsed deltas can locate the remaining owner.
No arm grants stored-byte, Law, reader, product-speed, v0.29 or v0.30 authority.
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
from benchmarks.one.one_g02_minimizer_event_ab import _EventResult, _bind_event, _call_event
from benchmarks.one.one_g02_minimizer_native_probe import _KernelResult, _cases, MINIMIZER_SPAN, WINDOW
from benchmarks.one.one_g02_minimizer_segmented_residual import _bind_gear, _call_gear
from benchmarks.one.one_g02_minimizer_wrap_ab import LARGE_CASES


class _CostResult(ctypes.Structure):
    _fields_ = [
        ("final_state", ctypes.c_uint64),
        ("positions_considered", ctypes.c_uint64),
        ("reserved_state_bytes", ctypes.c_uint64),
        ("derived_state_reads", ctypes.c_uint64),
        ("suffix_blocks_built", ctypes.c_uint64),
        ("suffix_blocks_skipped_dead", ctypes.c_uint64),
        ("checksum", ctypes.c_uint64),
    ]


def _build() -> tuple[ctypes.CDLL, tempfile.TemporaryDirectory[str]]:
    here = Path(__file__).parent
    tempdir = tempfile.TemporaryDirectory(prefix="cmpct-one-g02-cost-ladder-")
    library = Path(tempdir.name) / "libone_g02_cost_ladder.so"
    subprocess.run(
        [
            os.environ.get("CC", "cc"), "-O3", "-std=c11", "-fPIC", "-shared",
            str(here / "one_g02_minimizer_kernel.c"),
            str(here / "one_g02_minimizer_cost_ladder.c"),
            str(here / "one_g02_minimizer_event_kernel.c"),
            "-o", str(library),
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return ctypes.CDLL(str(library)), tempdir


def _bind_cost(lib: ctypes.CDLL, name: str):
    fn = getattr(lib, name)
    fn.argtypes = [
        ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t, ctypes.POINTER(ctypes.c_uint64),
        ctypes.c_size_t, ctypes.c_size_t, ctypes.POINTER(_CostResult),
    ]
    fn.restype = ctypes.c_int
    return fn


def _call_cost(fn, gear, data_array, length: int) -> _CostResult:
    out = _CostResult()
    rc = fn(data_array, length, gear, WINDOW, MINIMIZER_SPAN, ctypes.byref(out))
    if rc != 0:
        raise RuntimeError(f"cost-ladder kernel failed: {rc}")
    return out


def run() -> dict[str, object]:
    lib, tempdir = _build()
    try:
        gear_fn = _bind_gear(lib)
        buffer_fn = _bind_cost(lib, "one_g02_buffer_prefix_cost_kernel")
        suffix_fn = _bind_cost(lib, "one_g02_dense_suffix_cost_kernel")
        event_fn = _bind_event(lib)
        gear = (ctypes.c_uint64 * 256)(*_GEAR)
        rows: list[dict[str, object]] = []

        for name, data in _cases().items():
            if name not in LARGE_CASES:
                continue
            data_array = (ctypes.c_uint8 * len(data)).from_buffer_copy(data)
            expected_trace, expected_state, expected_considered = _python_anchor_trace(data)
            gear_once = _call_gear(gear_fn, gear, data_array, len(data))
            buffer_once = _call_cost(buffer_fn, gear, data_array, len(data))
            suffix_once = _call_cost(suffix_fn, gear, data_array, len(data))
            event_once = _call_event(event_fn, gear, data_array, len(data))
            if (
                int(gear_once.final_state) != expected_state
                or int(buffer_once.final_state) != expected_state
                or int(suffix_once.final_state) != expected_state
                or int(event_once.final_state) != expected_state
                or int(gear_once.positions_considered) != expected_considered
                or int(buffer_once.positions_considered) != expected_considered
                or int(suffix_once.positions_considered) != expected_considered
                or int(event_once.positions_considered) != expected_considered
                or int(event_once.emitted) != len(expected_trace)
            ):
                raise AssertionError(f"cost-ladder recurrence/count mismatch for {name}")

            gear_ns = _median_ns(lambda: _call_gear(gear_fn, gear, data_array, len(data)))
            buffer_ns = _median_ns(lambda: _call_cost(buffer_fn, gear, data_array, len(data)))
            suffix_ns = _median_ns(lambda: _call_cost(suffix_fn, gear, data_array, len(data)))
            event_ns = _median_ns(lambda: _call_event(event_fn, gear, data_array, len(data)))
            rows.append({
                "case": name,
                "input_bytes": len(data),
                "gear_only_median_ns": gear_ns,
                "buffer_prefix_median_ns": buffer_ns,
                "dense_suffix_no_selection_median_ns": suffix_ns,
                "event_exact_median_ns": event_ns,
                "buffer_over_gear_ratio": buffer_ns / gear_ns,
                "suffix_over_buffer_ratio": suffix_ns / buffer_ns,
                "event_over_suffix_ratio": event_ns / suffix_ns,
                "event_over_gear_ratio": event_ns / gear_ns,
                "buffer_incremental_ns_per_byte": (buffer_ns - gear_ns) / len(data),
                "suffix_incremental_ns_per_byte": (suffix_ns - buffer_ns) / len(data),
                "event_selection_incremental_ns_per_byte": (event_ns - suffix_ns) / len(data),
                "dense_suffix_derived_state_reads": int(suffix_once.derived_state_reads),
                "event_selection_recomputes": int(event_once.selection_recomputes),
                "event_suffix_candidate_loads": int(event_once.suffix_candidate_loads),
                "source_byte_rescans": 0,
            })

        return {
            "schema": "cmpct-one-g02-minimizer-cost-ladder-v1",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "purpose": "same-run causal elapsed attribution across Gear recurrence, derived-state buffering/prefix bookkeeping, dense suffix materialization, and exact event-driven selection",
            "interpretation_rule": "middle arms are non-semantic cost ablations; use deltas to choose the next causal Builder, never as compression or selector evidence",
            "rows": rows,
        }
    finally:
        tempdir.cleanup()


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True, indent=2))
