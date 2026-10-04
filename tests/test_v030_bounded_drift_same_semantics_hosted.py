from __future__ import annotations

from benchmarks import v030_bounded_drift_same_semantics_oracle as ORACLE


EXPECTED_SOURCE_TREE = "d9106dcdc8f965d45236c241d6c45f773e10b84ac204acc3c3521d889cd3a8fd"
MAX_DECODE_UNIT = 8 * 1024 * 1024
MAX_AMPLIFICATION = 8.0


def test_bounded_drift_same_semantics_hosted_oracle(tmp_path) -> None:
    result = ORACLE.run(tmp_path / "bounded-drift-same-semantics.json")

    source = result["source"]
    candidate = result["bounded_drift_semantic_sibling"]
    control = result["prefixgraph_same_run"]
    delta = result["delta"]["bounded_drift_minus_prefixgraph_bytes"]

    # The deterministic logical source identity is stable, but independently
    # regenerated filesystem-v1 metadata may change complete physical bytes.
    # The scientific claim is same-run physical dominance under equal semantics.
    assert source["tree_sha256"] == EXPECTED_SOURCE_TREE
    candidate_bytes = int(candidate["archive_bytes"])
    control_bytes = int(control["archive_bytes"])
    assert candidate_bytes > 0
    assert control_bytes > 0
    assert delta == candidate_bytes - control_bytes
    assert delta < 0

    assert candidate["tree_sha256"] == EXPECTED_SOURCE_TREE
    assert candidate["manifest_semantics_exact"] is True
    assert candidate["corruption_rejected"] is True
    assert candidate["max_decode_unit_bytes"] <= MAX_DECODE_UNIT
    assert candidate["max_member_read_amplification"] <= MAX_AMPLIFICATION

    assert control["verified"] is True
    assert control["max_member_read_amplification"] <= MAX_AMPLIFICATION
    assert result["release_credit"] is False
