"""ONE-G0.2 falsifier: can sparse-anchor starvation gate late minimizer work?

Mission lock
============
The full rolling minimizer preserves shift-invariant reuse but exports material selector
compute on random/already-compressed negatives. Sparse Gear is much cheaper but has a
known deterministic starvation blind spot. This experiment asks whether the expensive
minimizer can remain cold until a content-derived sparse-anchor gap reaches the frozen
4,096-position minimizer span, then recover the unique reuse opportunity without changing
reader semantics.

The threshold is inherited from MINIMIZER_SPAN and is not tuned here. A cold-start rescue
must preserve every opportunity that is uniquely supplied by the full minimizer beyond the
existing fixed/sparse cheap observers. Any such loss rejects this integration shape; the
result must not be repaired by moving the threshold after observing the answer.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import json
import os
import random

from benchmarks.one.one_g02_gear_replacement_ab import (
    _GEAR, _U64_MASK, ANCHOR_MASK, WINDOW, MIN_RUN, FIXED_MAX_INDEX_ENTRIES,
    GEAR_MAX_INDEX_ENTRIES, _cases, _extend_left, _extend_right, _gear_observe,
)
from benchmarks.one.one_g02_minimizer_gear_ab import _minimizer_observe, MINIMIZER_SPAN
from experiments.one.observe import observe

GATE_GAP = MINIMIZER_SPAN


@dataclass(frozen=True)
class RescueResult:
    reuse_opportunity_bytes: int
    reuse_regions: int
    rescue_active_positions: int
    emitted_minimizers: int
    sparse_anchors: int
    peak_queue_entries: int
    verification_read_bytes: int
    extension_read_bytes: int


def _late_rescue_observe(data: bytes) -> RescueResult:
    if not data:
        return RescueResult(0, 0, 0, 0, 0, 0, 0, 0)

    sparse_index: dict[int, int] = {}
    rescue_index: dict[int, int] = {}
    minima: deque[tuple[int, int]] = deque()
    h = 0
    last_sparse_position: int | None = None
    rescue_started_at: int | None = None
    last_emitted_position = -1
    rescue_active_positions = emitted = anchors = peak_queue = 0
    reuse_opportunity = reuse_regions = 0
    verify_reads = extension_reads = 0
    covered_until = 0
    run_value = data[0]
    run_length = 0

    def audition(start: int, source: int | None) -> None:
        nonlocal reuse_opportunity, reuse_regions, verify_reads, extension_reads, covered_until
        if source is None or start < covered_until:
            return
        verify_reads += 2 * WINDOW
        if data[source:source + WINDOW] != data[start:start + WINDOW]:
            return
        left, lreads = _extend_left(data, source, start, covered_until)
        right, rreads = _extend_right(data, source, start)
        extension_reads += lreads + rreads
        target_start = max(start - left, covered_until)
        target_end = start + right
        if target_end > target_start:
            reuse_regions += 1
            reuse_opportunity += target_end - target_start
            covered_until = target_end

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
        start = position + 1 - WINDOW
        run_dominated = run_length >= max(MIN_RUN, WINDOW)

        sparse_anchor = not (h & ANCHOR_MASK) and not run_dominated
        if sparse_anchor:
            anchors += 1
            source = sparse_index.get(h)
            audition(start, source)
            if source is None and len(sparse_index) < GEAR_MAX_INDEX_ENTRIES:
                sparse_index[h] = start
            last_sparse_position = position
            rescue_started_at = None
            minima.clear()
            last_emitted_position = -1
            continue

        gap = position - last_sparse_position if last_sparse_position is not None else position + 1 - WINDOW
        if run_dominated or gap < GATE_GAP:
            continue

        rescue_active_positions += 1
        if rescue_started_at is None:
            rescue_started_at = position
            minima.clear()
            last_emitted_position = -1

        while minima and minima[-1][0] >= h:
            minima.pop()
        minima.append((h, position))
        first_valid = position - MINIMIZER_SPAN + 1
        while minima and minima[0][1] < first_valid:
            minima.popleft()
        peak_queue = max(peak_queue, len(minima))

        # Cold activation intentionally has to accumulate a complete minimizer span.
        if position - rescue_started_at + 1 < MINIMIZER_SPAN:
            continue
        signal, anchor_position = minima[0]
        if anchor_position == last_emitted_position:
            continue
        last_emitted_position = anchor_position
        emitted += 1
        anchor_start = anchor_position + 1 - WINDOW
        source = rescue_index.get(signal)
        audition(anchor_start, source)
        if source is None and len(rescue_index) < GEAR_MAX_INDEX_ENTRIES:
            rescue_index[signal] = anchor_start

    return RescueResult(
        reuse_opportunity, reuse_regions, rescue_active_positions, emitted, anchors,
        peak_queue, verify_reads, extension_reads,
    )


def run() -> dict[str, object]:
    cases = _cases()
    starved = random.Random(4876).randbytes(8 * 1024)
    cases["starved_repeat_basis_8k_16k"] = starved * 2
    cases["starved_shifted_basis_8k_insert1"] = starved + b"X" + starved

    rows = []
    hard_losses = []
    for name, data in cases.items():
        fixed = observe(data, min_run=MIN_RUN, chunk_size=WINDOW, max_index_entries=FIXED_MAX_INDEX_ENTRIES)
        sparse = _gear_observe(data)
        full = _minimizer_observe(data)
        rescue = _late_rescue_observe(data)
        best_cheap = max(fixed.stats.reuse_opportunity_bytes, sparse.reuse_opportunity_bytes)
        hard_rescue = full.reuse_opportunity_bytes > best_cheap
        if hard_rescue and rescue.reuse_opportunity_bytes < full.reuse_opportunity_bytes:
            hard_losses.append(name)
        rows.append({
            "case": name,
            "input_bytes": len(data),
            "fixed_reuse_opportunity_bytes": fixed.stats.reuse_opportunity_bytes,
            "sparse_reuse_opportunity_bytes": sparse.reuse_opportunity_bytes,
            "best_cheap_reuse_opportunity_bytes": best_cheap,
            "full_minimizer_reuse_opportunity_bytes": full.reuse_opportunity_bytes,
            "late_rescue_reuse_opportunity_bytes": rescue.reuse_opportunity_bytes,
            "hard_rescue_needed": hard_rescue,
            "late_minus_full_opportunity_bytes": rescue.reuse_opportunity_bytes - full.reuse_opportunity_bytes,
            "rescue_active_positions": rescue.rescue_active_positions,
            "rescue_active_fraction": rescue.rescue_active_positions / len(data) if data else 0.0,
            "emitted_rescue_minimizers": rescue.emitted_minimizers,
            "sparse_anchors": rescue.sparse_anchors,
            "peak_rescue_queue_entries": rescue.peak_queue_entries,
            "verification_read_bytes": rescue.verification_read_bytes,
            "extension_read_bytes": rescue.extension_read_bytes,
        })

    return {
        "schema": "cmpct-one-g02-late-minimizer-rescue-v2",
        "experimental_version": "ONE-G0.2",
        "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
        "frozen_gate_gap_positions": GATE_GAP,
        "hypothesis": "cold minimizer activation after a 4096-position sparse-anchor starvation gap preserves every full-minimizer opportunity uniquely missing from the fixed/sparse cheap observers",
        "disproof": "any hard-rescue case loses full-minimizer opportunity; ordinary-negative activation remains separately reported rather than tuned away",
        "decision": "late_rescue_survives_hard_opportunity_falsifier" if not hard_losses else "reject_cold_late_rescue",
        "hard_rescue_loss_cases": hard_losses,
        "claim_boundary": "encoder-discovery falsifier only; no threshold tuning, stored-byte, native-speed, or reader authority",
        "rows": rows,
    }


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True, indent=2))
