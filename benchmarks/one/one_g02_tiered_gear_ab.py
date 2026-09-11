"""ONE-G0.2 A/B for one Gear signal with bounded local + sparse global retention.

Sparse-only Gear is phase-blind on some short periodic sources. This is the lowest-sufficient
follow-up: keep ONE generic exact-reuse semantics and the same Gear state, but retain it at
two horizons. A 64-entry aligned local cache protects short-repeat opportunity; a sparse
1/1024 global table protects long/shifted opportunity. No reader-visible CDC mechanism is
introduced. Exact proof traffic and Python reference time are charged.
"""
from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
import json
import os
import statistics
import time

from experiments.one.observe import Observation, observe
from benchmarks.one.one_g02_gear_replacement_ab import (
    _GEAR,
    _cases,
    _extend_left,
    _extend_right,
    ANCHOR_MASK,
    MIN_RUN,
    WINDOW,
    FIXED_MAX_INDEX_ENTRIES,
    GEAR_MAX_INDEX_ENTRIES,
    REPETITIONS,
    _U64_MASK,
)

LOCAL_ENTRIES = 64


@dataclass(frozen=True)
class TieredResult:
    run_opportunity_bytes: int
    reuse_opportunity_bytes: int
    reuse_regions: int
    verification_read_bytes: int
    extension_read_bytes: int
    global_entries: int
    local_entries: int
    global_anchors: int
    local_probes: int

    @property
    def total_source_read_bytes(self) -> int:
        return self.input_bytes + self.verification_read_bytes + self.extension_read_bytes

    @property
    def retained_index_payload_bytes(self) -> int:
        return 16 * (self.global_entries + self.local_entries)

    input_bytes: int = 0


def _tiered_observe(data: bytes) -> TieredResult:
    if not data:
        return TieredResult(0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

    global_index: dict[int, int] = {}
    local_index: OrderedDict[int, int] = OrderedDict()
    h = 0
    run_value = data[0]
    run_length = run_opportunity = 0
    reuse_opportunity = reuse_regions = 0
    verify_reads = extension_reads = 0
    global_anchors = local_probes = 0
    covered_until = 0

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
        if run_length >= max(MIN_RUN, WINDOW):
            continue

        # One signal, two retention horizons. Local alignment is only a storage schedule;
        # it does not create another fingerprint family or another reader operation.
        aligned = (position + 1) % WINDOW == 0
        sparse = (h & ANCHOR_MASK) == 0
        source = None
        if aligned:
            local_probes += 1
            source = local_index.get(h)
        if source is None and sparse:
            global_anchors += 1
            source = global_index.get(h)
        if source is None:
            if aligned:
                local_index[h] = start
                local_index.move_to_end(h)
                if len(local_index) > LOCAL_ENTRIES:
                    local_index.popitem(last=False)
            if sparse and len(global_index) < GEAR_MAX_INDEX_ENTRIES:
                global_index.setdefault(h, start)
            continue
        if start < covered_until:
            continue

        verify_reads += 2 * WINDOW
        if data[source : source + WINDOW] != data[start : start + WINDOW]:
            continue
        left, lreads = _extend_left(data, source, start, covered_until)
        right, rreads = _extend_right(data, source, start)
        extension_reads += lreads + rreads
        target_start = max(start - left, covered_until)
        target_end = start + right
        if target_end > target_start:
            reuse_regions += 1
            reuse_opportunity += target_end - target_start
            covered_until = target_end

    if run_length >= MIN_RUN:
        run_opportunity += run_length
    return TieredResult(
        run_opportunity,
        reuse_opportunity,
        reuse_regions,
        verify_reads,
        extension_reads,
        len(global_index),
        len(local_index),
        global_anchors,
        local_probes,
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
    rows = []
    opportunity_losses = []
    for name, data in _cases().items():
        fixed_ns, fixed_obj = _median(lambda: observe(
            data, min_run=MIN_RUN, chunk_size=WINDOW, max_index_entries=FIXED_MAX_INDEX_ENTRIES
        ))
        tiered_ns, tiered = _median(lambda: _tiered_observe(data))
        assert isinstance(fixed_obj, Observation)
        assert isinstance(tiered, TieredResult)
        fixed = fixed_obj.stats
        assert tiered.run_opportunity_bytes == fixed.run_opportunity_bytes
        if fixed.reuse_opportunity_bytes and tiered.reuse_opportunity_bytes < fixed.reuse_opportunity_bytes:
            opportunity_losses.append(name)
        rows.append({
            "case": name,
            "input_bytes": len(data),
            "fixed_reuse_opportunity_bytes": fixed.reuse_opportunity_bytes,
            "tiered_reuse_opportunity_bytes": tiered.reuse_opportunity_bytes,
            "tiered_minus_fixed_opportunity_bytes": tiered.reuse_opportunity_bytes - fixed.reuse_opportunity_bytes,
            "fixed_retained_index_payload_bytes": fixed.retained_index_payload_bytes,
            "tiered_retained_index_payload_bytes": tiered.retained_index_payload_bytes,
            "tiered_index_payload_fraction_of_fixed": (
                tiered.retained_index_payload_bytes / fixed.retained_index_payload_bytes
                if fixed.retained_index_payload_bytes else None
            ),
            "fixed_total_source_read_bytes": fixed.total_source_read_bytes,
            "tiered_total_source_read_bytes": tiered.total_source_read_bytes,
            "tiered_total_source_read_ratio_over_fixed": tiered.total_source_read_bytes / fixed.total_source_read_bytes,
            "fixed_median_ns": fixed_ns,
            "tiered_median_ns": tiered_ns,
            "tiered_elapsed_ratio_over_fixed": tiered_ns / fixed_ns,
            "tiered_global_entries": tiered.global_entries,
            "tiered_local_entries": tiered.local_entries,
            "tiered_global_anchors": tiered.global_anchors,
            "tiered_local_probes": tiered.local_probes,
        })
    return {
        "schema": "cmpct-one-g02-tiered-gear-ab-v1",
        "experimental_version": "ONE-G0.2",
        "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
        "hypothesis": "the same Gear state retained at bounded local and sparse global horizons removes sparse phase blindness without restoring fixed-index memory traffic",
        "disproof": "any fixed-signal opportunity loss or compute/read/state carrying cost large enough to erase the intended efficiency gain rejects this intervention",
        "decision": "opportunity_semantics_survive" if not opportunity_losses else "reject_tiered_gear_opportunity_loss",
        "opportunity_loss_cases": opportunity_losses,
        "local_entries": LOCAL_ENTRIES,
        "global_max_entries": GEAR_MAX_INDEX_ENTRIES,
        "claim_boundary": "encoder discovery research only; Python timing is causal cost evidence, not product-speed authority",
        "rows": rows,
    }


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True, indent=2))
