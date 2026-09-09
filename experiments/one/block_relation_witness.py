"""ONE-G0.2 block observation record for actionable relation witnesses.

This is writer-only discovery state.  It reuses the 64-byte observation cadence and
retains bounded transform-invariant signatures.  A witness is only a nomination;
exact verification remains mandatory before any Law enters a Program.
"""
from __future__ import annotations

from dataclasses import dataclass

BLOCK = 64
PROBES = (5, 27, 53)
MAX_RECORDS = 8192
MAX_WITNESSES = 64


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


def _add_signature(block: bytes) -> tuple[int, int]:
    a, b, c = (block[p] for p in PROBES)
    return ((b - a) & 0xFF, (c - a) & 0xFF)


def _xor_signature(block: bytes) -> tuple[int, int]:
    a, b, c = (block[p] for p in PROBES)
    return (b ^ a, c ^ a)


def _value(parent: bytes, child: bytes, op: str) -> int | None:
    if op == "add8":
        values = tuple((child[p] - parent[p]) & 0xFF for p in PROBES)
    elif op == "xor":
        values = tuple(child[p] ^ parent[p] for p in PROBES)
    else:
        raise ValueError(op)
    return values[0] if values[0] != 0 and values.count(values[0]) == len(values) else None


def observe_relation_witnesses(data: bytes) -> WitnessObservation:
    """Make one forward pass and return bounded, directly actionable nominations.

    Transform-invariant signatures allow a later block to nominate an earlier block
    without rescanning source bytes.  The first record for each signature is retained
    until the bounded table is full.  Signature collisions are harmless because the
    downstream exact verifier is authoritative.
    """
    add_records: dict[tuple[int, int], tuple[int, bytes]] = {}
    xor_records: dict[tuple[int, int], tuple[int, bytes]] = {}
    witnesses: list[RelationWitness] = []
    full = len(data) - (len(data) % BLOCK)
    for off in range(0, full, BLOCK):
        block = data[off : off + BLOCK]
        add_sig = _add_signature(block)
        xor_sig = _xor_signature(block)
        if len(witnesses) < MAX_WITNESSES:
            prior = add_records.get(add_sig)
            if prior is not None:
                value = _value(prior[1], block, "add8")
                if value is not None:
                    witnesses.append(RelationWitness("add8", value, prior[0], off))
        if len(witnesses) < MAX_WITNESSES:
            prior = xor_records.get(xor_sig)
            if prior is not None:
                value = _value(prior[1], block, "xor")
                if value is not None:
                    witnesses.append(RelationWitness("xor", value, prior[0], off))
        if add_sig not in add_records and len(add_records) < MAX_RECORDS:
            add_records[add_sig] = (off, block)
        if xor_sig not in xor_records and len(xor_records) < MAX_RECORDS:
            xor_records[xor_sig] = (off, block)
    # Model only retained discovery state, not CPython object overhead.  A native form
    # needs 2-byte signature + 4-byte offset + 3 sampled bytes + table overhead; 16 B
    # per retained record is deliberately conservative at this stage.
    records = len(add_records) + len(xor_records)
    return WitnessObservation(
        witnesses=tuple(witnesses),
        source_scan_bytes=len(data),
        probe_bytes=(full // BLOCK) * len(PROBES),
        retained_records=records,
        modeled_state_bytes=records * 16 + len(witnesses) * 16,
    )
