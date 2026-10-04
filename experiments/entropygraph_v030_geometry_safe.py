"""Resource-bounded execution facade for the v0.30 Geometry Compiler seed.

The core delimiter representation is byte-bounded, but its straightforward ragged transpose walks a
rectangular `segment_count * max_segment_length` cell space. A hostile authenticated descriptor can make
that rectangle much larger than the logical node even when total declared bytes remain <=512 KiB.

This facade closes that CPU-boundary hole without changing a transform's byte contract or cost model:
writer nomination filters shapes above the budget and the reader rejects them before allocation/work.
Because `entropygraph_v030_geometry` resolves these helpers through module globals, patching the module
here constrains its existing builder/reader paths rather than creating a second grammar.
"""
from __future__ import annotations

from experiments import entropygraph_v030_geometry as geometry

MAX_DELIMITER_CELL_SCANS = 8 * geometry.MAX_CHUNK
_original_rank = geometry._delimiter_rank
_original_forward = geometry.delimiter_forward
_original_inverse = geometry.delimiter_inverse


def _cell_work(raw: bytes, delimiter: int) -> int:
    parts = raw.split(bytes((delimiter,)))
    return len(parts) * max(map(len, parts), default=0)


def _rank(raw: bytes) -> list[int]:
    candidates: list[int] = []
    for delimiter in _original_rank(raw):
        if _cell_work(raw, delimiter) <= MAX_DELIMITER_CELL_SCANS:
            candidates.append(delimiter)
        # Footnote: an over-budget candidate is not malformed user data. It simply loses nomination,
        # preserving direct/lane fallback and preventing a complexity guard from becoming archive failure.
    return candidates


def _forward(raw: bytes, delimiter: int) -> bytes:
    if not 0 <= delimiter <= 255:
        raise ValueError("invalid Geometry delimiter")
    if _cell_work(raw, delimiter) > MAX_DELIMITER_CELL_SCANS:
        raise ValueError("Geometry delimiter transpose exceeds cell-work budget")
    return _original_forward(raw, delimiter)


def _inverse(encoded: bytes, logical_size: int) -> bytes:
    if not encoded.startswith(b"DGT1") or len(encoded) < 6:
        raise RuntimeError("invalid Geometry delimiter magic")
    count, pos = geometry._get_varint(encoded, 5)
    if count < 1 or count > geometry.MAX_DELIMITER_SEGMENTS:
        raise RuntimeError("Geometry delimiter segment count out of bounds")
    lengths: list[int] = []
    total = 0
    for _ in range(count):
        length, pos = geometry._get_varint(encoded, pos)
        if length > geometry.MAX_CHUNK or total + length > geometry.MAX_CHUNK:
            raise RuntimeError("Geometry delimiter length budget exceeded")
        lengths.append(length)
        total += length
    if count * max(lengths, default=0) > MAX_DELIMITER_CELL_SCANS:
        # Footnote: the bound is checked before allocating output rows or entering the rectangular
        # transpose loop, so malicious but checksum-consistent metadata cannot buy unbounded CPU.
        raise RuntimeError("Geometry delimiter transpose exceeds cell-work budget")
    return _original_inverse(encoded, logical_size)


geometry._delimiter_rank = _rank
geometry.delimiter_forward = _forward
geometry.delimiter_inverse = _inverse
geometry.MAX_DELIMITER_CELL_SCANS = MAX_DELIMITER_CELL_SCANS

# Re-export the patched module's research API. These are aliases to the same functions; their global
# delimiter lookups now hit the bounded helpers above.
build = geometry.build
extract = geometry.extract
strong_verify = geometry.strong_verify
treehash = geometry.treehash
MAX_CHUNK = geometry.MAX_CHUNK
MAX_DECODE_UNIT = geometry.MAX_DECODE_UNIT
MAX_DECODER_MEMORY = geometry.MAX_DECODER_MEMORY

if __name__ == "__main__":
    geometry._main()
