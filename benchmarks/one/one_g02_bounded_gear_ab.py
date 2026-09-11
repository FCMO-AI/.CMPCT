"""ONE-G0.2 A/B: one Gear signal with local retention and bounded global starvation.

Sparse masking is efficient but offers no worst-case anchor spacing. This lowest-sufficient
repair keeps the same Gear state and generic exact-reuse Law nomination, adding only a
maximum global nomination gap. Content anchors reset the gap naturally; a deterministic
fallback fires only after starvation. The 64-entry local horizon protects short periodic
relations. No new reader-visible operation or legacy chunk format is introduced.
"""
from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
import json
import os
import statistics
import time

from benchmarks.one.one_g02_gear_replacement_ab import (
    _GEAR,
    _cases,
    _extend_left,
    _extend_right,
    ANCHOR_MASK,
    FIXED_MAX_INDEX_ENTRIES,
    GEAR_MAX_INDEX_ENTRIES,
    MIN_RUN,
    REPETITIONS,
    WINDOW,
    _U64_MASK,
)
from experiments.one.observe import Observation, observe

LOCAL_ENTRIES = 64
MAX_GLOBAL_GAP = 4096


@dataclass(frozen=True)
class BoundedResult:
    run_opportunity_bytes: int
    reuse_opportunity_bytes: int
    reuse_regions: int
    verification_read_bytes: int
    extension_read_bytes: int
    global_entries: int
    local_entries: int
    masked_anchors: int
    fallback_anchors: int
    input_bytes: int

    @property
    def total_source_read_bytes(self) -> int:
        return self.input_bytes + self.verification_read_bytes + self.extension_read_bytes

    @property
    def retained_index_payload_bytes(self) -> int:
        return 16 * (self.global_entries + self.local_entries)


def _bounded_observe(data: bytes) -> BoundedResult:
    if not data:
        return BoundedResult(0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

    global_index: dict[int, int] = {}
    local_index: OrderedDict[int, int] = OrderedDict()
    h = 0
    run_value = data[0]
    run_length = run_opportunity = 0
    reuse_opportunity = reuse_regions = 0
    verify_reads = extension_reads = 0
    masked_anchors = fallback_anchors = 0
    covered_until = 0
    last_global_position = -MAX_GLOBAL_GAP

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

        aligned = (position + 1) % WINDOW == 0
        masked = (h & ANCHOR_MASK) == 0
        starved = position - last_global_position >= MAX_GLOBAL_GAP
        global_nomination = masked or starved
        if global_nomination:
            if masked:
                masked_anchors += 1
            else:
                fallback_anchors += 1
            last_global_position = position

        source = local_index.get(h) if aligned else None
        if source is None and global_nomination:
            source = global_index.get(h)

        if source is None:
            if aligned:
                local_index[h] = start
                local_index.move_to_end(h)
                if len(local_index) > LOCAL_ENTRIES:
                    local_index.popitem(last=False)
            if global_nomination and len(global_index) < GEAR_MAX_INDEX_ENTRIES:
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
    return BoundedResult(
        run_opportunity,
        reuse_opportunity,
        reuse_regions,
        verify_reads,
        extension_reads,
        len(global_index),
        len(local_index),
        masked_anchors,
        fallback_anchors,
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
    # Deterministic hostile cycle proven to contain zero masked anchors.
    import random
    starved_basis = random.Random(4876).randbytes(8 * 1024)
    cases["starved_repeat_basis_8k_16k"] = starved_basis * 2

    rows = []
    losses = []
    for name, data in cases.items():
        fixed_ns, fixed_obj = _median(lambda: observe(
            data, min_run=MIN_RUN, chunk_size=WINDOW, max_index_entries=FIXED_MAX_INDEX_ENTRIES
        ))
        bounded_ns, bounded = _median(lambda: _bounded_observe(data))
        assert isinstance(fixed_obj, Observation)
        assert isinstance(bounded, BoundedResult)
        fixed = fixed_obj.stats
        assert bounded.run_opportunity_bytes == fixed.run_opportunity_bytes
        if fixed.reuse_opportunity_bytes and bounded.reuse_opportunity_bytes < fixed.reuse_opportunity_bytes:
            losses.append(name)
        rows.append({
            "case": name,
            "input_bytes": len(data),
            "fixed_reuse_opportunity_bytes": fixed.reuse_opportunity_bytes,
            "bounded_reuse_opportunity_bytes": bounded.reuse_opportunity_bytes,
            "bounded_minus_fixed_opportunity_bytes": bounded.reuse_opportunity_bytes - fixed.reuse_opportunity_bytes,
            "fixed_retained_index_payload_bytes": fixed.retained_index_payload_bytes,
            "bounded_retained_index_payload_bytes": bounded.retained_index_payload_bytes,
            "bounded_index_payload_fraction_of_fixed": (
                bounded.retained_index_payload_bytes / fixed.retained_index_payload_bytes
                if fixed.retained_index_payload_bytes else None
            ),
            "fixed_total_source_read_bytes": fixed.total_source_read_bytes,
            "bounded_total_source_read_bytes": bounded.total_source_read_bytes,
            "bounded_total_source_read_ratio_over_fixed": bounded.total_source_read_bytes / fixed.total_source_read_bytes,
            "fixed_median_ns": fixed_ns,
            "bounded_median_ns": bounded_ns,
            "bounded_elapsed_ratio_over_fixed": bounded_ns / fixed_ns,
            "bounded_global_entries": bounded.global_entries,
            "bounded_local_entries": bounded.local_entries,
            "masked_anchors": bounded.masked_anchors,
            "fallback_anchors": bounded.fallback_anchors,
        })
    return {
        "schema": "cmpct-one-g02-bounded-gear-ab-v1",
        "experimental_version": "ONE-G0.2",
        "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
        "max_global_gap": MAX_GLOBAL_GAP,
        "local_entries": LOCAL_ENTRIES,
        "hypothesis": "a maximum nomination-gap fallback on the same Gear stream removes sparse starvation while retaining much lower discovery state than the fixed index",
        "disproof": "hostile opportunity loss, excessive false nominations/proof reads, or compute/state carrying cost rejects the bounded-gap policy",
        "decision": "opportunity_semantics_survive_current_falsifiers" if not losses else "reject_bounded_gear_opportunity_loss",
        "opportunity_loss_cases": losses,
        "claim_boundary": "encoder discovery research only; no reader-visible CDC semantics and Python timing is not product-speed authority",
        "rows": rows,
    }


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True, indent=2))
