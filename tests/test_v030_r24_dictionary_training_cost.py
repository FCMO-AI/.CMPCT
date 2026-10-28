from __future__ import annotations

from pathlib import Path

from benchmarks import v030_r24_dictionary_training_cost_oracle as ORACLE


def _row(*, tree: str, seconds: float) -> dict:
    return {
        "archive_bytes": 1234,
        "archive_sha256": "a" * 64,
        "tree_sha256": tree,
        "complete_create_s": seconds,
    }


def test_material_opportunity_compares_canonical_product_tree_not_historical_source_hash(monkeypatch, tmp_path: Path) -> None:
    canonical_tree = "canonical-product-tree"
    monkeypatch.setattr(ORACLE, "_shipping_build", lambda root, out: _row(tree=canonical_tree, seconds=0.100))
    monkeypatch.setattr(ORACLE, "_no_dictionary_build", lambda root, out: _row(tree=canonical_tree, seconds=0.080))

    result = ORACLE._measure(tmp_path, tmp_path / "work", "accepted-historical-source-tree")

    assert result["accepted_source_tree_sha256"] == "accepted-historical-source-tree"
    assert result["shipping_verified_tree_sha256"] == canonical_tree
    assert result["no_dictionary_verified_tree_sha256"] == canonical_tree
    assert result["canonical_product_tree_equal"] is True
    assert result["exact_archive_bytes_and_sha"] is True
    assert result["material_exact_opportunity"] is True


def test_material_opportunity_fails_closed_when_product_trees_differ(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(ORACLE, "_shipping_build", lambda root, out: _row(tree="shipping-tree", seconds=0.100))
    monkeypatch.setattr(ORACLE, "_no_dictionary_build", lambda root, out: _row(tree="candidate-tree", seconds=0.080))

    result = ORACLE._measure(tmp_path, tmp_path / "work", "accepted-historical-source-tree")

    assert result["canonical_product_tree_equal"] is False
    assert result["material_exact_opportunity"] is False
