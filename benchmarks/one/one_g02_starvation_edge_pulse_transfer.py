"""ONE-G0.2 edge-pulse historical replay transfer falsifier.

Mission lock
============
Compact continuous rescue reversed the large-path compute debt but remains ~2.97x slower
than the promoted selector on the 8,193-byte hard-transfer row. The causal owner on that
small row is per-position queue maintenance after activation, not missing history: bounded
history+seed now exists and has already preserved the 35/35 hard-transfer opportunity in
the complete rescue family.

Builder hypothesis: for short starvation episodes, exact continuous queue maintenance is
not necessary for discovery opportunity. Replay the bounded historical states only at the
*edges* of a starvation episode — activation and episode exit/EOF — and audition those two
rightmost-minimum candidates. This retains the historical information that cold rescue lost
without maintaining a minimizer queue on every active byte.

This is NOT a new reader opcode and does not change the 4,096 starvation/span constants.
It is an encoder discovery-scheduling experiment only.

Frozen disproof before result-bearing execution:
- generator selection remains the first 12 4,096-byte bases in seeds [0,4095] with zero
  qualifying sparse Gear anchors, independent of rescue outcome;
- insertion lengths remain 1, 8 and 31 bytes;
- every row where the full minimizer owns marginal opportunity beyond fixed+sparse cheap
  observers must retain 100% of that full-minimizer opportunity under edge-pulse rescue;
- zero hard rows is inconclusive; any hard-row loss rejects edge-pulse rescue as a complete
  small-case replacement.
All replay work, pulse count and proof reads are reported. Native elapsed is deliberately
not inferred from this semantic falsifier.
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
from benchmarks.one.one_g02_late_rescue_transfer import _starved_bases, INSERTIONS
from experiments.one.observe import observe

GATE_GAP = MINIMIZER_SPAN


@dataclass(frozen=True)
class PulseResult:
    reuse_opportunity_bytes: int
    pulses: int
    replayed_positions: int
    sparse_anchors: int
    verification_read_bytes: int
    extension_read_bytes: int


def _edge_pulse_observe(data: bytes) -> PulseResult:
    if not data:
        return PulseResult(0, 0, 0, 0, 0, 0)

    sparse_index: dict[int, int] = {}
    rescue_index: dict[int, int] = {}
    # Semantic history oracle: stores exactly the states/positions that a byte-history+seed
    # implementation can reproduce by bounded replay. Native cost is tested separately.
    history: deque[tuple[int, int]] = deque(maxlen=MINIMIZER_SPAN)
    h = 0
    last_sparse_position: int | None = None
    active = False
    last_pulse_anchor = -1
    pulses = replayed = anchors = 0
    reuse_opportunity = verify_reads = extension_reads = 0
    covered_until = 0
    run_value = data[0]
    run_length = 0

    def audition(start: int, signal: int, index: dict[int, int]) -> None:
        nonlocal reuse_opportunity, verify_reads, extension_reads, covered_until
        if start < 0 or start < covered_until:
            return
        source = index.get(signal)
        if source is None:
            if len(index) < GEAR_MAX_INDEX_ENTRIES:
                index[signal] = start
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
            reuse_opportunity += target_end - target_start
            covered_until = target_end

    def pulse() -> None:
        nonlocal pulses, replayed, last_pulse_anchor
        if len(history) < MINIMIZER_SPAN:
            return
        pulses += 1
        replayed += len(history)
        # Rightmost minimum: ties replace the earlier position, matching the full recurrence.
        signal, anchor_position = history[0]
        for candidate_signal, candidate_position in history:
            if candidate_signal <= signal:
                signal, anchor_position = candidate_signal, candidate_position
        if anchor_position == last_pulse_anchor:
            return
        last_pulse_anchor = anchor_position
        audition(anchor_position + 1 - WINDOW, signal, rescue_index)

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
        run_dominated = run_length >= max(MIN_RUN, WINDOW)
        sparse = not (h & ANCHOR_MASK) and not run_dominated

        # Close an active starvation episode using the history *before* the sparse reset.
        if sparse and active:
            pulse()
            active = False
            last_pulse_anchor = -1

        if sparse:
            anchors += 1
            audition(position + 1 - WINDOW, h, sparse_index)
            last_sparse_position = position

        history.append((h, position))
        if sparse or run_dominated:
            continue

        gap = position - last_sparse_position if last_sparse_position is not None else position + 1 - WINDOW
        if gap >= GATE_GAP and not active:
            pulse()
            active = True

    if active:
        pulse()

    return PulseResult(reuse_opportunity, pulses, replayed, anchors, verify_reads, extension_reads)


def run() -> dict[str, object]:
    selected = _starved_bases()
    rows=[]; hard_rows=0; losses=[]
    for seed,basis in selected:
        for insertion in INSERTIONS:
            data=basis+insertion+basis
            fixed=observe(data,min_run=MIN_RUN,chunk_size=WINDOW,max_index_entries=FIXED_MAX_INDEX_ENTRIES)
            sparse=_gear_observe(data)
            full=_minimizer_observe(data)
            pulse=_edge_pulse_observe(data)
            cheap=max(fixed.stats.reuse_opportunity_bytes,sparse.reuse_opportunity_bytes)
            hard=full.reuse_opportunity_bytes>cheap
            if hard:
                hard_rows+=1
                if pulse.reuse_opportunity_bytes < full.reuse_opportunity_bytes:
                    losses.append(f"seed={seed}/insert={len(insertion)}")
            rows.append({
                "seed":seed,"insertion_bytes":len(insertion),"input_bytes":len(data),
                "fixed_reuse_opportunity_bytes":fixed.stats.reuse_opportunity_bytes,
                "sparse_reuse_opportunity_bytes":sparse.reuse_opportunity_bytes,
                "full_minimizer_reuse_opportunity_bytes":full.reuse_opportunity_bytes,
                "edge_pulse_reuse_opportunity_bytes":pulse.reuse_opportunity_bytes,
                "hard_rescue_needed":hard,
                "pulse_minus_full_opportunity_bytes":pulse.reuse_opportunity_bytes-full.reuse_opportunity_bytes,
                "pulses":pulse.pulses,"replayed_positions":pulse.replayed_positions,
                "verification_read_bytes":pulse.verification_read_bytes,
                "extension_read_bytes":pulse.extension_read_bytes,
            })
    decision=("edge_pulse_transfer_survives" if hard_rows and not losses
              else "transfer_inconclusive_no_hard_rows" if not hard_rows
              else "reject_edge_pulse_as_complete_small_case_rescue")
    return {
        "schema":"cmpct-one-g02-starvation-edge-pulse-transfer-v1",
        "experimental_version":"ONE-G0.2",
        "source_sha":os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
        "selection_rule":"first 12 seeds in [0,4095] whose 4096-byte basis has zero qualifying sparse Gear anchors",
        "insertion_lengths":[len(x) for x in INSERTIONS],
        "frozen_gate_gap_positions":GATE_GAP,
        "hard_rescue_rows":hard_rows,
        "hard_rescue_loss_cases":losses,
        "decision":decision,
        "claim_boundary":"generator-distinct encoder-discovery transfer only; semantic falsifier, not native/product/release authority",
        "rows":rows,
    }

if __name__=="__main__":
    print(json.dumps(run(),indent=2,sort_keys=True))
