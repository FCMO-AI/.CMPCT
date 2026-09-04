from __future__ import annotations

import random

from benchmarks.one.one_g02_bounded_gear_ab import _bounded_observe
from benchmarks.one.one_g02_gear_replacement_ab import _gear_observe
from benchmarks.one.one_g02_minimizer_gear_ab import _minimizer_observe
from benchmarks.one.one_g02_tiered_gear_ab import _tiered_observe
from experiments.one.observe import observe


def _fixed(data: bytes):
    return observe(data, min_run=8, chunk_size=64, max_index_entries=1 << 14).stats


def test_sparse_only_gear_has_a_short_period_phase_blind_spot() -> None:
    """Negative evidence: a repeating cycle can contain no sparse masked Gear state."""
    basis = random.Random(18).randbytes(64)
    data = basis * 64
    fixed = _fixed(data)
    sparse = _gear_observe(data)

    assert fixed.reuse_opportunity_bytes == len(data) - len(basis)
    assert sparse.anchors == 0
    assert sparse.reuse_opportunity_bytes == 0


def test_tiered_same_signal_recovers_short_period_opportunity() -> None:
    basis = random.Random(18).randbytes(64)
    data = basis * 64
    fixed = _fixed(data)
    tiered = _tiered_observe(data)

    assert tiered.reuse_opportunity_bytes == fixed.reuse_opportunity_bytes
    assert tiered.retained_index_payload_bytes <= fixed.retained_index_payload_bytes


def test_tiered_same_signal_preserves_shifted_relation_sparse_value() -> None:
    basis = random.Random(13).randbytes(64 * 1024)
    data = basis + b"X" + basis
    fixed = _fixed(data)
    tiered = _tiered_observe(data)

    assert fixed.reuse_opportunity_bytes == 0
    assert tiered.reuse_opportunity_bytes >= len(basis)


def test_tiered_same_signal_does_not_invent_random_reuse() -> None:
    data = random.Random(11).randbytes(128 * 1024)
    tiered = _tiered_observe(data)
    assert tiered.reuse_opportunity_bytes == 0


def test_local_plus_sparse_tier_is_still_blind_after_local_eviction() -> None:
    """A sparse expected density is not a worst-case nomination-spacing guarantee."""
    basis = random.Random(4876).randbytes(8 * 1024)
    data = basis * 2
    fixed = _fixed(data)
    sparse = _gear_observe(data)
    tiered = _tiered_observe(data)

    assert sparse.anchors == 0
    assert fixed.reuse_opportunity_bytes == len(basis)
    assert tiered.reuse_opportunity_bytes == 0


def test_bounded_gap_same_signal_repairs_aligned_anchor_starvation() -> None:
    basis = random.Random(4876).randbytes(8 * 1024)
    data = basis * 2
    fixed = _fixed(data)
    bounded = _bounded_observe(data)

    assert bounded.masked_anchors == 0
    assert bounded.fallback_anchors > 0
    assert bounded.reuse_opportunity_bytes == fixed.reuse_opportunity_bytes
    assert bounded.retained_index_payload_bytes < fixed.retained_index_payload_bytes


def test_coordinate_gap_fallback_loses_insertion_shift_invariance() -> None:
    basis = random.Random(4876).randbytes(8 * 1024)
    data = basis + b"X" + basis
    bounded = _bounded_observe(data)

    assert bounded.masked_anchors == 0
    assert bounded.fallback_anchors > 0
    assert bounded.reuse_opportunity_bytes == 0


def test_minimizer_same_signal_recovers_shifted_anchor_starvation() -> None:
    basis = random.Random(4876).randbytes(8 * 1024)
    data = basis + b"X" + basis
    minimizer = _minimizer_observe(data)

    assert minimizer.reuse_opportunity_bytes >= len(basis)
    assert minimizer.global_entries > 0


def test_minimizer_same_signal_keeps_random_negative_path_exact() -> None:
    data = random.Random(11).randbytes(128 * 1024)
    minimizer = _minimizer_observe(data)
    assert minimizer.reuse_opportunity_bytes == 0
