"""ONE-G0.2 preregistered end-to-end A/B for 8 KiB selector dispatch.

Mission lock / Referee
======================
A paired geometric crossover selected 8192 input bytes mechanically as the
smallest tested region where offset-only beats the counter selector across all
frozen content regimes.  This Builder charges the actual C branch/wrapper: use
counter below 8192 bytes and offset-only at/above 8192.  The representation is
encoder-discovery state only; reader/Law/wire semantics do not branch.

Frozen promotion law before result-bearing execution
----------------------------------------------------
* dispatcher and counter must both reproduce the independent Python anchor
  oracle on every case;
* dispatcher path must be counter iff actual length <8192, offset otherwise;
* dispatcher state must equal the selected implementation's state;
* 13 warm-started counter-dispatch-dispatch-counter rounds per case, with tiny
  inputs batched;
* every counter-region case median dispatch/counter <=1.03 and p90 <=1.05;
* every offset-region case median <=0.98 and p90 <=1.03;
* cross-large median <=0.95;
* PROMOTE only if all conditions hold.  Any counter-region median >1.05 or any
  large median >=1.03 rejects the wrapper for exported elapsed debt; otherwise
  preserve as inconclusive.

The 8192 boundary is frozen from prior evidence and cannot move in this test.
No comparator, stored-byte, product-speed, reader or release authority is made.
"""
from __future__ import annotations

import ctypes
import json
import os
import random
from pathlib import Path
import statistics
import subprocess
import tempfile
import time
import zlib

from benchmarks.one.one_g02_gear_replacement_ab import _GEAR
from benchmarks.one.one_g02_minimizer_block_ab import _python_anchor_trace
from benchmarks.one.one_g02_minimizer_counter_ab import _bind_counter, _call_counter
from benchmarks.one.one_g02_minimizer_native_probe import MINIMIZER_SPAN, WINDOW

THRESHOLD = 8192
SIZES = (1024, 4159, 4160, 8191, 8192, 16384, 65536, 262144, 1048576)
REGIMES = ("random", "repeated_4k_basis", "zlib_random")
ROUNDS = 13
MAX_COUNTER_MEDIAN = 1.03
MAX_COUNTER_P90 = 1.05
MAX_OFFSET_MEDIAN = 0.98
MAX_OFFSET_P90 = 1.03
MAX_CROSS_LARGE_MEDIAN = 0.95
REJECT_COUNTER_MEDIAN = 1.05
REJECT_LARGE_MEDIAN = 1.03


class _DispatchResult(ctypes.Structure):
    _fields_ = [
        ("emitted", ctypes.c_uint64),
        ("final_state", ctypes.c_uint64),
        ("positions_considered", ctypes.c_uint64),
        ("reserved_state_bytes", ctypes.c_uint64),
        ("derived_state_reads", ctypes.c_uint64),
        ("suffix_blocks_built", ctypes.c_uint64),
        ("suffix_blocks_skipped_dead", ctypes.c_uint64),
        ("suffix_value_indirect_loads", ctypes.c_uint64),
        ("selected_offset_path", ctypes.c_uint64),
    ]


def _build():
    here = Path(__file__).parent
    td = tempfile.TemporaryDirectory(prefix="cmpct-one-g02-size-dispatch-")
    lib = Path(td.name) / "lib.so"
    subprocess.run(
        [
            os.environ.get("CC", "cc"), "-O3", "-std=c11", "-fPIC", "-shared",
            str(here / "one_g02_minimizer_segmented_counter_kernel.c"),
            str(here / "one_g02_minimizer_offset_only_kernel.c"),
            str(here / "one_g02_minimizer_size_dispatch_kernel.c"),
            "-o", str(lib),
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return ctypes.CDLL(str(lib)), td


def _bind_dispatch(lib: ctypes.CDLL):
    fn = lib.one_g02_minimizer_size_dispatch_kernel
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
        raise RuntimeError(f"size dispatcher failed: {rc}")
    return out


def _payloads(size: int) -> dict[str, bytes]:
    rnd = random.Random(0xD15A7C + size).randbytes(size)
    basis = random.Random(0x51A7).randbytes(4096)
    repeated = (basis * ((size + len(basis) - 1) // len(basis)))[:size]
    compressed = zlib.compress(random.Random(0xBAD5EED + size).randbytes(size), 9)
    return {"random": rnd, "repeated_4k_basis": repeated, "zlib_random": compressed}


def _batch_count(n: int) -> int:
    if n <= 8192:
        return 128
    if n <= 65536:
        return 16
    if n <= 262144:
        return 4
    return 1


def _batch(fn, count: int) -> float:
    start = time.perf_counter_ns()
    for _ in range(count):
        fn()
    return (time.perf_counter_ns() - start) / count


def _quantile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    x = q * (len(ordered) - 1)
    lo = int(x)
    hi = min(lo + 1, len(ordered) - 1)
    frac = x - lo
    return ordered[lo] * (1.0 - frac) + ordered[hi] * frac


def _abba(counter, dispatch, batch: int) -> list[float]:
    _batch(counter, batch); _batch(dispatch, batch)
    ratios = []
    for _ in range(ROUNDS):
        c1 = _batch(counter, batch)
        d1 = _batch(dispatch, batch)
        d2 = _batch(dispatch, batch)
        c2 = _batch(counter, batch)
        ratios.append(((d1 + d2) * 0.5) / ((c1 + c2) * 0.5))
    return ratios


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
            decision = "promote_8k_size_dispatch"
        elif (
            any(float(r["median_dispatch_over_counter"]) > REJECT_COUNTER_MEDIAN for r in counter_rows)
            or any(float(r["median_dispatch_over_counter"]) >= REJECT_LARGE_MEDIAN for r in large_rows)
        ):
            decision = "reject_8k_dispatch_for_elapsed_debt"
        else:
            decision = "size_dispatch_inconclusive"

        output = os.environ.get("GITHUB_OUTPUT")
        if output:
            with open(output, "a", encoding="utf-8") as f:
                f.write(f"decision={decision}\n")
                f.write(f"cross_large_median={cross_large_median:.6f}\n")
        return {
            "schema": "cmpct-one-g02-minimizer-size-dispatch-ab-v1",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "frozen_threshold_bytes": THRESHOLD,
            "frozen_sizes": SIZES,
            "regimes": REGIMES,
            "rounds": ROUNDS,
            "frozen_max_counter_median": MAX_COUNTER_MEDIAN,
            "frozen_max_counter_p90": MAX_COUNTER_P90,
            "frozen_max_offset_median": MAX_OFFSET_MEDIAN,
            "frozen_max_offset_p90": MAX_OFFSET_P90,
            "frozen_max_cross_large_median": MAX_CROSS_LARGE_MEDIAN,
            "cross_large_median_dispatch_over_counter": cross_large_median,
            "decision": decision,
            "claim_boundary": "encoder-discovery research baseline only; no reader/wire/stored-byte/product/comparator authority",
            "rows": rows,
        }
    finally:
        td.cleanup()


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True, indent=2))
