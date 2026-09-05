"""ONE-G0.2 preregistered A/B: offset-only baseline vs sequential query cache.

Mission lock / Referee freeze before result-bearing execution
=============================================================
The rolling-min construction experiment halved a source-level suffix-build read
counter but produced only a 1.33% cross-large elapsed improvement, and generated
code remained essentially identical (326 instructions each, 150 vs 148 static
memory-operand instructions).  Meanwhile the promoted offset-only query path
still performs roughly one suffix argmin + retained-state indirect load for every
eligible query window (~1.043M loads on mature 1 MiB cases).

Within a current block the suffix start r+1 advances monotonically.  For the old
block q-4, the exact rightmost suffix argmin can only stay put until the start
passes it, then advance.  The candidate caches the current old-block suffix
value/argmin and refreshes only at those crossings.  It charges 24 B of extra
modeled discovery state and keeps suffix construction unchanged.

Frozen hypothesis
-----------------
A tiny predictable event gate at the query boundary can eliminate most of the
actual indirect suffix-value load stream and materially reduce elapsed time
without reproducing the broad event-driven-maintenance control debt.

Disproof / promotion law
------------------------
* baseline and candidate must exactly match the independent Python anchor trace,
  final Gear state and considered-position count on every standard case;
* suffix build/skipped lifecycle and derived-state-read count stay identical;
* source rescans remain zero;
* candidate state may increase only by the explicitly charged 24 B and must be
  <=1.001x baseline on enabled rows;
* on every selected row (input >=8192 B), candidate suffix-value indirect loads
  must be <=0.05x baseline;
* timing uses 17 warm-started baseline-candidate-candidate-baseline rounds;
* PROMOTE iff every selected median <=1.03x, every large p90 <=1.05x, and the
  cross-large median <=0.95x;
* REJECT for event/control debt iff any large median >=1.05x;
* otherwise preserve as inconclusive.

The 8 KiB dispatcher threshold, selector semantics, suffix representation,
reader ontology, wire format and product/comparator claims are immutable here.
"""
from __future__ import annotations

import ctypes
import json
import os
from pathlib import Path
import statistics
import subprocess
import tempfile
import time

from benchmarks.one.one_g02_gear_replacement_ab import _GEAR
from benchmarks.one.one_g02_minimizer_block_ab import _python_anchor_trace
from benchmarks.one.one_g02_minimizer_native_probe import _cases, MINIMIZER_SPAN, WINDOW
from benchmarks.one.one_g02_minimizer_offset_only_ab import _bind_offset, _call_offset
from benchmarks.one.one_g02_minimizer_wrap_ab import LARGE_CASES

ROUNDS = 17
DISPATCH_THRESHOLD = 8192
MAX_STATE_RATIO = 1.001
MAX_LOAD_RATIO = 0.05
MAX_SELECTED_MEDIAN = 1.03
MAX_LARGE_P90 = 1.05
MAX_CROSS_LARGE_MEDIAN = 0.95
REJECT_LARGE_MEDIAN = 1.05


class _QueryCacheResult(ctypes.Structure):
    _fields_ = [
        ("emitted", ctypes.c_uint64),
        ("final_state", ctypes.c_uint64),
        ("positions_considered", ctypes.c_uint64),
        ("reserved_state_bytes", ctypes.c_uint64),
        ("derived_state_reads", ctypes.c_uint64),
        ("suffix_blocks_built", ctypes.c_uint64),
        ("suffix_blocks_skipped_dead", ctypes.c_uint64),
        ("suffix_value_indirect_loads", ctypes.c_uint64),
        ("suffix_query_refreshes", ctypes.c_uint64),
        ("suffix_query_cache_hits", ctypes.c_uint64),
    ]


