"""ONE-G0.2 preregistered causal A/B: runtime div/mod vs monotone block counters.

Mission lock / Referee:
The promoted tail-aware four-segment minimizer still reconstructs q/r from
state_index with division and remainder on every considered state.  Because
block_size is a runtime parameter, this may leave an integer-division-shaped
cost in the hot loop.  The Builder changes only coordinate maintenance: q/r
become monotone counters.  Gear identity, exact rightmost-minimum semantics,
suffix/prefix algorithms, tail-dead-work elimination, state budget and source
traffic are unchanged.

Disproof / decision law, frozen before result-bearing execution:
* every emitted anchor trace, final Gear state and considered count must equal
  the independent Python oracle on every case;
* reserved state, derived-state reads, suffix blocks built/skipped and source
  rescans must remain identical to the promoted tail-aware baseline;
* PROMOTE only if every large case is at least 5% faster, median large-case
  elapsed is at least 10% faster, and no tested case regresses by >5%;
* RETIRE as primary owner if median large-case improvement is <2% or any large
  case regresses by >10%; otherwise preserve as inconclusive evidence.

This is encoder-discovery microkernel evidence only.  It grants no wire,
reader, stored-byte, product-speed, v0.29 or deferred-v0.30 authority.
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
from benchmarks.one.one_g02_minimizer_native_probe import _cases, MINIMIZER_SPAN, WINDOW
from benchmarks.one.one_g02_minimizer_segmented_tail_ab import (
    _TailResult,
    _bind_tail,
    _call_tail,
)
from benchmarks.one.one_g02_minimizer_wrap_ab import LARGE_CASES

PROMOTE_EVERY_LARGE_RATIO = 0.95
PROMOTE_MEDIAN_LARGE_RATIO = 0.90
MAX_ANY_CASE_RATIO = 1.05
RETIRE_MEDIAN_LARGE_RATIO = 0.98
RETIRE_ANY_LARGE_RATIO = 1.10


class _CounterResult(ctypes.Structure):
    _fields_ = _TailResult._fields_


def _build() -> tuple[ctypes.CDLL, tempfile.TemporaryDirectory[str]]:
    here = Path(__file__).parent
    tempdir = tempfile.TemporaryDirectory(prefix="cmpct-one-g02-counter-ab-")
    library = Path(tempdir.name) / "libone_g02_counter_ab.so"
    subprocess.run(
        [
            os.environ.get("CC", "cc"),
            "-O3",
            "-std=c11",
            "-fPIC",
            "-shared",
            str(here / "one_g02_minimizer_segmented_tail_kernel.c"),
            str(here / "one_g02_minimizer_segmented_counter_kernel.c"),
            "-o",
            str(library),
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return ctypes.CDLL(str(library)), tempdir


def _bind_counter(lib: ctypes.CDLL):
    fn = lib.one_g02_minimizer_segmented_counter_kernel
    fn.argtypes = [
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_uint64),
        ctypes.c_size_t,
        ctypes.c_size_t,
        ctypes.POINTER(_CounterResult),
        ctypes.POINTER(ctypes.c_uint64),
        ctypes.c_size_t,
    ]
    fn.restype = ctypes.c_int
    return fn


def _call_counter(fn, gear, data_array, length: int, trace=None, trace_capacity: int = 0):
    out = _CounterResult()
    rc = fn(
        data_array,
        length,
        gear,
        WINDOW,
        MINIMIZER_SPAN,
        ctypes.byref(out),
        trace if trace is not None else None,
        trace_capacity,
    )
    if rc != 0:
        raise RuntimeError(f"counter segmented kernel failed: {rc}")
    return out


def _write_github_output(decision: str, median_large_ratio: float, worst_ratio: float) -> None:
    path = os.environ.get("GITHUB_OUTPUT")
    if not path:
        return
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(f"decision={decision}\n")
        handle.write(f"median_large_ratio={median_large_ratio:.6f}\n")
        handle.write(f"worst_ratio={worst_ratio:.6f}\n")


def run() -> dict[str, object]:
    lib, tempdir = _build()
    try:
        tail = _bind_tail(lib)
        counter = _bind_counter(lib)
        gear = (ctypes.c_uint64 * 256)(*_GEAR)
        rows: list[dict[str, object]] = []
        large_ratios: list[float] = []
        all_ratios: list[float] = []

        for name, data in _cases().items():
            expected_trace, expected_state, expected_considered = _python_anchor_trace(data)
            data_array = (ctypes.c_uint8 * len(data)).from_buffer_copy(data)
            capacity = max(1, len(data))
            tail_trace = (ctypes.c_uint64 * capacity)()
            counter_trace = (ctypes.c_uint64 * capacity)()
            tail_once = _call_tail(tail, gear, data_array, len(data), tail_trace, capacity)
            counter_once = _call_counter(counter, gear, data_array, len(data), counter_trace, capacity)
            tail_positions = [int(tail_trace[i]) for i in range(int(tail_once.emitted))]
            counter_positions = [int(counter_trace[i]) for i in range(int(counter_once.emitted))]

            semantic_equal = (
                tail_positions == expected_trace
                and counter_positions == expected_trace
                and int(tail_once.final_state) == expected_state
                and int(counter_once.final_state) == expected_state
                and int(tail_once.positions_considered) == expected_considered
                and int(counter_once.positions_considered) == expected_considered
            )
            accounting_equal = (
                int(counter_once.reserved_state_bytes) == int(tail_once.reserved_state_bytes)
                and int(counter_once.derived_state_reads) == int(tail_once.derived_state_reads)
                and int(counter_once.suffix_blocks_built) == int(tail_once.suffix_blocks_built)
                and int(counter_once.suffix_blocks_skipped_dead) == int(tail_once.suffix_blocks_skipped_dead)
            )
            if not semantic_equal:
                raise AssertionError(f"counter semantic mismatch for {name}")
            if not accounting_equal:
                raise AssertionError(f"counter accounting drift for {name}")

            tail_ns = _median_ns(lambda: _call_tail(tail, gear, data_array, len(data)))
            counter_ns = _median_ns(lambda: _call_counter(counter, gear, data_array, len(data)))
            ratio = counter_ns / tail_ns
            all_ratios.append(ratio)
            if name in LARGE_CASES:
                large_ratios.append(ratio)

            rows.append(
                {
                    "case": name,
                    "input_bytes": len(data),
                    "large_case": name in LARGE_CASES,
                    "anchor_trace_equal": semantic_equal,
                    "accounting_equal": accounting_equal,
                    "tail_median_ns": tail_ns,
                    "counter_median_ns": counter_ns,
                    "counter_over_tail_ratio": ratio,
                    "counter_incremental_ns_per_byte": (counter_ns - tail_ns) / len(data),
                    "reserved_state_bytes": int(counter_once.reserved_state_bytes),
                    "derived_state_reads": int(counter_once.derived_state_reads),
                    "suffix_blocks_built": int(counter_once.suffix_blocks_built),
                    "suffix_blocks_skipped_dead": int(counter_once.suffix_blocks_skipped_dead),
                    "source_byte_rescans": 0,
                }
            )

        median_large_ratio = float(statistics.median(large_ratios))
        worst_ratio = max(all_ratios)
        promote = (
            all(r <= PROMOTE_EVERY_LARGE_RATIO for r in large_ratios)
            and median_large_ratio <= PROMOTE_MEDIAN_LARGE_RATIO
            and worst_ratio <= MAX_ANY_CASE_RATIO
        )
        retire = (
            median_large_ratio >= RETIRE_MEDIAN_LARGE_RATIO
            or any(r > RETIRE_ANY_LARGE_RATIO for r in large_ratios)
        )
        if promote:
            decision = "promote_counter_bookkeeping"
        elif retire:
            decision = "retire_counter_bookkeeping_as_primary_owner"
        else:
            decision = "counter_bookkeeping_inconclusive"

        _write_github_output(decision, median_large_ratio, worst_ratio)
        return {
            "schema": "cmpct-one-g02-minimizer-counter-ab-v1",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "hypothesis": "runtime quotient/remainder reconstruction materially owns promoted tail-aware minimizer cost; monotone q/r counters remove it without changing selector semantics or state traffic",
            "disproof": "semantic/accounting drift, failure to materially improve every large case, or a >5% tested-case regression disproves promotion; <2% median large gain retires it as the primary owner",
            "frozen_promote_every_large_ratio": PROMOTE_EVERY_LARGE_RATIO,
            "frozen_promote_median_large_ratio": PROMOTE_MEDIAN_LARGE_RATIO,
            "frozen_max_any_case_ratio": MAX_ANY_CASE_RATIO,
            "frozen_retire_median_large_ratio": RETIRE_MEDIAN_LARGE_RATIO,
            "frozen_retire_any_large_ratio": RETIRE_ANY_LARGE_RATIO,
            "median_large_ratio": median_large_ratio,
            "worst_ratio": worst_ratio,
            "decision": decision,
            "claim_boundary": "encoder discovery causal A/B only; no wire/reader/stored-byte/product/comparator claim",
            "rows": rows,
        }
    finally:
        tempdir.cleanup()


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True, indent=2))
