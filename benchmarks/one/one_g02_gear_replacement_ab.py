"""ONE-G0.2 direct A/B: fixed-chunk reuse signal versus sparse Gear replacement.

This experiment asks a narrow architectural question: can the exact historical CMPCT Gear
content signal replace, rather than accompany, the current fixed-chunk FNV reuse index in
the ONE fused observer? Both arms retain the same run observation and exact-proof rule.
The Gear arm is still discovery-only and emits generic exact-reuse opportunities, never a
reader-visible CDC mechanism.

The falsifier is deliberate: a sparse signal is not a win if lower index traffic comes from
silently missing useful short or aligned relationships. Every row therefore reports exact
reuse opportunity mass, verification traffic, retained index payload and elapsed reference
work. Python timing is causal research evidence only, not a product-speed claim.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import blake2b
import json
import os
import random
import statistics
import time
import zlib

from experiments.one.observe import Observation, observe

REPETITIONS = 7
MIN_RUN = 8
WINDOW = 64
PROOF_BLOCK = 4096
FIXED_MAX_INDEX_ENTRIES = 1 << 14
GEAR_MAX_INDEX_ENTRIES = 1 << 13
ANCHOR_BITS = 10
ANCHOR_MASK = (1 << ANCHOR_BITS) - 1
_U64_MASK = (1 << 64) - 1


def _u64(data: bytes, *, person: bytes) -> int:
    return int.from_bytes(blake2b(data, digest_size=8, person=person[:16]).digest(), "little")


# Exact historical CMPCT resemblance signal. Only encoder discovery knowledge is reused.
_GEAR = tuple(_u64(bytes([i]), person=b"cmpct-gear-v1") for i in range(256))


@dataclass(frozen=True)
class _GearObservation:
    run_opportunity_bytes: int
    reuse_opportunity_bytes: int
    reuse_regions: int
    anchors: int
    lookups: int
    verifications: int
    verification_read_bytes: int
    extension_read_bytes: int
    total_source_read_bytes: int
    peak_index_entries: int
    retained_index_payload_bytes: int


def _extend_right(data: bytes, source: int, target: int) -> tuple[int, int]:
    """Return exact non-overlapping prefix length and charged proof reads.

    The 64-byte nomination window is already proven before entry. Larger proof blocks let
    Python delegate equality to its bulk byte comparator rather than spending one Python
    branch per byte. On the first unequal block we refine only that block. The second read
    during refinement is charged too; elapsed-time improvement therefore cannot hide I/O.
    """
    max_length = min(target - source, len(data) - target)
    matched = WINDOW
    reads = 0
    while matched < max_length:
        step = min(PROOF_BLOCK, max_length - matched)
        reads += 2 * step
        if data[source + matched : source + matched + step] == data[
            target + matched : target + matched + step
        ]:
            matched += step
            continue
        for offset in range(step):
            reads += 2
            if data[source + matched + offset] != data[target + matched + offset]:
                return matched + offset, reads
        matched += step
    return matched, reads


def _extend_left(data: bytes, source: int, target: int, covered_until: int) -> tuple[int, int]:
    """Return exact backwards extension without crossing prior target coverage."""
    max_length = min(source, target - covered_until)
    matched = 0
    reads = 0
    while matched < max_length:
        step = min(PROOF_BLOCK, max_length - matched)
        source_start = source - matched - step
        target_start = target - matched - step
        reads += 2 * step
        if data[source_start : source - matched] == data[target_start : target - matched]:
            matched += step
            continue
        for offset in range(1, step + 1):
            reads += 2
            if data[source - matched - offset] != data[target - matched - offset]:
                return matched + offset - 1, reads
        matched += step
    return matched, reads


def _gear_observe(data: bytes) -> _GearObservation:
    """One forward pass for runs + sparse Gear reuse, with exact bulk extension proof."""
    if not data:
        return _GearObservation(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

    index: dict[int, int] = {}
    h = 0
    anchors = lookups = verifications = 0
    verification_read_bytes = extension_read_bytes = 0
    reuse_regions = reuse_opportunity_bytes = 0
    covered_until = 0

    run_value = data[0]
    run_length = 0
    run_opportunity_bytes = 0

    for position, value in enumerate(data):
        if run_length == 0:
            run_value = value
            run_length = 1
        elif value == run_value:
            run_length += 1
        else:
            if run_length >= MIN_RUN:
                run_opportunity_bytes += run_length
            run_value = value
            run_length = 1

        h = ((h << 1) + _GEAR[value]) & _U64_MASK
        if position + 1 < WINDOW or h & ANCHOR_MASK:
            continue

        anchors += 1
        start = position + 1 - WINDOW

        # Match the current observer's content-derived run-dominance gate: a window
        # already wholly explained by a qualifying run does not need a reuse audition.
        if run_length >= max(MIN_RUN, WINDOW):
            continue

        source = index.get(h)
        if source is None:
            if len(index) < GEAR_MAX_INDEX_ENTRIES:
                index[h] = start
            continue
        lookups += 1
        if start < covered_until:
            continue

        verifications += 1
        verification_read_bytes += 2 * WINDOW
        if data[source : source + WINDOW] != data[start : start + WINDOW]:
            # A 64-bit collision never becomes a Law.
            continue

        # Expand one exact nomination into a contiguous generic reuse relation. Bulk
        # proof makes the implementation reflect the intended SIMD/memcmp-friendly
        # mechanism while every examined byte remains charged as discovery traffic.
        left, left_reads = _extend_left(data, source, start, covered_until)
        right, right_reads = _extend_right(data, source, start)
        extension_read_bytes += left_reads + right_reads

        target_start = max(start - left, covered_until)
        target_end = start + right
        if target_end <= target_start:
            continue
        reuse_regions += 1
        reuse_opportunity_bytes += target_end - target_start
        covered_until = target_end

    if run_length >= MIN_RUN:
        run_opportunity_bytes += run_length

    retained_index_payload_bytes = 16 * len(index)  # one u64 key + one u64 source offset
    total_source_read_bytes = len(data) + verification_read_bytes + extension_read_bytes
    return _GearObservation(
        run_opportunity_bytes=run_opportunity_bytes,
        reuse_opportunity_bytes=reuse_opportunity_bytes,
        reuse_regions=reuse_regions,
        anchors=anchors,
        lookups=lookups,
        verifications=verifications,
        verification_read_bytes=verification_read_bytes,
        extension_read_bytes=extension_read_bytes,
        total_source_read_bytes=total_source_read_bytes,
        peak_index_entries=len(index),
        retained_index_payload_bytes=retained_index_payload_bytes,
    )


def _cases() -> dict[str, bytes]:
    shifted = random.Random(13).randbytes(512 * 1024)
    basis64 = random.Random(18).randbytes(64)
    basis128 = random.Random(19).randbytes(128)
    basis256 = random.Random(23).randbytes(256)
    basis512 = random.Random(20).randbytes(512)
    basis4k = random.Random(21).randbytes(4 * 1024)
    basis16k = random.Random(22).randbytes(16 * 1024)
    basis64k = random.Random(12).randbytes(64 * 1024)
    exact_pair = random.Random(25).randbytes(512 * 1024)
    return {
        "random_1mib": random.Random(11).randbytes(1024 * 1024),
        "zlib_random_payload": zlib.compress(random.Random(14).randbytes(1024 * 1024), level=9),
        "zeros_1mib": b"\0" * (1024 * 1024),
        # These deliberately attack sparse-anchor phase blindness. A global 1/1024
        # mask can see zero anchors forever when a short cycle contains none of the
        # qualifying Gear states, despite a large exact-reuse opportunity.
        "repeat_basis_64b_4k": basis64 * 64,
        "repeat_basis_128b_4k": basis128 * 32,
        "repeat_basis_256b_4k": basis256 * 16,
        "repeat_basis_512b_4k": basis512 * 8,
        "repeat_basis_4k_64k": basis4k * 16,
        "repeat_basis_16k_1mib": basis16k * 64,
        "repeat_basis_64k_1mib": basis64k * 16,
        "exact_pair_512k": exact_pair + exact_pair,
        "shifted_version_pair_1byte_insert": shifted + b"X" + shifted,
    }


def _median(fn):
    samples: list[int] = []
    result = None
    for _ in range(REPETITIONS):
        t0 = time.perf_counter_ns()
        result = fn()
        samples.append(time.perf_counter_ns() - t0)
    assert result is not None
    return int(statistics.median(samples)), result


def run() -> dict[str, object]:
    rows: list[dict[str, object]] = []
    blind_spots: list[str] = []
    for name, data in _cases().items():
        fixed_ns, fixed_obj = _median(
            lambda: observe(
                data,
                min_run=MIN_RUN,
                chunk_size=WINDOW,
                max_index_entries=FIXED_MAX_INDEX_ENTRIES,
            )
        )
        gear_ns, gear = _median(lambda: _gear_observe(data))
        assert isinstance(fixed_obj, Observation)
        assert isinstance(gear, _GearObservation)
        fixed = fixed_obj.stats

        # Both arms share the run detector. A mismatch would make the reuse comparison
        # uninterpretable and must fail rather than be narrated away.
        assert gear.run_opportunity_bytes == fixed.run_opportunity_bytes
        if fixed.reuse_opportunity_bytes and gear.reuse_opportunity_bytes < fixed.reuse_opportunity_bytes:
            blind_spots.append(name)

        rows.append({
            "case": name,
            "input_bytes": len(data),
            "fixed_median_ns": fixed_ns,
            "gear_median_ns": gear_ns,
            "gear_elapsed_ratio_over_fixed": gear_ns / fixed_ns,
            "fixed_reuse_opportunity_bytes": fixed.reuse_opportunity_bytes,
            "gear_reuse_opportunity_bytes": gear.reuse_opportunity_bytes,
            "gear_minus_fixed_reuse_opportunity_bytes": gear.reuse_opportunity_bytes - fixed.reuse_opportunity_bytes,
            "gear_reuse_opportunity_fraction_of_fixed": (
                gear.reuse_opportunity_bytes / fixed.reuse_opportunity_bytes
                if fixed.reuse_opportunity_bytes
                else None
            ),
            "fixed_reuse_regions": fixed.reuse_candidates,
            "gear_reuse_regions": gear.reuse_regions,
            "fixed_verification_read_bytes": fixed.verification_read_bytes,
            "gear_verification_read_bytes": gear.verification_read_bytes,
            "gear_extension_read_bytes": gear.extension_read_bytes,
            "fixed_total_source_read_bytes": fixed.total_source_read_bytes,
            "gear_total_source_read_bytes": gear.total_source_read_bytes,
            "gear_total_source_read_ratio_over_fixed": gear.total_source_read_bytes / fixed.total_source_read_bytes,
            "fixed_peak_index_entries": fixed.peak_index_entries,
            "gear_peak_index_entries": gear.peak_index_entries,
            "fixed_retained_index_payload_bytes": fixed.retained_index_payload_bytes,
            "gear_retained_index_payload_bytes": gear.retained_index_payload_bytes,
            "gear_index_payload_fraction_of_fixed": (
                gear.retained_index_payload_bytes / fixed.retained_index_payload_bytes
                if fixed.retained_index_payload_bytes
                else None
            ),
            "gear_anchors": gear.anchors,
            "gear_lookups": gear.lookups,
            "gear_verifications": gear.verifications,
        })

    return {
        "schema": "cmpct-one-g02-gear-replacement-ab-v3",
        "experimental_version": "ONE-G0.2",
        "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
        "repetitions": REPETITIONS,
        "window": WINDOW,
        "proof_block": PROOF_BLOCK,
        "anchor_bits": ANCHOR_BITS,
        "signal_identity": "historical cmpct-gear-v1 BLAKE2 table derivation",
        "hypothesis": "one sparse Gear signal can replace the fixed reuse index while preserving useful exact-reuse opportunity mass and reducing retained discovery state",
        "disproof": "material opportunity loss on short/aligned relationships, hidden proof rereads, or materially worse negative-path work rejects replacement at this sparsity",
        "decision": (
            "reject_sparse_gear_as_complete_replacement"
            if blind_spots
            else "sparse_gear_replacement_survives_current_falsifiers"
        ),
        "blind_spot_cases": blind_spots,
        "causal_interpretation": (
            "a periodic source whose repeating Gear-state cycle contains no masked anchor remains invisible to a global sparse-only index"
            if blind_spots
            else "no sparse-anchor phase blind spot observed in the current corpus"
        ),
        "claim_boundary": "ONE discovery A/B only; exact reuse is byte-proven; no reader-visible CDC semantics and no product-speed claim",
        "rows": rows,
    }


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True, indent=2))
