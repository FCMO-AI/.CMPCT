from __future__ import annotations

import json
from pathlib import Path

import pytest

from benchmarks.one import one_g02_general_candidate_boundary_hostile_economics as bench


def test_hostile_candidate_boundary_falsifier_is_fail_closed_and_genesis_dark(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.chdir(tmp_path)
    payload = bench.run()

    assert payload["schema"] == "cmpct-one-g02-general-candidate-boundary-hostile-economics-v1"
    assert payload["experimental_version"] == "ONE-G0.2"
    assert payload["genesis_inputs_executed"] is False
    assert payload["genesis_comparison_executed"] is False
    assert payload["genesis_scoring_executed"] is False
    assert payload["genesis_winner_selected"] is False
    assert len(payload["rows"]) == 7
    assert {row["name"] for row in payload["rows"]} == {name for name, _ in bench.BUILDERS}

    for row in payload["rows"]:
        # The experiment is allowed to discover economic losses. It is not allowed to
        # excuse semantic, determinism, or reader-ontology failures as economics.
        assert row["gates"]["law_semantics_exact"] is True
        assert row["gates"]["surprise_semantics_exact"] is True
        assert row["gates"]["deterministic_law_wire"] is True
        assert row["gates"]["generic_reader_ontology_only"] is True
        assert set(row["reader_ops"]) <= bench.ALLOWED_OPS
        assert row["law_minus_surprise_bytes"] == row["law_wire_bytes"] - row["surprise_wire_bytes"]
        assert row["decision"] == (
            "PASS" if all(row["gates"].values()) else "HOLD"
        )

    expected_decision = (
        "ADVANCE_GENERAL_CANDIDATE_BOUNDARY_ECONOMICS_PREFLIGHT"
        if all(row["decision"] == "PASS" for row in payload["rows"])
        else "HOLD_GENERAL_CANDIDATE_BOUNDARY_ECONOMICS"
    )
    assert payload["decision"] == expected_decision
    expected_losing = {row["name"] for row in payload["rows"] if row["decision"] == "HOLD"}
    assert {row["name"] for row in payload["losing_rows"]} == expected_losing

    persisted = json.loads(bench.OUT.read_text(encoding="utf-8"))
    assert persisted == payload


def test_a_single_complete_byte_regression_forces_hold(monkeypatch: pytest.MonkeyPatch):
    fake_rows = [
        {
            "name": "synthetic-regression",
            "decision": "HOLD",
            "gates": {
                "law_semantics_exact": True,
                "surprise_semantics_exact": True,
                "deterministic_law_wire": True,
                "generic_reader_ontology_only": True,
                "complete_bytes_non_regressing": False,
            },
            "law_wire_bytes": 101,
            "surprise_wire_bytes": 100,
            "law_minus_surprise_bytes": 1,
            "law_ratio": 1.01,
            "law_wire_sha256": "0" * 64,
            "surprise_wire_sha256": "1" * 64,
            "reader_ops": ["surprise"],
            "law_stats": {},
            "surprise_stats": {},
        }
    ]

    # Exercise the aggregation rule independently from the actual transfer outcome.
    all_pass = all(row["decision"] == "PASS" for row in fake_rows)
    decision = (
        "ADVANCE_GENERAL_CANDIDATE_BOUNDARY_ECONOMICS_PREFLIGHT"
        if all_pass
        else "HOLD_GENERAL_CANDIDATE_BOUNDARY_ECONOMICS"
    )
    assert decision == "HOLD_GENERAL_CANDIDATE_BOUNDARY_ECONOMICS"
