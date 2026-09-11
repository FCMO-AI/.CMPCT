"""ONE-G0.2 paired repeatability test for cached offset recurrence.

Referee freeze before result-bearing execution
==============================================
The exact-head single-batch A/B at 3b36c5e8 found the cached suffix recurrence
cut enabled-case derived reads to ~0.50024x and improved every large case by
6.6--15.6%, but its immutable promotion gate was blocked by a 19% slowdown on
4159 B -- one byte below selector enablement, where neither offset suffix
algorithm executes any suffix work.  A single all-A then all-B timer can still
confound code-layout/frequency/order effects, especially for microsecond cases.

This companion does not rewrite that gate.  It freezes 9 warm-started A-B-B-A
rounds with small-input batching and asks whether the observed enabled-case
speed effect repeats under order-neutral measurement.

Classification law
------------------
* exact oracle semantics, suffix lifecycle, reserved state and query indirect
  loads must match before timing;
* `repeatably_positive_enabled` iff every enabled case has median cached/offset
  <=0.97 and p90 <=1.00, and every large case has median <=0.95;
* `repeatably_negative_enabled` iff any enabled case has median >=1.05;
* otherwise `timing_uncertain_enabled`;
* the below-enablement 4159 B row is classified separately as
  `repeatable_unenabled_overhead` only when its median >=1.05 AND p10 >1.00;
  otherwise it is `unenabled_timing_not_repeatably_negative`.

No prior decision is promoted retroactively.  A positive result supports a new
superseding implementation freeze; a negative result sends the Builder back to
causal profiling.  No reader, Law, wire, stored-byte or comparator authority is
created.
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
from benchmarks.one.one_g02_minimizer_offset_cached_ab import _bind_cached, _call_cached
from benchmarks.one.one_g02_minimizer_wrap_ab import LARGE_CASES

ROUNDS = 9
ENABLED_MEDIAN = 0.97
ENABLED_P90 = 1.00
LARGE_MEDIAN = 0.95
NEGATIVE_MEDIAN = 1.05
UNENABLED_NEGATIVE_MEDIAN = 1.05


def _build() -> tuple[ctypes.CDLL, tempfile.TemporaryDirectory[str]]:
    here = Path(__file__).parent
    td = tempfile.TemporaryDirectory(prefix="cmpct-one-g02-offset-cached-repeat-")
    lib = Path(td.name) / "libone_g02_offset_cached_repeat.so"
    subprocess.run(
        [
            os.environ.get("CC", "cc"), "-O3", "-std=c11", "-fPIC", "-shared",
            str(here / "one_g02_minimizer_offset_only_kernel.c"),
            str(here / "one_g02_minimizer_offset_cached_kernel.c"),
            "-o", str(lib),
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return ctypes.CDLL(str(lib)), td


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
        offset = _bind_offset(lib)
        cached = _bind_cached(lib)
        gear = (ctypes.c_uint64 * 256)(*_GEAR)
        rows: list[dict[str, object]] = []

        for name, data in _cases().items():
            expected_trace, expected_state, expected_considered = _python_anchor_trace(data)
            arr = (ctypes.c_uint8 * len(data)).from_buffer_copy(data)
            capacity = max(1, len(data))
            at = (ctypes.c_uint64 * capacity)()
            bt = (ctypes.c_uint64 * capacity)()
            ao = _call_offset(offset, gear, arr, len(data), at, capacity)
            bo = _call_cached(cached, gear, arr, len(data), bt, capacity)
            atrace = [int(at[i]) for i in range(int(ao.emitted))]
            btrace = [int(bt[i]) for i in range(int(bo.emitted))]
            semantic_equal = (
                atrace == expected_trace and btrace == expected_trace
                and int(ao.final_state) == expected_state and int(bo.final_state) == expected_state
                and int(ao.positions_considered) == expected_considered
                and int(bo.positions_considered) == expected_considered
            )
            accounting_equal = (
                int(ao.reserved_state_bytes) == int(bo.reserved_state_bytes)
                and int(ao.suffix_blocks_built) == int(bo.suffix_blocks_built)
                and int(ao.suffix_blocks_skipped_dead) == int(bo.suffix_blocks_skipped_dead)
                and int(ao.suffix_value_indirect_loads) == int(bo.suffix_value_indirect_loads)
            )
            if not semantic_equal or not accounting_equal:
                raise AssertionError(f"cached repeatability semantic/accounting mismatch: {name}")

            a = lambda: _call_offset(offset, gear, arr, len(data))
            b = lambda: _call_cached(cached, gear, arr, len(data))
            batch = _batch_count(len(data))
            ratios = _abba(a, b, batch)
            rows.append({
                "case": name,
                "input_bytes": len(data),
                "enabled": len(data) >= MINIMIZER_SPAN + WINDOW,
                "large_case": name in LARGE_CASES,
                "rounds": ROUNDS,
                "batch_count": batch,
                "median_ratio": float(statistics.median(ratios)),
                "p10_ratio": _quantile(ratios, 0.10),
                "p90_ratio": _quantile(ratios, 0.90),
                "min_ratio": min(ratios),
                "max_ratio": max(ratios),
                "round_ratios": ratios,
                "offset_derived_state_reads": int(ao.derived_state_reads),
                "cached_derived_state_reads": int(bo.derived_state_reads),
                "reserved_state_bytes": int(bo.reserved_state_bytes),
            })

        enabled = [r for r in rows if r["enabled"]]
        large = [r for r in rows if r["large_case"]]
        if (
            all(float(r["median_ratio"]) <= ENABLED_MEDIAN and float(r["p90_ratio"]) <= ENABLED_P90 for r in enabled)
            and all(float(r["median_ratio"]) <= LARGE_MEDIAN for r in large)
        ):
            enabled_decision = "repeatably_positive_enabled"
        elif any(float(r["median_ratio"]) >= NEGATIVE_MEDIAN for r in enabled):
            enabled_decision = "repeatably_negative_enabled"
        else:
            enabled_decision = "timing_uncertain_enabled"

        unenabled = next(r for r in rows if r["case"] == "below_enablement_4159b")
        if float(unenabled["median_ratio"]) >= UNENABLED_NEGATIVE_MEDIAN and float(unenabled["p10_ratio"]) > 1.0:
            unenabled_decision = "repeatable_unenabled_overhead"
        else:
            unenabled_decision = "unenabled_timing_not_repeatably_negative"

        output = os.environ.get("GITHUB_OUTPUT")
        if output:
            with open(output, "a", encoding="utf-8") as f:
                f.write(f"enabled_decision={enabled_decision}\n")
                f.write(f"unenabled_decision={unenabled_decision}\n")

        return {
            "schema": "cmpct-one-g02-minimizer-offset-cached-repeatability-v1",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "protocol": "9 warm-started A-B-B-A rounds; small inputs batched; allocator work retained",
            "frozen_enabled_median_ratio": ENABLED_MEDIAN,
            "frozen_enabled_p90_ratio": ENABLED_P90,
            "frozen_large_median_ratio": LARGE_MEDIAN,
            "frozen_negative_median_ratio": NEGATIVE_MEDIAN,
            "enabled_decision": enabled_decision,
            "unenabled_decision": unenabled_decision,
            "claim_boundary": "timing confidence and causal maintenance evidence only; prior immutable gate unchanged",
            "rows": rows,
        }
    finally:
        td.cleanup()


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True, indent=2))
