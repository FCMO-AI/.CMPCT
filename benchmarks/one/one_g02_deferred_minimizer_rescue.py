"""ONE-G0.2 rehabilitation: starvation-gated minimizer with deferred materialization.

The cold-start transfer falsifier showed that waiting 4,096 positions to prove sparse-anchor
starvation and then waiting another full minimizer span creates an avoidable blind interval.
This candidate changes the execution boundary rather than the gate: the fused observation
pass retains the last 4,096 already-computed Gear states in a bounded history ring.  When
starvation is proven, it materializes the exact rolling-min deque from that history and may
nominate immediately. No source bytes are rescanned and the reader remains unchanged.

The retained history and its writes are explicit carrying cost. This experiment first asks
semantic/transfer survival; elapsed/state rehabilitation is a separate gate if it survives.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import json
import os
import random

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
HISTORY_ENTRY_BYTES = 16  # modeled u64 Gear state + u64 absolute position


@dataclass(frozen=True)
class DeferredResult:
    reuse_opportunity_bytes: int
    reuse_regions: int
    rescue_active_positions: int
    emitted_minimizers: int
    sparse_anchors: int
    peak_minima_entries: int
    history_entries: int
    history_payload_bytes: int
    materialization_input_entries: int
    verification_read_bytes: int
    extension_read_bytes: int


def _deferred_rescue_observe(data: bytes) -> DeferredResult:
    if not data:
        return DeferredResult(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

    sparse_index: dict[int, int] = {}
    rescue_index: dict[int, int] = {}
    history: deque[tuple[int, int]] = deque(maxlen=MINIMIZER_SPAN)
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
        history.append((h, position))

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
            if len(history) < MINIMIZER_SPAN:
                continue
            # Build exactly the monotonic state the always-on rolling minimizer would
            # have after consuming this same 4,096-state suffix. Equal states pop so
            # the surviving minimum is the rightmost minimum, matching canonical G0.2.
            minima.clear()
            for signal, hist_position in history:
                while minima and minima[-1][0] >= signal:
                    minima.pop()
                minima.append((signal, hist_position))
            materialized_entries += len(history)
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

    return DeferredResult(
        reuse_opportunity, reuse_regions, rescue_active_positions, emitted, anchors,
        peak_minima, len(history), len(history) * HISTORY_ENTRY_BYTES,
        materialized_entries, verify_reads, extension_reads,
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
            deferred = _deferred_rescue_observe(data)
            cheap = max(fixed.stats.reuse_opportunity_bytes, sparse.reuse_opportunity_bytes)
            hard = full.reuse_opportunity_bytes > cheap
            if hard:
                hard_rows += 1
                if deferred.reuse_opportunity_bytes < full.reuse_opportunity_bytes:
                    hard_losses.append(f"seed={seed}/insert={len(insertion)}")
                else:
                    hard_wins += 1
            rows.append({
                "seed": seed,
                "insertion_bytes": len(insertion),
                "input_bytes": len(data),
                "fixed_reuse_opportunity_bytes": fixed.stats.reuse_opportunity_bytes,
                "sparse_reuse_opportunity_bytes": sparse.reuse_opportunity_bytes,
                "full_minimizer_reuse_opportunity_bytes": full.reuse_opportunity_bytes,
                "deferred_rescue_reuse_opportunity_bytes": deferred.reuse_opportunity_bytes,
                "hard_rescue_needed": hard,
                "deferred_minus_full_opportunity_bytes": deferred.reuse_opportunity_bytes - full.reuse_opportunity_bytes,
                "rescue_active_fraction": deferred.rescue_active_positions / len(data),
                "history_payload_bytes": deferred.history_payload_bytes,
                "materialization_input_entries": deferred.materialization_input_entries,
                "peak_minima_entries": deferred.peak_minima_entries,
                "verification_read_bytes": deferred.verification_read_bytes,
                "extension_read_bytes": deferred.extension_read_bytes,
            })

    return {
        "schema": "cmpct-one-g02-deferred-minimizer-rescue-v1",
        "experimental_version": "ONE-G0.2",
        "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
        "selection_rule": f"same frozen {TARGET_STARVED_BASES} zero-sparse-anchor {BASIS_BYTES}-byte bases selected within seeds 0..{MAX_SEED}",
        "selected_seeds": [seed for seed, _ in selected],
        "insertion_lengths": [len(x) for x in INSERTIONS],
        "frozen_gate_gap_positions": GATE_GAP,
        "modeled_history_entry_bytes": HISTORY_ENTRY_BYTES,
        "hypothesis": "retaining one bounded span of already-computed Gear states removes cold-start blindness and restores full-minimizer hard-rescue opportunity without source rescans",
        "disproof": "any generator-distinct hard-rescue row still loses full-minimizer opportunity; surviving semantics advance to elapsed/state carrying-cost review",
        "hard_rescue_rows": hard_rows,
        "hard_rescue_rows_preserved": hard_wins,
        "hard_rescue_loss_cases": hard_losses,
        "decision": "advance_deferred_materialization" if hard_rows > 0 and not hard_losses else "reject_deferred_materialization",
        "claim_boundary": "encoder-discovery transfer rehabilitation only; modeled history cost is explicit; no native/product or release authority",
        "rows": rows,
    }


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True, indent=2))
