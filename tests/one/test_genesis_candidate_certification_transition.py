from __future__ import annotations

from pathlib import Path

import pytest

import benchmarks.one.one_genesis_candidate_certification_transition as mod


def _hold() -> dict:
    return {
        "schema": "cmpct-one-genesis-one-candidate-boundary-v1",
        "experimental_version": "ONE-G0.2",
        "status": mod.HOLD_STATUS,
        "genesis_inputs_executed": False,
        "comparison_executed": False,
        "scoring_executed": False,
        "winner_selected": False,
    }


def test_transition_is_calendar_locked_before_september_11(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(mod, "_validate_checkout", lambda _checkout: pytest.fail("checkout must not be consulted pre-boundary"))
    with pytest.raises(RuntimeError, match="calendar-locked"):
        mod.certify(
            _hold(),
            candidate_checkout=tmp_path,
            now_value="2026-09-10T23:59:59-06:00",
        )


def test_exact_post_boundary_transition_changes_only_certification_state(monkeypatch, tmp_path: Path):
    payload = _hold()
    payload["authorities"] = {"canon": "kept"}
    seen = []
    monkeypatch.setattr(mod, "_validate_checkout", lambda checkout: seen.append(("checkout", checkout)))
    monkeypatch.setattr(mod, "validate_authority", lambda result, candidate_checkout=None: seen.append(("authority", result, candidate_checkout)))
    result = mod.certify(
        payload,
        candidate_checkout=tmp_path,
        now_value="2026-09-11T00:00:00-06:00",
    )
    assert result is not payload
    assert payload["status"] == mod.HOLD_STATUS
    assert "certified_candidate" not in payload
    assert result["status"] == mod.CERTIFIED_STATUS
    assert result["production_eligible"] is True
    assert result["certified_candidate"] == mod.EXPECTED
    assert result["authorities"] == {"canon": "kept"}
    assert result["genesis_inputs_executed"] is False
    assert result["comparison_executed"] is False
    assert result["scoring_executed"] is False
    assert result["winner_selected"] is False
    assert seen[0] == ("checkout", tmp_path)
    assert seen[1][0] == "authority"


def test_transition_rejects_non_hold_or_preexisting_certification(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(mod, "_validate_checkout", lambda _checkout: None)
    monkeypatch.setattr(mod, "validate_authority", lambda *args, **kwargs: None)

    wrong = _hold()
    wrong["status"] = mod.CERTIFIED_STATUS
    with pytest.raises(RuntimeError, match="not the pre-certification HOLD"):
        mod.certify(wrong, candidate_checkout=tmp_path, now_value="2026-09-11T00:00:00-06:00")

    already = _hold()
    already["certified_candidate"] = dict(mod.EXPECTED)
    with pytest.raises(RuntimeError, match="already contains certification state"):
        mod.certify(already, candidate_checkout=tmp_path, now_value="2026-09-11T00:00:00-06:00")


def test_transition_rejects_any_prior_execution_flag(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(mod, "_validate_checkout", lambda _checkout: None)
    for field in ("genesis_inputs_executed", "comparison_executed", "scoring_executed", "winner_selected"):
        payload = _hold()
        payload[field] = True
        with pytest.raises(RuntimeError, match=field):
            mod.certify(payload, candidate_checkout=tmp_path, now_value="2026-09-11T00:00:00-06:00")
