"""ONE-G0.2 preregistered causal A/B: offset-only suffix build vs cached recurrence.

Mission lock / Referee
======================
The offset-only dense suffix candidate removed duplicated uint64 suffix values and
retained only uint16 argmins, cutting reserved state by about one sixth, but its
backward suffix build then reread block_values[next_argmin] on every step.  The
suffix recurrence already carries the minimum value and argmin from i+1 to i.
The Builder in one_g02_minimizer_offset_cached_kernel.c keeps that recurrence
state in scalar registers and writes only the argmin table.

This experiment changes no Gear identity, window/span, selector, source pass,
reader surface, Law, wire representation, state budget, or proof semantics.  It
isolates redundant derived-state read traffic during suffix construction.

Frozen decision law before result-bearing execution
----------------------------------------------------
* cached and offset-only emitted anchor positions, final Gear state and considered
  positions must equal the independent Python oracle on every case;
* suffix block build/skip lifecycle and query-time suffix-value indirect-load
  counts must match exactly;
* cached reserved state must equal offset-only reserved state;
* on every enabled case cached derived-state reads must be <=0.51x offset-only;
* no tested case may be >1.05x offset-only elapsed;
* PROMOTE the recurrence cache as the new offset-only implementation if every
  large case is <=0.97x offset-only and median large-case elapsed is <=0.95x;
* RETIRE redundant build-time reads as a primary elapsed owner if median large
  elapsed is >=0.99x despite the required traffic reduction; otherwise preserve
  as inconclusive.

Counter-baseline timing/state are retained only to show whether the rehabilitated
offset representation approaches the promoted counter baseline.  They do not
rewrite the immutable earlier offset-only decision gate.  No stored-byte,
product-speed, reader, v0.29 or v0.30 authority is created.
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
from benchmarks.one.one_g02_minimizer_counter_ab import _bind_counter, _call_counter
from benchmarks.one.one_g02_minimizer_native_probe import _cases, MINIMIZER_SPAN, WINDOW
from benchmarks.one.one_g02_minimizer_offset_only_ab import (
    _OffsetOnlyResult,
    _bind_offset,
    _call_offset,
)
from benchmarks.one.one_g02_minimizer_wrap_ab import LARGE_CASES

MAX_TRAFFIC_RATIO = 0.51
MAX_ANY_RATIO = 1.05
PROMOTE_EVERY_LARGE_RATIO = 0.97
PROMOTE_MEDIAN_LARGE_RATIO = 0.95
RETIRE_MEDIAN_LARGE_RATIO = 0.99


def _build() -> tuple[ctypes.CDLL, tempfile.TemporaryDirectory[str]]:
    here = Path(__file__).parent
    tempdir = tempfile.TemporaryDirectory(prefix="cmpct-one-g02-offset-cached-ab-")
    library = Path(tempdir.name) / "libone_g02_offset_cached_ab.so"
    subprocess.run(
        [
            os.environ.get("CC", "cc"), "-O3", "-std=c11", "-fPIC", "-shared",
            str(here / "one_g02_minimizer_segmented_counter_kernel.c"),
            str(here / "one_g02_minimizer_offset_only_kernel.c"),
            str(here / "one_g02_minimizer_offset_cached_kernel.c"),
            "-o", str(library),
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return ctypes.CDLL(str(library)), tempdir


def _bind_cached(lib: ctypes.CDLL):
    fn = lib.one_g02_minimizer_offset_cached_kernel
    fn.argtypes = [
        ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t, ctypes.POINTER(ctypes.c_uint64),
        ctypes.c_size_t, ctypes.c_size_t, ctypes.POINTER(_OffsetOnlyResult),
        ctypes.POINTER(ctypes.c_uint64), ctypes.c_size_t,
    ]
    fn.restype = ctypes.c_int
    return fn


def _call_cached(fn, gear, data_array, length: int, trace=None, trace_capacity: int = 0):
    out = _OffsetOnlyResult()
    rc = fn(
        data_array, length, gear, WINDOW, MINIMIZER_SPAN, ctypes.byref(out),
        trace if trace is not None else None, trace_capacity,
    )
    if rc != 0:
        raise RuntimeError(f"offset-cached segmented kernel failed: {rc}")
    return out


def _write_outputs(decision: str, median_large: float, worst_large: float, worst_any: float, traffic_ratio: float) -> None:
    path = os.environ.get("GITHUB_OUTPUT")
    if not path:
        return
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(f"decision={decision}\n")
        handle.write(f"median_large_ratio={median_large:.6f}\n")
        handle.write(f"worst_large_ratio={worst_large:.6f}\n")
        handle.write(f"worst_any_ratio={worst_any:.6f}\n")
        handle.write(f"worst_traffic_ratio={traffic_ratio:.6f}\n")


def run() -> dict[str, object]:
    lib, tempdir = _build()
    try:
        counter = _bind_counter(lib)
        offset = _bind_offset(lib)
        cached = _bind_cached(lib)
        gear = (ctypes.c_uint64 * 256)(*_GEAR)
        rows: list[dict[str, object]] = []
        large_ratios: list[float] = []
        all_ratios: list[float] = []
        traffic_ratios: list[float] = []

        for name, data in _cases().items():
            expected_trace, expected_state, expected_considered = _python_anchor_trace(data)
            data_array = (ctypes.c_uint8 * len(data)).from_buffer_copy(data)
            capacity = max(1, len(data))
            offset_trace = (ctypes.c_uint64 * capacity)()
            cached_trace = (ctypes.c_uint64 * capacity)()
            counter_once = _call_counter(counter, gear, data_array, len(data))
            offset_once = _call_offset(offset, gear, data_array, len(data), offset_trace, capacity)
            cached_once = _call_cached(cached, gear, data_array, len(data), cached_trace, capacity)
            offset_positions = [int(offset_trace[i]) for i in range(int(offset_once.emitted))]
            cached_positions = [int(cached_trace[i]) for i in range(int(cached_once.emitted))]
            semantic_equal = (
                offset_positions == expected_trace
                and cached_positions == expected_trace
                and int(offset_once.final_state) == expected_state
                and int(cached_once.final_state) == expected_state
                and int(offset_once.positions_considered) == expected_considered
                and int(cached_once.positions_considered) == expected_considered
            )
            lifecycle_equal = (
                int(offset_once.suffix_blocks_built) == int(cached_once.suffix_blocks_built)
                and int(offset_once.suffix_blocks_skipped_dead) == int(cached_once.suffix_blocks_skipped_dead)
            )
            query_loads_equal = int(offset_once.suffix_value_indirect_loads) == int(cached_once.suffix_value_indirect_loads)
            state_equal = int(offset_once.reserved_state_bytes) == int(cached_once.reserved_state_bytes)
            if not semantic_equal:
                raise AssertionError(f"offset-cached semantic mismatch for {name}")
            if not lifecycle_equal or not query_loads_equal or not state_equal:
                raise AssertionError(f"offset-cached accounting/lifecycle drift for {name}")

            offset_reads = int(offset_once.derived_state_reads)
            cached_reads = int(cached_once.derived_state_reads)
            traffic_ratio = cached_reads / offset_reads if offset_reads else 0.0
            if offset_reads:
                traffic_ratios.append(traffic_ratio)
                if traffic_ratio > MAX_TRAFFIC_RATIO:
                    raise AssertionError(f"offset-cached traffic reduction missed for {name}: {traffic_ratio:.6f}")

            counter_ns = _median_ns(lambda: _call_counter(counter, gear, data_array, len(data)))
            offset_ns = _median_ns(lambda: _call_offset(offset, gear, data_array, len(data)))
            cached_ns = _median_ns(lambda: _call_cached(cached, gear, data_array, len(data)))
            ratio = cached_ns / offset_ns
            all_ratios.append(ratio)
            if name in LARGE_CASES:
                large_ratios.append(ratio)

            rows.append({
                "case": name,
                "input_bytes": len(data),
                "large_case": name in LARGE_CASES,
                "anchor_trace_equal": semantic_equal,
                "suffix_lifecycle_equal": lifecycle_equal,
                "query_indirect_loads_equal": query_loads_equal,
                "reserved_state_equal": state_equal,
                "counter_median_ns": counter_ns,
                "offset_only_median_ns": offset_ns,
                "offset_cached_median_ns": cached_ns,
                "cached_over_offset_elapsed_ratio": ratio,
                "cached_over_counter_elapsed_ratio": cached_ns / counter_ns,
                "counter_reserved_state_bytes": int(counter_once.reserved_state_bytes),
                "offset_reserved_state_bytes": int(offset_once.reserved_state_bytes),
                "cached_reserved_state_bytes": int(cached_once.reserved_state_bytes),
                "offset_derived_state_reads": offset_reads,
                "cached_derived_state_reads": cached_reads,
                "cached_over_offset_derived_read_ratio": traffic_ratio,
                "suffix_value_indirect_loads": int(cached_once.suffix_value_indirect_loads),
                "source_byte_rescans": 0,
            })

        median_large = float(statistics.median(large_ratios))
        worst_large = max(large_ratios)
        worst_any = max(all_ratios)
        worst_traffic = max(traffic_ratios, default=0.0)
        promote = (
            worst_traffic <= MAX_TRAFFIC_RATIO
            and worst_any <= MAX_ANY_RATIO
            and worst_large <= PROMOTE_EVERY_LARGE_RATIO
            and median_large <= PROMOTE_MEDIAN_LARGE_RATIO
        )
        if promote:
            decision = "promote_cached_offset_recurrence"
        elif median_large >= RETIRE_MEDIAN_LARGE_RATIO:
            decision = "retire_redundant_suffix_build_reads_as_primary_owner"
        else:
            decision = "cached_offset_recurrence_inconclusive"

        _write_outputs(decision, median_large, worst_large, worst_any, worst_traffic)
        return {
            "schema": "cmpct-one-g02-minimizer-offset-cached-ab-v1",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "hypothesis": "carrying suffix minimum value/argmin in scalar recurrence removes redundant build-time derived-state reads and materially lowers offset-only maintenance elapsed without changing selector semantics or state",
            "disproof": "oracle/accounting drift, >0.51x retained build-read traffic, >5% any-case regression, failure to improve every large case by >=3%, or median large improvement <5% blocks promotion; median >=0.99x retires redundant reads as primary owner",
            "frozen_max_traffic_ratio": MAX_TRAFFIC_RATIO,
            "frozen_max_any_ratio": MAX_ANY_RATIO,
            "frozen_promote_every_large_ratio": PROMOTE_EVERY_LARGE_RATIO,
            "frozen_promote_median_large_ratio": PROMOTE_MEDIAN_LARGE_RATIO,
            "frozen_retire_median_large_ratio": RETIRE_MEDIAN_LARGE_RATIO,
            "median_large_ratio": median_large,
            "worst_large_ratio": worst_large,
            "worst_any_ratio": worst_any,
            "worst_traffic_ratio": worst_traffic,
            "decision": decision,
            "claim_boundary": "encoder discovery suffix-maintenance A/B only; no Law/wire/reader/stored-byte/product/comparator authority",
            "rows": rows,
        }
    finally:
        tempdir.cleanup()


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True, indent=2))
