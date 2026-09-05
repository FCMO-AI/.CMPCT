"""ONE-G0.2 compact-history rehabilitation for deferred minimizer materialization.

The first deferred candidate proves that one pre-trigger span removes cold-start blindness,
but modeled each retained Gear state with an explicit absolute position (16 B/entry). Absolute
positions are derivable from ring order plus the current input position, so they carry zero
information. This candidate retains only the u64 Gear signal in a fixed 4,096-entry ring.
Modeled history payload therefore falls from 65,536 B to 32,768 B with identical gate and
reader semantics. Python object overhead is not presented as native/RSS authority.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import json
import os

from benchmarks.one.one_g02_gear_replacement_ab import (
    _GEAR, _U64_MASK, ANCHOR_MASK, WINDOW, MIN_RUN, FIXED_MAX_INDEX_ENTRIES,
    GEAR_MAX_INDEX_ENTRIES, _extend_left, _extend_right, _gear_observe,
)
from benchmarks.one.one_g02_minimizer_gear_ab import _minimizer_observe, MINIMIZER_SPAN
from benchmarks.one.one_g02_late_rescue_transfer import (
    BASIS_BYTES, TARGET_STARVED_BASES, MAX_SEED, INSERTIONS, _starved_bases,
)
from experiments.one.observe import observe

GATE_GAP = MINIMIZER_SPAN
HISTORY_ENTRY_BYTES = 8
HISTORY_PAYLOAD_BYTES = MINIMIZER_SPAN * HISTORY_ENTRY_BYTES


@dataclass(frozen=True)
class CompactDeferredResult:
    reuse_opportunity_bytes: int
    reuse_regions: int
    rescue_active_positions: int
    emitted_minimizers: int
    sparse_anchors: int
    peak_minima_entries: int
    history_payload_bytes: int
    materialization_input_entries: int
    verification_read_bytes: int
    extension_read_bytes: int


def _compact_deferred_observe(data: bytes) -> CompactDeferredResult:
    if not data:
        return CompactDeferredResult(0, 0, 0, 0, 0, 0, HISTORY_PAYLOAD_BYTES, 0, 0, 0)

    sparse_index: dict[int, int] = {}
    rescue_index: dict[int, int] = {}
    history = [0] * MINIMIZER_SPAN
    history_count = 0
    history_next = 0
    minima: deque[tuple[int, int]] = deque()
    active = False
    h = 0
    last_sparse_position: int | None = None
    last_emitted_position = -1
    rescue_active_positions = emitted = anchors = peak_minima = materialized_entries = 0
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

        history[history_next] = h
        history_next = (history_next + 1) % MINIMIZER_SPAN
        history_count = min(history_count + 1, MINIMIZER_SPAN)

        sparse_anchor = not (h & ANCHOR_MASK) and not run_dominated
        if sparse_anchor:
            anchors += 1
            source = sparse_index.get(h)
            audition(start, source)
            if source is None and len(sparse_index) < GEAR_MAX_INDEX_ENTRIES:
                sparse_index[h] = start
            last_sparse_position = position
            active = False
            minima.clear()
            last_emitted_position = -1
            continue

        gap = position - last_sparse_position if last_sparse_position is not None else position + 1 - WINDOW
        if run_dominated or gap < GATE_GAP:
            continue

        rescue_active_positions += 1
        if not active:
            if history_count < MINIMIZER_SPAN:
                continue
            minima.clear()
            oldest_position = position - history_count + 1
            oldest_slot = history_next if history_count == MINIMIZER_SPAN else 0
            for j in range(history_count):
                signal = history[(oldest_slot + j) % MINIMIZER_SPAN]
                hist_position = oldest_position + j
                while minima and minima[-1][0] >= signal:
                    minima.pop()
                minima.append((signal, hist_position))
            materialized_entries += history_count
            active = True
        else:
            while minima and minima[-1][0] >= h:
                minima.pop()
            minima.append((h, position))
            first_valid = position - MINIMIZER_SPAN + 1
            while minima and minima[0][1] < first_valid:
                minima.popleft()

        peak_minima = max(peak_minima, len(minima))
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

    return CompactDeferredResult(
        reuse_opportunity, reuse_regions, rescue_active_positions, emitted, anchors,
        peak_minima, HISTORY_PAYLOAD_BYTES, materialized_entries, verify_reads, extension_reads,
    )


def run() -> dict[str, object]:
    selected = _starved_bases()
    rows = []
    hard_rows = hard_wins = 0
    hard_losses: list[str] = []
    for seed, basis in selected:
        for insertion in INSERTIONS:
            data = basis + insertion + basis
            fixed = observe(data, min_run=MIN_RUN, chunk_size=WINDOW, max_index_entries=FIXED_MAX_INDEX_ENTRIES)
            sparse = _gear_observe(data)
            full = _minimizer_observe(data)
            compact = _compact_deferred_observe(data)
            cheap = max(fixed.stats.reuse_opportunity_bytes, sparse.reuse_opportunity_bytes)
            hard = full.reuse_opportunity_bytes > cheap
            if hard:
                hard_rows += 1
                if compact.reuse_opportunity_bytes < full.reuse_opportunity_bytes:
                    hard_losses.append(f"seed={seed}/insert={len(insertion)}")
                else:
                    hard_wins += 1
            rows.append({
                "seed": seed,
                "insertion_bytes": len(insertion),
                "input_bytes": len(data),
                "full_minimizer_reuse_opportunity_bytes": full.reuse_opportunity_bytes,
                "compact_rescue_reuse_opportunity_bytes": compact.reuse_opportunity_bytes,
                "hard_rescue_needed": hard,
                "compact_minus_full_opportunity_bytes": compact.reuse_opportunity_bytes - full.reuse_opportunity_bytes,
                "history_payload_bytes": compact.history_payload_bytes,
                "materialization_input_entries": compact.materialization_input_entries,
                "peak_minima_entries": compact.peak_minima_entries,
                "rescue_active_fraction": compact.rescue_active_positions / len(data),
            })

    return {
        "schema": "cmpct-one-g02-compact-history-rescue-v1",
        "experimental_version": "ONE-G0.2",
        "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
        "frozen_gate_gap_positions": GATE_GAP,
        "modeled_history_payload_bytes": HISTORY_PAYLOAD_BYTES,
        "removed_redundant_position_payload_bytes": MINIMIZER_SPAN * 8,
        "hypothesis": "absolute positions in retained Gear history are derivable state, so removing them halves modeled history payload without changing hard-rescue opportunity",
        "disproof": "any hard transfer row loses opportunity relative to the full minimizer",
        "hard_rescue_rows": hard_rows,
        "hard_rescue_rows_preserved": hard_wins,
        "hard_rescue_loss_cases": hard_losses,
        "decision": "advance_compact_history" if hard_rows > 0 and not hard_losses else "reject_compact_history",
        "claim_boundary": "bounded-state representation experiment; Python object RSS differs from modeled u64 payload; no native/product or release authority",
        "rows": rows,
    }


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True, indent=2))
