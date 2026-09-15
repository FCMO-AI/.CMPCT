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

# The reviewed bulk-v1 inverse is retained as the fallback/oracle. Its dense-prefix optimization is excellent when
# every segment is non-empty, but one empty/short segment collapses min_len and sends the entire ragged rectangle
# through the historical Python cell loop. The banded arm bulk-copies equal-active-row intervals instead. A cheap
# structural cost guard keeps bulk-v1 when many unique lengths would create too many Python slice operations.
_BULK_V1_DELIMITER_INVERSE = _bulk_delimiter_inverse


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
    for _ in range(count):
        length, pos = O._get_varint(encoded, pos)
        if length > O.MAX_OVERLAY_RECORD or logical_members + length > O.MAX_OVERLAY_RECORD:
            raise RuntimeError("Geometry overlay delimiter length budget")
        lengths.append(length)
        logical_members += length
    if logical_members + count - 1 != logical_size:
        raise RuntimeError("Geometry overlay delimiter logical-size mismatch")
    max_len = max(lengths, default=0)
    cell_scans = count * max_len
    if cell_scans > O.MAX_DELIMITER_CELL_SCANS:
        raise RuntimeError("Geometry overlay delimiter cell-work budget")
    body = encoded[pos:]
    if len(body) != logical_members:
        raise RuntimeError("Geometry overlay delimiter body-size mismatch")

    ends = sorted(set(lengths))
    active_counts = [sum(length >= end for length in lengths) for end in ends if end > 0]
    # Banded work pays one full length scan per distinct positive endpoint plus one strided assignment per active
    # row/band. Require a conservative >=4x reduction in Python-level operations versus the bulk-v1 ragged cell
    # loop; otherwise preserve the reviewed implementation. The fallback re-parses only on shapes for which this
    # arm explicitly declines promotion, keeping worst-case behavior bounded and semantically independent.
    band_python_ops = len(active_counts) * count + sum(active_counts)
    if cell_scans < 64 or band_python_ops * 4 > cell_scans:
        return _BULK_V1_DELIMITER_INVERSE(encoded, logical_size)

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
        active = [index for index, length in enumerate(lengths) if length >= end]
        active_count = len(active)
        band_bytes = active_count * width
        band = body[body_offset : body_offset + band_bytes]
        if len(band) != band_bytes:
            raise RuntimeError("Geometry overlay delimiter band underflow")
        for rank, index in enumerate(active):
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
DELIMITER_INVERSE_FALLBACK = "bulk-rectangular-prefix-v1"
