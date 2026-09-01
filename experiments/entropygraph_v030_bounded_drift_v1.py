from __future__ import annotations

"""Generic bounded-drift edit primitive for the v0.30 Shifted candidate.

Research/productization seam only: no canonical archive grammar, selector, or release credit.
The primitive is deliberately blind to workload names, paths, frozen hashes and benchmark
identity. Base choice depends only on logical bytes; reconstruction is depth-1 and bounded.
"""

from dataclasses import dataclass
import hashlib

SYNC_BYTES = 48
MAX_RESYNC_BYTES = 1024
MAX_DECODE_UNIT = 8 * 1024 * 1024
_COMMON_CHUNK = 4096


@dataclass(frozen=True)
class EditProgram:
    raw: bytes
    logical_size: int
    sha256: bytes
    records: int
    copied_bytes: int
    deleted_bytes: int
    inserted_bytes: int


def put_varint(out: bytearray, value: int) -> None:
    if value < 0:
        raise ValueError("negative varint")
    while value >= 0x80:
        out.append((value & 0x7F) | 0x80)
        value >>= 7
    out.append(value)


def get_varint(buf: bytes, pos: int) -> tuple[int, int]:
    value = 0
    shift = 0
    while True:
        if pos >= len(buf) or shift > 63:
            raise ValueError("malformed varint")
        b = buf[pos]
        pos += 1
        value |= (b & 0x7F) << shift
        if not b & 0x80:
            return value, pos
        shift += 7


def select_base(members: list[bytes]) -> bytes:
    if not members:
        raise ValueError("bounded-drift requires at least one member")
    if any(not isinstance(x, bytes) for x in members):
        raise TypeError("bounded-drift members must be bytes")
    # Digest + bytes makes collisions deterministic without importing path/order identity.
    return min(members, key=lambda x: (hashlib.sha256(x).digest(), x))


def _common_prefix_len(a: bytes, b: bytes, ai: int, bi: int) -> int:
    limit = min(len(a) - ai, len(b) - bi)
    n = 0
    while n + _COMMON_CHUNK <= limit and a[ai+n:ai+n+_COMMON_CHUNK] == b[bi+n:bi+n+_COMMON_CHUNK]:
        n += _COMMON_CHUNK
    while n < limit and a[ai+n] == b[bi+n]:
        n += 1
    return n


def _find_resync(base: bytes, target: bytes, i: int, j: int) -> tuple[int, int]:
    rem_b, rem_t = len(base) - i, len(target) - j
    for k in range(1, min(MAX_RESYNC_BYTES, rem_b, rem_t) + 1):
        if min(rem_b-k, rem_t-k) < SYNC_BYTES:
            break
        if base[i+k:i+k+SYNC_BYTES] == target[j+k:j+k+SYNC_BYTES]:
            return k, k
    candidates: list[tuple[int, int]] = []
    if rem_b >= SYNC_BYTES:
        token = base[i:i+SYNC_BYTES]
        p = target.find(token, j+1, min(len(target), j+MAX_RESYNC_BYTES+SYNC_BYTES))
        if p >= 0:
            candidates.append((0, p-j))
    if rem_t >= SYNC_BYTES:
        token = target[j:j+SYNC_BYTES]
        p = base.find(token, i+1, min(len(base), i+MAX_RESYNC_BYTES+SYNC_BYTES))
        if p >= 0:
            candidates.append((p-i, 0))
    if candidates:
        return min(candidates, key=lambda x: (x[0]+x[1], max(x), x))
    step = min(256, rem_b, rem_t)
    return (step, step) if step else (rem_b, rem_t)


def encode_program(base: bytes, target: bytes) -> EditProgram:
    if len(base) > MAX_DECODE_UNIT or len(target) > MAX_DECODE_UNIT:
        raise ValueError("bounded-drift member exceeds decode-unit limit")
    i = j = copied = deleted = inserted = 0
    rows: list[tuple[int, int, bytes]] = []
    while i < len(base) or j < len(target):
        common = _common_prefix_len(base, target, i, j) if i < len(base) and j < len(target) else 0
        i += common; j += common; copied += common
        if i == len(base) and j == len(target):
            rows.append((common, 0, b"")); break
        if i == len(base):
            lit = target[j:]; rows.append((common, 0, lit)); inserted += len(lit); j = len(target); continue
        if j == len(target):
            n = len(base)-i; rows.append((common, n, b"")); deleted += n; i = len(base); continue
        dn, ins = _find_resync(base, target, i, j)
        lit = target[j:j+ins]
        rows.append((common, dn, lit)); i += dn; j += ins; deleted += dn; inserted += ins
    out = bytearray(); put_varint(out, len(rows))
    for copy_n, delete_n, lit in rows:
        put_varint(out, copy_n); put_varint(out, delete_n); put_varint(out, len(lit)); out.extend(lit)
    if len(out) > MAX_DECODE_UNIT:
        raise ValueError("bounded-drift program exceeds decode-unit limit")
    return EditProgram(bytes(out), len(target), hashlib.sha256(target).digest(), len(rows), copied, deleted, inserted)


def decode_program(base: bytes, program: EditProgram) -> bytes:
    pos = cursor = 0
    count, pos = get_varint(program.raw, pos)
    out = bytearray()
    for _ in range(count):
        copy_n, pos = get_varint(program.raw, pos)
        delete_n, pos = get_varint(program.raw, pos)
        insert_n, pos = get_varint(program.raw, pos)
        if cursor + copy_n + delete_n > len(base) or pos + insert_n > len(program.raw):
            raise ValueError("bounded-drift edit exceeds input")
        out.extend(base[cursor:cursor+copy_n]); cursor += copy_n + delete_n
        out.extend(program.raw[pos:pos+insert_n]); pos += insert_n
        if len(out) > MAX_DECODE_UNIT:
            raise ValueError("bounded-drift decode exceeds limit")
    if pos != len(program.raw) or cursor != len(base) or len(out) != program.logical_size:
        raise ValueError("bounded-drift terminal mismatch")
    result = bytes(out)
    if hashlib.sha256(result).digest() != program.sha256:
        raise ValueError("bounded-drift logical digest mismatch")
    return result


def encode_family(members: list[bytes]) -> tuple[bytes, list[EditProgram]]:
    base = select_base(members)
    return base, [encode_program(base, member) for member in members]
