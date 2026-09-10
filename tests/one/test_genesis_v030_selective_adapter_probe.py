from __future__ import annotations

import pytest

from benchmarks.one.one_genesis_v030_selective_adapter_probe import validate_member_stats


def test_valid_selective_stats_are_preserved():
    stats = validate_member_stats(
        member_bytes=b"abcdef",
        archive_bytes=100,
        stats={
            "method": "chunked",
            "compressed_bytes_touched": 17,
            "uncompressed_bytes_decoded": 32,
            "chunks_touched": 1,
        },
    )
    assert stats["compressed_bytes_touched"] == 17
    assert stats["uncompressed_bytes_decoded"] == 32


@pytest.mark.parametrize(
    "stats,match",
    [
        ({"method": "chunked", "compressed_bytes_touched": 1, "uncompressed_bytes_decoded": 6}, "missing fields"),
        ({"method": "", "compressed_bytes_touched": 1, "uncompressed_bytes_decoded": 6, "chunks_touched": 1}, "method"),
        ({"method": "chunked", "compressed_bytes_touched": -1, "uncompressed_bytes_decoded": 6, "chunks_touched": 1}, "non-negative"),
        ({"method": "chunked", "compressed_bytes_touched": 1, "uncompressed_bytes_decoded": 5, "chunks_touched": 1}, "smaller"),
        ({"method": "chunked", "compressed_bytes_touched": 101, "uncompressed_bytes_decoded": 6, "chunks_touched": 1}, "exceed"),
        ({"method": "chunked", "compressed_bytes_touched": 1, "uncompressed_bytes_decoded": 6, "chunks_touched": 0}, "one chunk"),
    ],
)
def test_invalid_selective_stats_fail_closed(stats, match):
    with pytest.raises(RuntimeError, match=match):
        validate_member_stats(member_bytes=b"abcdef", archive_bytes=100, stats=stats)


def test_empty_member_may_legitimately_touch_zero_chunks():
    stats = validate_member_stats(
        member_bytes=b"",
        archive_bytes=10,
        stats={
            "method": "empty",
            "compressed_bytes_touched": 0,
            "uncompressed_bytes_decoded": 0,
            "chunks_touched": 0,
        },
    )
    assert stats["chunks_touched"] == 0
