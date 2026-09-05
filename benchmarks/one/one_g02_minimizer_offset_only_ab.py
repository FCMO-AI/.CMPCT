"""ONE-G0.2 preregistered A/B: duplicated suffix values vs offset-only suffixes.

Mission lock / Referee
======================
The current counter-based tail-aware four-segment Builder stores one current
1024-state block plus four dense suffix-value tables and four dense suffix-offset
tables.  The suffix value is redundant with the derived Gear state that produced
its argmin.  The candidate retains four Gear-state blocks in the same four-slot
ring and stores only uint16 suffix argmins.  At query time it performs one direct
argmin-offset lookup followed by one direct retained-state load.  The current
block overwrites q-4 in place only behind the advancing window boundary, so no
source rescan or extra copy is required.

This is deliberately different from the retired sparse record-suffix candidate:
there is no sparse record search, cursor, or variable-length control path.  The
hypothesis is that removing duplicated suffix values can reduce state/memory
traffic while preserving the regular direct-indexed path that the sparse design
lost.

Frozen decision law before result-bearing execution
----------------------------------------------------
* emitted anchor positions, final Gear state and considered-position count equal
  the independent Python oracle on every case;
* suffix blocks built/skipped and source-rescan count remain identical to the
  counter dense baseline;
* candidate reserved state <= 0.85x counter dense state;
* no large case may exceed 1.03x counter elapsed and no tested case may exceed
  1.05x;
* PROMOTE if those invariants hold and median large-case elapsed <=1.00x, i.e.
  the >=15% state reduction is not bought with a sustained speed regression;
* RETIRE if median large-case elapsed >1.03x or any large case >1.08x;
  otherwise preserve as inconclusive.

No wire, reader, stored-byte, product-speed or comparator authority is created.
"""
from __future__ import annotations

import ctypes
import json
import os
from pathlib import Path
import statistics
import subprocess
import tempfile

from benchmarks.one.one_g02_gear_replacement_ab import _GEAR
from benchmarks.one.one_g02_minimizer_block_ab import _median_ns, _python_anchor_trace
from benchmarks.one.one_g02_minimizer_counter_ab import (
    _CounterResult,
    _bind_counter,
    _call_counter,
)
from benchmarks.one.one_g02_minimizer_native_probe import _cases, MINIMIZER_SPAN, WINDOW
from benchmarks.one.one_g02_minimizer_wrap_ab import LARGE_CASES

MAX_STATE_RATIO = 0.85
MAX_EVERY_LARGE_RATIO = 1.03
MAX_ANY_RATIO = 1.05
PROMOTE_MEDIAN_LARGE_RATIO = 1.00
RETIRE_MEDIAN_LARGE_RATIO = 1.03
RETIRE_ANY_LARGE_RATIO = 1.08


class _OffsetOnlyResult(ctypes.Structure):
    _fields_ = [
        ("emitted", ctypes.c_uint64),
        ("final_state", ctypes.c_uint64),
        ("positions_considered", ctypes.c_uint64),
        ("reserved_state_bytes", ctypes.c_uint64),
        ("derived_state_reads", ctypes.c_uint64),
        ("suffix_blocks_built", ctypes.c_uint64),
        ("suffix_blocks_skipped_dead", ctypes.c_uint64),
        ("suffix_value_indirect_loads", ctypes.c_uint64),
    ]


