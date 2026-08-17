"""CMPCT v0.30 research — Hierarchical Geometry / Prefix Planes.

This module extends the Geometry Compiler seed without changing the canonical archive grammar.  The core
idea is to synthesize a small reversible *layout program* directly from bytes:

1. nominate a primary recurring separator from gap statistics;
2. split the resulting records with a second recurring separator whose per-record multiplicity is stable;
3. transpose discovered field positions into column-major order;
4. optionally front-compress each discovered column against its preceding value (prefix planes);
5. ask the real compressor whether either representation actually beats direct bytes.

No extension, MIME type, JSON/CSV/log parser, field name, UTF-8 assumption, or workload identity is used.
The transform is therefore closer to a tiny byte-layout compiler than to schema-aware serialization.

Footnote: this file is deliberately a *transform/oracle layer*, not a promoted CMPCT writer.  Full-artifact
integration belongs at Mosaic's authenticated physical-record boundary only after the transform survives
exact public-corpus, malformed-input, timing, memory, native-reader, portability and direct-base gates.
"""
from __future__ import annotations

from collections import Counter
import math

from experiments import entropygraph_v030_geometry as G

MAGIC_PLAIN = b"HGT2"
MAGIC_PREFIX = b"HGP2"
MIN_NODE_BYTES = 16 * 1024
MIN_PAYLOAD_SAVING = 64
MAX_PRIMARY_CANDIDATES = 4
MAX_SECONDARY_CANDIDATES = 6
MAX_ROWS = 65_536
MAX_FIELDS_PER_ROW = 256
MAX_FIELD_DESCRIPTORS = 131_072
MAX_CELL_SCANS = 8 * G.MAX_CHUNK
SECONDARY_SAMPLE_ROWS = 1_024
SCREEN_LEVEL = 6
EXACT_LEVEL = 19
MAX_EXACT_FINALISTS = 3


def _put_varint(out: bytearray, value: int) -> None:
    if value < 0:
        raise ValueError("negative Hierarchical Geometry varint")
    while True:
        byte = value & 0x7F
        value >>= 7
        out.append(byte | (0x80 if value else 0))
        if not value:
            return


def _get_varint(buf: bytes, pos: int) -> tuple[int, int]:
    value = shift = 0
    for _ in range(10):
        if pos >= len(buf):
            raise RuntimeError("short Hierarchical Geometry varint")
        byte = buf[pos]
        pos += 1
        value |= (byte & 0x7F) << shift
        if not byte & 0x80:
            return value, pos
        shift += 7
    raise RuntimeError("overlong Hierarchical Geometry varint")


def _common_prefix(left: bytes, right: bytes) -> int:
    limit = min(len(left), len(right))
    index = 0
    while index < limit and left[index] == right[index]:
        index += 1
    return index


def primary_candidates(raw: bytes) -> list[int]:
    """Nominate a few recurring bytes whose *complete* recurrence intervals are relatively structured.

    Footnote: the leading bytes before the first occurrence and trailing bytes after the last occurrence are
    censored observations, not full recurrence intervals.  Treating them as ordinary gaps systematically
    penalizes legitimate record-boundary bytes: an end-of-record separator naturally has a zero trailing
    fragment, while an interior lexical byte often has two symmetric edge fragments.  Only inter-occurrence
    gaps therefore enter the regularity score.  The pass remains O(n), byte-semantic-free and bounded to four
    nominees; exact level-19 stored bytes still decide whether any proposed geometry is admitted.
    """
    positions: list[list[int]] = [[] for _ in range(256)]
    for index, byte in enumerate(raw):
        positions[byte].append(index)

    ranked: list[tuple[float, int]] = []
    for byte, pos in enumerate(positions):
        count = len(pos)
        if count < 64 or count + 1 > MAX_ROWS:
            continue
        gaps = [right - left - 1 for left, right in zip(pos, pos[1:])]
        if not gaps:
            continue
        mean = sum(gaps) / len(gaps)
        if mean < 1.0:
            continue
        variance = sum((gap - mean) ** 2 for gap in gaps) / len(gaps)
        cv = math.sqrt(variance) / (mean + 1.0)
        density = count / max(1, len(raw))
        score = cv + 4.0 / math.sqrt(count) + max(0.0, density - 0.20) * 10.0
        ranked.append((score, byte))
    ranked.sort()
    return [byte for _, byte in ranked[:MAX_PRIMARY_CANDIDATES]]


