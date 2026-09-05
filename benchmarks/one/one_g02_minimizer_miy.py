"""ONE-G0.2 marginal information yield map for the promoted minimizer selector.

Mission lock / Referee
======================
After the tail-return 8 KiB dispatcher promotion, two causal attempts to reduce
local selector operation counts failed to produce corresponding elapsed wins:
rolling-min construction halved a source counter but compiled to near-identical
machine shape, and a suffix query cache removed >99% of indirect loads while
slowing large cases.  The next question is therefore economic rather than local:
does the promoted selector recover enough additional reusable structure per unit
of charged selector compute/state/proof traffic to justify deeper integration?

This instrument does not promote or reject ONE.  It maps marginal opportunity
value against a cheap fixed observer on the existing frozen reuse-falsifier case
family.  Opportunity bytes are nominations proven by the existing Python oracle;
they are NOT stored-byte savings.  Native selector cost is measured separately
as the promoted tail-return selector minus the same compiled Gear recurrence.
Index/proof traffic and state are reported explicitly rather than gifted.
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

from benchmarks.one.one_g02_gear_replacement_ab import (
    _GEAR,
    _cases,
    FIXED_MAX_INDEX_ENTRIES,
    MIN_RUN,
    WINDOW,
)
from benchmarks.one.one_g02_minimizer_block_ab import _python_anchor_trace
from benchmarks.one.one_g02_minimizer_gear_ab import _minimizer_observe, MINIMIZER_SPAN
from benchmarks.one.one_g02_minimizer_native_probe import _KernelResult
from benchmarks.one.one_g02_minimizer_size_dispatch_ab import _DispatchResult
from experiments.one.observe import observe

ROUNDS = 13
LOCAL_INDEX_BYTES_PER_ENTRY = 16
GLOBAL_INDEX_BYTES_PER_ENTRY = 16


def _build() -> tuple[ctypes.CDLL, tempfile.TemporaryDirectory[str]]:
    here = Path(__file__).parent
    td = tempfile.TemporaryDirectory(prefix="cmpct-one-g02-miy-")
    lib = Path(td.name) / "lib.so"
    subprocess.run(
        [
            os.environ.get("CC", "cc"), "-O3", "-std=c11", "-fPIC", "-shared",
            str(here / "one_g02_minimizer_kernel.c"),
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


def _bind(lib: ctypes.CDLL):
    dispatch = lib.one_g02_minimizer_size_dispatch_tail_kernel
    dispatch.argtypes = [
        ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t, ctypes.POINTER(ctypes.c_uint64),
        ctypes.c_size_t, ctypes.c_size_t, ctypes.POINTER(_DispatchResult),
        ctypes.POINTER(ctypes.c_uint64), ctypes.c_size_t,
    ]
    dispatch.restype = ctypes.c_int
    gear_only = lib.one_g02_gear_only_kernel
    gear_only.argtypes = [
        ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t, ctypes.POINTER(ctypes.c_uint64),
        ctypes.c_size_t, ctypes.POINTER(_KernelResult),
    ]
    gear_only.restype = ctypes.c_int
    return dispatch, gear_only


def _dispatch_call(fn, gear, arr, n: int, trace=None, capacity: int = 0) -> _DispatchResult:
    out = _DispatchResult()
    rc = fn(arr, n, gear, WINDOW, MINIMIZER_SPAN, ctypes.byref(out), trace, capacity)
    if rc:
        raise RuntimeError(f"tail dispatch failed: {rc}")
    return out


def _gear_call(fn, gear, arr, n: int) -> _KernelResult:
    out = _KernelResult()
    rc = fn(arr, n, gear, WINDOW, ctypes.byref(out))
    if rc:
        raise RuntimeError(f"gear-only failed: {rc}")
    return out


def _time_once(fn) -> int:
    t0 = time.perf_counter_ns()
    fn()
    return time.perf_counter_ns() - t0


def _paired_cost(gear_fn, dispatch_fn) -> tuple[float, float, float]:
    # Warm both code paths, then use G-D-D-G to neutralize first-order drift.
    gear_fn(); dispatch_fn()
    gear_samples: list[float] = []
    dispatch_samples: list[float] = []
    increments: list[float] = []
    for _ in range(ROUNDS):
        g1 = _time_once(gear_fn)
        d1 = _time_once(dispatch_fn)
        d2 = _time_once(dispatch_fn)
        g2 = _time_once(gear_fn)
        g = (g1 + g2) * 0.5
        d = (d1 + d2) * 0.5
        gear_samples.append(g)
        dispatch_samples.append(d)
        increments.append(d - g)
    return (
        float(statistics.median(gear_samples)),
        float(statistics.median(dispatch_samples)),
        float(statistics.median(increments)),
    )


def run() -> dict[str, object]:
    cases = _cases()
    # Preserve the two explicit anchor-starvation falsifiers used by the
    # minimizer opportunity experiment.
    import random
    starved = random.Random(4876).randbytes(8 * 1024)
    cases["starved_repeat_basis_8k_16k"] = starved * 2
    cases["starved_shifted_basis_8k_insert1"] = starved + b"X" + starved

    lib, td = _build()
    try:
        dispatch, gear_only = _bind(lib)
        gear = (ctypes.c_uint64 * 256)(*_GEAR)
        rows: list[dict[str, object]] = []
        positive_marginal = []

        for name, data in cases.items():
            fixed = observe(
                data, min_run=MIN_RUN, chunk_size=WINDOW,
                max_index_entries=FIXED_MAX_INDEX_ENTRIES,
            )
            minimizer = _minimizer_observe(data)

            arr = (ctypes.c_uint8 * len(data)).from_buffer_copy(data)
            capacity = max(1, len(data))
            trace = (ctypes.c_uint64 * capacity)()
            once = _dispatch_call(dispatch, gear, arr, len(data), trace, capacity)
            expected, expected_state, expected_considered = _python_anchor_trace(data)
            observed_trace = [int(trace[i]) for i in range(int(once.emitted))]
            if (
                observed_trace != expected
                or int(once.final_state) != expected_state
                or int(once.positions_considered) != expected_considered
            ):
                raise AssertionError(f"promoted selector semantic drift: {name}")

            gear_ns, dispatch_ns, incremental_ns = _paired_cost(
                lambda: _gear_call(gear_only, gear, arr, len(data)),
                lambda: _dispatch_call(dispatch, gear, arr, len(data)),
            )
            if incremental_ns <= 0:
                raise AssertionError(f"non-positive selector incremental cost: {name} {incremental_ns}")

            marginal = minimizer.reuse_opportunity_bytes - fixed.stats.reuse_opportunity_bytes
            if marginal > 0:
                positive_marginal.append(name)
            index_state = (
                minimizer.global_entries * GLOBAL_INDEX_BYTES_PER_ENTRY
                + minimizer.local_entries * LOCAL_INDEX_BYTES_PER_ENTRY
            )
            modeled_state = int(once.reserved_state_bytes) + index_state
            incremental_ms = incremental_ns / 1_000_000.0
            rows.append({
                "case": name,
                "input_bytes": len(data),
                "fixed_reuse_opportunity_bytes": fixed.stats.reuse_opportunity_bytes,
                "minimizer_reuse_opportunity_bytes": minimizer.reuse_opportunity_bytes,
                "marginal_reuse_opportunity_bytes": marginal,
                "fixed_retained_index_payload_bytes": fixed.stats.retained_index_payload_bytes,
                "selector_reserved_state_bytes": int(once.reserved_state_bytes),
                "minimizer_index_payload_bytes": index_state,
                "minimizer_modeled_discovery_state_bytes": modeled_state,
                "minimizer_verification_read_bytes": minimizer.verification_read_bytes,
                "minimizer_extension_read_bytes": minimizer.extension_read_bytes,
                "minimizer_total_source_read_bytes": minimizer.total_source_read_bytes,
                "fixed_total_source_read_bytes": fixed.stats.total_source_read_bytes,
                "native_gear_median_ns": gear_ns,
                "native_promoted_selector_median_ns": dispatch_ns,
                "native_incremental_selector_ns": incremental_ns,
                "native_incremental_selector_ns_per_input_byte": incremental_ns / max(1, len(data)),
                "marginal_opportunity_bytes_per_incremental_selector_ms": (
                    marginal / incremental_ms if marginal > 0 else 0.0
                ),
                "total_minimizer_opportunity_bytes_per_incremental_selector_ms": (
                    minimizer.reuse_opportunity_bytes / incremental_ms
                ),
                "emitted_minimizers": int(once.emitted),
                "selected_offset_path": bool(once.selected_offset_path),
                "source_byte_rescans": 0,
            })

        return {
            "schema": "cmpct-one-g02-minimizer-miy-v1",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "rounds": ROUNDS,
            "decision": "marginal_opportunity_map_complete",
            "positive_marginal_cases": positive_marginal,
            "interpretation_rule": "opportunity bytes are headroom only; selector cost excludes downstream Law encoding and candidate byte savings must not be inferred",
            "claim_boundary": "encoder-discovery marginal-yield map only; no stored-byte/product/comparator authority",
            "rows": rows,
        }
    finally:
        td.cleanup()


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True, indent=2))
