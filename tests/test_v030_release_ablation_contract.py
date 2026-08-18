from __future__ import annotations

"""Fast contract tests for the expensive canonical v0.30 evidence split."""

import pytest

from benchmarks import v030_release_ablation_canonical as A
from benchmarks import v030_release_generalization as G


def test_ablation_variants_and_historical_release_floors_are_frozen() -> None:
    assert A.VARIANTS == ("v029", "geometry_only", "prefixgraph_only", "combined")
    assert A.HISTORICAL_SUBSTRATE != A.PRODUCT_SUBSTRATE
    assert G.EXPECTED_V029_TOTAL == 137_501_815
    assert G.MIN_RELEASE_SAVING_BYTES == 687_783
    assert G.MIN_IMPROVED_ROWS == 3
    assert G.MAX_MEMBER_READ_AMP == 8.0


def test_prefixgraph_feature_toggle_uses_exact_historical_v029_fallback() -> None:
    assert A._select_prefixgraph_candidate(100, 99, True) == "prefixgraph"
    assert A._select_prefixgraph_candidate(100, 100, True) == "v029-fallback"
    assert A._select_prefixgraph_candidate(100, 101, True) == "v029-fallback"
    assert A._select_prefixgraph_candidate(100, 90, False) == "v029-fallback"
    assert A._select_prefixgraph_candidate(100, None, False) == "v029-fallback"

    # Footnote: exact ties intentionally preserve the inherited historical archive. An approximate nomination
    # or feature label cannot displace v0.29 and then masquerade as causal byte evidence.


def test_complete_artifact_comparison_rejects_semantic_substrate_mismatch() -> None:
    historical = {"substrate_id": A.HISTORICAL_SUBSTRATE, "archive_bytes": 100}
    product = {"substrate_id": A.PRODUCT_SUBSTRATE, "archive_bytes": 90}
    with pytest.raises(RuntimeError, match="incomparable complete-artifact substrates"):
        A._require_same_substrate(historical, product)


def test_missing_substrate_is_not_silently_assumed_equivalent() -> None:
    charged = {"substrate_id": A.PRODUCT_SUBSTRATE, "archive_bytes": 100}
    uncharged = {"archive_bytes": 90}
    with pytest.raises(RuntimeError, match="incomparable complete-artifact substrates"):
        A._require_same_substrate(charged, uncharged)

    # Footnote: this is the regression vector from slot-00 review. A manifest/fallback charge omitted from one
    # variant must fail the benchmark contract before a tempting smaller byte count can enter an exact-min claim.


def test_product_surface_dependency_fails_closed_when_contract_is_incomplete(monkeypatch) -> None:
    import experiments.entropygraph_v030_canonical as canonical

    monkeypatch.delattr(canonical, "build_ablation", raising=False)
    with pytest.raises(A.ProductSurfaceUnavailable, match="build_ablation"):
        A._load_product_module()
