from __future__ import annotations

import pytest

from benchmarks.one.one_genesis_historical_metric_normalization import (
    normalize_missing_v029_selective_surface,
    normalize_v030_read_member_stats,
)


def test_v030_r24_unknown_decode_context_is_unavailable_not_zero():
    row = normalize_v030_read_member_stats(
        {
            "archive_version": 24,
            "stored_bytes": 1234,
            "member_stored_bytes": 321,
            "decoded_context_bytes": None,
            "amplification": None,
            "note": "r24 baseline has no authenticated selective leaf metadata; instrument cold read separately or use the historical read-amplification artifact",
        },
        requested_bytes=4096,
    )
    assert row["status"] == "unavailable"
    assert row["observed"]["decoded_context_bytes"] is None
    assert row["observed"]["amplification"] is None
    assert 0 not in (row["observed"]["decoded_context_bytes"], row["observed"]["amplification"])


def test_v030_measured_selective_stats_preserve_true_amplification():
    row = normalize_v030_read_member_stats(
        {
            "archive_version": 25,
            "stored_bytes": 10000,
            "member_stored_bytes": 5000,
            "decoded_context_bytes": 8192,
            "amplification": 2.0,
        },
        requested_bytes=4096,
    )
    assert row == {
        "measured": True,
        "requested_bytes": 4096,
        "decoded_context_bytes": 8192,
        "amplification": 2.0,
        "archive_version": 25,
        "stored_bytes": 10000,
        "member_stored_bytes": 5000,
    }


def test_v030_contradictory_amplification_fails_closed():
    with pytest.raises(ValueError, match="contradicts"):
        normalize_v030_read_member_stats(
            {"decoded_context_bytes": 8192, "amplification": 1.0},
            requested_bytes=4096,
        )


def test_v030_negative_or_boolean_resource_values_fail_closed():
    with pytest.raises(ValueError):
        normalize_v030_read_member_stats(
            {"decoded_context_bytes": -1, "amplification": 0.0}, requested_bytes=4096
        )
    with pytest.raises(ValueError):
        normalize_v030_read_member_stats(
            {"decoded_context_bytes": True, "amplification": 0.0}, requested_bytes=4096
        )


def test_v029_absent_surface_is_explicitly_unavailable():
    row = normalize_missing_v029_selective_surface()
    assert row["status"] == "unavailable"
    assert "not zero-cost" in row["reason"]
