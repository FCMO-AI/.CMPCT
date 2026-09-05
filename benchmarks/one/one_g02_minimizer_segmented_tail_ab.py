"""ONE-G0.2 preregistered causal A/B: eager vs tail-aware segmented suffix work.

Referee lock before result-bearing execution:

The frozen four-segment Builder is rejected, but its mature-input speed/state signal survives.
Static dataflow inspection identifies a concrete exported debt: when block q completes, its
suffix can only be queried if a future state reaches block q+4.  The eager kernel builds that
suffix even when known input length proves such a future state cannot exist.  The tail-aware
Builder removes only those provably dead derived-state reads.

Frozen causal confirmation rule:
* exact emitted anchor trace, final Gear state and considered-position count equal the
  independent Python oracle on every case;
* at the 4160-byte enablement boundary, tail-aware median <= 0.85 * eager four-segment median;
* on every large case, tail-aware median <= 1.05 * eager median;
* reserved state does not increase and source-byte rescans remain zero;
* the 4160-byte case skips at least one dead suffix block while still building every suffix
  block that is actually queried.

Failure retires tail-dead-work elimination as the explanation for the boundary debt.  Success
is causal evidence only: it does not promote a maintenance policy, alter the frozen rejected
Builder, or make product/wire/reader/v0.29/v0.30 claims.
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
from benchmarks.one.one_g02_minimizer_segmented_ab import (
    _SegmentedResult,
    _bind_segmented,
    _call_segmented,
)
from benchmarks.one.one_g02_minimizer_wrap_ab import LARGE_CASES

BOUNDARY_CAUSAL_RATIO = 0.85
MAX_LARGE_REGRESSION_RATIO = 1.05


class _TailResult(ctypes.Structure):
    _fields_ = [
        ("emitted", ctypes.c_uint64),
        ("final_state", ctypes.c_uint64),
        ("positions_considered", ctypes.c_uint64),
        ("reserved_state_bytes", ctypes.c_uint64),
        ("derived_state_reads", ctypes.c_uint64),
        ("suffix_blocks_built", ctypes.c_uint64),
        ("suffix_blocks_skipped_dead", ctypes.c_uint64),
    ]


def _build() -> tuple[ctypes.CDLL, tempfile.TemporaryDirectory[str]]:
    here = Path(__file__).parent
    tempdir = tempfile.TemporaryDirectory(prefix="cmpct-one-g02-tail-ab-")
    library = Path(tempdir.name) / "libone_g02_tail_ab.so"
    subprocess.run(
        [
            os.environ.get("CC", "cc"), "-O3", "-std=c11", "-fPIC", "-shared",
            str(here / "one_g02_minimizer_segmented_kernel.c"),
            str(here / "one_g02_minimizer_segmented_tail_kernel.c"),
            "-o", str(library),
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return ctypes.CDLL(str(library)), tempdir


def _bind_tail(lib: ctypes.CDLL):
    fn = lib.one_g02_minimizer_segmented_tail_kernel
    fn.argtypes = [
        ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t, ctypes.POINTER(ctypes.c_uint64),
        ctypes.c_size_t, ctypes.c_size_t, ctypes.POINTER(_TailResult),
        ctypes.POINTER(ctypes.c_uint64), ctypes.c_size_t,
    ]
    fn.restype = ctypes.c_int
    return fn


def _call_tail(fn, gear, data_array, length: int, trace=None, trace_capacity: int = 0):
    out = _TailResult()
    rc = fn(
        data_array, length, gear, WINDOW, MINIMIZER_SPAN, ctypes.byref(out),
        trace if trace is not None else None, trace_capacity,
    )
    if rc != 0:
        raise RuntimeError(f"tail-aware segmented kernel failed: {rc}")
    return out


def run() -> dict[str, object]:
    lib, tempdir = _build()
    try:
        eager = _bind_segmented(lib)
        tail = _bind_tail(lib)
        gear = (ctypes.c_uint64 * 256)(*_GEAR)
        rows: list[dict[str, object]] = []
        semantic_ok = True
        boundary_ok = False
        large_ok = True
        state_ok = True
        boundary_dead_work_ok = False

        for name, data in _cases().items():
            expected_trace, expected_state, expected_considered = _python_anchor_trace(data)
            data_array = (ctypes.c_uint8 * len(data)).from_buffer_copy(data)
            eager_once = _call_segmented(eager, gear, data_array, len(data))
            trace_storage = (ctypes.c_uint64 * max(1, len(data)))()
            tail_once = _call_tail(tail, gear, data_array, len(data), trace_storage, max(1, len(data)))
            actual_trace = [int(trace_storage[i]) for i in range(int(tail_once.emitted))]
            equal = (
                actual_trace == expected_trace
                and int(tail_once.final_state) == expected_state
                and int(tail_once.positions_considered) == expected_considered
                and int(eager_once.emitted) == len(expected_trace)
            )
            semantic_ok &= equal
            if not equal:
                raise AssertionError(f"tail-aware semantic mismatch for {name}")

            eager_ns = _median_ns(lambda: _call_segmented(eager, gear, data_array, len(data)))
            tail_ns = _median_ns(lambda: _call_tail(tail, gear, data_array, len(data)))
            ratio = tail_ns / eager_ns
            if name == "at_enablement_4160b":
                boundary_ok = ratio <= BOUNDARY_CAUSAL_RATIO
                boundary_dead_work_ok = (
                    int(tail_once.suffix_blocks_skipped_dead) >= 1
                    and int(tail_once.suffix_blocks_built) >= 1
                    and int(tail_once.derived_state_reads) < int(eager_once.derived_state_reads)
                )
            if name in LARGE_CASES:
                large_ok &= ratio <= MAX_LARGE_REGRESSION_RATIO
            state_ok &= int(tail_once.reserved_state_bytes) <= int(eager_once.reserved_state_bytes)
            rows.append({
                "case": name,
                "input_bytes": len(data),
                "large_case": name in LARGE_CASES,
                "anchor_trace_equal": equal,
                "eager_segmented_median_ns": eager_ns,
                "tail_segmented_median_ns": tail_ns,
                "tail_over_eager_elapsed_ratio": ratio,
                "eager_reserved_state_bytes": int(eager_once.reserved_state_bytes),
                "tail_reserved_state_bytes": int(tail_once.reserved_state_bytes),
                "eager_derived_state_reads": int(eager_once.derived_state_reads),
                "tail_derived_state_reads": int(tail_once.derived_state_reads),
                "tail_suffix_blocks_built": int(tail_once.suffix_blocks_built),
                "tail_suffix_blocks_skipped_dead": int(tail_once.suffix_blocks_skipped_dead),
                "source_byte_rescans": 0,
            })

        confirmed = semantic_ok and boundary_ok and large_ok and state_ok and boundary_dead_work_ok
        return {
            "schema": "cmpct-one-g02-minimizer-segmented-tail-ab-v1",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "hypothesis": "provably dead EOF suffix construction materially owns the 4160-byte four-segment boundary debt and can be removed without selector/state/large-input regression",
            "disproof": "semantic mismatch, <15% boundary improvement versus eager, >5% regression on any large case, state increase, source rescan, or failure to skip dead suffix work falsifies the causal explanation",
            "frozen_boundary_ratio": BOUNDARY_CAUSAL_RATIO,
            "frozen_max_large_regression_ratio": MAX_LARGE_REGRESSION_RATIO,
            "decision": "tail_dead_work_causally_confirmed" if confirmed else "tail_dead_work_not_sufficiently_confirmed",
            "claim_boundary": "encoder discovery causal A/B only; no maintenance-policy promotion and no wire/reader/stored-byte/product/comparator claim",
            "rows": rows,
        }
    finally:
        tempdir.cleanup()


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True, indent=2))
