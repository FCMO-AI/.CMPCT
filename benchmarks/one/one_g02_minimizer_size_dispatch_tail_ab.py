"""ONE-G0.2 superseding A/B: tail-return rehabilitation of 8 KiB dispatch.

Referee freeze before result-bearing execution
==============================================
The first 8 KiB dispatcher was rejected under its immutable gate.  It selected
the intended algorithms correctly but copied the selected result field-by-field
and exported tiny-path overhead; cross-large improvement also missed the 5%
research-baseline bar.  This superseding Builder changes only integration cost:
its common result prefix is ABI-compatible with both selector results, the path
bit is written before dispatch, and the selected call is returned directly.

The 8192-byte boundary, payload identities, 13-round warm-started A-B-B-A
protocol and promotion/rejection thresholds are copied unchanged from the
rejected Builder.  This is not a second chance with easier rules.

Promotion requires exact oracle semantics/path/state, every counter-region
median <=1.03 and p90 <=1.05, every offset-region median <=0.98 and p90 <=1.03,
and cross-large median <=0.95.  Any counter-region median >1.05 or any large
median >=1.03 rejects the rehabilitation.  Otherwise it remains inconclusive.
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
from benchmarks.one.one_g02_minimizer_block_ab import _python_anchor_trace
from benchmarks.one.one_g02_minimizer_counter_ab import _bind_counter, _call_counter
from benchmarks.one.one_g02_minimizer_native_probe import MINIMIZER_SPAN, WINDOW
from benchmarks.one.one_g02_minimizer_size_dispatch_ab import (
    _DispatchResult,
    _abba,
    _batch_count,
    _payloads,
    _quantile,
    MAX_COUNTER_MEDIAN,
    MAX_COUNTER_P90,
    MAX_CROSS_LARGE_MEDIAN,
    MAX_OFFSET_MEDIAN,
    MAX_OFFSET_P90,
    REJECT_COUNTER_MEDIAN,
    REJECT_LARGE_MEDIAN,
    REGIMES,
    ROUNDS,
    SIZES,
    THRESHOLD,
)


def _build():
    here = Path(__file__).parent
    td = tempfile.TemporaryDirectory(prefix="cmpct-one-g02-size-dispatch-tail-")
    lib = Path(td.name) / "lib.so"
    subprocess.run(
        [
            os.environ.get("CC", "cc"), "-O3", "-std=c11", "-fPIC", "-shared",
            str(here / "one_g02_minimizer_segmented_counter_kernel.c"),
            str(here / "one_g02_minimizer_offset_only_kernel.c"),
            str(here / "one_g02_minimizer_size_dispatch_tail_kernel.c"),
            "-o", str(lib),
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return ctypes.CDLL(str(lib)), td


def _bind_dispatch(lib: ctypes.CDLL):
    fn = lib.one_g02_minimizer_size_dispatch_tail_kernel
    fn.argtypes = [
        ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t, ctypes.POINTER(ctypes.c_uint64),
        ctypes.c_size_t, ctypes.c_size_t, ctypes.POINTER(_DispatchResult),
        ctypes.POINTER(ctypes.c_uint64), ctypes.c_size_t,
    ]
    fn.restype = ctypes.c_int
    return fn


def _call_dispatch(fn, gear, arr, length: int, trace=None, capacity: int = 0):
    out = _DispatchResult()
    rc = fn(arr, length, gear, WINDOW, MINIMIZER_SPAN, ctypes.byref(out), trace, capacity)
    if rc != 0:
        raise RuntimeError(f"tail size dispatcher failed: {rc}")
    return out


def run() -> dict[str, object]:
    lib, td = _build()
    try:
        cfn = _bind_counter(lib)
        dfn = _bind_dispatch(lib)
        gear = (ctypes.c_uint64 * 256)(*_GEAR)
        rows: list[dict[str, object]] = []
        large_medians: list[float] = []

        for requested in SIZES:
            for regime, data in _payloads(requested).items():
                arr = (ctypes.c_uint8 * len(data)).from_buffer_copy(data)
                capacity = max(1, len(data))
                ct = (ctypes.c_uint64 * capacity)()
                dt = (ctypes.c_uint64 * capacity)()
                co = _call_counter(cfn, gear, arr, len(data), ct, capacity)
                do = _call_dispatch(dfn, gear, arr, len(data), dt, capacity)
                expected, state, considered = _python_anchor_trace(data)
                if (
                    [int(ct[i]) for i in range(int(co.emitted))] != expected
                    or [int(dt[i]) for i in range(int(do.emitted))] != expected
                    or int(co.final_state) != state or int(do.final_state) != state
                    or int(co.positions_considered) != considered or int(do.positions_considered) != considered
                ):
                    raise AssertionError((requested, regime, "semantic"))
                expect_offset = len(data) >= THRESHOLD
                if bool(do.selected_offset_path) != expect_offset:
                    raise AssertionError((requested, regime, "dispatch", len(data)))
                expected_state_bytes = 41056 if expect_offset and len(data) >= MINIMIZER_SPAN + WINDOW else int(co.reserved_state_bytes)
                if int(do.reserved_state_bytes) != expected_state_bytes:
                    raise AssertionError((requested, regime, "state", int(do.reserved_state_bytes), expected_state_bytes))

                batch = _batch_count(len(data))
                counter = lambda: _call_counter(cfn, gear, arr, len(data))
                dispatch = lambda: _call_dispatch(dfn, gear, arr, len(data))
                ratios = _abba(counter, dispatch, batch)
                median = float(statistics.median(ratios))
                p90 = _quantile(ratios, 0.90)
                large = len(data) >= 262144
                if large:
                    large_medians.append(median)
                rows.append({
                    "requested_size": requested,
                    "actual_input_bytes": len(data),
                    "regime": regime,
                    "selected_offset_path": expect_offset,
                    "large_case": large,
                    "rounds": ROUNDS,
                    "batch_count": batch,
                    "median_dispatch_over_counter": median,
                    "p10_dispatch_over_counter": _quantile(ratios, 0.10),
                    "p90_dispatch_over_counter": p90,
                    "min_dispatch_over_counter": min(ratios),
                    "max_dispatch_over_counter": max(ratios),
                    "counter_reserved_state_bytes": int(co.reserved_state_bytes),
                    "dispatch_reserved_state_bytes": int(do.reserved_state_bytes),
                    "source_byte_rescans": 0,
                })

        counter_rows = [r for r in rows if not r["selected_offset_path"]]
        offset_rows = [r for r in rows if r["selected_offset_path"]]
        large_rows = [r for r in rows if r["large_case"]]
        cross_large_median = float(statistics.median(large_medians))
        promote = (
            all(float(r["median_dispatch_over_counter"]) <= MAX_COUNTER_MEDIAN and float(r["p90_dispatch_over_counter"]) <= MAX_COUNTER_P90 for r in counter_rows)
            and all(float(r["median_dispatch_over_counter"]) <= MAX_OFFSET_MEDIAN and float(r["p90_dispatch_over_counter"]) <= MAX_OFFSET_P90 for r in offset_rows)
            and cross_large_median <= MAX_CROSS_LARGE_MEDIAN
        )
        if promote:
            decision = "promote_tail_8k_size_dispatch"
        elif (
            any(float(r["median_dispatch_over_counter"]) > REJECT_COUNTER_MEDIAN for r in counter_rows)
            or any(float(r["median_dispatch_over_counter"]) >= REJECT_LARGE_MEDIAN for r in large_rows)
        ):
            decision = "reject_tail_8k_dispatch_for_elapsed_debt"
        else:
            decision = "tail_size_dispatch_inconclusive"

        output = os.environ.get("GITHUB_OUTPUT")
        if output:
            with open(output, "a", encoding="utf-8") as f:
                f.write(f"decision={decision}\n")
                f.write(f"cross_large_median={cross_large_median:.6f}\n")
        return {
            "schema": "cmpct-one-g02-minimizer-size-dispatch-tail-ab-v1",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "frozen_threshold_bytes": THRESHOLD,
            "frozen_sizes": SIZES,
            "regimes": REGIMES,
            "rounds": ROUNDS,
            "frozen_gate_source": "one_g02_minimizer_size_dispatch_ab.py unchanged thresholds/protocol",
            "cross_large_median_dispatch_over_counter": cross_large_median,
            "decision": decision,
            "claim_boundary": "encoder-discovery integration rehabilitation only; no reader/wire/stored-byte/product/comparator authority",
            "rows": rows,
        }
    finally:
        td.cleanup()


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True, indent=2))
