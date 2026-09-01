from __future__ import annotations

"""Deterministic research container for the v0.30 bounded-drift primitive.

This is deliberately non-canonical (`CMPNX*`). It exists to prove generic framing, selected
member reconstruction, resource bounds and corruption behavior before any r25 grammar change.
No paths, workload names, benchmark hashes or frozen identities participate in encoding.
"""

from dataclasses import dataclass
import hashlib

import zstandard as zstd

from experiments import entropygraph_v030_bounded_drift_v1 as BD

MAGIC = b"CMPNXBD2"
LEVEL = 19
MAX_MEMBERS = 4096
MAX_CONTEXT_BYTES = BD.MAX_DECODE_UNIT
MAX_CONTAINER_BYTES = 3 * BD.MAX_DECODE_UNIT
_DIGEST = hashlib.sha256().digest_size


@dataclass(frozen=True)
class MemberEntry:
    logical_size: int
    program_offset: int
    program_length: int
    sha256: bytes


@dataclass(frozen=True)
class ParsedContainer:
    base: bytes
    patch_raw: bytes
    entries: tuple[MemberEntry, ...]


@dataclass(frozen=True)
class MemberResourceFacts:
    logical_size: int
    decoded_context_bytes: int
    max_decode_unit_bytes: int
    member_read_amplification: float


def _put(out: bytearray, value: int) -> None:
    BD.put_varint(out, value)


def _get(buf: bytes, pos: int) -> tuple[int, int]:
    return BD.get_varint(buf, pos)


def _compress(data: bytes) -> bytes:
    return zstd.ZstdCompressor(level=LEVEL, threads=0, write_checksum=True).compress(data)


def _checked_index(parsed: ParsedContainer, index: int) -> MemberEntry:
    if not isinstance(index, int) or isinstance(index, bool):
        raise TypeError("bounded-drift member index must be int")
    if index < 0 or index >= len(parsed.entries):
        raise IndexError("bounded-drift member index out of range")
    return parsed.entries[index]


def encode_container(members: list[bytes]) -> bytes:
    if not members or len(members) > MAX_MEMBERS:
        raise ValueError("bounded-drift container member count out of range")
    if any(not isinstance(member, bytes) for member in members):
        raise TypeError("bounded-drift container members must be bytes")
    if any(len(member) > BD.MAX_DECODE_UNIT for member in members):
        raise ValueError("bounded-drift member exceeds decode-unit limit")

    # Canonicalize by content only. Duplicate logical members remain duplicate table entries;
    # caller ordering and names cannot affect physical bytes.
    ordered = sorted(members, key=lambda data: (hashlib.sha256(data).digest(), data))
    base = BD.select_base(ordered)
    programs = [BD.encode_program(base, member) for member in ordered]

    patch = bytearray()
    entries: list[MemberEntry] = []
    for program in programs:
        offset = len(patch)
        patch.extend(program.raw)
        entries.append(MemberEntry(program.logical_size, offset, len(program.raw), program.sha256))
    patch_raw = bytes(patch)
    if len(patch_raw) > MAX_CONTEXT_BYTES:
        raise ValueError("bounded-drift shared edit context exceeds decode-unit limit")

    base_stored = _compress(base)
    patch_stored = _compress(patch_raw)
    if len(base_stored) > MAX_CONTEXT_BYTES or len(patch_stored) > MAX_CONTEXT_BYTES:
        raise ValueError("bounded-drift compressed context exceeds resource limit")

    out = bytearray(MAGIC)
    _put(out, len(entries))
    _put(out, len(base))
    _put(out, len(base_stored))
    _put(out, len(patch_raw))
    _put(out, len(patch_stored))
    out.extend(hashlib.sha256(base).digest())
    out.extend(base_stored)
    out.extend(patch_stored)
    for entry in entries:
        _put(out, entry.logical_size)
        _put(out, entry.program_offset)
        _put(out, entry.program_length)
        out.extend(entry.sha256)
    out.extend(hashlib.sha256(out).digest())
    if len(out) > MAX_CONTAINER_BYTES:
        raise ValueError("bounded-drift container exceeds resource limit")
    return bytes(out)


