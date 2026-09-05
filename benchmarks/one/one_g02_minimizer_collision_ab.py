"""ONE-G0.2 hostile A/B for collision poisoning in minimizer source retention.

The production research selector uses a 64-bit Gear state, so accidental collisions should be
rare, but a one-source-per-signal table has a structural weakness: one false source can occupy
a signal forever. This experiment deliberately truncates the encoder-side signal key to 8/12/16
bits to make that failure observable at small deterministic scale. Exact 64-byte proof remains
mandatory, so the stress cannot create an incorrect Law.

This is not a claim about natural 64-bit collision frequency. It asks whether bounded multiple-
source retention is a robust repair when collisions or aliases do occur, and charges proof reads,
modeled retained-state payload and repeated hosted elapsed time for that repair.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import json
import os
import random
import statistics
import time

from benchmarks.one.one_g02_gear_replacement_ab import (
    _GEAR,
    _extend_left,
    _extend_right,
    WINDOW,
    _U64_MASK,
)
from benchmarks.one.one_g02_minimizer_gear_ab import MINIMIZER_SPAN

TARGET_BYTES = 256 * 1024
PREFIX_BYTES = 512 * 1024
SEPARATOR_BYTES = 8 * 1024
BUCKET_WIDTH = 4
SIGNAL_BITS = (8, 12, 16)
REPETITIONS = 3


@dataclass(frozen=True)
class CollisionResult:
    reuse_bytes: int
    reuse_regions: int
    verification_reads: int
    extension_reads: int
    emitted: int
    index_keys: int
    source_entries: int
    peak_queue_entries: int

    @property
    def total_proof_reads(self) -> int:
        return self.verification_reads + self.extension_reads

    @property
    def modeled_state_payload_bytes(self) -> int:
        # One u64 key per bucket, one u64 source offset per retained source, plus
        # the rolling queue's (u64 state, u64 position) entries.
        return 8 * self.index_keys + 8 * self.source_entries + 16 * self.peak_queue_entries


def _observe(data: bytes, *, signal_bits: int, bucket_width: int) -> CollisionResult:
    if bucket_width < 1:
        raise ValueError("bucket_width must be positive")
    mask = (1 << signal_bits) - 1
    index: dict[int, deque[int]] = {}
    minima: deque[tuple[int, int]] = deque()
    h = 0
    peak_queue = emitted = 0
    verification_reads = extension_reads = 0
    reuse_bytes = reuse_regions = 0
    covered_until = 0
    last_emitted_position = -1

    for position, value in enumerate(data):
        h = ((h << 1) + _GEAR[value]) & _U64_MASK
        if position + 1 < WINDOW:
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

        full_signal, anchor_position = minima[0]
        if anchor_position == last_emitted_position:
            continue
        last_emitted_position = anchor_position
        emitted += 1
        start = anchor_position + 1 - WINDOW
        if start < covered_until:
            continue

        key = full_signal & mask
        bucket = index.get(key)
        matched = False
        if bucket:
            # Newest-first favors nearby/version-local parents while remaining bounded.
            for source in reversed(bucket):
                verification_reads += 2 * WINDOW
                if data[source : source + WINDOW] != data[start : start + WINDOW]:
                    continue
                left, left_reads = _extend_left(data, source, start, covered_until)
                right, right_reads = _extend_right(data, source, start)
                extension_reads += left_reads + right_reads
                target_start = max(start - left, covered_until)
                target_end = start + right
                if target_end > target_start:
                    reuse_regions += 1
                    reuse_bytes += target_end - target_start
                    covered_until = target_end
                matched = True
                break

        # First-writer width=1 reproduces the current structural policy: a populated key
        # never learns a replacement source. Wider buckets learn a new exact-window class
        # after all retained sources fail proof, evicting the oldest when bounded.
        if not matched:
            if bucket is None:
                bucket = deque()
                index[key] = bucket
            if bucket_width > 1 or not bucket:
                bucket.append(start)
                while len(bucket) > bucket_width:
                    bucket.popleft()

    return CollisionResult(
        reuse_bytes=reuse_bytes,
        reuse_regions=reuse_regions,
        verification_reads=verification_reads,
        extension_reads=extension_reads,
        emitted=emitted,
        index_keys=len(index),
        source_entries=sum(len(bucket) for bucket in index.values()),
        peak_queue_entries=peak_queue,
    )


def _median(data: bytes, *, signal_bits: int, bucket_width: int) -> tuple[int, CollisionResult]:
    samples: list[int] = []
    result: CollisionResult | None = None
    for _ in range(REPETITIONS):
        start = time.perf_counter_ns()
        result = _observe(data, signal_bits=signal_bits, bucket_width=bucket_width)
        samples.append(time.perf_counter_ns() - start)
    assert result is not None
    return int(statistics.median(samples)), result


def _corpus() -> bytes:
    prefix = random.Random(7301).randbytes(PREFIX_BYTES)
    target = random.Random(7302).randbytes(TARGET_BYTES)
    separator = random.Random(7303).randbytes(SEPARATOR_BYTES)
    return prefix + target + separator + target


def run() -> dict[str, object]:
    data = _corpus()
    rows: list[dict[str, object]] = []
    improvements = 0
    for bits in SIGNAL_BITS:
        single_ns, single = _median(data, signal_bits=bits, bucket_width=1)
        multi_ns, multi = _median(data, signal_bits=bits, bucket_width=BUCKET_WIDTH)
        delta = multi.reuse_bytes - single.reuse_bytes
        if delta > 0:
            improvements += 1
        rows.append({
            "signal_bits": bits,
            "input_bytes": len(data),
            "known_repeated_target_bytes": TARGET_BYTES,
            "single_source_reuse_bytes": single.reuse_bytes,
            "multi_source_reuse_bytes": multi.reuse_bytes,
            "multi_minus_single_reuse_bytes": delta,
            "single_source_proof_read_bytes": single.total_proof_reads,
            "multi_source_proof_read_bytes": multi.total_proof_reads,
            "multi_proof_read_ratio_over_single": (
                multi.total_proof_reads / single.total_proof_reads
                if single.total_proof_reads else None
            ),
            "single_source_modeled_state_bytes": single.modeled_state_payload_bytes,
            "multi_source_modeled_state_bytes": multi.modeled_state_payload_bytes,
            "multi_state_ratio_over_single": multi.modeled_state_payload_bytes / single.modeled_state_payload_bytes,
            "single_source_median_ns": single_ns,
            "multi_source_median_ns": multi_ns,
            "multi_elapsed_ratio_over_single": multi_ns / single_ns,
            "single_source_entries": single.source_entries,
            "multi_source_entries": multi.source_entries,
            "emitted_minimizers": single.emitted,
            "peak_minimizer_queue_entries": single.peak_queue_entries,
        })

    return {
        "schema": "cmpct-one-g02-minimizer-collision-ab-v2",
        "experimental_version": "ONE-G0.2",
        "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
        "repetitions": REPETITIONS,
        "signal_bits_under_stress": list(SIGNAL_BITS),
        "natural_selector_signal_bits": 64,
        "bounded_bucket_width": BUCKET_WIDTH,
        "hypothesis": "first-writer source retention is structurally vulnerable to signal poisoning, while a small bounded source bucket can recover exact-reuse opportunity under collision pressure without unbounded state",
        "disproof": "bounded multi-source retention does not recover additional exact reuse under deterministic collision stress, or its proof/state/elapsed carrying cost is disproportionate to recovered opportunity",
        "decision": (
            "bounded_multisource_recovers_collision_stressed_opportunity"
            if improvements else "one_source_survives_current_collision_stress"
        ),
        "claim_boundary": "hostile encoder-side collision amplification only; truncated keys are not evidence that natural 64-bit collisions are frequent, timings are hosted Python carrying-cost evidence only, and every surviving reuse remains exact-byte-proven",
        "rows": rows,
    }


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True, indent=2))
