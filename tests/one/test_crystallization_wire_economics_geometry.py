from __future__ import annotations

from pathlib import Path

from benchmarks.one import one_g02_crystallization_wire_economics_geometry as geometry


def test_geometry_matrix_is_frozen_and_genesis_dark(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    payload = geometry.run()
    assert payload["schema"] == "cmpct-one-g02-crystallization-wire-economics-geometry-v2"
    assert payload["experimental_version"] == "ONE-G0.2"
    assert payload["lengths"] == list(geometry.LENGTHS)
    assert payload["families"] == list(geometry.FAMILIES)
    assert len(payload["rows"]) == len(geometry.LENGTHS) * len(geometry.FAMILIES)
    assert {(r["family"], r["length"]) for r in payload["rows"]} == {
        (family, length) for family in geometry.FAMILIES for length in geometry.LENGTHS
    }
    for flag in ("genesis_inputs_executed", "genesis_comparison_executed", "genesis_scoring_executed", "genesis_winner_selected"):
        assert payload[flag] is False


def test_every_geometry_row_proves_reader_structure_and_exact_semantics(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    payload = geometry.run()
    for row in payload["rows"]:
        assert row["semantic_exact"] is True
        assert row["deterministic_wire"] is True
        assert row["generic_reader_ontology_only"] is True
        assert row["reader_structure_evidence"]["ok"] is True
        assert row["candidate_minus_control_bytes"] == row["candidate_wire_bytes"] - row["control_wire_bytes"]
        assert row["non_regressing"] is (row["candidate_minus_control_bytes"] <= 0)
        assert row["candidate_stats"]["source_read_bytes"] == row["candidate_stats"]["logical_file_bytes"]
        assert row["candidate_stats"]["authentication_source_reread_bytes"] == 0


def test_summary_crossover_is_derived_from_raw_rows(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    payload = geometry.run()
    for family in geometry.FAMILIES:
        family_rows = sorted(
            (r for r in payload["rows"] if r["family"] == family),
            key=lambda row: row["length"],
        )
        hits = [r["length"] for r in family_rows if r["non_regressing"]]
        assert payload["first_non_regressing_length"][family] == (min(hits) if hits else None)

        stable = None
        for index, row in enumerate(family_rows):
            if all(tail["non_regressing"] for tail in family_rows[index:]):
                stable = row["length"]
                break
        assert payload["stable_non_regressing_length"][family] == stable

        first_index = next((i for i, row in enumerate(family_rows) if row["non_regressing"]), None)
        expected_post_first = [] if first_index is None else [
            row["length"] for row in family_rows[first_index + 1 :] if not row["non_regressing"]
        ]
        assert payload["post_first_crossover_regression_lengths"][family] == expected_post_first

    expected_eventual = all(payload["first_non_regressing_length"][family] is not None for family in geometry.FAMILIES)
    expected_stable = all(payload["stable_non_regressing_length"][family] is not None for family in geometry.FAMILIES)
    assert payload["every_family_eventually_non_regressing"] is expected_eventual
    assert payload["stable_non_regressing_tail_all_families"] is expected_stable
    if not payload["all_structural_gates_exact"]:
        assert payload["decision"] == "RETIRE_OR_REPAIR_CRYSTALLIZATION_ECONOMICS_MODEL"
    elif expected_eventual:
        assert payload["decision"] == "ADVANCE_CRYSTALLIZATION_ECONOMICS_MODEL"
    else:
        assert payload["decision"] == "HOLD_CRYSTALLIZATION_ECONOMICS_MODEL"


def test_stable_tail_rejects_isolated_green_point():
    rows = [
        {"length": 2, "non_regressing": False},
        {"length": 4, "non_regressing": True},
        {"length": 8, "non_regressing": False},
        {"length": 16, "non_regressing": True},
        {"length": 32, "non_regressing": True},
    ]
    assert geometry._stable_non_regressing_length(rows) == 16
    assert geometry._post_first_crossover_regressions(rows) == [8]


def test_stable_tail_is_none_when_largest_measured_point_regresses():
    rows = [
        {"length": 2, "non_regressing": True},
        {"length": 4, "non_regressing": True},
        {"length": 8, "non_regressing": False},
    ]
    assert geometry._stable_non_regressing_length(rows) is None
    assert geometry._post_first_crossover_regressions(rows) == [8]
