"""ONE-G0.2 paired crossover map for counter vs offset-only suffix state.

Referee freeze before result-bearing execution
==============================================
The 17-round Pareto replay showed a structural regime split: offset-only is
~20% faster on all 1 MiB-class large cases and uses 16.63% less state, while
exact enablement at 4,160 B is slower.  That blocks a single unconditional
baseline but makes size-gated discovery a causal opportunity question.

This instrument freezes the existing geometric size ladder and three content
regimes, then runs warm-started A-B-B-A timing at every size.  It selects a
candidate dispatch boundary mechanically; no threshold is chosen after seeing
results.

Frozen selection law
--------------------
Candidate thresholds are the enabled requested sizes in ascending order.  The
selected threshold is the smallest T for which *every* tested row at requested
size >= T has median offset/counter <=0.98 and p90 <=1.03.  If no such T exists,
`no_stable_offset_region` is returned.  This map itself does not promote a
dispatcher.  A selected boundary must be validated by a separately frozen
end-to-end dispatcher A/B before baseline promotion.

Both implementations must match the independent Python anchor oracle.  No
source rescans, Law, reader, wire format, or stored-byte semantics change.
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
from benchmarks.one.one_g02_minimizer_offset_only_ab import _bind_offset, _call_offset

SIZES = (4160, 8192, 16384, 32768, 65536, 131072, 262144, 524288, 1048576)
REGIMES = ("random", "repeated_4k_basis", "zlib_random")
ROUNDS = 9
MAX_MEDIAN = 0.98
MAX_P90 = 1.03


def _build():
    here = Path(__file__).parent
    td = tempfile.TemporaryDirectory(prefix="cmpct-one-g02-offset-cross-paired-")
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


def _payloads(size: int) -> dict[str, bytes]:
    rnd = random.Random(0xC0FFEE + size).randbytes(size)
    basis = random.Random(0x51A7).randbytes(4096)
    repeated = (basis * ((size + len(basis) - 1) // len(basis)))[:size]
    compressed = zlib.compress(random.Random(0xBADC0DE + size).randbytes(size), 9)
    return {"random": rnd, "repeated_4k_basis": repeated, "zlib_random": compressed}


def _batch_count(n: int) -> int:
    if n <= 16384:
        return 64
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


def _abba(counter, offset, batch: int) -> list[float]:
    _batch(counter, batch); _batch(offset, batch)
    ratios: list[float] = []
    for _ in range(ROUNDS):
        c1 = _batch(counter, batch)
        o1 = _batch(offset, batch)
        o2 = _batch(offset, batch)
        c2 = _batch(counter, batch)
        ratios.append(((o1 + o2) * 0.5) / ((c1 + c2) * 0.5))
    return ratios


def run() -> dict[str, object]:
    lib, td = _build()
    try:
        cfn = _bind_counter(lib)
        ofn = _bind_offset(lib)
        gear = (ctypes.c_uint64 * 256)(*_GEAR)
        rows: list[dict[str, object]] = []

        for requested in SIZES:
            for regime, data in _payloads(requested).items():
                arr = (ctypes.c_uint8 * len(data)).from_buffer_copy(data)
                capacity = max(1, len(data))
                ct = (ctypes.c_uint64 * capacity)()
                ot = (ctypes.c_uint64 * capacity)()
                co = _call_counter(cfn, gear, arr, len(data), ct, capacity)
                oo = _call_offset(ofn, gear, arr, len(data), ot, capacity)
                expected, state, considered = _python_anchor_trace(data)
                if (
                    [int(ct[i]) for i in range(int(co.emitted))] != expected
                    or [int(ot[i]) for i in range(int(oo.emitted))] != expected
                    or int(co.final_state) != state or int(oo.final_state) != state
                    or int(co.positions_considered) != considered or int(oo.positions_considered) != considered
                ):
                    raise AssertionError((requested, regime))
                batch = _batch_count(len(data))
                counter = lambda: _call_counter(cfn, gear, arr, len(data))
                offset = lambda: _call_offset(ofn, gear, arr, len(data))
                ratios = _abba(counter, offset, batch)
                rows.append({
                    "requested_size": requested,
                    "actual_input_bytes": len(data),
                    "regime": regime,
                    "rounds": ROUNDS,
                    "batch_count": batch,
                    "median_ratio": float(statistics.median(ratios)),
                    "p10_ratio": _quantile(ratios, 0.10),
                    "p90_ratio": _quantile(ratios, 0.90),
                    "min_ratio": min(ratios),
                    "max_ratio": max(ratios),
                    "counter_reserved_state_bytes": int(co.reserved_state_bytes),
                    "offset_reserved_state_bytes": int(oo.reserved_state_bytes),
                    "source_byte_rescans": 0,
                })

        selected: int | None = None
        for threshold in SIZES:
            region = [r for r in rows if int(r["requested_size"]) >= threshold]
            if region and all(float(r["median_ratio"]) <= MAX_MEDIAN and float(r["p90_ratio"]) <= MAX_P90 for r in region):
                selected = threshold
                break

        summary = {}
        for size in SIZES:
            rr = [r for r in rows if int(r["requested_size"]) == size]
            summary[str(size)] = {
                "median_of_regime_medians": float(statistics.median(float(r["median_ratio"]) for r in rr)),
                "worst_regime_median": max(float(r["median_ratio"]) for r in rr),
                "worst_regime_p90": max(float(r["p90_ratio"]) for r in rr),
            }
        decision = f"candidate_dispatch_from_{selected}" if selected is not None else "no_stable_offset_region"
        output = os.environ.get("GITHUB_OUTPUT")
        if output:
            with open(output, "a", encoding="utf-8") as f:
                f.write(f"decision={decision}\n")
                f.write(f"selected_threshold={selected if selected is not None else 'none'}\n")
        return {
            "schema": "cmpct-one-g02-minimizer-offset-crossover-paired-v1",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "frozen_requested_sizes": SIZES,
            "regimes": REGIMES,
            "rounds": ROUNDS,
            "frozen_max_median_ratio": MAX_MEDIAN,
            "frozen_max_p90_ratio": MAX_P90,
            "decision": decision,
            "selected_threshold_requested_bytes": selected,
            "summary_by_requested_size": summary,
            "claim_boundary": "paired crossover/dispatch-candidate discovery only; no dispatcher promotion or product authority",
            "rows": rows,
        }
    finally:
        td.cleanup()


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True, indent=2))