def secondary_candidates(rows: list[bytes], primary: int) -> list[int]:
    """Find a second separator whose occurrence pattern is stable across discovered records."""
    if not rows:
        return []
    if len(rows) > SECONDARY_SAMPLE_ROWS:
        step = len(rows) / SECONDARY_SAMPLE_ROWS
        sample = [rows[min(len(rows) - 1, int(index * step))] for index in range(SECONDARY_SAMPLE_ROWS)]
    else:
        sample = rows

    counters = [Counter(row) for row in sample]
    ranked: list[tuple[float, int]] = []
    for byte in range(256):
        if byte == primary:
            continue
        counts = [counter.get(byte, 0) for counter in counters]
        total = sum(counts)
        if total < 64:
            continue
        coverage = sum(value > 0 for value in counts) / len(counts)
        if coverage < 0.50:
            continue
        if max(counts, default=0) + 1 > MAX_FIELDS_PER_ROW:
            continue
        mean = total / len(counts)
        variance = sum((value - mean) ** 2 for value in counts) / len(counts)
        cv = math.sqrt(variance) / (mean + 1.0)
        score = 2.0 * (1.0 - coverage) + cv + 1.0 / math.sqrt(total)
        ranked.append((score, byte))
    ranked.sort()
    return [byte for _, byte in ranked[:MAX_SECONDARY_CANDIDATES]]


def _parse_shape(raw: bytes, primary: int, secondary: int) -> tuple[list[list[bytes]], int, int]:
    if len(raw) > G.MAX_CHUNK:
        raise ValueError("Hierarchical Geometry input exceeds logical-node ceiling")
    if not 0 <= primary <= 255 or not 0 <= secondary <= 255 or primary == secondary:
        raise ValueError("invalid Hierarchical Geometry separators")
    rows = raw.split(bytes((primary,)))
    if not 1 <= len(rows) <= MAX_ROWS:
        raise ValueError("Hierarchical Geometry row count out of bounds")

    fields: list[list[bytes]] = []
    descriptors = 0
    max_fields = 0
    for row in rows:
        current = row.split(bytes((secondary,)))
        if len(current) > MAX_FIELDS_PER_ROW:
            raise ValueError("Hierarchical Geometry fields-per-row cap exceeded")
        descriptors += len(current)
        if descriptors > MAX_FIELD_DESCRIPTORS:
            raise ValueError("Hierarchical Geometry field-descriptor cap exceeded")
        fields.append(current)
        max_fields = max(max_fields, len(current))

    cell_scans = len(fields) * max_fields
    if cell_scans > MAX_CELL_SCANS:
        raise ValueError("Hierarchical Geometry cell-work budget exceeded")
    return fields, max_fields, descriptors


def hierarchy_forward(raw: bytes, primary: int, secondary: int, *, prefix_planes: bool = False) -> bytes:
    fields, max_fields, _ = _parse_shape(raw, primary, secondary)
    out = bytearray(MAGIC_PREFIX if prefix_planes else MAGIC_PLAIN)
    out.extend((primary, secondary))
    _put_varint(out, len(fields))
    for row in fields:
        _put_varint(out, len(row))
        for field in row:
            _put_varint(out, len(field))

    payloads: list[bytes] = []
    for column in range(max_fields):
        previous = b""
        for row in fields:
            if column >= len(row):
                continue
            field = row[column]
            if prefix_planes:
                prefix = _common_prefix(previous, field)
                _put_varint(out, prefix)
                payloads.append(field[prefix:])
                previous = field
            else:
                payloads.append(field)

    for payload in payloads:
        out.extend(payload)
    if len(out) > G.MAX_DECODE_UNIT:
        raise ValueError("Hierarchical Geometry transformed record exceeds decode ceiling")
    return bytes(out)


def hierarchy_inverse(encoded: bytes, logical_size: int) -> bytes:
    if len(encoded) < 7 or encoded[:4] not in {MAGIC_PLAIN, MAGIC_PREFIX}:
        raise RuntimeError("invalid Hierarchical Geometry magic")
    prefix_planes = encoded[:4] == MAGIC_PREFIX
    primary, secondary = encoded[4], encoded[5]
    if primary == secondary:
        raise RuntimeError("Hierarchical Geometry separators alias")
    row_count, pos = _get_varint(encoded, 6)
    if not 1 <= row_count <= MAX_ROWS:
        raise RuntimeError("Hierarchical Geometry row count out of bounds")

    lengths: list[list[int]] = []
    total_fields = 0
    total_field_bytes = 0
    max_fields = 0
    separator_bytes = row_count - 1
    for _ in range(row_count):
        field_count, pos = _get_varint(encoded, pos)
        if not 1 <= field_count <= MAX_FIELDS_PER_ROW:
            raise RuntimeError("Hierarchical Geometry field count out of bounds")
        total_fields += field_count
        if total_fields > MAX_FIELD_DESCRIPTORS:
            raise RuntimeError("Hierarchical Geometry field-descriptor cap exceeded")
        row_lengths: list[int] = []
        for _ in range(field_count):
            length, pos = _get_varint(encoded, pos)
            if length > G.MAX_CHUNK or total_field_bytes + length > G.MAX_CHUNK:
                raise RuntimeError("Hierarchical Geometry field-length budget exceeded")
            row_lengths.append(length)
            total_field_bytes += length
        lengths.append(row_lengths)
        max_fields = max(max_fields, field_count)
        separator_bytes += field_count - 1

    if row_count * max_fields > MAX_CELL_SCANS:
        raise RuntimeError("Hierarchical Geometry cell-work budget exceeded")
    if total_field_bytes + separator_bytes != logical_size or logical_size > G.MAX_CHUNK:
        raise RuntimeError("Hierarchical Geometry logical-size mismatch")

    prefixes: list[list[int | None]] = [[None] * len(row) for row in lengths]
    if prefix_planes:
        for column in range(max_fields):
            previous_length = 0
            for row_index, row in enumerate(lengths):
                if column >= len(row):
                    continue
                prefix, pos = _get_varint(encoded, pos)
                if prefix > min(previous_length, row[column]):
                    raise RuntimeError("Hierarchical Geometry prefix exceeds neighboring field")
                prefixes[row_index][column] = prefix
                previous_length = row[column]

    rows: list[list[bytes | None]] = [[None] * len(row) for row in lengths]
    cursor = pos
    for column in range(max_fields):
        previous = b""
        for row_index, row in enumerate(lengths):
            if column >= len(row):
                continue
            length = row[column]
            prefix = int(prefixes[row_index][column] or 0)
            suffix_length = length - prefix
            end = cursor + suffix_length
            if end > len(encoded):
                raise RuntimeError("short Hierarchical Geometry payload")
            field = previous[:prefix] + encoded[cursor:end]
            if len(field) != length:
                raise RuntimeError("Hierarchical Geometry field reconstruction mismatch")
            rows[row_index][column] = field
            previous = field
            cursor = end
    if cursor != len(encoded):
        raise RuntimeError("trailing Hierarchical Geometry payload")

    row_bytes = [bytes((secondary,)).join(field for field in row if field is not None) for row in rows]
    raw = bytes((primary,)).join(row_bytes)
    if len(raw) != logical_size:
        raise RuntimeError("Hierarchical Geometry inverse length mismatch")
    return raw


