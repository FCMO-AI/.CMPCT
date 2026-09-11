"""ONE-G0.2 A/B: one Gear stream selected by rolling minimizers.

Sparse masks are shift-invariant but have no worst-case spacing guarantee. Coordinate gap
fallbacks bound spacing but lose shift invariance. A rolling minimizer combines both useful
properties: every full selector window owns a content-derived minimum, and exact repeated
content produces the same interior minima independent of absolute offset. A tiny aligned
local horizon remains solely for relationships shorter than the minimizer span.

This remains encoder-side nomination of the same generic exact-reuse Law. The reader sees
neither Gear nor minimizers. Every nominated reuse is byte-proven and proof rereads are
charged. Python elapsed time is causal implementation evidence only.
"""
from __future__ import annotations

from collections import OrderedDict, deque
from dataclasses import dataclass
import json
import os
import random
import statistics
import time

from benchmarks.one.one_g02_gear_replacement_ab import (
    _GEAR,
    _cases,
    _extend_left,
    _extend_right,
    FIXED_MAX_INDEX_ENTRIES,
    GEAR_MAX_INDEX_ENTRIES,
    MIN_RUN,
    REPETITIONS,
    WINDOW,
    _U64_MASK,
)
from experiments.one.observe import Observation, observe

MINIMIZER_SPAN = 4096
LOCAL_ENTRIES = 64


@dataclass(frozen=True)
class MinimizerResult:
    run_opportunity_bytes: int
    reuse_opportunity_bytes: int
    reuse_regions: int
    verification_read_bytes: int
    extension_read_bytes: int
    global_entries: int
    local_entries: int
    emitted_minimizers: int
    peak_minimizer_queue_entries: int
    input_bytes: int

    @property
    def total_source_read_bytes(self) -> int:
        return self.input_bytes + self.verification_read_bytes + self.extension_read_bytes

    @property
    def retained_state_payload_bytes(self) -> int:
        return 16 * (self.global_entries + self.local_entries + self.peak_minimizer_queue_entries)


