from __future__ import annotations

import json

import pytest

import benchmarks.one.one_genesis_certified_adapter as mod


def _boundary(tmp_path, *, status=mod.CERTIFIED_STATUS, eligible=True, candidate="a" * 40):
    path = tmp_path / "boundary.json"
    path.write_text(
        json.dumps(
            {
                "schema": "cmpct-one-genesis-one-candidate-boundary-v1",
                "status": status,
                "production_eligible": eligible,
                "certified_candidate": {"candidate_sha": candidate},
            }
        ),
        encoding="utf-8",
    )
    return path


def test_cmpct1_matching_certification_routes_frozen_runtime_then_delegates(monkeypatch, tmp_path):
    monkeypatch.setattr(mod, "BOUNDARY", _boundary(tmp_path))
    monkeypatch.setenv("CMPCT_GENESIS_REAL_GATE_AUTHORIZED", "1")
    monkeypatch.setenv("CMPCT_GENESIS_CONTENDER", "cmpct1")
    monkeypatch.setenv("CMPCT_GENESIS_SOURCE_SHA", "a" * 40)
    expected = {"schema": "cmpct-one-genesis-contender-raw-v1", "rows": [], "scoring_executed": False}
    routed = []
    monkeypatch.setattr(mod, "_route_cmpct1_worker_to_frozen_checkout", lambda: routed.append(True))
    monkeypatch.setattr(mod, "run_raw_adapter", lambda: expected)
    assert mod.run() is expected
    assert routed == [True]


def test_cmpct1_candidate_sha_substitution_fails_closed(monkeypatch, tmp_path):
    monkeypatch.setattr(mod, "BOUNDARY", _boundary(tmp_path, candidate="a" * 40))
    monkeypatch.setenv("CMPCT_GENESIS_REAL_GATE_AUTHORIZED", "1")
    monkeypatch.setenv("CMPCT_GENESIS_CONTENDER", "cmpct1")
    monkeypatch.setenv("CMPCT_GENESIS_SOURCE_SHA", "b" * 40)
    monkeypatch.setattr(mod, "run_raw_adapter", lambda: pytest.fail("raw adapter must not execute"))
    with pytest.raises(RuntimeError, match="certified candidate SHA differs"):
        mod.run()


def test_cmpct1_hold_boundary_fails_closed(monkeypatch, tmp_path):
    monkeypatch.setattr(mod, "BOUNDARY", _boundary(tmp_path, status="HOLD_UNTIL_COMPLETE_PRODUCT_BOUNDARY_IS_CERTIFIED"))
    monkeypatch.setenv("CMPCT_GENESIS_REAL_GATE_AUTHORIZED", "1")
    monkeypatch.setenv("CMPCT_GENESIS_CONTENDER", "cmpct1")
    monkeypatch.setenv("CMPCT_GENESIS_SOURCE_SHA", "a" * 40)
    monkeypatch.setattr(mod, "run_raw_adapter", lambda: pytest.fail("raw adapter must not execute"))
    with pytest.raises(RuntimeError, match="not certified"):
        mod.run()


def test_cmpct1_noneligible_boundary_fails_closed(monkeypatch, tmp_path):
    monkeypatch.setattr(mod, "BOUNDARY", _boundary(tmp_path, eligible=False))
    monkeypatch.setenv("CMPCT_GENESIS_REAL_GATE_AUTHORIZED", "1")
    monkeypatch.setenv("CMPCT_GENESIS_CONTENDER", "cmpct1")
    monkeypatch.setenv("CMPCT_GENESIS_SOURCE_SHA", "a" * 40)
    monkeypatch.setattr(mod, "run_raw_adapter", lambda: pytest.fail("raw adapter must not execute"))
    with pytest.raises(RuntimeError, match="not certified"):
        mod.run()


def test_missing_explicit_executor_authorization_fails_closed(monkeypatch, tmp_path):
    monkeypatch.setattr(mod, "BOUNDARY", _boundary(tmp_path))
    monkeypatch.delenv("CMPCT_GENESIS_REAL_GATE_AUTHORIZED", raising=False)
    monkeypatch.setenv("CMPCT_GENESIS_CONTENDER", "cmpct1")
    monkeypatch.setenv("CMPCT_GENESIS_SOURCE_SHA", "a" * 40)
    monkeypatch.setattr(mod, "run_raw_adapter", lambda: pytest.fail("raw adapter must not execute"))
    with pytest.raises(RuntimeError, match="explicit real-gate"):
        mod.run()


def test_frozen_comparator_does_not_consume_one_candidate_boundary_or_route_one_worker(monkeypatch, tmp_path):
    monkeypatch.setattr(mod, "BOUNDARY", _boundary(tmp_path, status="HOLD_UNTIL_COMPLETE_PRODUCT_BOUNDARY_IS_CERTIFIED"))
    monkeypatch.setenv("CMPCT_GENESIS_REAL_GATE_AUTHORIZED", "1")
    monkeypatch.setenv("CMPCT_GENESIS_CONTENDER", "v0.29")
    monkeypatch.setenv("CMPCT_GENESIS_SOURCE_SHA", "c" * 40)
    expected = {"schema": "cmpct-one-genesis-contender-raw-v1", "rows": [], "scoring_executed": False}
    monkeypatch.setattr(mod, "_route_cmpct1_worker_to_frozen_checkout", lambda: pytest.fail("comparator must not route CMPCT1 worker"))
    monkeypatch.setattr(mod, "run_raw_adapter", lambda: expected)
    assert mod.run() is expected
