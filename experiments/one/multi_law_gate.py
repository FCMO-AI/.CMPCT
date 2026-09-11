"""ONE-G0.2 fused multi-Law opportunity gate.

Writer-side discovery only. The gate consumes each source byte once and emits cheap,
content-derived nominations for deeper exact search. It never emits Law, changes wire
bytes, or weakens the requirement that downstream candidates prove exact reconstruction.

Signals deliberately share one forward pass:
- run morphology;
- aligned 64-bit FNV fingerprints for exact-reuse nomination;
- dominant modulo-256 first difference for add8-style arithmetic structure;
- dominant xor relation at one bounded lag for xor/resemblance structure.

The gate is intentionally conservative: a nomination authorizes deeper proof; absence
means the expensive family is skipped for this object. False negatives are therefore
more dangerous than false positives and are measured against independent synthetic
oracles in the frozen benchmark.
"""
from __future__ import annotations

from dataclasses import dataclass

_FNV64_OFFSET = 0xCBF29CE484222325
_FNV64_PRIME = 0x100000001B3
_U64_MASK = (1 << 64) - 1


@dataclass(frozen=True)
class LawGateDecision:
    run: bool
    reuse: bool
    add8: bool
    xor: bool
    run_support_bytes: int
    reuse_support_bytes: int
    add8_support_bytes: int
    xor_support_bytes: int


@dataclass(frozen=True)
class LawGateStats:
    input_bytes: int
    source_scan_bytes: int
    chunk_fingerprints: int
    retained_fingerprint_entries: int
    arithmetic_pairs: int
    xor_pairs: int
    retained_feature_payload_bytes: int


@dataclass(frozen=True)
class LawGateObservation:
    decision: LawGateDecision
    stats: LawGateStats


def observe_multi_law_gate(
    data: bytes,
    *,
    min_run: int = 8,
    chunk_size: int = 64,
    xor_lag: int = 64,
    min_arithmetic_pairs: int = 256,
    min_relation_pairs: int = 256,
    support_fraction: float = 0.875,
    max_fingerprint_entries: int = 256,
) -> LawGateObservation:
    """Collect bounded nominations for four generic ONE Law families in one pass.

    `support_fraction` applies only to arithmetic/xor relation evidence. Reuse is
    nominated after a repeated aligned 64-bit fingerprint and remains subject to exact
    downstream byte proof. The fingerprint table retains only the first occurrence per
    digest because the gate needs existence evidence, not a complete match list.
    """
    if type(data) is not bytes:
        raise TypeError("ONE multi-Law gate input must be bytes")
    for name, value in {
        "min_run": min_run,
        "chunk_size": chunk_size,
        "xor_lag": xor_lag,
        "min_arithmetic_pairs": min_arithmetic_pairs,
        "min_relation_pairs": min_relation_pairs,
        "max_fingerprint_entries": max_fingerprint_entries,
    }.items():
        if type(value) is not int or value <= 0:
            raise ValueError(f"{name} must be a positive integer")
    if not 0.5 <= support_fraction <= 1.0:
        raise ValueError("support_fraction must be in [0.5, 1.0]")

    if not data:
        return LawGateObservation(
            LawGateDecision(False, False, False, False, 0, 0, 0, 0),
            LawGateStats(0, 0, 0, 0, 0, 0, 0),
        )

    fingerprints: dict[int, int] = {}
    repeated_chunks = 0
    chunk_hash = _FNV64_OFFSET
    chunk_start = 0

    run_value = data[0]
    run_length = 0
    run_support = 0

    delta_counts = [0] * 256
    xor_counts = [0] * 256
    arithmetic_pairs = 0
    xor_pairs = 0
    previous = 0

    # Bounded lag ring. This is discovery state only and never reader-visible.
    lag_ring = bytearray(xor_lag)

    for position, value in enumerate(data):
        if run_length == 0:
            run_value = value
            run_length = 1
        elif value == run_value:
            run_length += 1
        else:
            if run_length >= min_run:
                run_support += run_length
            run_value = value
            run_length = 1

        if position:
            delta = (value - previous) & 0xFF
            delta_counts[delta] += 1
            arithmetic_pairs += 1
        previous = value

        if position >= xor_lag:
            relation = value ^ lag_ring[position % xor_lag]
            xor_counts[relation] += 1
            xor_pairs += 1
        lag_ring[position % xor_lag] = value

        chunk_hash ^= value
        chunk_hash = (chunk_hash * _FNV64_PRIME) & _U64_MASK
        if (position + 1) % chunk_size == 0:
            fingerprint = chunk_hash
            source = fingerprints.get(fingerprint)
            if source is not None:
                repeated_chunks += 1
            elif len(fingerprints) < max_fingerprint_entries:
                fingerprints[fingerprint] = chunk_start
            chunk_hash = _FNV64_OFFSET
            chunk_start = position + 1

    if run_length >= min_run:
        run_support += run_length

    reuse_support = repeated_chunks * chunk_size

    add8_support = max(delta_counts) if arithmetic_pairs else 0
    # delta==0 is already cheaply represented by Fill/Repeat; do not launch arithmetic
    # proof solely for a constant run.
    dominant_delta = delta_counts.index(add8_support) if add8_support else 0
    add8 = (
        arithmetic_pairs >= min_arithmetic_pairs
        and dominant_delta != 0
        and add8_support / arithmetic_pairs >= support_fraction
    )

    xor_support = max(xor_counts) if xor_pairs else 0
    dominant_xor = xor_counts.index(xor_support) if xor_support else 0
    # xor==0 at the bounded lag is ordinary repeat/reuse evidence.
    xor = (
        xor_pairs >= min_relation_pairs
        and dominant_xor != 0
        and xor_support / xor_pairs >= support_fraction
    )

    decision = LawGateDecision(
        run=run_support >= min_run,
        reuse=repeated_chunks > 0,
        add8=add8,
        xor=xor,
        run_support_bytes=run_support,
        reuse_support_bytes=reuse_support,
        add8_support_bytes=add8_support + 1 if add8 else 0,
        xor_support_bytes=xor_support if xor else 0,
    )
    # Lower-bound payload accounting: retained u64 fingerprint+offset pairs, two
    # 256-entry u64 histograms, and the bounded xor lag ring.
    retained = 16 * len(fingerprints) + 8 * 256 * 2 + xor_lag
    return LawGateObservation(
        decision=decision,
        stats=LawGateStats(
            input_bytes=len(data),
            source_scan_bytes=len(data),
            chunk_fingerprints=len(data) // chunk_size,
            retained_fingerprint_entries=len(fingerprints),
            arithmetic_pairs=arithmetic_pairs,
            xor_pairs=xor_pairs,
            retained_feature_payload_bytes=retained,
        ),
    )
