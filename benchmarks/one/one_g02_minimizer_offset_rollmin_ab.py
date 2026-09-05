"""ONE-G0.2 preregistered causal A/B: offset-only suffix vs rolling-min suffix build.

Mission lock / Referee freeze before result-bearing execution
=============================================================
Paired residual attribution no longer supports treating dense-suffix construction
or exact selection as a stable isolated global owner: their rank flips across
hosted reruns while both remain much larger than buffer/prefix work.  The current
offset-only kernel also exposes a concrete shared-work defect: during backwards
suffix construction it reloads block_values[next_argmin] even though that value
is exactly the running suffix minimum already established by the previous step.

Hypothesis
----------
Carry the running suffix minimum value and argmin offset in registers while
building the existing uint16 suffix-offset table.  This should cut suffix-build
derived-state reads by about half without changing state layout, query path,
rightmost-min tie semantics, source traffic, reader semantics, or the promoted
8 KiB counter/offset dispatch law.

Disproof / promotion law (frozen before execution)
-------------------------------------------------
* both kernels must exactly match the independent Python anchor oracle, final
  Gear state and considered-position count on every standard case;
* suffix block lifecycle, enabled reserved state and query-time indirect-load
  count must remain identical between baseline offset-only and rolling-min;
* source-byte rescans remain zero;
* on every enabled case, rolling derived-state reads must be <=0.55x baseline;
* timing uses 13 warm-started baseline-candidate-candidate-baseline rounds;
* timing promotion is judged only where the offset path is selected by the
  already-promoted law (input >=8192 B): every selected-case median <=1.03x,
  every large-case p90 <=1.05x, and cross-large median <=0.97x;
* reject for elapsed debt if any large-case median >=1.05x; otherwise preserve
  as inconclusive.

No size threshold, selector semantics, reader opcode, wire format, stored-byte
claim, product-speed claim, or comparator authority may change in this test.
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
from benchmarks.one.one_g02_minimizer_offset_only_ab import _OffsetOnlyResult, _bind_offset, _call_offset
from benchmarks.one.one_g02_minimizer_wrap_ab import LARGE_CASES

ROUNDS = 13
DISPATCH_THRESHOLD = 8192
MAX_DERIVED_READ_RATIO = 0.55
MAX_SELECTED_MEDIAN = 1.03
MAX_LARGE_P90 = 1.05
MAX_CROSS_LARGE_MEDIAN = 0.97
REJECT_LARGE_MEDIAN = 1.05


def _build() -> tuple[ctypes.CDLL, tempfile.TemporaryDirectory[str]]:
    here = Path(__file__).parent
    td = tempfile.TemporaryDirectory(prefix="cmpct-one-g02-offset-rollmin-")
    lib = Path(td.name) / "lib.so"
    subprocess.run(
        [
            os.environ.get("CC", "cc"), "-O3", "-std=c11", "-fPIC", "-shared",
            str(here / "one_g02_minimizer_offset_only_kernel.c"),
            str(here / "one_g02_minimizer_offset_rollmin_kernel.c"),
            "-o", str(lib),
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return ctypes.CDLL(str(lib)), td


def _bind_rollmin(lib: ctypes.CDLL):
    fn = lib.one_g02_minimizer_offset_rollmin_kernel
    fn.argtypes = [
        ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t, ctypes.POINTER(ctypes.c_uint64),
        ctypes.c_size_t, ctypes.c_size_t, ctypes.POINTER(_OffsetOnlyResult),
        ctypes.POINTER(ctypes.c_uint64), ctypes.c_size_t,
    ]
    fn.restype = ctypes.c_int
    return fn


def _call(fn, gear, data_array, length: int, trace=None, trace_capacity: int = 0):
    out = _OffsetOnlyResult()
    rc = fn(
        data_array, length, gear, WINDOW, MINIMIZER_SPAN, ctypes.byref(out),
        trace if trace is not None else None, trace_capacity,
    )
    if rc != 0:
        raise RuntimeError(f"rolling-min kernel failed: {rc}")
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
        candidate = _bind_rollmin(lib)
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
            co = _call(candidate, gear, arr, len(data), ct, capacity)
            expected_trace, expected_state, expected_considered = _python_anchor_trace(data)
            btrace = [int(bt[i]) for i in range(int(bo.emitted))]
            ctrace = [int(ct[i]) for i in range(int(co.emitted))]
            if (
                btrace != expected_trace or ctrace != expected_trace
                or int(bo.final_state) != expected_state or int(co.final_state) != expected_state
                or int(bo.positions_considered) != expected_considered
                or int(co.positions_considered) != expected_considered
            ):
                raise AssertionError(f"rolling-min semantic mismatch: {name}")
            if (
                int(bo.suffix_blocks_built) != int(co.suffix_blocks_built)
                or int(bo.suffix_blocks_skipped_dead) != int(co.suffix_blocks_skipped_dead)
                or int(bo.reserved_state_bytes) != int(co.reserved_state_bytes)
                or int(bo.suffix_value_indirect_loads) != int(co.suffix_value_indirect_loads)
            ):
                raise AssertionError(f"rolling-min lifecycle/state/query drift: {name}")

            enabled = len(data) >= MINIMIZER_SPAN + WINDOW
            selected = len(data) >= DISPATCH_THRESHOLD
            if enabled and int(bo.derived_state_reads):
                read_ratio = int(co.derived_state_reads) / int(bo.derived_state_reads)
                if read_ratio > MAX_DERIVED_READ_RATIO:
                    raise AssertionError(f"derived read reduction missed: {name} {read_ratio}")
            else:
                read_ratio = 1.0

            batch = _batch_count(len(data))
            a = lambda: _call_offset(baseline, gear, arr, len(data))
            b = lambda: _call(candidate, gear, arr, len(data))
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
                "baseline_derived_state_reads": int(bo.derived_state_reads),
                "candidate_derived_state_reads": int(co.derived_state_reads),
                "derived_state_read_ratio": read_ratio,
                "suffix_value_indirect_loads": int(co.suffix_value_indirect_loads),
                "median_rollmin_over_offset": median,
                "p10_rollmin_over_offset": float(_quantile(ratios, 0.10)),
                "p90_rollmin_over_offset": p90,
                "min_rollmin_over_offset": min(ratios),
                "max_rollmin_over_offset": max(ratios),
                "source_byte_rescans": 0,
            }
            rows.append(row)
            if selected:
                selected_rows.append(row)
            if name in LARGE_CASES:
                large_medians.append(median)

        cross_large_median = float(statistics.median(large_medians))
        promote = (
            all(float(r["median_rollmin_over_offset"]) <= MAX_SELECTED_MEDIAN for r in selected_rows)
            and all(float(r["p90_rollmin_over_offset"]) <= MAX_LARGE_P90 for r in rows if r["large_case"])
            and cross_large_median <= MAX_CROSS_LARGE_MEDIAN
        )
        if promote:
            decision = "promote_offset_rollmin_suffix_fusion"
        elif any(float(r["median_rollmin_over_offset"]) >= REJECT_LARGE_MEDIAN for r in rows if r["large_case"]):
            decision = "reject_offset_rollmin_for_elapsed_debt"
        else:
            decision = "offset_rollmin_inconclusive"

        output = os.environ.get("GITHUB_OUTPUT")
        if output:
            with open(output, "a", encoding="utf-8") as f:
                f.write(f"decision={decision}\n")
                f.write(f"cross_large_median={cross_large_median:.6f}\n")

        return {
            "schema": "cmpct-one-g02-offset-rollmin-ab-v1",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "hypothesis": "carry suffix running min in registers to eliminate redundant retained-state loads without moving cost into selection",
            "protocol": "13 warm-started offset-rollmin-rollmin-offset rounds; small cases batched",
            "frozen_dispatch_threshold": DISPATCH_THRESHOLD,
            "frozen_max_derived_read_ratio": MAX_DERIVED_READ_RATIO,
            "frozen_max_selected_median": MAX_SELECTED_MEDIAN,
            "frozen_max_large_p90": MAX_LARGE_P90,
            "frozen_max_cross_large_median": MAX_CROSS_LARGE_MEDIAN,
            "frozen_reject_large_median": REJECT_LARGE_MEDIAN,
            "cross_large_median_rollmin_over_offset": cross_large_median,
            "decision": decision,
            "claim_boundary": "encoder-discovery suffix/selection fusion only; no reader/wire/stored-byte/product/comparator authority",
            "rows": rows,
        }
    finally:
        td.cleanup()


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True, indent=2))
