"""ONE-G0.2 timing-confidence instrument: paired ABBA replay of surviving Builders.

Why this exists
---------------
The immutable single-batch A/Bs remain evidence, but exact-head replays changed the frozen
promotion label for identical counter/offset code while preserving the direction of most
large-case effects. Their timer measures all baseline repetitions before all candidate
repetitions, so runner frequency/thermal drift can enter the ratio.

This new instrument does not rewrite any old threshold or result. It freezes an order-neutral
paired protocol: warm both arms, then measure A-B-B-A rounds and divide the within-round mean
candidate time by the within-round mean baseline time. Small inputs are batched to reduce
Python/clock quantization while retaining allocator cost inside each kernel call.

Confidence interpretation (frozen before execution)
---------------------------------------------------
For each pair and case we report median, p10 and p90 paired ratios over 9 ABBA rounds. A speed
effect is `repeatably_positive` only when every large-case median <=0.97 and every large-case
p90 <=1.00. It is `repeatably_negative` when any large-case median >=1.05. Otherwise it is
`timing_uncertain`. This is a confidence classifier, not a replacement promotion gate.

Exact anchor semantics are independently checked before timing. No bytes, source traffic,
state accounting, selector, reader or wire semantics are gifted.
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
from benchmarks.one.one_g02_minimizer_inplace_fullblock_ab import _bind_inplace, _call_inplace
from benchmarks.one.one_g02_minimizer_native_probe import _cases, MINIMIZER_SPAN, WINDOW
from benchmarks.one.one_g02_minimizer_offset_only_ab import _bind_offset, _call_offset
from benchmarks.one.one_g02_minimizer_segmented_tail_ab import _bind_tail, _call_tail
from benchmarks.one.one_g02_minimizer_wrap_ab import LARGE_CASES

ROUNDS = 9
POSITIVE_MEDIAN = 0.97
POSITIVE_P90 = 1.00
NEGATIVE_MEDIAN = 1.05


def _build() -> tuple[ctypes.CDLL, tempfile.TemporaryDirectory[str]]:
    here = Path(__file__).parent
    td = tempfile.TemporaryDirectory(prefix="cmpct-one-g02-paired-")
    lib = Path(td.name) / "libone_g02_paired.so"
    subprocess.run(
        [
            os.environ.get("CC", "cc"), "-O3", "-std=c11", "-fPIC", "-shared",
            str(here / "one_g02_minimizer_segmented_tail_kernel.c"),
            str(here / "one_g02_minimizer_segmented_counter_kernel.c"),
            str(here / "one_g02_minimizer_offset_only_kernel.c"),
            str(here / "one_g02_minimizer_inplace_fullblock_kernel.c"),
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
        return 64
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
    # Warm allocator/code pages symmetrically before evidence.
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


def _classify(rows: list[dict[str, object]]) -> str:
    large = [r for r in rows if r["large_case"]]
    if all(float(r["median_ratio"]) <= POSITIVE_MEDIAN and float(r["p90_ratio"]) <= POSITIVE_P90 for r in large):
        return "repeatably_positive"
    if any(float(r["median_ratio"]) >= NEGATIVE_MEDIAN for r in large):
        return "repeatably_negative"
    return "timing_uncertain"


def run() -> dict[str, object]:
    lib, td = _build()
    try:
        tail = _bind_tail(lib)
        counter = _bind_counter(lib)
        offset = _bind_offset(lib)
        inplace = _bind_inplace(lib)
        gear = (ctypes.c_uint64 * 256)(*_GEAR)
        pairs = (
            ("counter_over_tail", tail, _call_tail, counter, _call_counter),
            ("offset_over_counter", counter, _call_counter, offset, _call_offset),
            ("inplace_fullblock_over_counter", counter, _call_counter, inplace, _call_inplace),
        )
        pair_rows: dict[str, list[dict[str, object]]] = {p[0]: [] for p in pairs}

        for name, data in _cases().items():
            expected_trace, expected_state, expected_considered = _python_anchor_trace(data)
            arr = (ctypes.c_uint8 * len(data)).from_buffer_copy(data)
            capacity = max(1, len(data))
            bound = []
            for pair_name, a_fn, a_call, b_fn, b_call in pairs:
                at = (ctypes.c_uint64 * capacity)()
                bt = (ctypes.c_uint64 * capacity)()
                ao = a_call(a_fn, gear, arr, len(data), at, capacity)
                bo = b_call(b_fn, gear, arr, len(data), bt, capacity)
                atrace = [int(at[i]) for i in range(int(ao.emitted))]
                btrace = [int(bt[i]) for i in range(int(bo.emitted))]
                if (
                    atrace != expected_trace or btrace != expected_trace
                    or int(ao.final_state) != expected_state or int(bo.final_state) != expected_state
                    or int(ao.positions_considered) != expected_considered
                    or int(bo.positions_considered) != expected_considered
                ):
                    raise AssertionError(f"paired semantic mismatch: {pair_name}/{name}")
                a_thunk = lambda fn=a_fn, call=a_call: call(fn, gear, arr, len(data))
                b_thunk = lambda fn=b_fn, call=b_call: call(fn, gear, arr, len(data))
                ratios = _abba(a_thunk, b_thunk, _batch_count(len(data)))
                pair_rows[pair_name].append({
                    "case": name,
                    "input_bytes": len(data),
                    "large_case": name in LARGE_CASES,
                    "rounds": ROUNDS,
                    "batch_count": _batch_count(len(data)),
                    "median_ratio": float(statistics.median(ratios)),
                    "p10_ratio": _quantile(ratios, 0.10),
                    "p90_ratio": _quantile(ratios, 0.90),
                    "min_ratio": min(ratios),
                    "max_ratio": max(ratios),
                    "round_ratios": ratios,
                })

        classifications = {name: _classify(rows) for name, rows in pair_rows.items()}
        output = os.environ.get("GITHUB_OUTPUT")
        if output:
            with open(output, "a", encoding="utf-8") as f:
                for name, decision in classifications.items():
                    f.write(f"{name}={decision}\n")
        return {
            "schema": "cmpct-one-g02-minimizer-paired-repeatability-v1",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "protocol": "9 warm-started A-B-B-A paired rounds; per-call allocator work retained; small inputs batched",
            "frozen_positive_median_ratio": POSITIVE_MEDIAN,
            "frozen_positive_p90_ratio": POSITIVE_P90,
            "frozen_negative_median_ratio": NEGATIVE_MEDIAN,
            "classification_boundary": "confidence only; old immutable promotion/retirement gates remain historical evidence",
            "classifications": classifications,
            "pairs": pair_rows,
        }
    finally:
        td.cleanup()


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True, indent=2))
