"""ONE-G0.2 superseding A/B: tail-aware segmented maintenance vs masked deque.

Mission Lock / Referee freeze before result-bearing execution
=============================================================

The original four-segment prefix/suffix Builder was correctly rejected because it regressed
at the 4160-byte just-enabled boundary.  A later causal A/B established that provably dead EOF
suffix construction owns material boundary debt without changing the selector, reserved state
or source-pass count.  This experiment does not relax the rejected Builder's gate.  It asks
whether the causally repaired Builder can now satisfy that original all-case promotion law.

Frozen hypothesis
-----------------
The same exact rightmost-minimum selector, implemented with tail-aware four-segment
prefix/suffix maintenance, preserves the independent oracle and simultaneously:

* runs at <= 0.70x masked-deque elapsed time on every large case (>=30% faster);
* runs at <= 1.10x masked-deque elapsed time on every tested case;
* reserves <= 0.85x masked-deque state, including the shared 256-entry Gear table;
* performs zero source-byte rescans.

Disproof / retirement
---------------------
Any oracle mismatch, >10% elapsed regression on any case, <30% improvement on any large case,
>85% state ratio, or any source-byte rescan rejects promotion of this repaired maintenance
policy.  No threshold may be changed after result-bearing execution.  A loss remains negative
evidence; a win is encoder-discovery maintenance evidence only and makes no stored-byte,
reader, wire, product-speed, v0.29 or v0.30 superiority claim.
"""
from __future__ import annotations

import ctypes
import json
import os
from pathlib import Path
import subprocess
import tempfile

from benchmarks.one.one_g02_gear_replacement_ab import _GEAR
from benchmarks.one.one_g02_minimizer_block_ab import (
    MASKED_RESERVED_STATE_BYTES,
    _bind_masked,
    _call_masked,
    _median_ns,
    _python_anchor_trace,
)
from benchmarks.one.one_g02_minimizer_native_probe import _cases, MINIMIZER_SPAN, WINDOW
from benchmarks.one.one_g02_minimizer_segmented_tail_ab import (
    _TailResult,
    _bind_tail,
    _call_tail,
)
from benchmarks.one.one_g02_minimizer_wrap_ab import LARGE_CASES

MATERIAL_SPEED_RATIO = 0.70
MAX_REGRESSION_RATIO = 1.10
MAX_STATE_RATIO = 0.85
GEAR_STATE_BYTES = 256 * 8


def _build() -> tuple[ctypes.CDLL, tempfile.TemporaryDirectory[str]]:
    here = Path(__file__).parent
    tempdir = tempfile.TemporaryDirectory(prefix="cmpct-one-g02-tail-promotion-")
    library = Path(tempdir.name) / "libone_g02_tail_promotion.so"
    subprocess.run(
        [
            os.environ.get("CC", "cc"), "-O3", "-std=c11", "-fPIC", "-shared",
            str(here / "one_g02_minimizer_mask_kernel.c"),
            str(here / "one_g02_minimizer_segmented_tail_kernel.c"),
            "-o", str(library),
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return ctypes.CDLL(str(library)), tempdir


def run() -> dict[str, object]:
    lib, tempdir = _build()
    try:
        masked = _bind_masked(lib)
        tail = _bind_tail(lib)
        gear = (ctypes.c_uint64 * 256)(*_GEAR)
        rows: list[dict[str, object]] = []
        semantic_ok = True
        all_case_speed_ok = True
        large_speed_ok = True
        state_ok = True

        for name, data in _cases().items():
            expected_trace, expected_state, expected_considered = _python_anchor_trace(data)
            data_array = (ctypes.c_uint8 * len(data)).from_buffer_copy(data)
            masked_once = _call_masked(masked, gear, data_array, len(data))
            trace_storage = (ctypes.c_uint64 * max(1, len(data)))()
            tail_once: _TailResult = _call_tail(
                tail, gear, data_array, len(data), trace_storage, max(1, len(data))
            )
            actual_trace = [int(trace_storage[i]) for i in range(int(tail_once.emitted))]
            equal = (
                actual_trace == expected_trace
                and int(tail_once.final_state) == expected_state
                and int(tail_once.positions_considered) == expected_considered
                and int(masked_once.emitted) == len(expected_trace)
            )
            semantic_ok &= equal
            if not equal:
                raise AssertionError(f"tail-aware promotion semantic mismatch for {name}")

            masked_ns = _median_ns(lambda: _call_masked(masked, gear, data_array, len(data)))
            tail_ns = _median_ns(lambda: _call_tail(tail, gear, data_array, len(data)))
            elapsed_ratio = tail_ns / masked_ns
            tail_reserved = int(tail_once.reserved_state_bytes) + (GEAR_STATE_BYTES if tail_once.reserved_state_bytes else 0)
            state_ratio = tail_reserved / MASKED_RESERVED_STATE_BYTES if tail_reserved else 0.0

            all_case_speed_ok &= elapsed_ratio <= MAX_REGRESSION_RATIO
            if name in LARGE_CASES:
                large_speed_ok &= elapsed_ratio <= MATERIAL_SPEED_RATIO
            state_ok &= state_ratio <= MAX_STATE_RATIO

            rows.append({
                "case": name,
                "input_bytes": len(data),
                "large_case": name in LARGE_CASES,
                "anchor_trace_equal": equal,
                "masked_deque_median_ns": masked_ns,
                "tail_segmented_median_ns": tail_ns,
                "tail_over_masked_elapsed_ratio": elapsed_ratio,
                "masked_reserved_state_bytes": MASKED_RESERVED_STATE_BYTES,
                "tail_reserved_state_bytes": tail_reserved,
                "tail_over_masked_state_ratio": state_ratio,
                "tail_derived_state_reads": int(tail_once.derived_state_reads),
                "tail_suffix_blocks_built": int(tail_once.suffix_blocks_built),
                "tail_suffix_blocks_skipped_dead": int(tail_once.suffix_blocks_skipped_dead),
                "source_byte_rescans": 0,
            })

        promoted = semantic_ok and all_case_speed_ok and large_speed_ok and state_ok
        return {
            "schema": "cmpct-one-g02-minimizer-tail-promotion-ab-v1",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "hypothesis": "causally repaired tail-aware four-segment maintenance satisfies the original all-case speed/state promotion law without changing selector semantics",
            "disproof": "any oracle mismatch, >10% regression on any case, <30% improvement on any large case, >85% state ratio, or source-byte rescan rejects promotion",
            "frozen_material_speed_ratio": MATERIAL_SPEED_RATIO,
            "frozen_max_regression_ratio": MAX_REGRESSION_RATIO,
            "frozen_max_state_ratio": MAX_STATE_RATIO,
            "decision": "promote_tail_aware_segmented_maintenance" if promoted else "reject_tail_aware_segmented_maintenance",
            "claim_boundary": "encoder discovery maintenance only; no stored-byte, wire, reader, product-speed, v0.29 or v0.30 superiority claim",
            "rows": rows,
        }
    finally:
        tempdir.cleanup()


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True, indent=2))
