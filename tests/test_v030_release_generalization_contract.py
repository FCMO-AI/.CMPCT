from __future__ import annotations

from pathlib import Path

from benchmarks import v030_release_generalization as gate
from benchmarks import v030_release_generalization_canonical as canonical


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
    # The canonical adapter swaps ``gate.RC`` for the r24/r25 release product only while its run executes. Its
    # user-tree hash intentionally covers a richer semantic domain than the historical v0.28/v0.29 identity.
    (tmp_path / "nested").mkdir()
    (tmp_path / "nested" / "payload.bin").write_bytes(b"cmpct-v030-dual-tree-domain\x00\xff")
    historical = gate._historical_treehash(tmp_path)

    monkeypatch.setattr(canonical.CANON, "treehash", lambda _root: "canonical-user-tree-domain")

    assert gate._historical_treehash(tmp_path) == historical
    assert canonical.CANON.treehash(tmp_path) == "canonical-user-tree-domain"
    assert historical != canonical.CANON.treehash(tmp_path)


def test_canonical_projection_cannot_substitute_staged_r25_floor_for_historical_v029(tmp_path, monkeypatch) -> None:
    # This reproduces the exact class of evidence bug that broke the first canonical-generalization run. The
    # shipping product may expose a staged-r25 research floor, but the frozen gate must use the independently
    # rebuilt original-tree v0.29 bytes supplied by the adapter.
    product = {
        "selected": "g04-overlay",
        "archive_bytes": 900,
        "format_revision": canonical.CANON.REVISION,
        "format_profile": "geometry-g04",
        "portfolio_create_s": 2.0,
        "v029_research_floor_bytes": 9_999_999,
        "r25": {
            "g04_bytes": 950,
            "g04_selected": "geometry-overlay-g04",
            "prefixgraph_contract_eligible": False,
            "prefixgraph_admitted": False,
            "prefixgraph_reject_reason": "not-smaller",
            "prefixgraph_bytes": None,
            "max_dependency_depth": 0,
            "max_selected_member_read_amplification": 1.25,
            "g04": {"v029": {"portfolio_create_s": 999.0}},
            "prefixgraph_locality": None,
        },
    }
    historical_stats = {"portfolio_create_s": 1.0, "archive_bytes": 1_234}

    normalized = canonical._normalize_product_stats(product, 1_234, historical_stats, tmp_path / "unused.cmpct")

    assert normalized["v029_bytes"] == 1_234
    assert normalized["v029_bytes"] != product["v029_research_floor_bytes"]
    assert normalized["g04"]["v029"] == historical_stats
    assert normalized["archive_bytes"] == 900
    assert normalized["max_selected_member_read_amplification"] == 1.25
    assert normalized["historical_v029_measurement"] == "independent-original-tree-build"


def test_canonical_adapter_is_scoped_and_restores_historical_harness(monkeypatch, tmp_path) -> None:
    original = gate.RC
    seen = []

    def fake_run(_work_root: Path):
        seen.append(gate.RC)
        return {"rows": [], "totals": {}, "gate": {"passed": True}}

    monkeypatch.setattr(gate, "run", fake_run)
    result = canonical.run(tmp_path)

    assert seen == [canonical.ADAPTER]
    assert gate.RC is original
    assert result["release_facade"] == "cmpct-v030-release-product-v1"
