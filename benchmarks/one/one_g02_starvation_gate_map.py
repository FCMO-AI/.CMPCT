"""ONE-G0.2 map for a sparse-anchor starvation gate.

Referee question
================
The promoted minimizer adds marginal reuse only on insertion/phase-shift cases in
the current frozen opportunity matrix, while random/compressed negatives pay its
full ~4 ms/MiB incremental selector cost.  Historical 1/1024 sparse Gear is much
cheaper and already recovers friendly shifted content, but its known failure is
long deterministic anchor starvation.

Before implementing a gated minimizer, test the information available to a one-
pass gate: after the existing 4,096-state minimizer span has elapsed without a
sparse Gear anchor, what fraction of positions would require rescue?  The gate
threshold is fixed to MINIMIZER_SPAN, not tuned from these results.

This is an activation-map instrument only.  It does not claim that turning the
minimizer on late preserves exact opportunity; that is the next falsifier if the
map shows useful separation.
"""
from __future__ import annotations

import json
import os
import random

from benchmarks.one.one_g02_gear_replacement_ab import (
    _GEAR,
    _U64_MASK,
    ANCHOR_MASK,
    WINDOW,
    MIN_RUN,
    FIXED_MAX_INDEX_ENTRIES,
    _cases,
    _gear_observe,
)
from benchmarks.one.one_g02_minimizer_gear_ab import _minimizer_observe, MINIMIZER_SPAN
from experiments.one.observe import observe

GATE_GAP = MINIMIZER_SPAN


def _gate_stats(data: bytes) -> dict[str, int | float]:
    h = 0
    last_anchor_position: int | None = None
    anchors = 0
    considered = 0
    rescue_positions = 0
    max_gap = 0
    current_gap = 0
    run_length = 0
    run_value = data[0] if data else 0

    for position, value in enumerate(data):
        if run_length == 0:
            run_value, run_length = value, 1
        elif value == run_value:
            run_length += 1
        else:
            run_value, run_length = value, 1

        h = ((h << 1) + _GEAR[value]) & _U64_MASK
        if position + 1 < WINDOW:
            continue
        considered += 1

        # A qualifying run is already explained by the run observer and should
        # not demand global-reuse rescue merely because its Gear phase starves.
        run_dominated = run_length >= max(MIN_RUN, WINDOW)
        if not (h & ANCHOR_MASK) and not run_dominated:
            anchors += 1
            last_anchor_position = position
            current_gap = 0
            continue

        current_gap += 1
        max_gap = max(max_gap, current_gap)
        gap_from_last = (
            position - last_anchor_position
            if last_anchor_position is not None
            else considered
        )
        if not run_dominated and gap_from_last >= GATE_GAP:
            rescue_positions += 1

    return {
        "sparse_anchors": anchors,
        "positions_considered": considered,
        "max_sparse_anchor_gap_positions": max_gap,
        "rescue_active_positions": rescue_positions,
        "rescue_active_fraction": rescue_positions / considered if considered else 0.0,
    }


def run() -> dict[str, object]:
    cases = _cases()
    starved = random.Random(4876).randbytes(8 * 1024)
    cases["starved_repeat_basis_8k_16k"] = starved * 2
    cases["starved_shifted_basis_8k_insert1"] = starved + b"X" + starved

    rows: list[dict[str, object]] = []
    hard_rescue_cases: list[str] = []
    for name, data in cases.items():
        fixed = observe(
            data, min_run=MIN_RUN, chunk_size=WINDOW,
            max_index_entries=FIXED_MAX_INDEX_ENTRIES,
        )
        sparse = _gear_observe(data)
        minimizer = _minimizer_observe(data)
        best_cheap = max(fixed.stats.reuse_opportunity_bytes, sparse.reuse_opportunity_bytes)
        hard_rescue = minimizer.reuse_opportunity_bytes > best_cheap
        if hard_rescue:
            hard_rescue_cases.append(name)
        rows.append({
            "case": name,
            "input_bytes": len(data),
            "fixed_reuse_opportunity_bytes": fixed.stats.reuse_opportunity_bytes,
            "sparse_gear_reuse_opportunity_bytes": sparse.reuse_opportunity_bytes,
            "minimizer_reuse_opportunity_bytes": minimizer.reuse_opportunity_bytes,
            "minimizer_marginal_over_best_cheap_bytes": minimizer.reuse_opportunity_bytes - best_cheap,
            "hard_rescue_needed": hard_rescue,
            **_gate_stats(data),
        })

    return {
        "schema": "cmpct-one-g02-starvation-gate-map-v1",
        "experimental_version": "ONE-G0.2",
        "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
        "sparse_anchor_mask": ANCHOR_MASK,
        "frozen_gate_gap_positions": GATE_GAP,
        "hard_rescue_cases": hard_rescue_cases,
        "hypothesis": "long sparse-anchor gaps identify the cases where minimizer rescue is uniquely valuable while remaining rare on random/compressed negatives",
        "disproof": "hard-rescue cases fail to activate strongly, or random/compressed negatives spend a large fraction of positions behind the same gate",
        "claim_boundary": "one-pass gate observability map only; no late-activation semantics, stored-byte, product-speed or comparator authority",
        "rows": rows,
    }


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True, indent=2))
