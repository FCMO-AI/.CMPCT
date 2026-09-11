"""ONE-G0.2 superseding Pareto test: counter baseline vs offset-only suffix.

Referee freeze before execution
===============================
The offset-only dense suffix cuts enabled reserved state from 49,248 B to
41,056 B (about 16.63%) but its prior all-A/all-B timing gate was inconclusive.
Later paired evidence showed that timing-order drift can move labels for the
same code.  This experiment therefore asks a narrower Pareto question with a
new, explicit freeze while preserving every historical result:

Can the lower-state offset-only representation be accepted as a research
baseline without material elapsed debt under order-neutral measurement?

Protocol and decision law
-------------------------
* exact Python anchor trace, final Gear state and considered-position count must
  match for counter and offset-only on every case;
* source rescans remain zero;
* enabled offset state must be <=0.85x counter state on every enabled case;
* 17 warm-started A-B-B-A rounds; inputs <32 KiB are batched 128 calls;
* PROMOTE lower-state offset representation iff every enabled-case median
  offset/counter <=1.03, every large-case p90 <=1.05, and cross-large median
  ratio <=1.02;
* REJECT for elapsed debt iff any large-case median >=1.05;
* otherwise preserve as inconclusive.

The 3% median / 5% tail confidence margins are intentionally tighter than a
simple 5% product-style regression allowance: this is a research-baseline
Pareto promotion, so a state win should not consume meaningful speed budget.
This freeze does not choose a size dispatch threshold and does not rewrite the
old offset-only experiment.
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
from benchmarks.one.one_g02_minimizer_counter_ab import _bind_counter, _call_counter
from benchmarks.one.one_g02_minimizer_native_probe import _cases, MINIMIZER_SPAN, WINDOW
from benchmarks.one.one_g02_minimizer_offset_only_ab import _bind_offset, _call_offset
from benchmarks.one.one_g02_minimizer_wrap_ab import LARGE_CASES

ROUNDS = 17
MAX_STATE_RATIO = 0.85
MAX_ENABLED_MEDIAN = 1.03
MAX_LARGE_P90 = 1.05
MAX_CROSS_LARGE_MEDIAN = 1.02
REJECT_LARGE_MEDIAN = 1.05


def _build():
    here = Path(__file__).parent
    td = tempfile.TemporaryDirectory(prefix="cmpct-one-g02-offset-pareto-")
    lib = Path(td.name) / "lib.so"
    subprocess.run(
        [
            os.environ.get("CC", "cc"), "-O3", "-std=c11", "-fPIC", "-shared",
            str(here / "one_g02_minimizer_segmented_counter_kernel.c"),
            str(here / "one_g02_minimizer_offset_only_kernel.c"),
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
    _batch(a, batch); _batch(b, batch)
    ratios = []
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
        counter = _bind_counter(lib)
        offset = _bind_offset(lib)
        gear = (ctypes.c_uint64 * 256)(*_GEAR)
        rows: list[dict[str, object]] = []
        large_medians: list[float] = []

        for case_name, data in _cases().items():
            arr = (ctypes.c_uint8 * len(data)).from_buffer_copy(data)
            capacity = max(1, len(data))
            ct = (ctypes.c_uint64 * capacity)()
            ot = (ctypes.c_uint64 * capacity)()
            co = _call_counter(counter, gear, arr, len(data), ct, capacity)
            oo = _call_offset(offset, gear, arr, len(data), ot, capacity)
            expected_trace, expected_state, expected_considered = _python_anchor_trace(data)
            ctrace = [int(ct[i]) for i in range(int(co.emitted))]
            otrace = [int(ot[i]) for i in range(int(oo.emitted))]
            if (
                ctrace != expected_trace or otrace != expected_trace
                or int(co.final_state) != expected_state or int(oo.final_state) != expected_state
                or int(co.positions_considered) != expected_considered
                or int(oo.positions_considered) != expected_considered
            ):
                raise AssertionError(f"counter/offset semantic mismatch: {case_name}")

            enabled = len(data) >= MINIMIZER_SPAN + WINDOW
            state_ratio = int(oo.reserved_state_bytes) / int(co.reserved_state_bytes) if int(co.reserved_state_bytes) else 1.0
            if enabled and state_ratio > MAX_STATE_RATIO:
                raise AssertionError(f"state Pareto prerequisite missed: {case_name} {state_ratio}")

            a = lambda: _call_counter(counter, gear, arr, len(data))
            b = lambda: _call_offset(offset, gear, arr, len(data))
            batch = _batch_count(len(data))
            ratios = _abba(a, b, batch)
            median = float(statistics.median(ratios))
            p90 = _quantile(ratios, 0.90)
            if case_name in LARGE_CASES:
                large_medians.append(median)
            rows.append({
                "case": case_name,
                "input_bytes": len(data),
                "enabled": enabled,
                "large_case": case_name in LARGE_CASES,
                "rounds": ROUNDS,
                "batch_count": batch,
                "counter_reserved_state_bytes": int(co.reserved_state_bytes),
                "offset_reserved_state_bytes": int(oo.reserved_state_bytes),
                "state_ratio": state_ratio,
                "median_offset_over_counter": median,
                "p10_offset_over_counter": _quantile(ratios, 0.10),
                "p90_offset_over_counter": p90,
                "min_offset_over_counter": min(ratios),
                "max_offset_over_counter": max(ratios),
                "round_ratios": ratios,
                "source_byte_rescans": 0,
            })

        enabled_rows = [r for r in rows if r["enabled"]]
        large_rows = [r for r in rows if r["large_case"]]
        cross_large_median = float(statistics.median(large_medians))
        promote = (
            all(float(r["median_offset_over_counter"]) <= MAX_ENABLED_MEDIAN for r in enabled_rows)
            and all(float(r["p90_offset_over_counter"]) <= MAX_LARGE_P90 for r in large_rows)
            and cross_large_median <= MAX_CROSS_LARGE_MEDIAN
        )
        if promote:
            decision = "promote_offset_only_pareto_baseline"
        elif any(float(r["median_offset_over_counter"]) >= REJECT_LARGE_MEDIAN for r in large_rows):
            decision = "reject_offset_only_for_elapsed_debt"
        else:
            decision = "offset_only_pareto_inconclusive"

        output = os.environ.get("GITHUB_OUTPUT")
        if output:
            with open(output, "a", encoding="utf-8") as f:
                f.write(f"decision={decision}\n")
                f.write(f"cross_large_median={cross_large_median:.6f}\n")
        return {
            "schema": "cmpct-one-g02-minimizer-offset-pareto-paired-v1",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "protocol": "17 warm-started counter-offset-offset-counter rounds; small inputs batched",
            "frozen_max_state_ratio": MAX_STATE_RATIO,
            "frozen_max_enabled_median": MAX_ENABLED_MEDIAN,
            "frozen_max_large_p90": MAX_LARGE_P90,
            "frozen_max_cross_large_median": MAX_CROSS_LARGE_MEDIAN,
            "frozen_reject_large_median": REJECT_LARGE_MEDIAN,
            "cross_large_median_offset_over_counter": cross_large_median,
            "decision": decision,
            "claim_boundary": "research discovery baseline Pareto decision only; no product-speed/format/comparator authority",
            "rows": rows,
        }
    finally:
        td.cleanup()


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True, indent=2))
