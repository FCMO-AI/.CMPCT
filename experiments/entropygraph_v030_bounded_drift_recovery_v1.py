from __future__ import annotations

"""Recovery-capable non-canonical framing for the bounded-drift research candidate.

The payload contexts are stored once. Only compact authenticated metadata is duplicated: a
primary copy before the contexts and an independently discoverable tail copy after them. A
valid primary copy is authoritative; the tail is used only when primary metadata is damaged.
This mirrors the repository's recovery law without spending the Shifted byte margin on a
second payload copy. `CMPNX*` means research-only, never canonical r25/release credit.
"""

from dataclasses import dataclass
import hashlib
import struct

import zstandard as zstd

from experiments import entropygraph_v030_bounded_drift_container_v1 as C
from experiments import entropygraph_v030_bounded_drift_v1 as BD

MAGIC = b"CMPNXBR3"
TAIL = b"CMNXBR3T"
HDR = struct.Struct("<8sI32s")
FTR = struct.Struct("<8sI32s")
MAX_META_BYTES = 512 * 1024
_DIGEST = hashlib.sha256().digest_size


@dataclass(frozen=True)
class RecoveryParse:
    parsed: C.ParsedContainer
    source: str
    metadata_bytes: int


def _put(out: bytearray, value: int) -> None:
    BD.put_varint(out, value)


def _get(buf: bytes, pos: int) -> tuple[int, int]:
    return BD.get_varint(buf, pos)


def _metadata(base: bytes, patch_raw: bytes, base_stored: bytes, patch_stored: bytes,
              entries: list[C.MemberEntry]) -> bytes:
    out = bytearray()
    _put(out, len(entries)); _put(out, len(base)); _put(out, len(base_stored))
    _put(out, len(patch_raw)); _put(out, len(patch_stored))
    out.extend(hashlib.sha256(base).digest())
    out.extend(hashlib.sha256(patch_raw).digest())
    for entry in entries:
        _put(out, entry.logical_size); _put(out, entry.program_offset); _put(out, entry.program_length)
        out.extend(entry.sha256)
    if len(out) > MAX_META_BYTES:
        raise ValueError("bounded-drift recovery metadata exceeds limit")
    return bytes(out)


def _decode_metadata(meta: bytes) -> tuple[int, int, int, int, bytes, bytes, tuple[C.MemberEntry, ...]]:
    if not meta or len(meta) > MAX_META_BYTES:
        raise ValueError("bounded-drift recovery metadata size out of range")
    pos = 0
    count, pos = _get(meta, pos); base_raw_n, pos = _get(meta, pos); base_stored_n, pos = _get(meta, pos)
    patch_raw_n, pos = _get(meta, pos); patch_stored_n, pos = _get(meta, pos)
    if not 1 <= count <= C.MAX_MEMBERS:
        raise ValueError("bounded-drift recovery member count out of range")
    if base_raw_n > BD.MAX_DECODE_UNIT or patch_raw_n > C.MAX_CONTEXT_BYTES:
        raise ValueError("bounded-drift recovery decoded context exceeds limit")
    if base_stored_n > C.MAX_CONTEXT_BYTES or patch_stored_n > C.MAX_CONTEXT_BYTES:
        raise ValueError("bounded-drift recovery stored context exceeds limit")
    if pos + 2 * _DIGEST > len(meta):
        raise ValueError("bounded-drift recovery digest table truncated")
    base_digest = meta[pos:pos+_DIGEST]; pos += _DIGEST
    patch_digest = meta[pos:pos+_DIGEST]; pos += _DIGEST
    entries: list[C.MemberEntry] = []
    previous_end = 0
    for _ in range(count):
        logical, pos = _get(meta, pos); offset, pos = _get(meta, pos); length, pos = _get(meta, pos)
        if pos + _DIGEST > len(meta):
            raise ValueError("bounded-drift recovery member table truncated")
        digest = meta[pos:pos+_DIGEST]; pos += _DIGEST
        if logical > BD.MAX_DECODE_UNIT or offset != previous_end or offset + length > patch_raw_n:
            raise ValueError("bounded-drift recovery member table invalid")
        entries.append(C.MemberEntry(logical, offset, length, digest)); previous_end = offset + length
    if pos != len(meta) or previous_end != patch_raw_n:
        raise ValueError("bounded-drift recovery metadata has trailing or unowned bytes")
    return base_raw_n, base_stored_n, patch_raw_n, patch_stored_n, base_digest, patch_digest, tuple(entries)


