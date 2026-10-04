from __future__ import annotations

import pytest

from benchmarks import v030_eg08_low_effort_composed_oracle as O


def test_capture_single_expansion_telemetry_preserves_candidate_result(monkeypatch):
    expected = {"compact_expansion_passes": 1, "sentinel": "unchanged"}

    def fake_candidate(*_args, **_kwargs):
        return dict(expected)

    monkeypatch.setattr(O.V6, "_candidate_once", fake_candidate)
    observed: list[int] = []
    with O._capture_single_expansion_telemetry(observed):
        assert O.V6._candidate_once(None) == expected

    assert observed == [1]


def test_capture_single_expansion_telemetry_fails_closed_when_owner_omits_evidence(monkeypatch):
    def fake_candidate(*_args, **_kwargs):
        return {"sentinel": "missing-telemetry"}

    monkeypatch.setattr(O.V6, "_candidate_once", fake_candidate)
    observed: list[int] = []
    with O._capture_single_expansion_telemetry(observed):
        with pytest.raises(RuntimeError, match="omitted compact-expansion telemetry"):
            O.V6._candidate_once(None)

    assert observed == []
