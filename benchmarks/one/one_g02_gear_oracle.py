"""ONE-G0.2 gear-anchor value/cost oracle.

Historical CMPCT CDC used a cheap gear recurrence for content-defined boundaries. This
instrument does not restore CDC as an archive mechanism. It asks whether the underlying
content-derived signal can nominate the same generic ONE reuse Law more cheaply than the
polynomial rolling-window oracle after insertion shifts, and whether one sparse signal
could subsume the large fixed-chunk index rather than coexist with it.

All accepted reuse is byte-verified and all extra comparison reads are charged.
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
ANCHOR_BITS = 10
ANCHOR_MASK = (1 << ANCHOR_BITS) - 1
MAX_INDEX_ENTRIES = 1 << 13
_U64_MASK = (1 << 64) - 1


def _splitmix64_table() -> tuple[int, ...]:
    x = 0x434D504354434443
    values: list[int] = []
    for _ in range(256):
        x = (x + 0x9E3779B97F4A7C15) & _U64_MASK
        z = x
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & _U64_MASK
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & _U64_MASK
        values.append((z ^ (z >> 31)) & _U64_MASK)
    return tuple(values)


_GEAR = _splitmix64_table()


@dataclass(frozen=True)
class GearResult:
    anchors: int
    lookups: int
    verifications: int
    verification_read_bytes: int
    extension_read_bytes: int
    regions: int
    opportunity_bytes: int
    peak_index_entries: int

    @property
    def extra_read_bytes(self) -> int:
        return self.verification_read_bytes + self.extension_read_bytes


def _gear_oracle(data: bytes) -> GearResult:
    if len(data) < WINDOW:
        return GearResult(0, 0, 0, 0, 0, 0, 0, 0)

    h = 0
    index: dict[int, int] = {}
    anchors = lookups = verifications = 0
    verify_reads = extension_reads = regions = opportunity_bytes = 0
    covered_until = 0

    for position, value in enumerate(data):
        h = ((h << 1) + _GEAR[value]) & _U64_MASK
        if position + 1 < WINDOW or h & ANCHOR_MASK:
            continue
        start = position + 1 - WINDOW
        anchors += 1
        source = index.get(h)
        if source is None:
            if len(index) < MAX_INDEX_ENTRIES:
                index[h] = start
            continue
        lookups += 1
        if start < covered_until:
            continue

        verifications += 1
        verify_reads += 2 * WINDOW
        if data[source : source + WINDOW] != data[start : start + WINDOW]:
            continue

        left = 0
        while source - left > 0 and start - left > 0:
            extension_reads += 2
            if data[source - left - 1] != data[start - left - 1]:
                break
            left += 1

        right = WINDOW
        while source + right < start and start + right < len(data):
            extension_reads += 2
            if data[source + right] != data[start + right]:
                break
            right += 1

        target_start = max(start - left, covered_until)
        target_end = start + right
        if target_end <= covered_until:
            continue
        regions += 1
        opportunity_bytes += target_end - target_start
        covered_until = target_end

    return GearResult(
        anchors,
        lookups,
        verifications,
        verify_reads,
        extension_reads,
        regions,
        opportunity_bytes,
        len(index),
    )


def _cases() -> dict[str, bytes]:
    shifted_basis = random.Random(13).randbytes(512 * 1024)
    basis16 = random.Random(22).randbytes(16 * 1024)
    basis64 = random.Random(12).randbytes(64 * 1024)
    basis256 = random.Random(24).randbytes(256 * 1024)
    pair512 = random.Random(25).randbytes(512 * 1024)
    return {
        "shifted_version_pair_1byte_insert": shifted_basis + b"X" + shifted_basis,
        "random_1mib": random.Random(11).randbytes(1024 * 1024),
        "zlib_random_payload": zlib.compress(random.Random(14).randbytes(1024 * 1024), level=9),
        "repeat_basis_16k": basis16 * 64,
        "repeat_basis_64k": basis64 * 16,
        "repeat_basis_256k": basis256 * 4,
        "exact_pair_512k": pair512 + pair512,
    }


def _median(fn) -> tuple[int, GearResult]:
    samples: list[int] = []
    result: GearResult | None = None
    for _ in range(REPETITIONS):
        t0 = time.perf_counter_ns()
        result = fn()
        samples.append(time.perf_counter_ns() - t0)
    assert result is not None
    return int(statistics.median(samples)), result


def run() -> dict[str, object]:
    rows: list[dict[str, object]] = []
    for name, data in _cases().items():
        fixed = observe(data, min_run=8, chunk_size=64, max_index_entries=1 << 14)
        elapsed, result = _median(lambda: _gear_oracle(data))
        fixed_payload = fixed.stats.retained_index_payload_bytes
        gear_payload = result.peak_index_entries * 16  # one u64 signal key + one u64 source offset
        rows.append({
            "case": name,
            "input_bytes": len(data),
            "fixed_reuse_opportunity_bytes": fixed.stats.reuse_opportunity_bytes,
            "fixed_retained_index_payload_bytes": fixed_payload,
            "gear_opportunity_bytes": result.opportunity_bytes,
            "gear_minus_fixed_opportunity_bytes": result.opportunity_bytes - fixed.stats.reuse_opportunity_bytes,
            "gear_opportunity_fraction": result.opportunity_bytes / len(data),
            "gear_regions": result.regions,
            "gear_anchors": result.anchors,
            "gear_anchor_density": result.anchors / max(1, len(data) - WINDOW + 1),
            "gear_lookups": result.lookups,
            "gear_verifications": result.verifications,
            "gear_verification_read_bytes": result.verification_read_bytes,
            "gear_extension_read_bytes": result.extension_read_bytes,
            "gear_extra_read_bytes": result.extra_read_bytes,
            "gear_extra_read_amplification": result.extra_read_bytes / len(data),
            "gear_peak_index_entries": result.peak_index_entries,
            "gear_retained_index_payload_bytes": gear_payload,
            "gear_payload_fraction_of_fixed": (gear_payload / fixed_payload if fixed_payload else None),
            "gear_median_ns": elapsed,
            "gear_reference_mib_s": (len(data) / (1024 * 1024)) / (elapsed / 1_000_000_000),
        })
    return {
        "schema": "cmpct-one-g02-gear-oracle-v2",
        "experimental_version": "ONE-G0.2",
        "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
        "window": WINDOW,
        "anchor_bits": ANCHOR_BITS,
        "max_index_entries": MAX_INDEX_ENTRIES,
        "repetitions": REPETITIONS,
        "claim_boundary": "historical CDC signal translated into ONE reuse discovery; oracle only, no reader-visible CDC semantics or product-speed claim",
        "rows": rows,
    }


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True, indent=2))
