from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("discovery_ledger", ROOT / "tools" / "discovery_ledger.py")
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


def test_empty_canonical_ledger_is_valid():
    rows = mod.load(ROOT / "research" / "discovery_episodes.jsonl")
    predictions, outcomes, lessons, unresolved = mod.audit(rows)
    assert predictions == {}
    assert dict(outcomes) == {}
    assert lessons == []
    assert unresolved == []


def test_prediction_outcome_round_trip(tmp_path):
    path = tmp_path / "episodes.jsonl"
    prediction = {
        "id": "E1", "event": "prediction", "timestamp": "2026-09-18T00:00:00Z",
        "family": "example", "start_commit": "abc", "problem": "p", "hypothesis": "h",
        "control": "c", "alternative": "a", "prediction": "x", "kill_condition": "k",
        "decision_unlocked": "d"
    }
    outcome = {
        "id": "E1", "event": "outcome", "timestamp": "2026-09-18T00:01:00Z",
        "family": "example", "disposition": "falsified", "decisive": True,
        "classification": "science", "observation": "not x", "next_action": "retire"
    }
    path.write_text(json.dumps(prediction) + "\n" + json.dumps(outcome) + "\n", encoding="utf-8")
    rows = mod.load(path)
    predictions, outcomes, _, unresolved = mod.audit(rows)
    assert list(predictions) == ["E1"]
    assert outcomes["E1"][0]["decisive"] is True
    assert unresolved == []
