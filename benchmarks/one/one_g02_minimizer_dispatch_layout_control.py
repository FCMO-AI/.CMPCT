"""ONE-G0.2 paired layout control for offset-only and tail dispatch.

Referee freeze before result-bearing execution
==============================================
The same offset-only source showed very different speed ratios when compiled
alone with the counter selector versus linked with the 8 KiB dispatcher.  The
tail dispatcher itself compiles to a 25-instruction zero-call branch/tail-jump
shape, yet the integrated large-case gain shrank materially.

This diagnostic loads two independently compiled shared objects in one process:

* BASE: counter + offset-only;
* AUGMENTED: counter + offset-only + tail dispatcher.

For the same frozen payloads it runs warm-started A-B-B-A measurements for
(1) base offset/base counter, (2) augmented offset/augmented counter, and
(3) augmented tail-dispatch/augmented direct-offset.  It changes no algorithm.

Frozen interpretation law
-------------------------
* wrapper overhead is `negligible` only when every tested dispatch/direct-offset
  median is in [0.97,1.03] and p90 <=1.05;
* binary-layout sensitivity is `supported` when at least half of tested large
  rows shift the direct offset/counter median by >=0.04 between BASE and
  AUGMENTED while wrapper overhead is negligible;
* otherwise the result is mixed/inconclusive and no threshold/implementation
  move follows from it.

Static/link placement is a diagnostic dimension, not a product optimization.
No reader, Law, wire, stored-byte or comparator authority is created.
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
from benchmarks.one.one_g02_minimizer_counter_ab import _bind_counter, _call_counter
from benchmarks.one.one_g02_minimizer_offset_only_ab import _bind_offset, _call_offset
from benchmarks.one.one_g02_minimizer_size_dispatch_ab import _payloads, _quantile
from benchmarks.one.one_g02_minimizer_size_dispatch_tail_ab import _bind_dispatch, _call_dispatch

SIZES = (8192, 16384, 65536, 262144, 1048576)
REGIMES = ("random", "repeated_4k_basis", "zlib_random")
ROUNDS = 11
WRAPPER_MIN_MEDIAN = 0.97
WRAPPER_MAX_MEDIAN = 1.03
WRAPPER_MAX_P90 = 1.05
LAYOUT_SHIFT = 0.04


def _compile(sources: list[Path], output: Path) -> None:
    subprocess.run(
        [os.environ.get("CC", "cc"), "-O3", "-std=c11", "-fPIC", "-shared", *map(str, sources), "-o", str(output)],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


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


def _summarize(ratios: list[float]) -> dict[str, float]:
    return {
        "median": float(statistics.median(ratios)),
        "p10": _quantile(ratios, 0.10),
        "p90": _quantile(ratios, 0.90),
        "min": min(ratios),
        "max": max(ratios),
    }


def run() -> dict[str, object]:
    here = Path(__file__).parent
    with tempfile.TemporaryDirectory(prefix="cmpct-one-g02-layout-control-") as td:
        td_path = Path(td)
        common = [
            here / "one_g02_minimizer_segmented_counter_kernel.c",
            here / "one_g02_minimizer_offset_only_kernel.c",
        ]
        base_path = td_path / "libbase.so"
        augmented_path = td_path / "libaugmented.so"
        _compile(common, base_path)
        _compile(common + [here / "one_g02_minimizer_size_dispatch_tail_kernel.c"], augmented_path)
        base = ctypes.CDLL(str(base_path))
        aug = ctypes.CDLL(str(augmented_path))
        bc = _bind_counter(base); bo = _bind_offset(base)
        ac = _bind_counter(aug); ao = _bind_offset(aug); ad = _bind_dispatch(aug)
        gear = (ctypes.c_uint64 * 256)(*_GEAR)
        rows: list[dict[str, object]] = []
        large_shift_hits = 0
        large_rows = 0
        wrapper_ok = True

        for requested in SIZES:
            for regime, data in _payloads(requested).items():
                arr = (ctypes.c_uint8 * len(data)).from_buffer_copy(data)
                batch = _batch_count(len(data))
                base_counter = lambda: _call_counter(bc, gear, arr, len(data))
                base_offset = lambda: _call_offset(bo, gear, arr, len(data))
                aug_counter = lambda: _call_counter(ac, gear, arr, len(data))
                aug_offset = lambda: _call_offset(ao, gear, arr, len(data))
                aug_dispatch = lambda: _call_dispatch(ad, gear, arr, len(data))
                base_ratio = _summarize(_abba(base_counter, base_offset, batch))
                aug_ratio = _summarize(_abba(aug_counter, aug_offset, batch))
                wrapper_ratio = _summarize(_abba(aug_offset, aug_dispatch, batch))
                shift = abs(aug_ratio["median"] - base_ratio["median"])
                large = len(data) >= 262144
                if large:
                    large_rows += 1
                    if shift >= LAYOUT_SHIFT:
                        large_shift_hits += 1
                if not (
                    WRAPPER_MIN_MEDIAN <= wrapper_ratio["median"] <= WRAPPER_MAX_MEDIAN
                    and wrapper_ratio["p90"] <= WRAPPER_MAX_P90
                ):
                    wrapper_ok = False
                rows.append({
                    "requested_size": requested,
                    "actual_input_bytes": len(data),
                    "regime": regime,
                    "large_case": large,
                    "batch_count": batch,
                    "base_offset_over_counter": base_ratio,
                    "augmented_offset_over_counter": aug_ratio,
                    "tail_dispatch_over_direct_offset": wrapper_ratio,
                    "absolute_layout_ratio_shift": shift,
                })

        layout_supported = wrapper_ok and large_rows > 0 and large_shift_hits * 2 >= large_rows
        if layout_supported:
            decision = "binary_layout_sensitivity_supported"
        elif wrapper_ok:
            decision = "wrapper_negligible_layout_not_materially_supported"
        else:
            decision = "wrapper_or_layout_effect_mixed"
        output = os.environ.get("GITHUB_OUTPUT")
        if output:
            with open(output, "a", encoding="utf-8") as f:
                f.write(f"decision={decision}\n")
                f.write(f"large_shift_hits={large_shift_hits}\n")
                f.write(f"large_rows={large_rows}\n")
        return {
            "schema": "cmpct-one-g02-minimizer-dispatch-layout-control-v1",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "rounds": ROUNDS,
            "frozen_sizes": SIZES,
            "regimes": REGIMES,
            "frozen_wrapper_median_interval": [WRAPPER_MIN_MEDIAN, WRAPPER_MAX_MEDIAN],
            "frozen_wrapper_max_p90": WRAPPER_MAX_P90,
            "frozen_layout_shift": LAYOUT_SHIFT,
            "large_shift_hits": large_shift_hits,
            "large_rows": large_rows,
            "decision": decision,
            "claim_boundary": "binary-composition/layout diagnostic only; no implementation, threshold or product authority",
            "rows": rows,
        }


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True, indent=2))