def encode_recovery_container(members: list[bytes]) -> bytes:
    if not members or len(members) > C.MAX_MEMBERS:
        raise ValueError("bounded-drift recovery member count out of range")
    if any(not isinstance(member, bytes) for member in members):
        raise TypeError("bounded-drift recovery members must be bytes")
    ordered = sorted(members, key=lambda data: (hashlib.sha256(data).digest(), data))
    base = BD.select_base(ordered)
    programs = [BD.encode_program(base, member) for member in ordered]
    patch = bytearray(); entries: list[C.MemberEntry] = []
    for program in programs:
        offset = len(patch); patch.extend(program.raw)
        entries.append(C.MemberEntry(program.logical_size, offset, len(program.raw), program.sha256))
    patch_raw = bytes(patch)
    if len(patch_raw) > C.MAX_CONTEXT_BYTES:
        raise ValueError("bounded-drift recovery patch context exceeds limit")
    base_stored = zstd.ZstdCompressor(level=C.LEVEL, threads=0, write_checksum=True).compress(base)
    patch_stored = zstd.ZstdCompressor(level=C.LEVEL, threads=0, write_checksum=True).compress(patch_raw)
    meta = _metadata(base, patch_raw, base_stored, patch_stored, entries)
    digest = hashlib.sha256(meta).digest()
    out = bytearray(HDR.pack(MAGIC, len(meta), digest)); out.extend(meta)
    out.extend(base_stored); out.extend(patch_stored); out.extend(meta); out.extend(FTR.pack(TAIL, len(meta), digest))
    if len(out) > C.MAX_CONTAINER_BYTES:
        raise ValueError("bounded-drift recovery container exceeds limit")
    return bytes(out)


def _primary_meta(blob: bytes) -> tuple[bytes, int]:
    if len(blob) < HDR.size:
        raise ValueError("short bounded-drift recovery header")
    magic, n, digest = HDR.unpack(blob[:HDR.size])
    if magic != MAGIC or n == 0 or n > MAX_META_BYTES or HDR.size + n > len(blob):
        raise ValueError("invalid bounded-drift recovery primary header")
    meta = blob[HDR.size:HDR.size+n]
    if hashlib.sha256(meta).digest() != digest:
        raise ValueError("bounded-drift recovery primary metadata digest mismatch")
    return meta, HDR.size + n


def _tail_meta(blob: bytes) -> tuple[bytes, int]:
    if len(blob) < FTR.size:
        raise ValueError("short bounded-drift recovery footer")
    magic, n, digest = FTR.unpack(blob[-FTR.size:])
    if magic != TAIL or n == 0 or n > MAX_META_BYTES or n + FTR.size > len(blob):
        raise ValueError("invalid bounded-drift recovery footer")
    start = len(blob) - FTR.size - n
    meta = blob[start:start+n]
    if hashlib.sha256(meta).digest() != digest:
        raise ValueError("bounded-drift recovery tail metadata digest mismatch")
    return meta, start


def parse_recovery_container(blob: bytes) -> RecoveryParse:
    if not isinstance(blob, bytes):
        raise TypeError("bounded-drift recovery container must be bytes")
    if len(blob) > C.MAX_CONTAINER_BYTES:
        raise ValueError("bounded-drift recovery container exceeds limit")
    try:
        meta, context_start = _primary_meta(blob)
        source = "primary"
    except ValueError:
        meta, tail_start = _tail_meta(blob)
        source = "tail"
        # The duplicated metadata has the same authenticated length as the primary copy, so the
        # physical contexts remain independently locatable even when the primary header is damaged.
        context_start = HDR.size + len(meta)
        if context_start > tail_start:
            raise ValueError("bounded-drift recovery contexts overlap tail metadata")
    base_raw_n, base_stored_n, patch_raw_n, patch_stored_n, base_digest, patch_digest, entries = _decode_metadata(meta)
    context_end = context_start + base_stored_n + patch_stored_n
    tail_meta_start = len(blob) - FTR.size - len(meta)
    if context_end != tail_meta_start:
        raise ValueError("bounded-drift recovery context boundary mismatch")
    base_stored = blob[context_start:context_start+base_stored_n]
    patch_stored = blob[context_start+base_stored_n:context_end]
    try:
        base = zstd.ZstdDecompressor().decompress(base_stored, max_output_size=BD.MAX_DECODE_UNIT)
        patch_raw = zstd.ZstdDecompressor().decompress(patch_stored, max_output_size=C.MAX_CONTEXT_BYTES)
    except zstd.ZstdError as exc:
        raise ValueError("bounded-drift recovery compressed context invalid") from exc
    if len(base) != base_raw_n or hashlib.sha256(base).digest() != base_digest:
        raise ValueError("bounded-drift recovery base identity mismatch")
    if len(patch_raw) != patch_raw_n or hashlib.sha256(patch_raw).digest() != patch_digest:
        raise ValueError("bounded-drift recovery patch identity mismatch")
    return RecoveryParse(C.ParsedContainer(base, patch_raw, entries), source, len(meta))


def decode_member(blob: bytes, index: int) -> bytes:
    parsed = parse_recovery_container(blob).parsed
    entry = C._checked_index(parsed, index)
    raw = parsed.patch_raw[entry.program_offset:entry.program_offset+entry.program_length]
    count, _ = BD.get_varint(raw, 0)
    return BD.decode_program(parsed.base, BD.EditProgram(raw, entry.logical_size, entry.sha256, count, 0, 0, 0))
