from __future__ import annotations

from copy import deepcopy

import benchmarks.one.one_genesis_gate_result_candidate_binding as mod


def _structurally_valid_payload() -> dict:
    candidate = mod.FROZEN_CANDIDATE_SHA
    return {
        "cmpct1_candidate_sha": candidate,
        "final_adjudication": {"gate_run_source_sha": candidate},
    }


def test_frozen_candidate_binding_accepts_exact_candidate(monkeypatch):
    payload = _structurally_valid_payload()
    monkeypatch.setattr(mod, "validate_gate_result", lambda _payload: type("R", (), {"errors": ()})())
    ok, errors = mod.validate_frozen_candidate_result(payload)
    assert ok is True
    assert errors == ()


def test_frozen_candidate_binding_rejects_candidate_substitution(monkeypatch):
    payload = _structurally_valid_payload()
    payload["cmpct1_candidate_sha"] = "a" * 40
    payload["final_adjudication"]["gate_run_source_sha"] = "a" * 40
    monkeypatch.setattr(mod, "validate_gate_result", lambda _payload: type("R", (), {"errors": ()})())
    ok, errors = mod.validate_frozen_candidate_result(payload)
    assert ok is False
    assert any("cmpct1_candidate_sha differs" in item for item in errors)
    assert any("gate_run_source_sha differs" in item for item in errors)


def test_frozen_candidate_binding_preserves_structural_failures(monkeypatch):
    payload = _structurally_valid_payload()
    monkeypatch.setattr(
        mod,
        "validate_gate_result",
        lambda _payload: type("R", (), {"errors": ("structural failure",)})(),
    )
    ok, errors = mod.validate_frozen_candidate_result(deepcopy(payload))
    assert ok is False
    assert "structural failure" in errors
