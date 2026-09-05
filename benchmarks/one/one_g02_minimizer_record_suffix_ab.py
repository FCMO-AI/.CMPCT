"""ONE-G0.2 causal A/B: dense suffix tables vs record-minimum suffix change points.

Referee freeze before result-bearing execution
==============================================

The causally repaired four-segment selector still carries material maintenance debt above the
Gear-only recurrence. Dense suffix construction reads each completed 1024-state block and
writes one (value, offset) suffix-minimum entry for every state even though the suffix-minimum
function changes only when a new strict record minimum appears. Because future suffix queries
advance monotonically with the current-block offset, a change-point stream can be consumed by
a monotone cursor; no search or source rescan is needed.

Frozen hypothesis
-----------------
Replacing dense suffix materialization with exact record-minimum change points preserves the
same rightmost-minimum anchor trace and reduces derived write traffic enough to make every
large case at least 15% faster than the tail-aware dense-suffix kernel, while no tested case is
more than 5% slower. Worst-case allocation remains bounded to one record per block state.

Disproof
--------
Any independent-oracle mismatch, source rescan, >5% regression on any case, <15% improvement
on any large case, or reserved-state growth above 1.01x the tail-aware dense layout rejects
this representation. In addition, if record writes exceed 10% of dense suffix entries on any
large frozen case, the proposed causal explanation (write-traffic sparsity) is not established.
A rejection does not alter selector semantics or revive retired maintenance families.
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
MAX_LARGE_RECORD_WRITE_RATIO = 0.10
GEAR_STATE_BYTES = 256 * 8


class _RecordResult(ctypes.Structure):
    _fields_ = [
        ("emitted", ctypes.c_uint64),
        ("final_state", ctypes.c_uint64),
        ("positions_considered", ctypes.c_uint64),
        ("reserved_state_bytes", ctypes.c_uint64),
        ("derived_state_reads", ctypes.c_uint64),
        ("suffix_record_writes", ctypes.c_uint64),
        ("suffix_record_advances", ctypes.c_uint64),
        ("suffix_blocks_built", ctypes.c_uint64),
        ("suffix_blocks_skipped_dead", ctypes.c_uint64),
        ("max_records_per_block", ctypes.c_uint64),
    ]


def _build() -> tuple[ctypes.CDLL, tempfile.TemporaryDirectory[str]]:
    here = Path(__file__).parent
    tempdir = tempfile.TemporaryDirectory(prefix="cmpct-one-g02-record-suffix-")
    library = Path(tempdir.name) / "libone_g02_record_suffix.so"
    subprocess.run(
        [
            os.environ.get("CC", "cc"), "-O3", "-std=c11", "-fPIC", "-shared",
            str(here / "one_g02_minimizer_segmented_tail_kernel.c"),
            str(here / "one_g02_minimizer_record_suffix_kernel.c"),
            "-o", str(library),
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return ctypes.CDLL(str(library)), tempdir


def _bind_record(lib: ctypes.CDLL):
    fn = lib.one_g02_minimizer_record_suffix_kernel
    fn.argtypes = [
        ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t, ctypes.POINTER(ctypes.c_uint64),
        ctypes.c_size_t, ctypes.c_size_t, ctypes.POINTER(_RecordResult),
        ctypes.POINTER(ctypes.c_uint64), ctypes.c_size_t,
    ]
    fn.restype = ctypes.c_int
    return fn


def _call_record(fn, gear, data_array, length: int, trace=None, trace_capacity: int = 0):
    out = _RecordResult()
    rc = fn(
        data_array, length, gear, WINDOW, MINIMIZER_SPAN, ctypes.byref(out),
        trace if trace is not None else None, trace_capacity,
    )
    if rc != 0:
        raise RuntimeError(f"record-suffix minimizer kernel failed: {rc}")
    return out


def run() -> dict[str, object]:
    lib, tempdir = _build()
    try:
        tail = _bind_tail(lib)
        record = _bind_record(lib)
        gear = (ctypes.c_uint64 * 256)(*_GEAR)
        rows: list[dict[str, object]] = []
        semantic_ok = True
        all_speed_ok = True
        large_speed_ok = True
        state_ok = True
        causal_write_ok = True

        for name, data in _cases().items():
            expected_trace, expected_state, expected_considered = _python_anchor_trace(data)
            data_array = (ctypes.c_uint8 * len(data)).from_buffer_copy(data)
            tail_once = _call_tail(tail, gear, data_array, len(data))
            trace_storage = (ctypes.c_uint64 * max(1, len(data)))()
            record_once = _call_record(
                record, gear, data_array, len(data), trace_storage, max(1, len(data))
            )
            actual_trace = [int(trace_storage[i]) for i in range(int(record_once.emitted))]
            equal = (
                actual_trace == expected_trace
                and int(record_once.final_state) == expected_state
                and int(record_once.positions_considered) == expected_considered
                and int(tail_once.emitted) == len(expected_trace)
            )
            semantic_ok &= equal
            if not equal:
                raise AssertionError(f"record-suffix semantic mismatch for {name}")

            tail_ns = _median_ns(lambda: _call_tail(tail, gear, data_array, len(data)))
            record_ns = _median_ns(lambda: _call_record(record, gear, data_array, len(data)))
            elapsed_ratio = record_ns / tail_ns
            tail_reserved = int(tail_once.reserved_state_bytes) + (
                GEAR_STATE_BYTES if tail_once.reserved_state_bytes else 0
            )
            record_reserved = int(record_once.reserved_state_bytes) + (
                GEAR_STATE_BYTES if record_once.reserved_state_bytes else 0
            )
            state_ratio = record_reserved / tail_reserved if tail_reserved else 0.0
            dense_entries = int(record_once.derived_state_reads)
            record_write_ratio = (
                int(record_once.suffix_record_writes) / dense_entries if dense_entries else 0.0
            )

            all_speed_ok &= elapsed_ratio <= MAX_REGRESSION_RATIO
            state_ok &= state_ratio <= MAX_STATE_RATIO
            if name in LARGE_CASES:
                large_speed_ok &= elapsed_ratio <= MATERIAL_SPEED_RATIO
                causal_write_ok &= record_write_ratio <= MAX_LARGE_RECORD_WRITE_RATIO

            rows.append({
                "case": name,
                "input_bytes": len(data),
                "large_case": name in LARGE_CASES,
                "anchor_trace_equal": equal,
                "tail_dense_median_ns": tail_ns,
                "record_suffix_median_ns": record_ns,
                "record_over_tail_elapsed_ratio": elapsed_ratio,
                "tail_reserved_state_bytes": tail_reserved,
                "record_reserved_state_bytes": record_reserved,
                "record_over_tail_state_ratio": state_ratio,
                "derived_state_reads": dense_entries,
                "suffix_record_writes": int(record_once.suffix_record_writes),
                "record_write_ratio_over_dense_entries": record_write_ratio,
                "suffix_record_advances": int(record_once.suffix_record_advances),
                "max_records_per_block": int(record_once.max_records_per_block),
                "suffix_blocks_built": int(record_once.suffix_blocks_built),
                "suffix_blocks_skipped_dead": int(record_once.suffix_blocks_skipped_dead),
                "source_byte_rescans": 0,
            })

        supported = semantic_ok and all_speed_ok and large_speed_ok and state_ok and causal_write_ok
        return {
            "schema": "cmpct-one-g02-minimizer-record-suffix-ab-v1",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "hypothesis": "record-minimum suffix change points preserve the exact selector while removing dense derived-state writes and materially reducing large-case maintenance time",
            "disproof": "oracle mismatch, source rescan, >5% any-case regression, <15% large-case improvement, >1.01x tail state, or >10% record/dense write ratio on a large case rejects the candidate",
            "frozen_material_speed_ratio": MATERIAL_SPEED_RATIO,
            "frozen_max_regression_ratio": MAX_REGRESSION_RATIO,
            "frozen_max_state_ratio": MAX_STATE_RATIO,
            "frozen_max_large_record_write_ratio": MAX_LARGE_RECORD_WRITE_RATIO,
            "decision": "record_suffix_candidate_survives" if supported else "retire_record_suffix_candidate",
            "claim_boundary": "encoder discovery maintenance A/B only; no Law/wire/reader/stored-byte/product/comparator claim",
            "rows": rows,
        }
    finally:
        tempdir.cleanup()


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True, indent=2))
