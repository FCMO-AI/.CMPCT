"""ONE-G0.2 diagnostic: map block-minimum setup amortization without promotion.

This is causal evidence following the frozen rejection in
`one_g02_minimizer_block_ab.py`. It does NOT change or supersede that decision and it has no
promotion threshold. The question is narrower: is the 4160-byte regression a predictable
fixed setup cost that amortizes with mature windows, or a content-dependent instability?

All selector semantics stay frozen. Exact anchor traces are checked against the independent
Python deque reference for every row. Source bytes are consumed once by both compiled arms;
block backward work touches derived Gear-state values only.
"""
from __future__ import annotations

import ctypes
import json
import os
import random

from benchmarks.one.one_g02_gear_replacement_ab import _GEAR
from benchmarks.one.one_g02_minimizer_block_ab import (
    MASKED_RESERVED_STATE_BYTES,
    _bind_block,
    _bind_masked,
    _build,
    _call_block,
    _call_masked,
    _median_ns,
    _python_anchor_trace,
)

LENGTHS = (4160, 4224, 4352, 4608, 5120, 6144, 8192, 12288, 16384, 24576, 32768, 65536)


def _regimes(length: int) -> dict[str, bytes]:
    rng = random.Random(0xC0A5E + length)
    random_bytes = bytes(rng.randrange(256) for _ in range(length))
    basis = bytes(((i * 73 + 19) & 0xFF) for i in range(257))
    repeated = (basis * ((length + len(basis) - 1) // len(basis)))[:length]
    return {
        "random": random_bytes,
        "zeros": bytes(length),
        "periodic257": repeated,
    }


def _first_at_or_below(rows: list[dict[str, object]], regime: str, ratio_limit: float):
    candidates = [
        int(row["input_bytes"])
        for row in rows
        if row["regime"] == regime and float(row["block_over_masked_elapsed_ratio"]) <= ratio_limit
    ]
    return min(candidates) if candidates else None


def run() -> dict[str, object]:
    lib, tempdir = _build()
    try:
        masked = _bind_masked(lib)
        block = _bind_block(lib)
        gear = (ctypes.c_uint64 * 256)(*_GEAR)
        rows: list[dict[str, object]] = []
        for length in LENGTHS:
            for regime, data in _regimes(length).items():
                expected_trace, expected_state, expected_considered = _python_anchor_trace(data)
                data_array = (ctypes.c_uint8 * len(data)).from_buffer_copy(data)

                masked_once = _call_masked(masked, gear, data_array, len(data))
                trace_storage = (ctypes.c_uint64 * max(1, len(data)))()
                block_once = _call_block(block, gear, data_array, len(data), trace_storage, max(1, len(data)))
                actual_trace = [int(trace_storage[i]) for i in range(int(block_once.emitted))]

                semantic_ok = (
                    int(masked_once.emitted) == len(expected_trace)
                    and int(masked_once.final_state) == expected_state
                    and int(masked_once.positions_considered) == expected_considered
                    and actual_trace == expected_trace
                    and int(block_once.final_state) == expected_state
                    and int(block_once.positions_considered) == expected_considered
                )
                if not semantic_ok:
                    raise AssertionError(f"semantic mismatch: regime={regime} length={length}")

                masked_ns = _median_ns(lambda: _call_masked(masked, gear, data_array, len(data)))
                block_ns = _median_ns(lambda: _call_block(block, gear, data_array, len(data)))
                block_reserved = int(block_once.reserved_state_bytes) + 256 * 8
                rows.append({
                    "regime": regime,
                    "input_bytes": length,
                    "mature_windows": max(0, length - 64 - 4096 + 1),
                    "anchor_count": len(expected_trace),
                    "anchor_trace_equal": True,
                    "masked_deque_median_ns": masked_ns,
                    "block_minimum_median_ns": block_ns,
                    "block_over_masked_elapsed_ratio": block_ns / masked_ns,
                    "block_speedup_over_masked": masked_ns / block_ns,
                    "masked_reserved_state_bytes": MASKED_RESERVED_STATE_BYTES,
                    "block_reserved_state_bytes": block_reserved,
                    "block_derived_state_reads": int(block_once.derived_state_reads),
                    "source_byte_rescans": 0,
                })

        regimes = ("random", "zeros", "periodic257")
        crossover = {
            regime: {
                "first_block_not_slower_bytes": _first_at_or_below(rows, regime, 1.0),
                "first_block_10pct_faster_bytes": _first_at_or_below(rows, regime, 0.9),
                "first_block_30pct_faster_bytes": _first_at_or_below(rows, regime, 0.7),
            }
            for regime in regimes
        }
        return {
            "schema": "cmpct-one-g02-minimizer-block-crossover-v1",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "purpose": "diagnose block-minimum fixed setup amortization after frozen rejection; no promotion decision",
            "claim_boundary": "encoder discovery microkernel diagnostic only; no product-speed, stored-byte, reader, v0.29 or v0.30 claim",
            "lengths": list(LENGTHS),
            "crossover": crossover,
            "rows": rows,
        }
    finally:
        tempdir.cleanup()


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True, indent=2))
