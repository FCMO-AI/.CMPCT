"""Resource-bounded execution facade for the v0.30 Geometry Compiler seed.

The core delimiter representation is byte-bounded, but its straightforward ragged transpose walks a
rectangular `segment_count * max_segment_length` cell space.  A hostile authenticated descriptor can make
that rectangle much larger than the logical node even when total declared bytes remain <=512 KiB.

This facade closes that CPU-boundary hole without changing a transform's byte contract or cost model:
both writer and reader reject delimiter geometries whose cell work exceeds 8x the inherited logical-node
ceiling.  Because `entropygraph_v030_geometry` resolves these helpers through module globals, patching the
module here also constrains its existing builder/reader paths rather than creating a second grammar.
"""
from __future__ import annotations

from experiments import entropygraph_v030_geometry as geometry

MAX_DELIMITER_CELL_SCANS = 8 * geometry.MAX_CHUNK
_original_forward = geometry.delimiter_forward
_original_inverse = geometry.delimiter_inverse


def _forward(raw: bytes, delimiter: int) -> bytes:
    if not 0 <= delimiter <= 255:
        raise ValueError("invalid Geometry delimiter")
    parts = raw.split(bytes((delimiter,)))
    max_length = max(map(len, parts), default=0)
    if len(parts) * max_length > MAX_DELIMITER_CELL_SCANS:
        # Footnote: this is a transform candidate, not user data rejection.  The encoder simply keeps
        # direct/lane storage when ragged geometry would export excessive CPU work.
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


geometry.delimiter_forward = _forward
geometry.delimiter_inverse = _inverse
geometry.MAX_DELIMITER_CELL_SCANS = MAX_DELIMITER_CELL_SCANS

# Re-export the patched module's research API.  These are aliases to the same functions; their global
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
