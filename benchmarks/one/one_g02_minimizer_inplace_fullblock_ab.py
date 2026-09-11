"""ONE-G0.2 preregistered rehabilitation A/B: counter four-segment vs in-place full-block.

Mission lock / Referee
======================
The original full-window prefix/suffix Builder was rejected because eager 4096-state suffix
construction made the just-enabled boundary regress and because it duplicated raw block and
suffix-value arrays. Later tail-aware evidence causally proved dead EOF suffix work was the
startup debt. This rehabilitation applies that proven repair and compiles raw-state and suffix
state into one in-place value ring: outgoing suffix slot r is dead before incoming raw state r
overwrites it, while suffix r+1 is queried first.

The representation is still the exact rightmost minimum over the same 4096 inherited Gear
states. No selector, proof, source-pass, Law, Surprise, or reader semantics change.

Frozen decision law before result-bearing execution
----------------------------------------------------
* every emitted anchor trace, final Gear state and considered-position count must equal the
  independent Python oracle on every frozen case;
* source-byte rescans remain zero;
* enabled reserved state must be <=0.85x the promoted counter four-segment baseline;
* PROMOTE only if every large case is <=0.95x counter elapsed, median large is <=0.95x,
  and no tested case is >1.05x;
* RETIRE as the primary rehabilitation if median large is >=0.99x or any large case is >1.10x;
  otherwise preserve as inconclusive.

This is encoder-discovery microkernel evidence only.
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
from benchmarks.one.one_g02_minimizer_counter_ab import _bind_counter, _call_counter
from benchmarks.one.one_g02_minimizer_native_probe import _cases, MINIMIZER_SPAN, WINDOW
from benchmarks.one.one_g02_minimizer_wrap_ab import LARGE_CASES

MAX_STATE_RATIO = 0.85
PROMOTE_EVERY_LARGE_RATIO = 0.95
PROMOTE_MEDIAN_LARGE_RATIO = 0.95
MAX_ANY_RATIO = 1.05
RETIRE_MEDIAN_LARGE_RATIO = 0.99
RETIRE_ANY_LARGE_RATIO = 1.10


class _InplaceResult(ctypes.Structure):
    _fields_ = [
        ("emitted", ctypes.c_uint64),
        ("final_state", ctypes.c_uint64),
        ("positions_considered", ctypes.c_uint64),
        ("reserved_state_bytes", ctypes.c_uint64),
        ("derived_state_reads", ctypes.c_uint64),
        ("suffix_blocks_built", ctypes.c_uint64),
        ("suffix_blocks_skipped_dead", ctypes.c_uint64),
    ]


def _build() -> tuple[ctypes.CDLL, tempfile.TemporaryDirectory[str]]:
    here = Path(__file__).parent
    td = tempfile.TemporaryDirectory(prefix="cmpct-one-g02-inplace-fullblock-")
    lib = Path(td.name) / "libone_g02_inplace_fullblock.so"
    subprocess.run(
        [
            os.environ.get("CC", "cc"), "-O3", "-std=c11", "-fPIC", "-shared",
            str(here / "one_g02_minimizer_segmented_counter_kernel.c"),
            str(here / "one_g02_minimizer_inplace_fullblock_kernel.c"),
            "-o", str(lib),
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return ctypes.CDLL(str(lib)), td


def _bind_inplace(lib: ctypes.CDLL):
    fn = lib.one_g02_minimizer_inplace_fullblock_kernel
    fn.argtypes = [
        ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t, ctypes.POINTER(ctypes.c_uint64),
        ctypes.c_size_t, ctypes.c_size_t, ctypes.POINTER(_InplaceResult),
        ctypes.POINTER(ctypes.c_uint64), ctypes.c_size_t,
    ]
    fn.restype = ctypes.c_int
    return fn


def _call_inplace(fn, gear, data_array, length: int, trace=None, trace_capacity: int = 0):
    out = _InplaceResult()
    rc = fn(
        data_array, length, gear, WINDOW, MINIMIZER_SPAN, ctypes.byref(out),
        trace if trace is not None else None, trace_capacity,
    )
    if rc != 0:
        raise RuntimeError(f"in-place full-block kernel failed: {rc}")
    return out


def _write_outputs(decision: str, median_large: float, worst_large: float, worst_any: float, state_ratio: float) -> None:
    path = os.environ.get("GITHUB_OUTPUT")
    if not path:
        return
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"decision={decision}\n")
        f.write(f"median_large_ratio={median_large:.6f}\n")
        f.write(f"worst_large_ratio={worst_large:.6f}\n")
        f.write(f"worst_any_ratio={worst_any:.6f}\n")
        f.write(f"state_ratio={state_ratio:.6f}\n")


def run() -> dict[str, object]:
    lib, td = _build()
    try:
        counter = _bind_counter(lib)
        inplace = _bind_inplace(lib)
        gear = (ctypes.c_uint64 * 256)(*_GEAR)
        rows: list[dict[str, object]] = []
        large_ratios: list[float] = []
        all_ratios: list[float] = []
        state_ratios: list[float] = []

        for name, data in _cases().items():
            expected_trace, expected_state, expected_considered = _python_anchor_trace(data)
            arr = (ctypes.c_uint8 * len(data)).from_buffer_copy(data)
            capacity = max(1, len(data))
            ct = (ctypes.c_uint64 * capacity)()
            it = (ctypes.c_uint64 * capacity)()
            c = _call_counter(counter, gear, arr, len(data), ct, capacity)
            i = _call_inplace(inplace, gear, arr, len(data), it, capacity)
            counter_trace = [int(ct[x]) for x in range(int(c.emitted))]
            inplace_trace = [int(it[x]) for x in range(int(i.emitted))]
            semantic_equal = (
                counter_trace == expected_trace
                and inplace_trace == expected_trace
                and int(c.final_state) == expected_state
                and int(i.final_state) == expected_state
                and int(c.positions_considered) == expected_considered
                and int(i.positions_considered) == expected_considered
            )
            if not semantic_equal:
                raise AssertionError(f"in-place full-block semantic mismatch for {name}")

            c_ns = _median_ns(lambda: _call_counter(counter, gear, arr, len(data)))
            i_ns = _median_ns(lambda: _call_inplace(inplace, gear, arr, len(data)))
            ratio = i_ns / c_ns
            all_ratios.append(ratio)
            if name in LARGE_CASES:
                large_ratios.append(ratio)
            state_ratio = (
                int(i.reserved_state_bytes) / int(c.reserved_state_bytes)
                if int(c.reserved_state_bytes) else 0.0
            )
            if int(c.reserved_state_bytes):
                state_ratios.append(state_ratio)
            rows.append({
                "case": name,
                "input_bytes": len(data),
                "large_case": name in LARGE_CASES,
                "anchor_trace_equal": semantic_equal,
                "counter_median_ns": c_ns,
                "inplace_fullblock_median_ns": i_ns,
                "inplace_over_counter_ratio": ratio,
                "counter_reserved_state_bytes": int(c.reserved_state_bytes),
                "inplace_reserved_state_bytes": int(i.reserved_state_bytes),
                "inplace_over_counter_state_ratio": state_ratio,
                "counter_derived_state_reads": int(c.derived_state_reads),
                "inplace_derived_state_reads": int(i.derived_state_reads),
                "counter_suffix_blocks_built": int(c.suffix_blocks_built),
                "inplace_suffix_blocks_built": int(i.suffix_blocks_built),
                "inplace_suffix_blocks_skipped_dead": int(i.suffix_blocks_skipped_dead),
                "source_byte_rescans": 0,
            })

        median_large = float(statistics.median(large_ratios))
        worst_large = max(large_ratios)
        worst_any = max(all_ratios)
        worst_state = max(state_ratios, default=0.0)
        promote = (
            worst_state <= MAX_STATE_RATIO
            and worst_large <= PROMOTE_EVERY_LARGE_RATIO
            and median_large <= PROMOTE_MEDIAN_LARGE_RATIO
            and worst_any <= MAX_ANY_RATIO
        )
        retire = median_large >= RETIRE_MEDIAN_LARGE_RATIO or worst_large > RETIRE_ANY_LARGE_RATIO
        if promote:
            decision = "promote_tail_aware_inplace_fullblock"
        elif retire:
            decision = "retire_tail_aware_inplace_fullblock_as_primary_rehabilitation"
        else:
            decision = "tail_aware_inplace_fullblock_inconclusive"
        _write_outputs(decision, median_large, worst_large, worst_any, worst_state)
        return {
            "schema": "cmpct-one-g02-inplace-fullblock-ab-v1",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "hypothesis": "tail awareness plus in-place overwrite removes the old full-block startup/state debt and can subsume four-segment maintenance with less state and lower elapsed",
            "disproof": "oracle drift, state ratio >0.85, any tested slowdown >5%, failure to improve every large case by >=5%, or median large ratio >=0.99 blocks promotion/retirement as frozen",
            "frozen_max_state_ratio": MAX_STATE_RATIO,
            "frozen_promote_every_large_ratio": PROMOTE_EVERY_LARGE_RATIO,
            "frozen_promote_median_large_ratio": PROMOTE_MEDIAN_LARGE_RATIO,
            "frozen_max_any_ratio": MAX_ANY_RATIO,
            "frozen_retire_median_large_ratio": RETIRE_MEDIAN_LARGE_RATIO,
            "frozen_retire_any_large_ratio": RETIRE_ANY_LARGE_RATIO,
            "median_large_ratio": median_large,
            "worst_large_ratio": worst_large,
            "worst_any_ratio": worst_any,
            "worst_state_ratio": worst_state,
            "decision": decision,
            "claim_boundary": "encoder discovery exact-selector maintenance only; no wire/reader/stored-byte/product/comparator claim",
            "rows": rows,
        }
    finally:
        td.cleanup()


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True, indent=2))