def _compressed_size(raw: bytes, level: int) -> int:
    compressed = G.zc(raw, level)
    return min(len(raw), len(compressed))


def audition(raw: bytes) -> dict:
    """Price bounded hierarchical layouts against direct level-19 storage.

    Candidate pairs are screened cheaply at level 6; only the three best screen results are recompressed
    at level 19.  This is intentional rehabilitation: discovery work is bounded independently of the number
    of possible byte pairs, while the final admission decision still uses the exact target compressor.
    """
    base_codec, base_payload = G._compress_physical(raw)
    best = {
        "kind": "direct",
        "primary": None,
        "secondary": None,
        "prefix_planes": False,
        "physical": raw,
        "codec": base_codec,
        "payload": base_payload,
        "payload_bytes": len(base_payload),
        "saving_bytes": 0,
        "screened_candidates": 0,
        "exact_finalists": 0,
    }
    if len(raw) < MIN_NODE_BYTES:
        return best

    screened: list[tuple[int, int, int, bool, bytes]] = []
    for primary in primary_candidates(raw):
        rows = raw.split(bytes((primary,)))
        for secondary in secondary_candidates(rows, primary):
            for prefix_planes in (False, True):
                try:
                    transformed = hierarchy_forward(raw, primary, secondary, prefix_planes=prefix_planes)
                except ValueError:
                    continue
                if hierarchy_inverse(transformed, len(raw)) != raw:
                    raise RuntimeError("Hierarchical Geometry candidate failed exact inverse")
                screen_bytes = _compressed_size(transformed, SCREEN_LEVEL)
                screened.append((screen_bytes, primary, secondary, prefix_planes, transformed))

    screened.sort(key=lambda row: (row[0], row[3], row[1], row[2]))
    finalists = screened[:MAX_EXACT_FINALISTS]
    for _, primary, secondary, prefix_planes, transformed in finalists:
        codec, payload = G._compress_physical(transformed)
        saving = len(base_payload) - len(payload)
        if saving < MIN_PAYLOAD_SAVING:
            continue
        rank = (len(payload), 0 if prefix_planes else 1, primary, secondary)
        incumbent = (
            best["payload_bytes"],
            0 if best["prefix_planes"] else 1,
            best["primary"] if best["primary"] is not None else 1 << 30,
            best["secondary"] if best["secondary"] is not None else 1 << 30,
        )
        if rank < incumbent:
            best = {
                "kind": "hierarchical",
                "primary": primary,
                "secondary": secondary,
                "prefix_planes": prefix_planes,
                "physical": transformed,
                "codec": codec,
                "payload": payload,
                "payload_bytes": len(payload),
                "saving_bytes": saving,
                "screened_candidates": len(screened),
                "exact_finalists": len(finalists),
            }
    best["screened_candidates"] = len(screened)
    best["exact_finalists"] = len(finalists)
    return best


RESOURCE_LIMITS = {
    "max_rows": MAX_ROWS,
    "max_fields_per_row": MAX_FIELDS_PER_ROW,
    "max_field_descriptors": MAX_FIELD_DESCRIPTORS,
    "max_cell_scans": MAX_CELL_SCANS,
    "max_exact_finalists": MAX_EXACT_FINALISTS,
    "screen_level": SCREEN_LEVEL,
    "exact_level": EXACT_LEVEL,
}
