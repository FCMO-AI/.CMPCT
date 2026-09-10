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
        # excuse semantic, determinism, reader-ontology, or missing intended structure
        # as economics. Otherwise a Surprise fallback could vacuously earn ADVANCE.
        assert row["gates"]["law_semantics_exact"] is True
        assert row["gates"]["surprise_semantics_exact"] is True
        assert row["gates"]["deterministic_law_wire"] is True
        assert row["gates"]["generic_reader_ontology_only"] is True
        assert row["gates"]["expected_structure_exercised"] is True
        assert row["expected_relation_field"] == bench.EXPECTED_RELATION_FIELD[row["name"]]
        assert set(row["reader_ops"]) <= bench.ALLOWED_OPS
        assert row["law_minus_surprise_bytes"] == row["law_wire_bytes"] - row["surprise_wire_bytes"]
        assert row["decision"] == (
            "PASS" if all(row["gates"].values()) else "HOLD"
        )

    assert payload["decision"] == bench._aggregate_decision(payload["rows"])
    expected_losing = {row["name"] for row in payload["rows"] if row["decision"] == "HOLD"}
    assert {row["name"] for row in payload["losing_rows"]} == expected_losing

    persisted = json.loads(bench.OUT.read_text(encoding="utf-8"))
    assert persisted == payload


def test_a_single_complete_byte_regression_forces_hold():
    fake_rows = [
        {
            "name": "synthetic-regression",
            "decision": "HOLD",
            "gates": {
                "law_semantics_exact": True,
                "surprise_semantics_exact": True,
                "deterministic_law_wire": True,
                "generic_reader_ontology_only": True,
                "expected_structure_exercised": True,
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

    assert bench._aggregate_decision(fake_rows) == bench.HOLD


def test_missing_intended_structure_forces_hold_even_when_bytes_do_not_regress():
    fake_rows = [
        {
            "name": "synthetic-vacuous-fallback",
            "decision": "HOLD",
            "gates": {
                "law_semantics_exact": True,
                "surprise_semantics_exact": True,
                "deterministic_law_wire": True,
                "generic_reader_ontology_only": True,
                "expected_structure_exercised": False,
                "complete_bytes_non_regressing": True,
            },
            "law_wire_bytes": 100,
            "surprise_wire_bytes": 100,
            "law_minus_surprise_bytes": 0,
            "law_ratio": 1.0,
            "law_wire_sha256": "0" * 64,
            "surprise_wire_sha256": "0" * 64,
            "reader_ops": ["surprise"],
            "law_stats": {},
            "surprise_stats": {},
        }
    ]

    assert bench._aggregate_decision(fake_rows) == bench.HOLD


def test_empty_row_set_cannot_vacuously_advance():
    # If corpus construction breaks and yields no rows, fail closed rather than letting
    # Python's all([]) turn missing evidence into an ADVANCE decision.
    assert bench._aggregate_decision([]) == bench.HOLD