def parse_container(blob: bytes) -> ParsedContainer:
    if not isinstance(blob, bytes):
        raise TypeError("bounded-drift container must be bytes")
    if len(blob) > MAX_CONTAINER_BYTES or len(blob) < len(MAGIC) + _DIGEST * 2 + 5:
        raise ValueError("bounded-drift container size out of range")
    if not blob.startswith(MAGIC):
        raise ValueError("bounded-drift container magic mismatch")
    body, trailer = blob[:-_DIGEST], blob[-_DIGEST:]
    if hashlib.sha256(body).digest() != trailer:
        raise ValueError("bounded-drift container digest mismatch")

    pos = len(MAGIC)
    count, pos = _get(body, pos)
    base_raw_n, pos = _get(body, pos)
    base_stored_n, pos = _get(body, pos)
    patch_raw_n, pos = _get(body, pos)
    patch_stored_n, pos = _get(body, pos)
    if not 1 <= count <= MAX_MEMBERS:
        raise ValueError("bounded-drift member count out of range")
    if base_raw_n > BD.MAX_DECODE_UNIT or patch_raw_n > MAX_CONTEXT_BYTES:
        raise ValueError("bounded-drift decoded context exceeds limit")
    if base_stored_n > MAX_CONTEXT_BYTES or patch_stored_n > MAX_CONTEXT_BYTES:
        raise ValueError("bounded-drift stored context exceeds limit")
    if pos + _DIGEST + base_stored_n + patch_stored_n > len(body):
        raise ValueError("bounded-drift context lengths exceed container")

    base_digest = body[pos:pos + _DIGEST]
    pos += _DIGEST
    base_stored = body[pos:pos + base_stored_n]
    pos += base_stored_n
    patch_stored = body[pos:pos + patch_stored_n]
    pos += patch_stored_n

    try:
        base = zstd.ZstdDecompressor().decompress(base_stored, max_output_size=BD.MAX_DECODE_UNIT)
        patch_raw = zstd.ZstdDecompressor().decompress(patch_stored, max_output_size=MAX_CONTEXT_BYTES)
    except zstd.ZstdError as exc:
        raise ValueError("bounded-drift compressed context invalid") from exc
    if len(base) != base_raw_n or hashlib.sha256(base).digest() != base_digest:
        raise ValueError("bounded-drift base identity mismatch")
    if len(patch_raw) != patch_raw_n:
        raise ValueError("bounded-drift patch context length mismatch")

    entries: list[MemberEntry] = []
    previous_end = 0
    for _ in range(count):
        logical_size, pos = _get(body, pos)
        offset, pos = _get(body, pos)
        program_length, pos = _get(body, pos)
        if pos + _DIGEST > len(body):
            raise ValueError("bounded-drift member table truncated")
        digest = body[pos:pos + _DIGEST]
        pos += _DIGEST
        if logical_size > BD.MAX_DECODE_UNIT:
            raise ValueError("bounded-drift member logical size exceeds limit")
        end = offset + program_length
        if offset != previous_end or end > len(patch_raw):
            raise ValueError("bounded-drift program ranges are not canonical")
        entries.append(MemberEntry(logical_size, offset, program_length, digest))
        previous_end = end
    if previous_end != len(patch_raw) or pos != len(body):
        raise ValueError("bounded-drift container has trailing or unowned data")
    return ParsedContainer(base, patch_raw, tuple(entries))


def member_resource_facts(blob: bytes, index: int) -> MemberResourceFacts:
    """Return release-law locality/decode facts for one selected member.

    Selected-member reconstruction decodes the complete shared base and patch context before
    producing the logical member. This intentionally matches the strict R4 floor's accounting;
    no compressed or shared context is treated as free just because another member may reuse it.
    """
    parsed = parse_container(blob)
    entry = _checked_index(parsed, index)
    decoded_context = len(parsed.base) + len(parsed.patch_raw) + entry.logical_size
    return MemberResourceFacts(
        logical_size=entry.logical_size,
        decoded_context_bytes=decoded_context,
        max_decode_unit_bytes=max(len(parsed.base), len(parsed.patch_raw), entry.logical_size),
        member_read_amplification=decoded_context / max(1, entry.logical_size),
    )


def decode_member(blob: bytes, index: int) -> bytes:
    parsed = parse_container(blob)
    entry = _checked_index(parsed, index)
    raw = parsed.patch_raw[entry.program_offset:entry.program_offset + entry.program_length]
    count, _ = BD.get_varint(raw, 0)
    program = BD.EditProgram(raw, entry.logical_size, entry.sha256, count, 0, 0, 0)
    return BD.decode_program(parsed.base, program)


def decode_all(blob: bytes) -> list[bytes]:
    parsed = parse_container(blob)
    out: list[bytes] = []
    for entry in parsed.entries:
        raw = parsed.patch_raw[entry.program_offset:entry.program_offset + entry.program_length]
        count, _ = BD.get_varint(raw, 0)
        out.append(BD.decode_program(parsed.base, BD.EditProgram(raw, entry.logical_size, entry.sha256, count, 0, 0, 0)))
    return out
