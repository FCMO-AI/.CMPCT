"""Canonical v0.30 execution wrapper with a guarded banded DGO1 inverse.

The reviewed canonical wrapper body is retained byte-for-byte in
``entropygraph_v030_canonical_final_bulk_v1.py`` and executed in this module's namespace. This preserves the
existing public monkeypatch/global-resolution contract while allowing one reader-only memory-movement optimization
to be isolated and reverted independently. Archive grammar, writer bytes, admission, locality and release policy are
unchanged.
"""
from __future__ import annotations

from pathlib import Path

_REVIEWED_WRAPPER = Path(__file__).with_name("entropygraph_v030_canonical_final_bulk_v1.py")
_REVIEWED_SOURCE = _REVIEWED_WRAPPER.read_bytes()
exec(compile(_REVIEWED_SOURCE, str(_REVIEWED_WRAPPER), "exec"), globals(), globals())

# The reviewed bulk-v1 inverse is retained as the semantic oracle. Its dense-prefix optimization is excellent when
# every segment is non-empty, but one empty/short segment collapses min_len and sends the remaining ragged rectangle
# through the historical Python cell loop. The banded arm bulk-copies equal-active-row intervals instead. A cheap
# structural cost guard keeps the reviewed reconstruction shape when many unique lengths would create too many
# Python slice operations.
_BULK_V1_DELIMITER_INVERSE = _bulk_delimiter_inverse


def _bulk_from_parsed(delimiter: int, lengths: list[int], body: bytes) -> bytes:
    """Reviewed bulk-v1 reconstruction using an already validated descriptor parse."""
    count = len(lengths)
    parts = [bytearray(length) for length in lengths]
    body_offset = 0
    min_len = min(lengths, default=0)
    if min_len:
        dense_bytes = count * min_len
        dense = body[:dense_bytes]
        if len(dense) != dense_bytes:
            raise RuntimeError("Geometry overlay delimiter dense-prefix underflow")
        for index, part in enumerate(parts):
            part[:min_len] = dense[index::count]
        body_offset = dense_bytes
    max_len = max(lengths, default=0)
    for column in range(min_len, max_len):
        for index, length in enumerate(lengths):
            if column < length:
                if body_offset >= len(body):
                    raise RuntimeError("Geometry overlay delimiter body underflow")
                parts[index][column] = body[body_offset]
                body_offset += 1
    if body_offset != len(body):
        raise RuntimeError("Geometry overlay delimiter trailing body")
    return bytes([delimiter]).join(bytes(part) for part in parts)


def _banded_delimiter_inverse(encoded: bytes, logical_size: int) -> bytes:
    O = SHARED.G.O
    if (
        not encoded.startswith(b"DGO1")
        or len(encoded) < 6
        or logical_size < 0
        or logical_size > O.MAX_OVERLAY_RECORD
    ):
        raise RuntimeError("invalid Geometry overlay delimiter descriptor")
    delimiter = encoded[4]
    count, pos = O._get_varint(encoded, 5)
    if count < 1 or count > O.MAX_DELIMITER_SEGMENTS:
        raise RuntimeError("Geometry overlay delimiter segment count")

    lengths: list[int] = []
    logical_members = 0
    length_counts: dict[int, int] = {}
    for _ in range(count):
        length, pos = O._get_varint(encoded, pos)
        if length > O.MAX_OVERLAY_RECORD or logical_members + length > O.MAX_OVERLAY_RECORD:
            raise RuntimeError("Geometry overlay delimiter length budget")
        lengths.append(length)
        logical_members += length
        length_counts[length] = length_counts.get(length, 0) + 1
    if logical_members + count - 1 != logical_size:
        raise RuntimeError("Geometry overlay delimiter logical-size mismatch")
    max_len = max(length_counts, default=0)
    cell_scans = count * max_len
    if cell_scans > O.MAX_DELIMITER_CELL_SCANS:
        raise RuntimeError("Geometry overlay delimiter cell-work budget")
    body = encoded[pos:]
    if len(body) != logical_members:
        raise RuntimeError("Geometry overlay delimiter body-size mismatch")

    ends = sorted(length_counts)
    active = count - length_counts.get(0, 0)
    active_counts: list[int] = []
    for end in ends:
        if end <= 0:
            continue
        active_counts.append(active)
        active -= length_counts[end]
    # Banded work pays one full length scan per distinct positive endpoint plus one strided assignment per active
    # row/band. Compute the guard from the histogram so a rejected high-cardinality shape does not itself pay the
    # O(unique_lengths * count) scan we are trying to avoid. Require a conservative >=4x reduction in estimated
    # Python-level operations versus the bulk-v1 ragged cell loop.
    band_python_ops = len(active_counts) * count + sum(active_counts)
    if cell_scans < 64 or band_python_ops * 4 > cell_scans:
        return _bulk_from_parsed(delimiter, lengths, body)

    starts: list[int] = []
    cursor = 0
    for index, length in enumerate(lengths):
        starts.append(cursor)
        cursor += length + (1 if index + 1 < count else 0)
    if cursor != logical_size:
        raise RuntimeError("Geometry overlay delimiter output-size mismatch")
    out = bytearray(logical_size)
    for index in range(count - 1):
        out[starts[index] + lengths[index]] = delimiter

    body_offset = 0
    previous = 0
    for end in ends:
        width = end - previous
        if width <= 0:
            continue
        active_indices = [index for index, length in enumerate(lengths) if length >= end]
        active_count = len(active_indices)
        band_bytes = active_count * width
        band = body[body_offset : body_offset + band_bytes]
        if len(band) != band_bytes:
            raise RuntimeError("Geometry overlay delimiter band underflow")
        for rank, index in enumerate(active_indices):
            out[starts[index] + previous : starts[index] + end] = band[rank::active_count]
        body_offset += band_bytes
        previous = end
    if body_offset != len(body):
        raise RuntimeError("Geometry overlay delimiter trailing body")
    return bytes(out)


SHARED.G.O.delimiter_inverse = _banded_delimiter_inverse
if getattr(POLICY.R.G04, "O", None) is not None:
    POLICY.R.G04.O.delimiter_inverse = _banded_delimiter_inverse

DELIMITER_INVERSE_IMPLEMENTATION = "guarded-banded-v2"
DELIMITER_INVERSE_FALLBACK = "bulk-rectangular-prefix-v1-parsed"
