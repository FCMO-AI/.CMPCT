from __future__ import annotations

import pytest

from experiments import entropygraph_v030_geometry as core
from experiments import entropygraph_v030_geometry_safe as safe


def _varint(value: int) -> bytes:
    out = bytearray(); core._put_varint(out, value); return bytes(out)


def test_safe_facade_preserves_golden_delimiter_bytes() -> None:
    raw = b"aa,bb,cc"
    transformed = core.delimiter_forward(raw, ord(","))
    assert transformed == b"DGT1,\x03\x02\x02\x02abcabc"
    assert core.delimiter_inverse(transformed, len(raw)) == raw


def test_inverse_rejects_large_rectangle_before_materialization() -> None:
    # 65,536 logical rows with a 65-byte max row can fit under the 512 KiB declared-byte budget while
    # forcing >4.2 million rectangular cell checks. The safe facade rejects that shape before rows are
    # allocated or the transpose loop starts.
    count = 65_536
    lengths = [65] + [1] * (count - 1)
    logical_size = sum(lengths) + count - 1
    encoded = bytearray(b"DGT1,")
    encoded += _varint(count)
    for length in lengths:
        encoded += _varint(length)
    encoded += b"x" * sum(lengths)
    assert logical_size <= core.MAX_CHUNK
    assert count * max(lengths) > safe.MAX_DELIMITER_CELL_SCANS
    with pytest.raises(RuntimeError, match="cell-work budget"):
        core.delimiter_inverse(bytes(encoded), logical_size)


def test_writer_rejects_excessive_rectangle_as_candidate_not_data() -> None:
    # 510,015 source bytes remain below the inherited node ceiling, yet 16 rows times the 300,000-byte
    # longest row would force 4.8 million cell checks. This attacks CPU amplification without relying on
    # malformed declared sizes.
    parts = [b"A" * 300_000] + [b"B" * 14_000] * 15
    raw = b",".join(parts)
    assert len(raw) <= core.MAX_CHUNK
    assert len(parts) * max(map(len, parts)) > safe.MAX_DELIMITER_CELL_SCANS
    with pytest.raises(ValueError, match="cell-work budget"):
        core.delimiter_forward(raw, ord(","))
