from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "docs" / "discovery" / "STATE.json"


def test_discovery_state_has_dependency_diverse_backup():
    data = json.loads(STATE.read_text(encoding="utf-8"))
    primary = data["primary_question"]
    backup = data["backup_question"]
    assert primary["id"] != backup["id"]
    assert primary["family"] != backup["family"]
    assert primary["status"] in {"READY", "RUNNING", "AMBIGUOUS"}
    assert backup["status"] == "READY"


def test_frontier_does_not_duplicate_primary_or_backup():
    data = json.loads(STATE.read_text(encoding="utf-8"))
    reserved = {data["primary_question"]["id"], data["backup_question"]["id"]}
    ids = [item["id"] for item in data["frontier_candidates"]]
    assert not reserved.intersection(ids)
    assert len(ids) == len(set(ids))


def test_cdr_adapter_is_local_projection_not_authority():
    adapter = json.loads((ROOT / "docs" / "discovery" / "CDR_ADAPTER.json").read_text(encoding="utf-8"))
    assert adapter["admission"] == "FULL"
    assert adapter["capabilities"]["executable_frontier"] == "LOCAL"
    assert adapter["surfaces"]["frontier"] == "docs/discovery/STATE.json"
    assert adapter["local_precedence"][0] == "repository/release/frozen law"
