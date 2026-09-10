from __future__ import annotations

from pathlib import Path

from benchmarks.one import one_g02_general_law_breadth_economics_transfer as economics


def test_breadth_law_pays_complete_bytes_without_semantic_debt(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(economics, "OUT", tmp_path / "economics.json")
    payload = economics.run()

    assert payload["decision"] == "ADVANCE_BREADTH_REPRESENTATION_ECONOMICS_ONLY"
    assert all(payload["gates"].values())
    assert payload["law"]["stored_bytes"] <= payload["surprise_only"]["stored_bytes"]
    assert payload["stored_byte_delta"] <= 0
    assert payload["law_over_surprise_stored_ratio"] <= 1.0
    assert payload["law"]["accounting"]["stored_bytes"] == payload["law"]["stored_bytes"]
    assert payload["surprise_only"]["accounting"]["stored_bytes"] == payload["surprise_only"]["stored_bytes"]
    assert payload["law"]["reader_relation_structure"]["add_target_op"] == "add8"
    assert payload["law"]["reader_relation_structure"]["xor_target_op"] == "xor"
    assert payload["law"]["reader_relation_structure"]["exact_copy_reuses_base_ref"] is True
    assert payload["genesis_comparison_executed"] is False
    assert payload["genesis_scoring_executed"] is False
    assert payload["genesis_winner_selected"] is False
    assert economics.OUT.is_file()


def test_decision_holds_on_each_individual_failed_gate():
    base = {
        "law_whole_tree_semantics_exact": True,
        "surprise_whole_tree_semantics_exact": True,
        "law_deterministic_wire": True,
        "surprise_deterministic_wire": True,
        "reader_relation_structure_exact": True,
        "generic_reader_ontology_only": True,
        "complete_stored_bytes_nonregression": True,
        "law_accounting_closes": True,
        "surprise_accounting_closes": True,
    }
    assert economics._decision(base) == "ADVANCE_BREADTH_REPRESENTATION_ECONOMICS_ONLY"
    for key in base:
        hostile = dict(base)
        hostile[key] = False
        assert economics._decision(hostile) == "HOLD_BREADTH_REPRESENTATION_ECONOMICS", key
