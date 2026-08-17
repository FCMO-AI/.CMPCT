"""Bounded multi-root resemblance primitives for CMPCT research.

This module is **not** canonical revision-24 grammar.  It prototypes one narrow question for the next
Opus-5 campaign: can a target that combines information from several independent roots beat the best
single-base delta without reintroducing recursive dependency chains?

A mosaic COPY therefore names one slot in a small caller-supplied root set.  All roots are independent
objects; the delta itself never references another delta.  Similarity/candidate discovery remains an
encoder concern and exact reconstruction remains the correctness oracle.

Footnote: this is intentionally a separate module from ``cmpct.resemblance``.  v0.28's single-base
primitive is already validated and should not be casually destabilized while a multi-root design is
still falsifiable research.  Promotion can consolidate code later if the benchmark earns it.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

MOD_ADLER = 65521
MOSAIC_LITERAL = 0
MOSAIC_COPY = 2


@dataclass(frozen=True)
class MosaicDeltaStats:
    literal_bytes: int
    copied_bytes: int
    copy_ops: int
    literal_ops: int
    indexed_source_bytes: int
    copied_by_base: tuple[int, ...]


@dataclass(frozen=True)
class MosaicDeltaResult:
    payload: bytes
    stats: MosaicDeltaStats


def _put_varint(out: bytearray, value: int) -> None:
    if value < 0:
        raise ValueError("varint cannot encode negative values")
    while value >= 0x80:
        out.append((value & 0x7F) | 0x80)
        value >>= 7
    out.append(value)


def _get_varint(payload: bytes, pos: int) -> tuple[int, int]:
    value = 0
    shift = 0
    for _ in range(10):
        if pos >= len(payload):
            raise ValueError("truncated varint")
        byte = payload[pos]
        pos += 1
        value |= (byte & 0x7F) << shift
        if not (byte & 0x80):
            return value, pos
        shift += 7
    raise ValueError("oversized varint")


def _weak_init(block: bytes) -> tuple[int, int]:
    s1 = sum(block) % MOD_ADLER
    width = len(block)
    s2 = sum((width - i) * byte for i, byte in enumerate(block)) % MOD_ADLER
    return s1, s2


def _weak_roll(s1: int, s2: int, old: int, new: int, width: int) -> tuple[int, int]:
    s1 = (s1 - old + new) % MOD_ADLER
    s2 = (s2 - width * old + s1) % MOD_ADLER
    return s1, s2


def _weak_key(s1: int, s2: int) -> int:
    return (s2 << 16) | s1


def mosaic_delta_encode(
    bases: Sequence[bytes],
    target: bytes,
    *,
    block: int = 64,
    max_bases: int = 4,
    max_source_index: int = 8 * 1024 * 1024,
    max_matches_per_key: int = 16,
) -> MosaicDeltaResult:
    """Encode ``target`` with COPY/LITERAL operations across several independent roots.

    Payload grammar used by this research primitive:

    - ``0`` + varint(length) + literal bytes;
    - ``2`` + varint(base_slot) + varint(base_offset) + varint(length).

    The source hash index is hard-bounded by both aggregate source bytes and candidate anchors per weak
    checksum.  Matching is deterministic: the longest exact extension wins, then the lower base slot,
    then the lower source offset.

    Footnote: indexing four 512 KiB roots is qualitatively different from allowing a graph walk.  The
    caller pays for every root in the read-amplification calculation and the decoder receives only this
    flat root set; there is no opcode capable of recursively resolving another delta.
    """
    if block < 16:
        raise ValueError("block size too small")
    if max_bases <= 0 or len(bases) > max_bases:
        raise ValueError("too many mosaic bases")
    if max_matches_per_key <= 0:
        raise ValueError("max_matches_per_key must be positive")
    indexed_source_bytes = sum(len(base) for base in bases)
    if indexed_source_bytes > max_source_index:
        raise ValueError("aggregate mosaic source index exceeds limit")
    if not target:
        return MosaicDeltaResult(
            b"",
            MosaicDeltaStats(0, 0, 0, 0, indexed_source_bytes, tuple(0 for _ in bases)),
        )
    if not bases or len(target) < block:
        out = bytearray([MOSAIC_LITERAL])
        _put_varint(out, len(target))
        out.extend(target)
        return MosaicDeltaResult(
            bytes(out),
            MosaicDeltaStats(len(target), 0, 0, 1, indexed_source_bytes, tuple(0 for _ in bases)),
        )

    # Weak checksums nominate anchors; exact byte equality below remains the acceptance proof.
    # A bounded row prevents an all-equal/adversarial source population from making one checksum fan
    # out into unbounded candidate comparisons.
    index: dict[int, list[tuple[int, int]]] = {}
    for base_slot, base in enumerate(bases):
        if len(base) < block:
            continue
        for offset in range(0, len(base) - block + 1, block):
            s1, s2 = _weak_init(base[offset : offset + block])
            row = index.setdefault(_weak_key(s1, s2), [])
            if len(row) < max_matches_per_key:
                row.append((base_slot, offset))

    out = bytearray()
    literal = bytearray()
    copied = copy_ops = literal_ops = 0
    copied_by_base = [0] * len(bases)

    def flush_literal() -> None:
        nonlocal literal_ops
        if not literal:
            return
        out.append(MOSAIC_LITERAL)
        _put_varint(out, len(literal))
        out.extend(literal)
        literal.clear()
        literal_ops += 1

    pos = 0
    if len(target) >= block:
        s1, s2 = _weak_init(target[:block])
    else:  # pragma: no cover - guarded above, retained to keep state initialization explicit.
        s1 = s2 = 0

    while pos + block <= len(target):
        best: tuple[int, int, int] | None = None  # length, base_slot, offset
        for base_slot, offset in index.get(_weak_key(s1, s2), ()):
            base = bases[base_slot]
            if base[offset : offset + block] != target[pos : pos + block]:
                continue
            length = block
            limit = min(len(base) - offset, len(target) - pos)
            while length < limit and base[offset + length] == target[pos + length]:
                length += 1
            candidate = (length, base_slot, offset)
            if best is None or (-candidate[0], candidate[1], candidate[2]) < (-best[0], best[1], best[2]):
                best = candidate

        if best is not None:
            length, base_slot, offset = best
            flush_literal()
            out.append(MOSAIC_COPY)
            _put_varint(out, base_slot)
            _put_varint(out, offset)
            _put_varint(out, length)
            copied += length
            copied_by_base[base_slot] += length
            copy_ops += 1
            pos += length
            if pos + block <= len(target):
                s1, s2 = _weak_init(target[pos : pos + block])
            continue

        literal.append(target[pos])
        if pos + block < len(target):
            s1, s2 = _weak_roll(s1, s2, target[pos], target[pos + block], block)
        pos += 1

    literal.extend(target[pos:])
    flush_literal()
    return MosaicDeltaResult(
        bytes(out),
        MosaicDeltaStats(
            literal_bytes=len(target) - copied,
            copied_bytes=copied,
            copy_ops=copy_ops,
            literal_ops=literal_ops,
            indexed_source_bytes=indexed_source_bytes,
            copied_by_base=tuple(copied_by_base),
        ),
    )


def mosaic_delta_decode(
    bases: Sequence[bytes],
    payload: bytes,
    *,
    expected_size: int | None = None,
    max_bases: int = 4,
    max_source_bytes: int = 8 * 1024 * 1024,
    max_output: int = 16 * 1024 * 1024,
) -> bytes:
    """Decode a bounded mosaic delta and fail closed on malformed root references."""
    if max_bases <= 0 or len(bases) > max_bases:
        raise ValueError("too many mosaic bases")
    if sum(len(base) for base in bases) > max_source_bytes:
        raise ValueError("mosaic source bytes exceed decoder limit")

    out = bytearray()
    pos = 0
    while pos < len(payload):
        tag = payload[pos]
        pos += 1
        if tag == MOSAIC_LITERAL:
            length, pos = _get_varint(payload, pos)
            if length > max_output - len(out) or pos + length > len(payload):
                raise ValueError("literal exceeds mosaic bounds")
            out.extend(payload[pos : pos + length])
            pos += length
        elif tag == MOSAIC_COPY:
            base_slot, pos = _get_varint(payload, pos)
            offset, pos = _get_varint(payload, pos)
            length, pos = _get_varint(payload, pos)
            if base_slot >= len(bases):
                raise ValueError("mosaic copy references missing base")
            base = bases[base_slot]
            if offset > len(base) or length > len(base) - offset:
                raise ValueError("mosaic copy exceeds base bounds")
            if length > max_output - len(out):
                raise ValueError("mosaic output exceeds limit")
            out.extend(base[offset : offset + length])
        else:
            raise ValueError("unknown mosaic delta opcode")

    if expected_size is not None and len(out) != expected_size:
        raise ValueError("mosaic delta reconstructed wrong length")
    return bytes(out)


def used_base_slots(stats: MosaicDeltaStats) -> tuple[int, ...]:
    """Return roots that actually contribute target bytes, in stable slot order."""
    return tuple(index for index, copied in enumerate(stats.copied_by_base) if copied > 0)
