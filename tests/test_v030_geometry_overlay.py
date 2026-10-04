from __future__ import annotations

import binascii
import pytest

from experiments import entropygraph_v030_geometry_overlay as overlay
from experiments import entropygraph_v030_geometry_overlay_strict as strict


def _record(raw: bytes):
    codec, payload = overlay.A5._compress_record(raw, 19)
    return (codec, len(raw), payload, binascii.crc32(raw) & 0xFFFFFFFF, overlay.H(raw))


def test_lane_golden_vector_matches_lattice_contract() -> None:
    raw = b"abcdefghijklmnop"
    transformed = overlay.lane_forward(raw, 4)
    assert transformed == b"aeimbfjncgkodhlp"
    assert overlay.lane_inverse(transformed, 4, len(raw)) == raw


def test_delimiter_overlay_round_trips_large_record() -> None:
    raw = b"tenant=17,status=active,value=123456789\n" * 20000
    assert 512 * 1024 < len(raw) < overlay.MAX_OVERLAY_RECORD
    transformed = overlay.delimiter_forward(raw, ord("\n"))
    assert overlay.delimiter_inverse(transformed, len(raw)) == raw


def test_over_eight_x_member_record_is_never_transformed() -> None:
    raw = b"row,with,very,regular,structure\n" * 5000
    original = _record(raw)
    chosen, transform, stats = overlay._audition_record(0, original, [1024])
    assert len(raw) / 1024 > overlay.MAX_MEMBER_READ_AMP
    assert chosen == original
    assert transform is None
    assert stats["selected"] == "none"


def test_strict_facade_resolves_hidden_placement_constants() -> None:
    assert strict._storage_attr(strict.A4, "TAIL") == strict.A4.IMPL.TAIL
    assert strict._storage_attr(strict.A4, "MAX_DECODE_UNIT") == strict.A4.IMPL.MAX_DECODE_UNIT
    assert strict._storage_attr(strict.A4, "MAX_DECODER_MEMORY") == strict.A4.IMPL.MAX_DECODER_MEMORY
