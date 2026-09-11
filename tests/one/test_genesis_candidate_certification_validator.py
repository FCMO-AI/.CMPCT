from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

import benchmarks.one.one_genesis_candidate_certification_validator as mod


def _certified() -> dict:
    return {
        "schema": "cmpct-one-genesis-one-candidate-boundary-v1",
        "experimental_version": "ONE-G0.2",
        "status": mod.CERTIFIED_STATUS,
        "production_eligible": True,
        "certified_candidate": dict(mod.EXPECTED),
        "genesis_inputs_executed": False,
        "comparison_executed": False,
        "scoring_executed": False,
        "winner_selected": False,
    }


def test_exact_certification_authority_is_accepted_without_execution():
    result = mod.validate_authority(_certified())
    assert result["status"] == "GENESIS_CANDIDATE_CERTIFICATION_EXACT"
    assert result["certified_candidate"] == mod.EXPECTED
    assert result["candidate_checkout_verified"] is False
    assert result["scoring_executed"] is False


@pytest.mark.parametrize("field", list(mod.EXPECTED))
def test_each_certified_identity_field_fails_closed_on_substitution(field: str):
    payload = _certified()
    payload["certified_candidate"][field] = "f" * 40 if field.endswith("sha") else "substituted/path"
    with pytest.raises(RuntimeError, match=field.replace("_", ".") if False else field):
        mod.validate_authority(payload)


def test_hold_authority_is_not_accepted_as_certification():
    payload = _certified()
    payload["status"] = "HOLD_UNTIL_COMPLETE_PRODUCT_BOUNDARY_IS_CERTIFIED"
    with pytest.raises(RuntimeError, match="not CERTIFIED_FOR_GENESIS"):
        mod.validate_authority(payload)


def test_scoring_or_execution_before_certification_validation_fails_closed():
    for field in ("genesis_inputs_executed", "comparison_executed", "scoring_executed", "winner_selected"):
        payload = _certified()
        payload[field] = True
        with pytest.raises(RuntimeError, match=field):
            mod.validate_authority(payload)


def test_candidate_checkout_identity_is_independently_bound(monkeypatch, tmp_path: Path):
    checkout = tmp_path / "candidate"
    checkout.mkdir()
    observed = {
        "HEAD": mod.FROZEN_CANDIDATE_SHA,
        f"HEAD:{mod.CREATOR_PATH}": mod.CREATOR_BLOB_SHA,
        f"HEAD:{mod.READER_PATH}": mod.READER_BLOB_SHA,
        f"HEAD:{mod.RUNTIME_TREE_PATH}": mod.RUNTIME_TREE_SHA,
    }
    monkeypatch.setattr(mod, "_assert_checkout_clean", lambda _checkout: None)
    monkeypatch.setattr(mod, "_git", lambda _checkout, spec: observed[spec])
    result = mod.validate_authority(_certified(), candidate_checkout=checkout)
    assert result["candidate_checkout_verified"] is True
    assert result["candidate_checkout_identity"]["runtime_tree_sha"] == mod.RUNTIME_TREE_SHA


def test_candidate_checkout_runtime_tree_drift_fails_closed(monkeypatch, tmp_path: Path):
    checkout = tmp_path / "candidate"
    checkout.mkdir()
    observed = {
        "HEAD": mod.FROZEN_CANDIDATE_SHA,
        f"HEAD:{mod.CREATOR_PATH}": mod.CREATOR_BLOB_SHA,
        f"HEAD:{mod.READER_PATH}": mod.READER_BLOB_SHA,
        f"HEAD:{mod.RUNTIME_TREE_PATH}": "0" * 40,
    }
    monkeypatch.setattr(mod, "_assert_checkout_clean", lambda _checkout: None)
    monkeypatch.setattr(mod, "_git", lambda _checkout, spec: observed[spec])
    with pytest.raises(RuntimeError, match="runtime_tree_sha differs"):
        mod.validate_authority(_certified(), candidate_checkout=checkout)


def test_candidate_checkout_worktree_drift_fails_closed(monkeypatch, tmp_path: Path):
    checkout = tmp_path / "candidate"
    checkout.mkdir()

    class Result:
        def __init__(self, stdout: str):
            self.stdout = stdout

    monkeypatch.setattr(
        mod.subprocess,
        "run",
        lambda *args, **kwargs: Result(" M experiments/one/general_law_archive.py\n"),
    )
    with pytest.raises(RuntimeError, match="working-tree drift"):
        mod._assert_checkout_clean(checkout)


def test_candidate_checkout_ignored_native_artifact_fails_closed(monkeypatch, tmp_path: Path):
    checkout = tmp_path / "candidate"
    checkout.mkdir()

    class Result:
        def __init__(self, stdout: str):
            self.stdout = stdout

    outputs = iter((Result(""), Result("experiments/one/general_law_archive.so\n")))
    monkeypatch.setattr(mod.subprocess, "run", lambda *args, **kwargs: next(outputs))
    with pytest.raises(RuntimeError, match="ignored native runtime artifacts"):
        mod._assert_checkout_clean(checkout)


def test_candidate_checkout_allows_ignored_bytecode(monkeypatch, tmp_path: Path):
    checkout = tmp_path / "candidate"
    checkout.mkdir()

    class Result:
        def __init__(self, stdout: str):
            self.stdout = stdout

    outputs = iter((Result(""), Result("experiments/one/__pycache__/wire.cpython-312.pyc\n")))
    monkeypatch.setattr(mod.subprocess, "run", lambda *args, **kwargs: next(outputs))
    mod._assert_checkout_clean(checkout)
