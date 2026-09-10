from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from benchmarks.one.one_genesis_gate_executor_preflight import _git_head
from benchmarks.one.one_genesis_gate_measurement_executor import (
    V029_SHA,
    _fixture_output,
    _validate_raw,
    execute,
)


def test_fixture_exercises_three_contender_join_without_scoring(tmp_path: Path):
    head = _git_head()
    result = execute(
        candidate_sha=head,
        raw_dir=tmp_path / "raw",
        now_value="2026-09-10T12:00:00-06:00",
        fixture=True,
        execute_real_gate=False,
        adapters_path=None,
        work_root=None,
    )
    assert result["schema"] == "cmpct-one-genesis-raw-measurements-v1"
    assert result["cmpct1_candidate_sha"] == head
    assert result["gate_open"] is False
    assert result["synthetic"] is True
    assert result["production_eligible"] is False
    assert len(result["workloads"]) == 15
    assert all(set(row["measurements"]) == {"cmpct1", "v0.29", "v0.30"} for row in result["workloads"])
    assert result["execution_state"] == {
        "contender_measurement_executed": False,
        "fixture_plumbing_executed": True,
        "comparisons_executed": False,
        "scoring_executed": False,
        "winner_selected": False,
    }
    for raw in result["raw_files"]:
        assert Path(raw).is_file()


def test_real_execution_is_fail_closed_before_gate(tmp_path: Path):
    head = _git_head()
    with pytest.raises(RuntimeError, match="calendar-locked"):
        execute(
            candidate_sha=head,
            raw_dir=tmp_path / "raw",
            now_value="2026-09-10T23:59:59-06:00",
            fixture=False,
            execute_real_gate=True,
            adapters_path=tmp_path / "adapters.json",
            work_root=tmp_path / "work",
        )


def test_gate_open_does_not_bypass_explicit_real_execution_switch(tmp_path: Path):
    head = _git_head()
    with pytest.raises(RuntimeError, match="explicit --execute-real-gate"):
        execute(
            candidate_sha=head,
            raw_dir=tmp_path / "raw",
            now_value="2026-09-11T00:00:00-06:00",
            fixture=False,
            execute_real_gate=False,
            adapters_path=tmp_path / "adapters.json",
            work_root=tmp_path / "work",
        )


def test_fixture_cannot_smuggle_real_execution_inputs(tmp_path: Path):
    head = _git_head()
    with pytest.raises(RuntimeError, match="fixture mode cannot accept real-execution inputs"):
        execute(
            candidate_sha=head,
            raw_dir=tmp_path / "raw",
            now_value="2026-09-10T12:00:00-06:00",
            fixture=True,
            execute_real_gate=False,
            adapters_path=tmp_path / "adapters.json",
            work_root=None,
        )


def test_raw_identity_drift_fails_closed():
    payload = _fixture_output("v0.29", V029_SHA)
    invalid = deepcopy(payload)
    invalid["rows"][0]["tree_sha256"] = "0" * 64
    with pytest.raises(RuntimeError, match="tree_sha256 differs from frozen identity"):
        _validate_raw(invalid, "v0.29", V029_SHA, synthetic=True)


def test_raw_measurement_family_omission_fails_closed():
    payload = _fixture_output("v0.29", V029_SHA)
    invalid = deepcopy(payload)
    del invalid["rows"][0]["measurement"]["selective_access"]
    with pytest.raises(RuntimeError, match="missing measurement fields"):
        _validate_raw(invalid, "v0.29", V029_SHA, synthetic=True)


def test_synthetic_output_can_never_claim_production_eligibility():
    payload = _fixture_output("v0.29", V029_SHA)
    payload["production_eligible"] = True
    with pytest.raises(RuntimeError, match="production_eligible=false"):
        _validate_raw(payload, "v0.29", V029_SHA, synthetic=True)
