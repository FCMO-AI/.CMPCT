from __future__ import annotations

from benchmarks import v030_release_generalization as gate


def test_accepted_v029_row_reconstruction_is_exact() -> None:
    rows = gate._accepted_v029_rows()
    assert len(rows) == 15
    assert sum(row["accepted_v029_bytes"] for row in rows.values()) == 137_499_525
    assert rows[("resemblance_hostile_v1", "01_shifted_versions")]["accepted_v029_bytes"] == 1_723_056
    assert rows[("resemblance_hostile_v1", "03_boundary_churn")]["accepted_v029_bytes"] == 79_876


def test_numeric_revision_floor_does_not_get_easier_on_smaller_v029_substrate() -> None:
    # Footnote: the accepted repair-v6 substrate made v0.29 2,290 B smaller. A naive percentage-only rule would
    # lower the absolute hurdle. The campaign explicitly carries 687,783 B forward, so v0.30 inherits that
    # stricter number rather than reverse-engineering a more convenient threshold from the repaired aggregate.
    assert gate.EXPECTED_V029_TOTAL == 137_499_525
    assert gate.INHERITED_ABSOLUTE_REVISION_FLOOR == 687_783
    assert gate.MIN_RELEASE_SAVING_BYTES == 687_783
    assert gate.MIN_RELEASE_SAVING_BYTES >= (gate.EXPECTED_V029_TOTAL + 199) // 200
    assert gate.MIN_IMPROVED_ROWS == 3
    assert gate.MAX_MEMBER_READ_AMP == 8.0


def test_historical_tree_identity_is_independent_of_candidate_product_hash(tmp_path, monkeypatch) -> None:
    # The canonical adapter swaps ``gate.RC`` for the r24/r25 release product. Its user-tree hash intentionally
    # covers a richer semantic domain than the historical v0.28/v0.29 benchmark identity. A product hash change
    # must therefore never masquerade as corpus drift or weaken the frozen repair-v6 source proof.
    (tmp_path / "nested").mkdir()
    (tmp_path / "nested" / "payload.bin").write_bytes(b"cmpct-v030-dual-tree-domain\x00\xff")
    historical = gate._historical_treehash(tmp_path)

    monkeypatch.setattr(gate.RC, "treehash", lambda _root: "canonical-user-tree-domain")

    assert gate._historical_treehash(tmp_path) == historical
    assert gate.RC.treehash(tmp_path) == "canonical-user-tree-domain"
    assert historical != gate.RC.treehash(tmp_path)
