"""ONE-G0.2 diagnostic: map segmented-minimum amortization crossover.

The preregistered four-block Builder is frozen rejected because it regressed the two shortest
cases even though it materially improved every large case and the 16 KiB hostile case. This
instrument does not reopen or modify that result. It asks the causal follow-up required before
any superseding hybrid-maintenance preregistration: at what input maturity does the same exact
segmented algorithm stop exporting its setup cost?

No promotion threshold is defined here. Gear identity, 64-byte recurrence window, 4096-state
rightmost-minimum semantics and independent reference trace are unchanged. Both arms consume
source bytes once; all extra segmented work touches derived Gear states only.
"""
from __future__ import annotations

import ctypes
import json
import os

from benchmarks.one.one_g02_gear_replacement_ab import _GEAR
from benchmarks.one.one_g02_minimizer_block_ab import (
    MASKED_RESERVED_STATE_BYTES,
    _bind_masked,
    _call_masked,
    _median_ns,
    _python_anchor_trace,
)
from benchmarks.one.one_g02_minimizer_block_crossover import LENGTHS, _regimes, _first_at_or_below
from benchmarks.one.one_g02_minimizer_segmented_ab import (
    _bind_segmented,
    _build,
    _call_segmented,
)


def run() -> dict[str, object]:
    lib, tempdir = _build()
    try:
        masked = _bind_masked(lib)
        segmented = _bind_segmented(lib)
        gear = (ctypes.c_uint64 * 256)(*_GEAR)
        rows: list[dict[str, object]] = []

        for length in LENGTHS:
            for regime, data in _regimes(length).items():
                expected_trace, expected_state, expected_considered = _python_anchor_trace(data)
                data_array = (ctypes.c_uint8 * len(data)).from_buffer_copy(data)
                masked_once = _call_masked(masked, gear, data_array, len(data))
                trace_storage = (ctypes.c_uint64 * max(1, len(data)))()
                segmented_once = _call_segmented(
                    segmented, gear, data_array, len(data), trace_storage, max(1, len(data))
                )
                actual_trace = [int(trace_storage[i]) for i in range(int(segmented_once.emitted))]
                semantic_ok = (
                    int(masked_once.emitted) == len(expected_trace)
                    and int(masked_once.final_state) == expected_state
                    and int(masked_once.positions_considered) == expected_considered
                    and actual_trace == expected_trace
                    and int(segmented_once.final_state) == expected_state
                    and int(segmented_once.positions_considered) == expected_considered
                )
                if not semantic_ok:
                    raise AssertionError(f"semantic mismatch: regime={regime} length={length}")

                masked_ns = _median_ns(lambda: _call_masked(masked, gear, data_array, len(data)))
                segmented_ns = _median_ns(
                    lambda: _call_segmented(segmented, gear, data_array, len(data))
                )
                segmented_reserved = int(segmented_once.reserved_state_bytes) + 256 * 8
                rows.append({
                    "regime": regime,
                    "input_bytes": length,
                    "mature_windows": max(0, length - 64 - 4096 + 1),
                    "anchor_count": len(expected_trace),
                    "anchor_trace_equal": True,
                    "masked_deque_median_ns": masked_ns,
                    "segmented_median_ns": segmented_ns,
                    "segmented_over_masked_elapsed_ratio": segmented_ns / masked_ns,
                    "segmented_speedup_over_masked": masked_ns / segmented_ns,
                    "masked_reserved_state_bytes": MASKED_RESERVED_STATE_BYTES,
                    "segmented_reserved_state_bytes": segmented_reserved,
                    "segmented_derived_state_reads": int(segmented_once.derived_state_reads),
                    "source_byte_rescans": 0,
                })

        regimes = ("random", "zeros", "periodic257")
        crossover = {
            regime: {
                "first_segmented_not_slower_bytes": _first_at_or_below(rows, regime, 1.0),
                "first_segmented_10pct_faster_bytes": _first_at_or_below(rows, regime, 0.9),
                "first_segmented_30pct_faster_bytes": _first_at_or_below(rows, regime, 0.7),
            }
            for regime in regimes
        }
        return {
            "schema": "cmpct-one-g02-minimizer-segmented-crossover-v1",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "purpose": "diagnose segmented fixed setup amortization after frozen rejection; no promotion decision",
            "claim_boundary": "encoder discovery microkernel diagnostic only; no product-speed, stored-byte, reader, v0.29 or v0.30 claim",
            "lengths": list(LENGTHS),
            "crossover": crossover,
            "rows": rows,
        }
    finally:
        tempdir.cleanup()


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True, indent=2))