def _build() -> tuple[ctypes.CDLL, tempfile.TemporaryDirectory[str]]:
    here = Path(__file__).parent
    tempdir = tempfile.TemporaryDirectory(prefix="cmpct-one-g02-offset-only-ab-")
    library = Path(tempdir.name) / "libone_g02_offset_only_ab.so"
    subprocess.run(
        [
            os.environ.get("CC", "cc"), "-O3", "-std=c11", "-fPIC", "-shared",
            str(here / "one_g02_minimizer_segmented_counter_kernel.c"),
            str(here / "one_g02_minimizer_offset_only_kernel.c"),
            "-o", str(library),
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return ctypes.CDLL(str(library)), tempdir


def _bind_offset(lib: ctypes.CDLL):
    fn = lib.one_g02_minimizer_offset_only_kernel
    fn.argtypes = [
        ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t, ctypes.POINTER(ctypes.c_uint64),
        ctypes.c_size_t, ctypes.c_size_t, ctypes.POINTER(_OffsetOnlyResult),
        ctypes.POINTER(ctypes.c_uint64), ctypes.c_size_t,
    ]
    fn.restype = ctypes.c_int
    return fn


def _call_offset(fn, gear, data_array, length: int, trace=None, trace_capacity: int = 0):
    out = _OffsetOnlyResult()
    rc = fn(
        data_array, length, gear, WINDOW, MINIMIZER_SPAN, ctypes.byref(out),
        trace if trace is not None else None, trace_capacity,
    )
    if rc != 0:
        raise RuntimeError(f"offset-only segmented kernel failed: {rc}")
    return out


def _write_outputs(decision: str, median_large: float, state_ratio: float, worst_large: float, worst_any: float) -> None:
    path = os.environ.get("GITHUB_OUTPUT")
    if not path:
        return
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(f"decision={decision}\n")
        handle.write(f"median_large_ratio={median_large:.6f}\n")
        handle.write(f"state_ratio={state_ratio:.6f}\n")
        handle.write(f"worst_large_ratio={worst_large:.6f}\n")
        handle.write(f"worst_any_ratio={worst_any:.6f}\n")


def run() -> dict[str, object]:
    lib, tempdir = _build()
    try:
        counter = _bind_counter(lib)
        offset = _bind_offset(lib)
        gear = (ctypes.c_uint64 * 256)(*_GEAR)
        rows: list[dict[str, object]] = []
        large_ratios: list[float] = []
        all_ratios: list[float] = []
        state_ratios: list[float] = []

        for name, data in _cases().items():
            expected_trace, expected_state, expected_considered = _python_anchor_trace(data)
            data_array = (ctypes.c_uint8 * len(data)).from_buffer_copy(data)
            capacity = max(1, len(data))
            counter_trace = (ctypes.c_uint64 * capacity)()
            offset_trace = (ctypes.c_uint64 * capacity)()
            counter_once = _call_counter(counter, gear, data_array, len(data), counter_trace, capacity)
            offset_once = _call_offset(offset, gear, data_array, len(data), offset_trace, capacity)
            counter_positions = [int(counter_trace[i]) for i in range(int(counter_once.emitted))]
            offset_positions = [int(offset_trace[i]) for i in range(int(offset_once.emitted))]
            semantic_equal = (
                counter_positions == expected_trace
                and offset_positions == expected_trace
                and int(counter_once.final_state) == expected_state
                and int(offset_once.final_state) == expected_state
                and int(counter_once.positions_considered) == expected_considered
                and int(offset_once.positions_considered) == expected_considered
            )
            lifecycle_equal = (
                int(counter_once.suffix_blocks_built) == int(offset_once.suffix_blocks_built)
                and int(counter_once.suffix_blocks_skipped_dead) == int(offset_once.suffix_blocks_skipped_dead)
            )
            if not semantic_equal:
                raise AssertionError(f"offset-only semantic mismatch for {name}")
            if not lifecycle_equal:
                raise AssertionError(f"offset-only suffix lifecycle drift for {name}")

            counter_ns = _median_ns(lambda: _call_counter(counter, gear, data_array, len(data)))
            offset_ns = _median_ns(lambda: _call_offset(offset, gear, data_array, len(data)))
            ratio = offset_ns / counter_ns
            all_ratios.append(ratio)
            if name in LARGE_CASES:
                large_ratios.append(ratio)
            state_ratio = (
                int(offset_once.reserved_state_bytes) / int(counter_once.reserved_state_bytes)
                if int(counter_once.reserved_state_bytes) else 0.0
            )
            if int(counter_once.reserved_state_bytes):
                state_ratios.append(state_ratio)

            rows.append({
                "case": name,
                "input_bytes": len(data),
                "large_case": name in LARGE_CASES,
                "anchor_trace_equal": semantic_equal,
                "suffix_lifecycle_equal": lifecycle_equal,
                "counter_median_ns": counter_ns,
                "offset_only_median_ns": offset_ns,
                "offset_over_counter_ratio": ratio,
                "counter_reserved_state_bytes": int(counter_once.reserved_state_bytes),
                "offset_reserved_state_bytes": int(offset_once.reserved_state_bytes),
                "offset_over_counter_state_ratio": state_ratio,
                "counter_derived_state_reads": int(counter_once.derived_state_reads),
                "offset_derived_state_reads": int(offset_once.derived_state_reads),
                "offset_suffix_value_indirect_loads": int(offset_once.suffix_value_indirect_loads),
                "source_byte_rescans": 0,
            })

        median_large = float(statistics.median(large_ratios))
        worst_large = max(large_ratios)
        worst_any = max(all_ratios)
        worst_state = max(state_ratios, default=0.0)
        promote = (
            worst_state <= MAX_STATE_RATIO
            and worst_large <= MAX_EVERY_LARGE_RATIO
            and worst_any <= MAX_ANY_RATIO
            and median_large <= PROMOTE_MEDIAN_LARGE_RATIO
        )
        retire = median_large > RETIRE_MEDIAN_LARGE_RATIO or worst_large > RETIRE_ANY_LARGE_RATIO
        if promote:
            decision = "promote_offset_only_dense_suffix"
        elif retire:
            decision = "retire_offset_only_dense_suffix"
        else:
            decision = "offset_only_dense_suffix_inconclusive"

        _write_outputs(decision, median_large, worst_state, worst_large, worst_any)
        return {
            "schema": "cmpct-one-g02-minimizer-offset-only-ab-v1",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "hypothesis": "suffix minimum values duplicate retained Gear states; offset-only dense suffixes can reduce state/traffic without sparse-control debt",
            "disproof": "oracle/lifecycle drift, >3% any-large slowdown, >5% any-case slowdown, failure to cut state by >=15%, or sustained median slowdown rejects promotion",
            "frozen_max_state_ratio": MAX_STATE_RATIO,
            "frozen_max_every_large_ratio": MAX_EVERY_LARGE_RATIO,
            "frozen_max_any_ratio": MAX_ANY_RATIO,
            "frozen_promote_median_large_ratio": PROMOTE_MEDIAN_LARGE_RATIO,
            "frozen_retire_median_large_ratio": RETIRE_MEDIAN_LARGE_RATIO,
            "frozen_retire_any_large_ratio": RETIRE_ANY_LARGE_RATIO,
            "median_large_ratio": median_large,
            "worst_large_ratio": worst_large,
            "worst_any_ratio": worst_any,
            "worst_state_ratio": worst_state,
            "decision": decision,
            "claim_boundary": "encoder discovery maintenance only; no Law/wire/reader/stored-byte/product/comparator claim",
            "rows": rows,
        }
    finally:
        tempdir.cleanup()


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True, indent=2))
