"""ONE-G0.2 sparse rolling-anchor headroom oracle.

This is deliberately *not* part of the fused observer yet. It asks one narrow question:
can a cheap content-defined rolling signal recover reuse hidden by fixed alignment after
small insertions, while remaining sparse on random/already-compressed input?

The oracle charges its full extra scan, rolling updates, exact anchor verification and
bytewise match-extension reads. A positive result is feature-value evidence only; it is
not permission to hide a second production scan or claim product speed.
"""
from __future__ import annotations

import json
import os
import random
import statistics
import time
import zlib
from dataclasses import dataclass

from experiments.one.observe import observe

REPETITIONS = 5
WINDOW = 64
ANCHOR_BITS = 10  # expected ~1 anchor / 1024 rolling positions
ANCHOR_MASK = (1 << ANCHOR_BITS) - 1
MAX_INDEX_ENTRIES = 1 << 13
_U64_MASK = (1 << 64) - 1
_BASE = 0x100000001B3
_OLD_FACTOR = pow(_BASE, WINDOW - 1, 1 << 64)


@dataclass(frozen=True)
class RollingResult:
    anchor_positions: int
    hash_lookups: int
    exact_anchor_verifications: int
    exact_verification_read_bytes: int
    extension_compare_read_bytes: int
    opportunity_regions: int
    opportunity_bytes: int
    peak_index_entries: int

    @property
    def total_extra_read_bytes(self) -> int:
        return self.exact_verification_read_bytes + self.extension_compare_read_bytes


def _rolling_oracle(data: bytes) -> RollingResult:
    if len(data) < WINDOW:
        return RollingResult(0, 0, 0, 0, 0, 0, 0, 0)

    rolling = 0
    for value in data[:WINDOW]:
        rolling = (rolling * _BASE + value + 1) & _U64_MASK

    index: dict[int, int] = {}
    anchors = 0
    lookups = 0
    verifications = 0
    verification_reads = 0
    extension_reads = 0
    regions = 0
    opportunity_bytes = 0
    covered_until = 0

    for start in range(0, len(data) - WINDOW + 1):
        if start:
            old = data[start - 1] + 1
            new = data[start + WINDOW - 1] + 1
            rolling = ((rolling - old * _OLD_FACTOR) * _BASE + new) & _U64_MASK

        if rolling & ANCHOR_MASK:
            continue
        anchors += 1
        source = index.get(rolling)
        if source is None:
            if len(index) < MAX_INDEX_ENTRIES:
                index[rolling] = start
            continue

        lookups += 1
        if start < covered_until:
            continue

        verifications += 1
        verification_reads += 2 * WINDOW
        if data[source : source + WINDOW] != data[start : start + WINDOW]:
            # A rolling collision can only waste discovery work; it cannot authorize a Law.
            continue

        # Extend a proven anchor in both directions. Source bytes must remain strictly
        # before target bytes so this oracle models DAG-friendly source-range reuse.
        left = 0
        while source - left > 0 and start - left > 0:
            extension_reads += 2
            if data[source - left - 1] != data[start - left - 1]:
                break
            left += 1

        right = WINDOW
        source_limit = start
        while source + right < source_limit and start + right < len(data):
            extension_reads += 2
            if data[source + right] != data[start + right]:
                break
            right += 1

        target_start = start - left
        target_end = start + right
        if target_end <= covered_until:
            continue
        if target_start < covered_until:
            target_start = covered_until
        regions += 1
        opportunity_bytes += target_end - target_start
        covered_until = target_end

    return RollingResult(
        anchor_positions=anchors,
        hash_lookups=lookups,
        exact_anchor_verifications=verifications,
        exact_verification_read_bytes=verification_reads,
        extension_compare_read_bytes=extension_reads,
        opportunity_regions=regions,
        opportunity_bytes=opportunity_bytes,
        peak_index_entries=len(index),
    )


def _cases() -> dict[str, bytes]:
    basis = random.Random(13).randbytes(512 * 1024)
    repeat_basis = random.Random(12).randbytes(64 * 1024)
    return {
        "shifted_version_pair_1byte_insert": basis + b"X" + basis,
        "random_1mib": random.Random(11).randbytes(1024 * 1024),
        "zlib_random_payload": zlib.compress(random.Random(14).randbytes(1024 * 1024), level=9),
        "repeated_64k_1mib": repeat_basis * 16,
    }


def _median_ns(fn) -> tuple[int, RollingResult]:
    samples: list[int] = []
    last: RollingResult | None = None
    for _ in range(REPETITIONS):
        start = time.perf_counter_ns()
        last = fn()
        samples.append(time.perf_counter_ns() - start)
    assert last is not None
    return int(statistics.median(samples)), last


def run() -> dict[str, object]:
    rows: list[dict[str, object]] = []
    for name, data in _cases().items():
        fixed = observe(data, min_run=8, chunk_size=64, max_index_entries=1 << 14)
        rolling_ns, rolling = _median_ns(lambda: _rolling_oracle(data))
        rows.append(
            {
                "case": name,
                "input_bytes": len(data),
                "fixed_reuse_opportunity_bytes": fixed.stats.reuse_opportunity_bytes,
                "rolling_opportunity_bytes": rolling.opportunity_bytes,
                "rolling_opportunity_fraction": rolling.opportunity_bytes / len(data),
                "rolling_regions": rolling.opportunity_regions,
                "rolling_anchor_positions": rolling.anchor_positions,
                "rolling_anchor_density": rolling.anchor_positions / max(1, len(data) - WINDOW + 1),
                "rolling_hash_lookups": rolling.hash_lookups,
                "rolling_exact_anchor_verifications": rolling.exact_anchor_verifications,
                "rolling_exact_verification_read_bytes": rolling.exact_verification_read_bytes,
                "rolling_extension_compare_read_bytes": rolling.extension_compare_read_bytes,
                "rolling_extra_read_bytes": rolling.total_extra_read_bytes,
                "rolling_read_amplification_excluding_base_scan": rolling.total_extra_read_bytes / len(data),
                "rolling_peak_index_entries": rolling.peak_index_entries,
                "rolling_median_ns": rolling_ns,
                "rolling_reference_mib_s": (len(data) / (1024 * 1024)) / (rolling_ns / 1_000_000_000),
            }
        )
    return {
        "schema": "cmpct-one-g02-rolling-oracle-v1",
        "experimental_version": "ONE-G0.2",
        "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
        "window": WINDOW,
        "anchor_bits": ANCHOR_BITS,
        "max_index_entries": MAX_INDEX_ENTRIES,
        "repetitions": REPETITIONS,
        "claim_boundary": "headroom/value-of-signal oracle; extra scan and all exact/extension rereads are explicit; not product-speed evidence",
        "rows": rows,
    }


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True, indent=2))
