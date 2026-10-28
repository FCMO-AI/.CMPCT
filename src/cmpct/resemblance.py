"""Reusable resemblance-compression primitives for CMPCT research encoders.

The canonical revision-24 reader does not depend on this module. It lives in ``src/cmpct`` rather than
an experiment script because the algorithms are format-agnostic and can be reused by future encoder
policy, benchmark tooling, or a native implementation without copying subtle bounds rules.

Footnote: every helper is deterministic for identical bytes and parameters. Similarity is used only
for candidate discovery; an edge is accepted only after measuring the actual delta representation, so
a sketch collision can waste encoder work but cannot make an archive incorrect or larger by fiat.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import blake2b
from typing import Iterable, Sequence

MOD_ADLER = 65521
MASK64 = (1 << 64) - 1


def _u64(data: bytes, *, person: bytes = b"cmpct-sim") -> int:
    return int.from_bytes(blake2b(data, digest_size=8, person=person[:16]).digest(), "little")


# Deterministic Gear table. Generating it from domain-separated BLAKE2 rather than process randomness
# makes chunk boundaries stable across machines and avoids carrying 256 unexplained magic constants.
GEAR = tuple(_u64(bytes([i]), person=b"cmpct-gear-v1") for i in range(256))


@dataclass(frozen=True)
class Chunk:
    offset: int
    length: int


@dataclass(frozen=True)
class SimilaritySketch:
    """Compact super-features used only to find plausible resemblance neighbors."""
    size_bucket: int
    features: tuple[int, ...]


@dataclass(frozen=True)
class DeltaStats:
    literal_bytes: int
    copied_bytes: int
    copy_ops: int
    literal_ops: int


@dataclass(frozen=True)
class DeltaResult:
    payload: bytes
    stats: DeltaStats


@dataclass(frozen=True)
class CandidateEdge:
    target: int
    base: int
    shared_features: int


def fastcdc(data: bytes, *, min_size: int = 16 * 1024, avg_size: int = 64 * 1024,
            max_size: int = 256 * 1024) -> list[Chunk]:
    """Return deterministic FastCDC-style Gear boundaries.

    This follows the FastCDC mechanism—Gear hashing, a skipped minimum region, and normalized masks
    around the target size—without claiming byte-for-byte compatibility with an external FastCDC.

    Footnote: ``max_size`` is a hard resource invariant. Even adversarial bytes cannot make a chunk
    exceed it; later delta and selective-read accounting therefore operate on bounded units.
    """
    n = len(data)
    if n == 0:
        return []
    if not (0 < min_size <= avg_size <= max_size):
        raise ValueError("require 0 < min_size <= avg_size <= max_size")
    bits = max(1, round(avg_size.bit_length() - 1))
    small_mask = (1 << min(63, bits + 1)) - 1
    large_mask = (1 << max(1, bits - 1)) - 1
    normal = min(max_size, max(min_size + 1, avg_size))
    out: list[Chunk] = []
    start = 0
    while start < n:
        hard_end = min(n, start + max_size)
        if hard_end - start <= min_size:
            out.append(Chunk(start, hard_end - start))
            break
        i = start + min_size
        h = 0
        early_end = min(hard_end, start + normal)
        cut = None
        while i < early_end:
            h = ((h << 1) + GEAR[data[i]]) & MASK64
            if (h & small_mask) == 0:
                cut = i + 1
                break
            i += 1
        if cut is None:
            while i < hard_end:
                h = ((h << 1) + GEAR[data[i]]) & MASK64
                if (h & large_mask) == 0:
                    cut = i + 1
                    break
                i += 1
        if cut is None:
            cut = hard_end
        out.append(Chunk(start, cut - start))
        start = cut
    return out


def similarity_sketch(data: bytes, *, bands: int = 8, shingle: int = 64) -> SimilaritySketch:
    """Build deterministic super-features from content shingles.

    Each band keeps the minimum hash in one logical region. A local edit therefore perturbs only some
    bands instead of invalidating one whole-file hash. The sketch is not trusted as proof of similarity;
    the measured delta representation remains the acceptance oracle.
    """
    if bands <= 0 or shingle <= 0:
        raise ValueError("bands and shingle must be positive")
    n = len(data)
    size_bucket = max(0, n.bit_length() - 1)
    if n == 0:
        return SimilaritySketch(size_bucket, tuple(0 for _ in range(bands)))
    region = max(shingle, (n + bands - 1) // bands)
    feats: list[int] = []
    for band in range(bands):
        start = min(n, band * region)
        end = n if band == bands - 1 else min(n, (band + 1) * region)
        if start >= end:
            feats.append(0)
            continue
        best = MASK64
        step = max(1, shingle // 2)
        last = max(start, end - shingle)
        pos = start
        while pos <= last:
            best = min(best, _u64(data[pos:min(end, pos + shingle)], person=b"cmpct-sf-v1"))
            pos += step
        if best == MASK64:
            best = _u64(data[start:end], person=b"cmpct-sf-v1")
        feats.append(best)
    return SimilaritySketch(size_bucket, tuple(feats))


def lsh_candidates(sketches: Sequence[SimilaritySketch], *, max_bucket: int = 48,
                   max_candidates: int = 8) -> list[CandidateEdge]:
    """Generate bounded resemblance candidates from super-feature collisions.

    Footnote: buckets retain only a bounded number of deterministic ids. A hostile all-equal sketch
    corpus therefore cannot turn candidate discovery into an O(N^2) delta storm.
    """
    if max_bucket <= 0 or max_candidates <= 0:
        raise ValueError("candidate bounds must be positive")
    buckets: dict[tuple[int, int, int], list[int]] = {}
    out: list[CandidateEdge] = []
    for idx, sketch in enumerate(sketches):
        counts: dict[int, int] = {}
        for band, feat in enumerate(sketch.features):
            for size_bucket in (sketch.size_bucket - 1, sketch.size_bucket, sketch.size_bucket + 1):
                for prior in buckets.get((band, feat, size_bucket), ()):
                    counts[prior] = counts.get(prior, 0) + 1
        ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:max_candidates]
        out.extend(CandidateEdge(idx, base, shared) for base, shared in ranked if shared > 0)
        for band, feat in enumerate(sketch.features):
            key = (band, feat, sketch.size_bucket)
            row = buckets.setdefault(key, [])
            row.append(idx)
            if len(row) > max_bucket:
                del row[:len(row) - max_bucket]
    return out


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


def delta_encode(base: bytes, target: bytes, *, block: int = 64,
                 max_base_index: int = 8 * 1024 * 1024) -> DeltaResult:
    """Encode target as bounded rsync-style COPY/LITERAL operations against base.

    Format: tag 0 + varint length + literal bytes, or tag 1 + varint base_offset + varint length.
    Source anchors are fixed blocks while the target checksum rolls byte-by-byte, so insertions do not
    destroy synchronization as they do with aligned block comparison.

    Footnote: source indexing is explicitly bounded. Larger objects should be CDC-split before reaching
    this function; refusing a giant base is safer than allowing resemblance work to consume unbounded RAM.
    """
    if block < 16:
        raise ValueError("block size too small")
    if len(base) > max_base_index:
        raise ValueError("base exceeds delta index limit")
    if not target:
        return DeltaResult(b"", DeltaStats(0, 0, 0, 0))
    if len(base) < block or len(target) < block:
        out = bytearray([0])
        _put_varint(out, len(target))
        out.extend(target)
        return DeltaResult(bytes(out), DeltaStats(len(target), 0, 0, 1))
    index: dict[int, list[int]] = {}
    for offset in range(0, len(base) - block + 1, block):
        s1, s2 = _weak_init(base[offset:offset + block])
        index.setdefault(_weak_key(s1, s2), []).append(offset)
    out = bytearray()
    literal = bytearray()
    copied = copy_ops = literal_ops = 0

    def flush_literal() -> None:
        nonlocal literal_ops
        if not literal:
            return
        out.append(0)
        _put_varint(out, len(literal))
        out.extend(literal)
        literal.clear()
        literal_ops += 1

    pos = 0
    s1, s2 = _weak_init(target[:block])
    while pos + block <= len(target):
        match_offset = -1
        for offset in index.get(_weak_key(s1, s2), ()):
            if base[offset:offset + block] == target[pos:pos + block]:
                match_offset = offset
                break
        if match_offset >= 0:
            length = block
            limit = min(len(base) - match_offset, len(target) - pos)
            while length < limit and base[match_offset + length] == target[pos + length]:
                length += 1
            flush_literal()
            out.append(1)
            _put_varint(out, match_offset)
            _put_varint(out, length)
            copied += length
            copy_ops += 1
            pos += length
            if pos + block <= len(target):
                s1, s2 = _weak_init(target[pos:pos + block])
            continue
        literal.append(target[pos])
        if pos + block < len(target):
            s1, s2 = _weak_roll(s1, s2, target[pos], target[pos + block], block)
        pos += 1
    literal.extend(target[pos:])
    flush_literal()
    return DeltaResult(bytes(out), DeltaStats(len(target) - copied, copied, copy_ops, literal_ops))


def delta_decode(base: bytes, payload: bytes, *, expected_size: int | None = None,
                 max_output: int = 16 * 1024 * 1024) -> bytes:
    """Decode a bounded delta payload and fail closed on malformed references."""
    out = bytearray()
    pos = 0
    while pos < len(payload):
        tag = payload[pos]
        pos += 1
        if tag == 0:
            length, pos = _get_varint(payload, pos)
            if length > max_output - len(out) or pos + length > len(payload):
                raise ValueError("literal exceeds delta bounds")
            out.extend(payload[pos:pos + length])
            pos += length
        elif tag == 1:
            offset, pos = _get_varint(payload, pos)
            length, pos = _get_varint(payload, pos)
            if offset > len(base) or length > len(base) - offset:
                raise ValueError("copy exceeds base bounds")
            if length > max_output - len(out):
                raise ValueError("delta output exceeds limit")
            out.extend(base[offset:offset + length])
        else:
            raise ValueError("unknown delta opcode")
    if expected_size is not None and len(out) != expected_size:
        raise ValueError("delta reconstructed wrong length")
    return bytes(out)


def choose_central_bases(node_count: int, candidates: Iterable[tuple[int, int, int]]) -> dict[int, int]:
    """Choose depth-1 bases by global saved-byte centrality.

    ``candidates`` contains (target, base, saving_bytes) rows already measured against direct storage.
    Bases that can remove the most aggregate bytes are promoted first. Once a node becomes a delta
    target it cannot itself become a base, enforcing dependency depth <= 1 without reader heuristics.
    """
    rows = [(target, base, saving) for target, base, saving in candidates
            if 0 <= target < node_count and 0 <= base < node_count and target != base and saving > 0]
    by_base: dict[int, list[tuple[int, int]]] = {}
    for target, base, saving in rows:
        by_base.setdefault(base, []).append((target, saving))
    base_order = sorted(by_base, key=lambda base: (-sum(s for _, s in by_base[base]), base))
    assignment: dict[int, int] = {}
    bases: set[int] = set()
    best_saving: dict[int, int] = {}
    for base in base_order:
        if base in assignment:
            continue
        bases.add(base)
        for target, saving in sorted(by_base[base], key=lambda item: (-item[1], item[0])):
            if target in bases:
                continue
            if saving > best_saving.get(target, 0):
                assignment[target] = base
                best_saving[target] = saving
    return assignment


def similarity_order(sketches: Sequence[SimilaritySketch]) -> list[int]:
    """Return a stable locality order that places super-feature neighbors together."""
    return sorted(range(len(sketches)), key=lambda i: (sketches[i].size_bucket, sketches[i].features, i))