def _minimizer_observe(data: bytes) -> MinimizerResult:
    if not data:
        return MinimizerResult(0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

    global_index: dict[int, int] = {}
    local_index: OrderedDict[int, int] = OrderedDict()
    minima: deque[tuple[int, int]] = deque()
    minimizer_enabled = len(data) >= MINIMIZER_SPAN + WINDOW
    peak_queue = 0
    last_emitted_position = -1
    h = 0
    run_value = data[0]
    run_length = run_opportunity = 0
    reuse_opportunity = reuse_regions = 0
    verify_reads = extension_reads = emitted = 0
    covered_until = 0

    def audition(start: int, source: int | None) -> None:
        nonlocal reuse_opportunity, reuse_regions, verify_reads, extension_reads, covered_until
        if source is None or start < covered_until:
            return
        verify_reads += 2 * WINDOW
        if data[source : source + WINDOW] != data[start : start + WINDOW]:
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
        if not run_length:
            run_value, run_length = value, 1
        elif value == run_value:
            run_length += 1
        else:
            if run_length >= MIN_RUN:
                run_opportunity += run_length
            run_value, run_length = value, 1

        h = ((h << 1) + _GEAR[value]) & _U64_MASK
        if position + 1 < WINDOW:
            continue
        start = position + 1 - WINDOW
        run_dominated = run_length >= max(MIN_RUN, WINDOW)
        run_start = position - run_length + 1

        if not run_dominated and (position + 1) % WINDOW == 0:
            source = local_index.get(h)
            audition(start, source)
            if source is None:
                local_index[h] = start
                local_index.move_to_end(h)
                if len(local_index) > LOCAL_ENTRIES:
                    local_index.popitem(last=False)

        # An input too short to fill one minimizer span cannot emit a global minimizer.
        # Skipping the dead queue is a structural impossibility gate, not workload dispatch.
        if not minimizer_enabled:
            continue

        while minima and minima[-1][0] >= h:
            minima.pop()
        minima.append((h, position))
        first_valid = position - MINIMIZER_SPAN + 1
        while minima and minima[0][1] < first_valid:
            minima.popleft()
        peak_queue = max(peak_queue, len(minima))

        if first_valid < WINDOW - 1:
            continue
        signal, anchor_position = minima[0]
        anchor_start = anchor_position + 1 - WINDOW
        if run_dominated and anchor_start >= run_start:
            continue
        if anchor_position == last_emitted_position:
            continue
        last_emitted_position = anchor_position
        emitted += 1
        source = global_index.get(signal)
        audition(anchor_start, source)
        if source is None and len(global_index) < GEAR_MAX_INDEX_ENTRIES:
            global_index[signal] = anchor_start

    if run_length >= MIN_RUN:
        run_opportunity += run_length
    return MinimizerResult(
        run_opportunity,
        reuse_opportunity,
        reuse_regions,
        verify_reads,
        extension_reads,
        len(global_index),
        len(local_index),
        emitted,
        peak_queue,
        len(data),
    )


def _median(fn):
    samples = []
    result = None
    for _ in range(REPETITIONS):
        t0 = time.perf_counter_ns()
        result = fn()
        samples.append(time.perf_counter_ns() - t0)
    return int(statistics.median(samples)), result


def run() -> dict[str, object]:
    cases = _cases()
    starved = random.Random(4876).randbytes(8 * 1024)
    cases["starved_repeat_basis_8k_16k"] = starved * 2
    cases["starved_shifted_basis_8k_insert1"] = starved + b"X" + starved

    rows = []
    losses = []
    for name, data in cases.items():
        fixed_ns, fixed_obj = _median(lambda: observe(
            data, min_run=MIN_RUN, chunk_size=WINDOW, max_index_entries=FIXED_MAX_INDEX_ENTRIES
        ))
        minimizer_ns, candidate = _median(lambda: _minimizer_observe(data))
        assert isinstance(fixed_obj, Observation)
        assert isinstance(candidate, MinimizerResult)
        fixed = fixed_obj.stats
        assert candidate.run_opportunity_bytes == fixed.run_opportunity_bytes
        if fixed.reuse_opportunity_bytes and candidate.reuse_opportunity_bytes < fixed.reuse_opportunity_bytes:
            losses.append(name)
        rows.append({
            "case": name,
            "input_bytes": len(data),
            "fixed_reuse_opportunity_bytes": fixed.reuse_opportunity_bytes,
            "minimizer_reuse_opportunity_bytes": candidate.reuse_opportunity_bytes,
            "minimizer_minus_fixed_opportunity_bytes": candidate.reuse_opportunity_bytes - fixed.reuse_opportunity_bytes,
            "fixed_retained_index_payload_bytes": fixed.retained_index_payload_bytes,
            "minimizer_retained_state_payload_bytes": candidate.retained_state_payload_bytes,
            "minimizer_state_fraction_of_fixed": (
                candidate.retained_state_payload_bytes / fixed.retained_index_payload_bytes
                if fixed.retained_index_payload_bytes else None
            ),
            "fixed_total_source_read_bytes": fixed.total_source_read_bytes,
            "minimizer_total_source_read_bytes": candidate.total_source_read_bytes,
            "minimizer_total_source_read_ratio_over_fixed": candidate.total_source_read_bytes / fixed.total_source_read_bytes,
            "fixed_median_ns": fixed_ns,
            "minimizer_median_ns": minimizer_ns,
            "minimizer_elapsed_ratio_over_fixed": minimizer_ns / fixed_ns,
            "minimizer_global_entries": candidate.global_entries,
            "minimizer_local_entries": candidate.local_entries,
            "emitted_minimizers": candidate.emitted_minimizers,
            "peak_minimizer_queue_entries": candidate.peak_minimizer_queue_entries,
        })

    shifted = next(row for row in rows if row["case"] == "starved_shifted_basis_8k_insert1")
    shifted_recovered = shifted["minimizer_reuse_opportunity_bytes"] >= 8 * 1024
    return {
        "schema": "cmpct-one-g02-minimizer-gear-ab-v3",
        "experimental_version": "ONE-G0.2",
        "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
        "minimizer_span": MINIMIZER_SPAN,
        "local_entries": LOCAL_ENTRIES,
        "hypothesis": "rolling minima over the one Gear stream provide bounded-spacing, shift-invariant global nominations while preserving fixed-signal opportunity mass with lower retained state on the large regimes where global discovery is needed",
        "disproof": "fixed-opportunity loss, failure on the anchor-starved one-byte-shift relation, redundant run reuse, or excessive queue/proof/elapsed carrying cost rejects minimizer retention",
        "decision": (
            "opportunity_semantics_survive_current_falsifiers_compute_review_required"
            if not losses and shifted_recovered
            else "reject_minimizer_gear_current_falsifiers"
        ),
        "opportunity_loss_cases": losses,
        "starved_shifted_relation_recovered": shifted_recovered,
        "claim_boundary": "encoder discovery research only; state and Python elapsed are carrying-cost evidence, not product-speed authority",
        "rows": rows,
    }


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True, indent=2))
