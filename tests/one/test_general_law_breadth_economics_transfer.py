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
    assert payload["law"]["reader_relation_structure"]["add_target_op"] == "add8"
    assert payload["law"]["reader_relation_structure"]["xor_target_op"] == "xor"
    assert payload["law"]["reader_relation_structure"]["exact_copy_reuses_base_ref"] is True
    assert payload["comparison_executed"] is False
    assert payload["scoring_executed"] is False
    assert payload["winner_selected"] is False
    assert economics.OUT.is_file()
