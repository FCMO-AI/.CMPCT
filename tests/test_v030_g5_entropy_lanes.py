from __future__ import annotations

import pytest

from experiments import entropygraph_v030_g5_entropy_lanes as G5
from experiments import entropygraph_v030_representation_compiler as RC


def test_g5_hand_derived_golden_vector_and_tail() -> None:
    raw = b"abcdefg"
    # width=2 complete body -> lane0=ace, lane1=bdf, tail=g; permutation (1,0).
    transformed = G5.forward(raw, 2, (1, 0))
    assert transformed == b"bdfaceg"
    assert G5.inverse(transformed, 2, (1, 0), len(raw)) == raw


def test_g5_round_trips_every_supported_width_with_odd_tails() -> None:
    raw = bytes((index * 73 + 11) & 255 for index in range(16_391))
    for width in G5.LANE_WIDTHS:
        orders = {tuple(range(width)), G5.entropy_order(raw, width), G5.histogram_chain_order(raw, width)}
        for order in orders:
            encoded = G5.forward(raw, width, order)
            assert len(encoded) == len(raw)
            assert G5.inverse(encoded, width, order, len(raw)) == raw


def test_g5_rejects_non_bijective_and_wrong_size_descriptors() -> None:
    with pytest.raises(ValueError, match="bijective"):
        G5.forward(b"abcdefgh", 4, (0, 1, 1, 3))
    with pytest.raises(ValueError, match="bijective"):
        G5.inverse(b"abcdefgh", 4, (0, 1, 2), 8)
    with pytest.raises(ValueError, match="logical-size"):
        G5.inverse(b"abcdefgh", 4, (0, 1, 2, 3), 7)


def test_g5_nomination_is_deterministic_unique_and_bounded() -> None:
    raw = (b"\x00\x00\x00\xff\x01\x02\x03\x04" * 4096) + b"tail"
    for width in G5.LANE_WIDTHS:
        first = G5.nominated_orders(raw, width)
        second = G5.nominated_orders(raw, width)
        assert first == second
        assert len(first) <= G5.MAX_NOMINATED_ORDERS_PER_WIDTH
        assert len(set(first)) == len(first)
        assert all(sorted(order) == list(range(width)) for order in first)


def test_representation_compiler_inverse_covers_all_local_kinds() -> None:
    raw = (b"alpha=0001 beta=0002 gamma=0003\n" * 600)
    selected = RC.encode_node(raw)
    restored = RC.inverse_physical(selected["kind"], selected.get("param", 0), selected["physical"], len(raw))
    assert restored == raw


def test_g5_selection_threshold_is_against_original_g0_g4_incumbent(monkeypatch) -> None:
    raw = b"x" * (16 * 1024)
    base_payload = b"I" * 1000
    monkeypatch.setattr(RC, "_g0_g4", lambda _raw: {
        "kind": "direct",
        "param": 0,
        "physical": _raw,
        "codec": 1,
        "payload": base_payload,
        "payload_bytes": 1000,
        "hierarchical_screened_candidates": 0,
        "hierarchical_exact_finalists": 0,
        "g5_screened_candidates": 0,
        "g5_exact_finalists": 0,
        "g5_strategy": None,
    })
    monkeypatch.setattr(RC.G5, "LANE_WIDTHS", (2,))
    monkeypatch.setattr(RC.G5, "entropy_order", lambda _raw, _width: (1, 0))
    monkeypatch.setattr(RC.G5, "histogram_chain_order", lambda _raw, _width: (0, 1))
    monkeypatch.setattr(RC.G5, "nominated_orders", lambda _raw, _width: ((1, 0), (0, 1)))
    monkeypatch.setattr(RC.G5, "forward", lambda _raw, _width, order: (b"A" if order == (1, 0) else b"B") * 1200)
    monkeypatch.setattr(RC.G5, "inverse", lambda _stored, _width, _order, logical_size: raw[:logical_size])
    monkeypatch.setattr(RC.G, "zc", lambda data, level: (b"s" * (900 if data[:1] == b"A" else 895)) if level == RC.G5_SCREEN_LEVEL else data)
    monkeypatch.setattr(RC.G, "_compress_physical", lambda data: (1, b"z" * (900 if data[:1] == b"A" else 895)))
    # Footnote: remove descriptor variability from this unit test so it isolates the admission-law invariant.
    # Descriptor charging itself is separately exercised by the real compiler path and complete-artifact gate.
    monkeypatch.setattr(RC, "_descriptor_bytes", lambda *_args, **_kwargs: 0)
    result = RC.encode_node(raw)
    assert result["kind"] == "lane_perm"
    assert result["payload_bytes"] == 895
    assert result["incremental_stored_saving_vs_g0_g4"] == 105


def test_resource_contract_never_expands_inherited_node_ceiling() -> None:
    assert RC.RESOURCE_LIMITS["max_logical_node_bytes"] <= 512 * 1024
    assert RC.RESOURCE_LIMITS["g5_exact_finalists"] <= 3
    assert G5.RESOURCE_LIMITS["max_width"] <= 16
    assert G5.RESOURCE_LIMITS["max_nominated_orders_per_width"] <= 2
