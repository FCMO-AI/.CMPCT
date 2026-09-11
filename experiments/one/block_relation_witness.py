"""ONE-G0.2 block observation record for actionable relation witnesses.

Writer-only discovery state. It reuses the 64-byte observation cadence and retains
bounded transform-invariant signatures. A witness is only a nomination; exact
verification remains mandatory before any Law enters a Program.
"""
from __future__ import annotations

from dataclasses import dataclass

BLOCK = 64
PROBES = (5, 27, 53)
MAX_SIGNATURES = 8192
BUCKET_RECORDS = 4
WITNESS_BLOCK_BUDGET = 128

Samples = tuple[int, int, int]


@dataclass(frozen=True)
class RelationWitness:
    op: str
    value: int
    parent_offset: int
    child_offset: int


@dataclass(frozen=True)
class WitnessObservation:
    witnesses: tuple[RelationWitness, ...]
    source_scan_bytes: int
    probe_bytes: int
    retained_records: int
    modeled_state_bytes: int


def _samples(block: bytes) -> Samples:
    return tuple(block[p] for p in PROBES)  # type: ignore[return-value]


def _add_signature(samples: Samples) -> tuple[int, int]:
    a, b, c = samples
    return ((b - a) & 0xFF, (c - a) & 0xFF)


def _xor_signature(samples: Samples) -> tuple[int, int]:
    a, b, c = samples
    return (b ^ a, c ^ a)


def _value(parent: Samples, child: Samples, op: str) -> int | None:
    if op == "add8":
        values = tuple((c - p) & 0xFF for p, c in zip(parent, child))
    elif op == "xor":
        values = tuple(c ^ p for p, c in zip(parent, child))
    else:
        raise ValueError(op)
    return values[0] if values[0] != 0 and values.count(values[0]) == len(values) else None


def _consider_bucket(
    witnesses: list[RelationWitness],
    bucket: list[tuple[int, Samples]],
    samples: Samples,
    *,
    op: str,
    child_offset: int,
) -> None:
    for parent_offset, parent_samples in bucket:
        value = _value(parent_samples, samples, op)
        if value is not None:
            witnesses.append(RelationWitness(op, value, parent_offset, child_offset))


def _remember(
    table: dict[tuple[int, int], list[tuple[int, Samples]]],
    signature: tuple[int, int],
    offset: int,
    samples: Samples,
) -> None:
    bucket = table.get(signature)
    if bucket is None:
        if len(table) >= MAX_SIGNATURES:
            return
        table[signature] = [(offset, samples)]
        return
    if len(bucket) < BUCKET_RECORDS:
        bucket.append((offset, samples))


def observe_relation_witnesses(data: bytes) -> WitnessObservation:
    """Return bounded directly-actionable relation nominations from one forward pass.

    All aligned blocks contribute transform-invariant signatures. Candidate witness
    material is retained only at a deterministic set of at most ~128 block positions
    spread over the stream; this is retention sampling, not observation sampling, so it
    cannot authorize a false Law and does not add source rereads. Up to four records per
    signature preserve bounded collision alternatives.
    """
    add_records: dict[tuple[int, int], list[tuple[int, Samples]]] = {}
    xor_records: dict[tuple[int, int], list[tuple[int, Samples]]] = {}
    witnesses: list[RelationWitness] = []
    full = len(data) - (len(data) % BLOCK)
    blocks = full // BLOCK
    witness_stride = max(1, (blocks + WITNESS_BLOCK_BUDGET - 1) // WITNESS_BLOCK_BUDGET)

    for block_index, off in enumerate(range(0, full, BLOCK)):
        block_samples = _samples(data[off : off + BLOCK])
        add_sig = _add_signature(block_samples)
        xor_sig = _xor_signature(block_samples)

        # Retain geometry at evenly spread stream positions. Every block is still
        # observed and indexed; only candidate handoff records are thinned.
        if block_index % witness_stride == 0:
            add_bucket = add_records.get(add_sig)
            if add_bucket is not None:
                _consider_bucket(witnesses, add_bucket, block_samples, op="add8", child_offset=off)
            xor_bucket = xor_records.get(xor_sig)
            if xor_bucket is not None:
                _consider_bucket(witnesses, xor_bucket, block_samples, op="xor", child_offset=off)

        _remember(add_records, add_sig, off, block_samples)
        _remember(xor_records, xor_sig, off, block_samples)

    signature_count = len(add_records) + len(xor_records)
    records = sum(map(len, add_records.values())) + sum(map(len, xor_records.values()))
    # Compact target accounting: signature/control ~=4 B per bucket, each retained
    # offset+3 samples rounded to 8 B, witness op/value+two offsets rounded to 12 B.
    return WitnessObservation(
        witnesses=tuple(witnesses),
        source_scan_bytes=len(data),
        probe_bytes=blocks * len(PROBES),
        retained_records=records,
        modeled_state_bytes=signature_count * 4 + records * 8 + len(witnesses) * 12,
    )
