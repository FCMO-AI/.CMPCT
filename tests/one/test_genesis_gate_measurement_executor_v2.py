from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from benchmarks.one.one_genesis_gate_executor_preflight import _git_head
from benchmarks.one import one_genesis_gate_measurement_executor as v1
from benchmarks.one.one_genesis_gate_measurement_executor_v2 import execute
from benchmarks.one.one_genesis_physical_seal_identity import scientific_identity_receipt


def _fake_seal(work_root: Path) -> dict:
    return {
        "schema": "cmpct-one-genesis-physical-input-seal-v1",
        "claim_boundary": "test seal",
        "all_15_identities_exact": True,
        "work_root": str(work_root.resolve()),
        "rows": deepcopy(v1._identity_rows()),
    }


def test_fixture_remains_non_evidence_and_executes_no_scientific_seal(tmp_path: Path):
    result = execute(
        candidate_sha=_git_head(),
        raw_dir=tmp_path / "raw",
        now_value="2026-09-10T12:00:00-06:00",
        fixture=True,
        execute_real_gate=False,
        adapters_path=None,
        work_root=None,
    )
    assert result["schema"] == "cmpct-one-genesis-raw-measurements-v1"
    assert result["evidence_contract"] == "portable-physical-input-identity-v2"
    assert result["production_eligible"] is False
    assert result["physical_input_seal"] == {"status": "not-executed-in-fixture"}
    assert result["execution_state"]["scientific_input_identity_executed"] is False
    assert result["execution_state"]["contender_measurement_executed"] is False
    assert result["execution_state"]["scoring_executed"] is False


def test_scientific_identity_ignores_runner_root_but_diagnostic_file_does_not(tmp_path: Path):
    first = _fake_seal(tmp_path / "runner-a")
    second = _fake_seal(tmp_path / "runner-b")
    a = scientific_identity_receipt(first)
    b = scientific_identity_receipt(second)
    assert a["scientific_identity_sha256"] == b["scientific_identity_sha256"]
    assert first["work_root"] != second["work_root"]


def test_scientific_identity_changes_when_exam_tree_changes(tmp_path: Path):
    first = _fake_seal(tmp_path / "runner-a")
    second = deepcopy(first)
    second["rows"][0]["tree_sha256"] = "0" * 64
    a = scientific_identity_receipt(first)
    b = scientific_identity_receipt(second)
    assert a["scientific_identity_sha256"] != b["scientific_identity_sha256"]


def test_real_path_persists_scientific_identity_before_first_adapter(monkeypatch, tmp_path: Path):
    head = _git_head()
    work_root = tmp_path / "physical"
    adapters = tmp_path / "adapters.json"
    adapters.write_text(
        '{"schema":"cmpct-one-genesis-adapters-v1","adapters":{'
        '"cmpct1":{"checkout":"x","command":["x"]},'
        '"v0.29":{"checkout":"x","command":["x"]},'
        '"v0.30":{"checkout":"x","command":["x"]}}}',
        encoding="utf-8",
    )
    monkeypatch.setattr(v1, "_seal_physical_inputs", lambda root: _fake_seal(root))
    monkeypatch.setattr(v1, "_assert_physical_inputs_unchanged", lambda root: None)

    calls: list[str] = []

    def fake_adapter(contender, source_sha, adapter, root, output_path):
        scientific = tmp_path / "raw" / "physical-input-scientific-identity.json"
        assert scientific.is_file(), "portable identity must exist before the first contender starts"
        calls.append(contender)
        payload = v1._fixture_output(contender, source_sha)
        payload["synthetic"] = False
        payload["production_eligible"] = True
        v1._write(output_path, payload)
        return payload

    monkeypatch.setattr(v1, "_adapter_output", fake_adapter)
    result = execute(
        candidate_sha=head,
        raw_dir=tmp_path / "raw",
        now_value="2026-09-11T00:00:00-06:00",
        fixture=False,
        execute_real_gate=True,
        adapters_path=adapters,
        work_root=work_root,
    )
    assert calls == ["cmpct1", "v0.29", "v0.30"]
    seal = result["physical_input_seal"]
    assert seal["sha256"].startswith("sha256:")
    assert seal["scientific_identity_sha256"].startswith("sha256:")
    assert seal["sha256_semantics"].startswith("diagnostic-file-receipt-only")
    assert "authoritative cross-run identity" in seal["scientific_identity_semantics"]
    assert result["execution_state"]["scientific_input_identity_executed"] is True
    assert result["execution_state"]["scoring_executed"] is False


def test_real_gate_remains_calendar_locked(tmp_path: Path):
    with pytest.raises(RuntimeError, match="calendar-locked"):
        execute(
            candidate_sha=_git_head(),
            raw_dir=tmp_path / "raw",
            now_value="2026-09-10T23:59:59-06:00",
            fixture=False,
            execute_real_gate=True,
            adapters_path=tmp_path / "adapters.json",
            work_root=tmp_path / "work",
        )
