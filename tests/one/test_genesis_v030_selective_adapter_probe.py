from __future__ import annotations

import pytest

from benchmarks.one.one_genesis_v030_selective_adapter_probe import normalize_member_stats


def test_directly_measured_locality_is_checked_and_preserved():
    stats = normalize_member_stats(
        member_bytes=b"abcdef",
        stats={
            "logical_bytes": 6,
            "decoded_context_bytes": 12,
            "decoded_context_amplification": 2.0,
            "format_profile": "test",
        },
    )
    assert stats["locality_measurement_state"] == "directly-measured"
    assert stats["decoded_context_bytes"] == 12


def test_historical_unavailable_locality_is_preserved_as_unavailable_not_zero():
    stats = normalize_member_stats(
        member_bytes=b"abcdef",
        stats={
            "logical_bytes": 6,
            "decoded_context_bytes": None,
            "decoded_context_amplification": None,
            "format_profile": "canonical-r24",
            "locality_accounting": "instrument-at-operation-or-inherited-r24-evidence",
        },
    )
    assert stats["locality_measurement_state"] == "external-instrumentation-required"
    assert stats["decoded_context_bytes"] is None
    assert stats["decoded_context_amplification"] is None


@pytest.mark.parametrize(
    "stats,match",
    [
        ({"logical_bytes": 5, "decoded_context_bytes": 6, "decoded_context_amplification": 1.0}, "logical_bytes"),
        ({"logical_bytes": 6, "decoded_context_bytes": None, "decoded_context_amplification": 1.0}, "cannot be measured"),
        ({"logical_bytes": 6, "decoded_context_bytes": 5, "decoded_context_amplification": 0.8}, "cover"),
        ({"logical_bytes": 6, "decoded_context_bytes": 12, "decoded_context_amplification": -1.0}, "non-negative"),
        ({"logical_bytes": 6, "decoded_context_bytes": 12, "decoded_context_amplification": 1.9}, "inconsistent"),
    ],
)
def test_invalid_selective_stats_fail_closed(stats, match):
    with pytest.raises(RuntimeError, match=match):
        normalize_member_stats(member_bytes=b"abcdef", stats=stats)


def test_empty_member_allows_zero_direct_context():
    stats = normalize_member_stats(
        member_bytes=b"",
        stats={
            "logical_bytes": 0,
            "decoded_context_bytes": 0,
            "decoded_context_amplification": 0.0,
        },
    )
    assert stats["locality_measurement_state"] == "directly-measured"