def _build() -> tuple[ctypes.CDLL, tempfile.TemporaryDirectory[str]]:
    here = Path(__file__).parent
    td = tempfile.TemporaryDirectory(prefix="cmpct-one-g02-query-cache-")
    lib = Path(td.name) / "lib.so"
    subprocess.run(
        [
            os.environ.get("CC", "cc"), "-O3", "-std=c11", "-fPIC", "-shared",
            str(here / "one_g02_minimizer_offset_only_kernel.c"),
            str(here / "one_g02_minimizer_offset_query_cache_kernel.c"),
            "-o", str(lib),
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return ctypes.CDLL(str(lib)), td


def _bind_candidate(lib: ctypes.CDLL):
    fn = lib.one_g02_minimizer_offset_query_cache_kernel
    fn.argtypes = [
        ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t, ctypes.POINTER(ctypes.c_uint64),
        ctypes.c_size_t, ctypes.c_size_t, ctypes.POINTER(_QueryCacheResult),
        ctypes.POINTER(ctypes.c_uint64), ctypes.c_size_t,
    ]
    fn.restype = ctypes.c_int
    return fn


def _call_candidate(fn, gear, data_array, length: int, trace=None, trace_capacity: int = 0):
    out = _QueryCacheResult()
    rc = fn(
        data_array, length, gear, WINDOW, MINIMIZER_SPAN, ctypes.byref(out),
        trace if trace is not None else None, trace_capacity,
    )
    if rc != 0:
        raise RuntimeError(f"query-cache kernel failed: {rc}")
    return out


def _batch(fn, count: int) -> float:
    start = time.perf_counter_ns()
    for _ in range(count):
        fn()
    return (time.perf_counter_ns() - start) / count


def _batch_count(n: int) -> int:
    if n < 32768:
        return 128
    if n < 262144:
        return 8
    if n < 1048576:
        return 2
    return 1


def _quantile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    x = q * (len(ordered) - 1)
    lo = int(x)
    hi = min(lo + 1, len(ordered) - 1)
    frac = x - lo
    return ordered[lo] * (1.0 - frac) + ordered[hi] * frac


def _abba(a, b, batch: int) -> list[float]:
    _batch(a, batch)
    _batch(b, batch)
    ratios: list[float] = []
    for _ in range(ROUNDS):
        a1 = _batch(a, batch)
        b1 = _batch(b, batch)
        b2 = _batch(b, batch)
        a2 = _batch(a, batch)
        ratios.append(((b1 + b2) * 0.5) / ((a1 + a2) * 0.5))
    return ratios


def run() -> dict[str, object]:
    lib, td = _build()
    try:
        baseline = _bind_offset(lib)
        candidate = _bind_candidate(lib)
        gear = (ctypes.c_uint64 * 256)(*_GEAR)
        rows: list[dict[str, object]] = []
        selected_rows: list[dict[str, object]] = []
        large_medians: list[float] = []

        for name, data in _cases().items():
            arr = (ctypes.c_uint8 * len(data)).from_buffer_copy(data)
            capacity = max(1, len(data))
            bt = (ctypes.c_uint64 * capacity)()
            ct = (ctypes.c_uint64 * capacity)()
            bo = _call_offset(baseline, gear, arr, len(data), bt, capacity)
            co = _call_candidate(candidate, gear, arr, len(data), ct, capacity)
            expected_trace, expected_state, expected_considered = _python_anchor_trace(data)
            btrace = [int(bt[i]) for i in range(int(bo.emitted))]
            ctrace = [int(ct[i]) for i in range(int(co.emitted))]
            if (
                btrace != expected_trace or ctrace != expected_trace
                or int(bo.final_state) != expected_state or int(co.final_state) != expected_state
                or int(bo.positions_considered) != expected_considered
                or int(co.positions_considered) != expected_considered
            ):
                raise AssertionError(f"query-cache semantic mismatch: {name}")
            if (
                int(bo.suffix_blocks_built) != int(co.suffix_blocks_built)
                or int(bo.suffix_blocks_skipped_dead) != int(co.suffix_blocks_skipped_dead)
                or int(bo.derived_state_reads) != int(co.derived_state_reads)
            ):
                raise AssertionError(f"query-cache suffix construction drift: {name}")

            enabled = len(data) >= MINIMIZER_SPAN + WINDOW
            selected = len(data) >= DISPATCH_THRESHOLD
            if enabled:
                state_ratio = int(co.reserved_state_bytes) / int(bo.reserved_state_bytes)
                if state_ratio > MAX_STATE_RATIO:
                    raise AssertionError(f"query-cache state debt exceeded: {name} {state_ratio}")
            else:
                state_ratio = 1.0

            baseline_loads = int(bo.suffix_value_indirect_loads)
            candidate_loads = int(co.suffix_value_indirect_loads)
            load_ratio = candidate_loads / baseline_loads if baseline_loads else 1.0
            if selected and baseline_loads and load_ratio > MAX_LOAD_RATIO:
                raise AssertionError(f"query-cache load reduction missed: {name} {load_ratio}")

            batch = _batch_count(len(data))
            a = lambda: _call_offset(baseline, gear, arr, len(data))
            b = lambda: _call_candidate(candidate, gear, arr, len(data))
            ratios = _abba(a, b, batch)
            median = float(statistics.median(ratios))
            p90 = float(_quantile(ratios, 0.90))
            row = {
                "case": name,
                "input_bytes": len(data),
                "selected_by_8k_dispatch": selected,
                "large_case": name in LARGE_CASES,
                "rounds": ROUNDS,
                "batch_count": batch,
                "baseline_reserved_state_bytes": int(bo.reserved_state_bytes),
                "candidate_reserved_state_bytes": int(co.reserved_state_bytes),
                "state_ratio": state_ratio,
                "derived_state_reads": int(co.derived_state_reads),
                "baseline_suffix_value_indirect_loads": baseline_loads,
                "candidate_suffix_value_indirect_loads": candidate_loads,
                "suffix_value_load_ratio": load_ratio,
                "suffix_query_refreshes": int(co.suffix_query_refreshes),
                "suffix_query_cache_hits": int(co.suffix_query_cache_hits),
                "median_cache_over_offset": median,
                "p10_cache_over_offset": float(_quantile(ratios, 0.10)),
                "p90_cache_over_offset": p90,
                "min_cache_over_offset": min(ratios),
                "max_cache_over_offset": max(ratios),
                "source_byte_rescans": 0,
            }
            rows.append(row)
            if selected:
                selected_rows.append(row)
            if name in LARGE_CASES:
                large_medians.append(median)

        cross_large_median = float(statistics.median(large_medians))
        promote = (
            all(float(r["median_cache_over_offset"]) <= MAX_SELECTED_MEDIAN for r in selected_rows)
            and all(float(r["p90_cache_over_offset"]) <= MAX_LARGE_P90 for r in rows if r["large_case"])
            and cross_large_median <= MAX_CROSS_LARGE_MEDIAN
        )
        if promote:
            decision = "promote_offset_suffix_query_cache"
        elif any(float(r["median_cache_over_offset"]) >= REJECT_LARGE_MEDIAN for r in rows if r["large_case"]):
            decision = "reject_suffix_query_cache_for_control_debt"
        else:
            decision = "suffix_query_cache_inconclusive"

        output = os.environ.get("GITHUB_OUTPUT")
        if output:
            with open(output, "a", encoding="utf-8") as f:
                f.write(f"decision={decision}\n")
                f.write(f"cross_large_median={cross_large_median:.6f}\n")

        return {
            "schema": "cmpct-one-g02-offset-query-cache-ab-v1",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "hypothesis": "monotone suffix-start cache can remove per-window indirect loads with a cheap predictable refresh gate",
            "protocol": "17 warm-started offset-cache-cache-offset rounds; small cases batched",
            "frozen_dispatch_threshold": DISPATCH_THRESHOLD,
            "frozen_max_state_ratio": MAX_STATE_RATIO,
            "frozen_max_load_ratio": MAX_LOAD_RATIO,
            "frozen_max_selected_median": MAX_SELECTED_MEDIAN,
            "frozen_max_large_p90": MAX_LARGE_P90,
            "frozen_max_cross_large_median": MAX_CROSS_LARGE_MEDIAN,
            "frozen_reject_large_median": REJECT_LARGE_MEDIAN,
            "cross_large_median_cache_over_offset": cross_large_median,
            "decision": decision,
            "claim_boundary": "encoder-discovery query maintenance only; no reader/wire/stored-byte/product/comparator authority",
            "rows": rows,
        }
    finally:
        td.cleanup()


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True, indent=2))
