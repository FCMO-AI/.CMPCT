from __future__ import annotations
import importlib.util, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("discovery_claims",ROOT/"tools"/"discovery_claims.py")
assert SPEC and SPEC.loader
mod=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(mod)

def test_unresolved_predictions_only():
    rows=[
      {"id":"E1","event":"prediction","family":"proof"},
      {"id":"E2","event":"prediction","family":"layout"},
      {"id":"E1","event":"outcome","family":"proof"},
    ]
    assert [x["id"] for x in mod.unresolved(rows)]==["E2"]

def test_candidates_include_state_and_unresolved():
    state={"primary_question":{"id":"P","family":"runtime","hypothesis":"avoid loser work","status":"READY"},
           "frontier_candidates":[{"id":"F","family":"representation","question":"new relation","status":"QUEUED"}]}
    rows=[{"id":"E","event":"prediction","family":"proof","problem":"bound","hypothesis":"early reject"}]
    got=mod.candidates(state,rows)
    assert {x["id"] for x in got}=={"P","F","E"}
    assert any(x["source"]=="ledger:unresolved" for x in got)
