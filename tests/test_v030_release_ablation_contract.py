from __future__ import annotations

"""Fast contract tests for the expensive canonical v0.30 four-configuration ablation."""

from benchmarks import v030_release_ablation_canonical as A
from benchmarks import v030_release_generalization as G


def test_ablation_variants_and_release_floors_are_frozen() -> None:
    assert A.VARIANTS == ("v029", "geometry_only", "prefixgraph_only", "combined")
    assert G.EXPECTED_V029_TOTAL == 137_501_815
    assert G.MIN_RELEASE_SAVING_BYTES == 687_783
    assert G.MIN_IMPROVED_ROWS == 3
    assert G.MAX_MEMBER_READ_AMP == 8.0


def test_prefixgraph_feature_toggle_uses_exact_v029_fallback() -> None:
    assert A._select_prefixgraph_candidate(100, 99, True) == "prefixgraph"
    assert A._select_prefixgraph_candidate(100, 100, True) == "v029-fallback"
    assert A._select_prefixgraph_candidate(100, 101, True) == "v029-fallback"
    assert A._select_prefixgraph_candidate(100, 90, False) == "v029-fallback"
    assert A._select_prefixgraph_candidate(100, None, False) == "v029-fallback"

    # Footnote: exact ties intentionally preserve the inherited archive.  If an approximate nomination or a
    # feature label could displace v0.29 on a tie, the ablation would be measuring policy drift rather than
    # the byte contribution of PrefixGraph.
