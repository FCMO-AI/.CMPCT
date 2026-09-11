"""ONE-G0.2 bounded byte-history rescue: transfer + paired carrying-cost falsifier.

The 32 KiB u64-signal ring proved that absolute positions are redundant, but every observed
position still writes eight history bytes. Gear states themselves are deterministic from one
prior Gear state and the observed source bytes. This candidate therefore retains a 4,096-byte
circular source-history cache plus one u64 seed and two u32 ring counters. On starvation it
replays that bounded cache to materialize the exact rolling-min state. This is not a source
rescan: bytes are retained during the fused observation pass and replayed only after the
pre-registered 4,096-position starvation trigger.

The gate is unchanged. Transfer selection is unchanged. The experiment rejects the candidate
if any generator-distinct hard row loses full-minimizer opportunity or if direct hosted paired
timing loses the established material advantage on random/already-compressed controls.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import gc
import json
import os
import random
import statistics
import time

from benchmarks.one.one_g02_gear_replacement_ab import (
    _GEAR, _U64_MASK, ANCHOR_MASK, WINDOW, MIN_RUN, FIXED_MAX_INDEX_ENTRIES,
    GEAR_MAX_INDEX_ENTRIES, _cases, _extend_left, _extend_right, _gear_observe,
)
from benchmarks.one.one_g02_minimizer_gear_ab import _minimizer_observe, MINIMIZER_SPAN
from benchmarks.one.one_g02_late_rescue_transfer import (
    BASIS_BYTES, TARGET_STARVED_BASES, MAX_SEED, INSERTIONS, _starved_bases,
)
from experiments.one.observe import observe

GATE_GAP = MINIMIZER_SPAN
HISTORY_BYTES = MINIMIZER_SPAN
MODELED_INCREMENTAL_STATE_BYTES = HISTORY_BYTES + 8 + 4 + 4  # byte ring + seed + next/count
ROUNDS = 9


@dataclass(frozen=True)
class ByteHistoryResult:
    reuse_opportunity_bytes: int
    reuse_regions: int
    rescue_active_positions: int
    emitted_minimizers: int
    sparse_anchors: int
    peak_minima_entries: int
    modeled_history_state_bytes: int
    materialization_replay_bytes: int
    verification_read_bytes: int
    extension_read_bytes: int


def _byte_history_rescue_observe(data: bytes) -> ByteHistoryResult:
    if not data:
        return ByteHistoryResult(0, 0, 0, 0, 0, 0, MODELED_INCREMENTAL_STATE_BYTES, 0, 0, 0)

    sparse_index: dict[int, int] = {}
    rescue_index: dict[int, int] = {}
    history = bytearray(HISTORY_BYTES)
    history_count = 0
    history_next = 0
    history_seed_h = 0  # Gear state immediately before the oldest retained eligible byte.
    minima: deque[tuple[int, int]] = deque()
    active = False
    h = 0
    last_sparse_position: int | None = None
    last_emitted_position = -1
    rescue_active_positions = emitted = anchors = peak_minima = replayed_bytes = 0
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

        h_before = h
        h = ((h << 1) + _GEAR[value]) & _U64_MASK
        if position + 1 < WINDOW:
            continue
        start = position + 1 - WINDOW
        run_dominated = run_length >= max(MIN_RUN, WINDOW)

        if history_count == 0:
            history_seed_h = h_before
        elif history_count == HISTORY_BYTES:
            oldest = history[history_next]
            history_seed_h = ((history_seed_h << 1) + _GEAR[oldest]) & _U64_MASK
        history[history_next] = value
        history_next = (history_next + 1) % HISTORY_BYTES
        history_count = min(history_count + 1, HISTORY_BYTES)

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
            if history_count < HISTORY_BYTES:
                continue
            minima.clear()
            replay_h = history_seed_h
            oldest_position = position - history_count + 1
            oldest_slot = history_next
            for j in range(history_count):
                replay_value = history[(oldest_slot + j) % HISTORY_BYTES]
                replay_h = ((replay_h << 1) + _GEAR[replay_value]) & _U64_MASK
                hist_position = oldest_position + j
                while minima and minima[-1][0] >= replay_h:
                    minima.pop()
                minima.append((replay_h, hist_position))
            replayed_bytes += history_count
            if replay_h != h:
                raise AssertionError("byte-history Gear replay diverged from fused observation state")
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

    return ByteHistoryResult(
        reuse_opportunity, reuse_regions, rescue_active_positions, emitted, anchors,
        peak_minima, MODELED_INCREMENTAL_STATE_BYTES, replayed_bytes,
        verify_reads, extension_reads,
    )


def _measure(fn):
    gc.disable()
    try:
        t0 = time.perf_counter_ns()
        result = fn()
        return time.perf_counter_ns() - t0, result
    finally:
        gc.enable()


def _paired(data: bytes) -> dict[str, object]:
    full_samples: list[int] = []
    byte_samples: list[int] = []
    full = byte = None
    for i in range(ROUNDS):
        if i % 2 == 0:
            ns, full = _measure(lambda: _minimizer_observe(data)); full_samples.append(ns)
            ns, byte = _measure(lambda: _byte_history_rescue_observe(data)); byte_samples.append(ns)
        else:
            ns, byte = _measure(lambda: _byte_history_rescue_observe(data)); byte_samples.append(ns)
            ns, full = _measure(lambda: _minimizer_observe(data)); full_samples.append(ns)
    assert full is not None and byte is not None
    full_median = int(statistics.median(full_samples))
    byte_median = int(statistics.median(byte_samples))
    return {
        "full_median_ns": full_median,
        "byte_history_median_ns": byte_median,
        "byte_history_elapsed_ratio_over_full": byte_median / full_median,
        "full_reuse_opportunity_bytes": full.reuse_opportunity_bytes,
        "byte_history_reuse_opportunity_bytes": byte.reuse_opportunity_bytes,
        "modeled_history_state_bytes": byte.modeled_history_state_bytes,
        "materialization_replay_bytes": byte.materialization_replay_bytes,
        "rescue_active_positions": byte.rescue_active_positions,
        "verification_read_bytes": byte.verification_read_bytes,
        "extension_read_bytes": byte.extension_read_bytes,
        "full_samples_ns": full_samples,
        "byte_history_samples_ns": byte_samples,
    }


def run() -> dict[str, object]:
    selected = _starved_bases()
    transfer_rows = []
    hard_rows = hard_wins = 0
    hard_losses: list[str] = []
    for seed, basis in selected:
        for insertion in INSERTIONS:
            data = basis + insertion + basis
            fixed = observe(data, min_run=MIN_RUN, chunk_size=WINDOW, max_index_entries=FIXED_MAX_INDEX_ENTRIES)
            sparse = _gear_observe(data)
            full = _minimizer_observe(data)
            byte = _byte_history_rescue_observe(data)
            cheap = max(fixed.stats.reuse_opportunity_bytes, sparse.reuse_opportunity_bytes)
            hard = full.reuse_opportunity_bytes > cheap
            if hard:
                hard_rows += 1
                if byte.reuse_opportunity_bytes < full.reuse_opportunity_bytes:
                    hard_losses.append(f"seed={seed}/insert={len(insertion)}")
                else:
                    hard_wins += 1
            transfer_rows.append({
                "seed": seed,
                "insertion_bytes": len(insertion),
                "input_bytes": len(data),
                "full_minimizer_reuse_opportunity_bytes": full.reuse_opportunity_bytes,
                "byte_history_reuse_opportunity_bytes": byte.reuse_opportunity_bytes,
                "hard_rescue_needed": hard,
                "byte_minus_full_opportunity_bytes": byte.reuse_opportunity_bytes - full.reuse_opportunity_bytes,
                "modeled_history_state_bytes": byte.modeled_history_state_bytes,
                "materialization_replay_bytes": byte.materialization_replay_bytes,
                "rescue_active_fraction": byte.rescue_active_positions / len(data),
            })

    base = _cases()
    timing_cases = {
        "random_1mib": base["random_1mib"],
        "zlib_random_payload": base["zlib_random_payload"],
        "repeat_basis_64k_1mib": base["repeat_basis_64k_1mib"],
        "shifted_version_pair_1byte_insert": base["shifted_version_pair_1byte_insert"],
        "transfer_starved_seed10_insert1": random.Random(10).randbytes(4096) + b"X" + random.Random(10).randbytes(4096),
    }
    timing_rows = [{"case": name, "input_bytes": len(data), **_paired(data)} for name, data in timing_cases.items()]
    negatives = [r for r in timing_rows if r["case"] in {"random_1mib", "zlib_random_payload"}]
    negative_ratio = statistics.median(r["byte_history_elapsed_ratio_over_full"] for r in negatives)
    hard_timing = next(r for r in timing_rows if r["case"] == "transfer_starved_seed10_insert1")
    hard_timing_preserved = hard_timing["byte_history_reuse_opportunity_bytes"] >= hard_timing["full_reuse_opportunity_bytes"]

    return {
        "schema": "cmpct-one-g02-byte-history-rescue-ab-v1",
        "experimental_version": "ONE-G0.2",
        "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
        "frozen_gate_gap_positions": GATE_GAP,
        "modeled_incremental_history_state_bytes": MODELED_INCREMENTAL_STATE_BYTES,
        "signal_ring_baseline_bytes": MINIMIZER_SPAN * 8,
        "tuple_ring_baseline_bytes": MINIMIZER_SPAN * 16,
        "history_state_reduction_vs_signal_ring_bytes": MINIMIZER_SPAN * 8 - MODELED_INCREMENTAL_STATE_BYTES,
        "history_state_reduction_vs_tuple_ring_bytes": MINIMIZER_SPAN * 16 - MODELED_INCREMENTAL_STATE_BYTES,
        "rounds": ROUNDS,
        "hypothesis": "one prior Gear state plus a 4,096-byte retained input ring is sufficient to materialize exact minimizer state on starvation, preserving transfer while reducing always-on retained state and keeping material negative-path elapsed advantage",
        "disproof": "any hard transfer opportunity loss, Gear replay divergence, or negative-control median elapsed ratio >= 0.9 rejects this execution shape",
        "hard_rescue_rows": hard_rows,
        "hard_rescue_rows_preserved": hard_wins,
        "hard_rescue_loss_cases": hard_losses,
        "negative_control_median_elapsed_ratio": negative_ratio,
        "hard_timing_preserved": hard_timing_preserved,
        "decision": (
            "advance_byte_history_rescue"
            if hard_rows > 0 and not hard_losses and hard_timing_preserved and negative_ratio < 0.9
            else "reject_or_rehabilitate_byte_history_rescue"
        ),
        "claim_boundary": "bounded encoder cache + hosted Python causal timing only; modeled native-sized state is not Python RSS; no stored-byte, native/product-speed, reader-format or release authority",
        "transfer_rows": transfer_rows,
        "timing_rows": timing_rows,
    }


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True, indent=2))
