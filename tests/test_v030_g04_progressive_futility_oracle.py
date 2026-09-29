from __future__ import annotations

import random
from types import SimpleNamespace

from benchmarks import v030_g04_progressive_futility_oracle as O


def test_progressive_floor_is_monotone_and_threshold_free():
    proof = O.ProgressiveFloor(
        fixed_framing_bytes=249,
        invariant_payload_bytes=1000,
        floor_bytes=1500,
    )
    assert proof.lower_bound_bytes == 1249
    assert not proof.decisive
    assert proof.observe_chosen_payload(200) == 1449
    assert not proof.decisive
    assert proof.observe_chosen_payload(51) == 1500
    assert proof.decisive


def test_progressive_floor_rejects_negative_payload_counts():
    proof = O.ProgressiveFloor(10, 20, 40)
    try:
        proof.observe_chosen_payload(-1)
    except ValueError:
        pass
    else:
        raise AssertionError("negative payload observation must fail closed")


def test_common_eligibility_uses_current_size_and_locality_contract():
    shared = SimpleNamespace(
        O=SimpleNamespace(
            MIN_RECORD_BYTES=16 * 1024,
            MAX_OVERLAY_RECORD=2 * 1024 * 1024,
            MAX_MEMBER_READ_AMP=8.0,
        )
    )
    payload = b"x" * 31
    record = (1, 64 * 1024, payload, 0, b"sha")

    eligible, amp = O._record_is_g04_eligible(shared, record, [16 * 1024])
    assert eligible
    assert amp == 4.0

    too_wide, amp = O._record_is_g04_eligible(shared, record, [4096])
    assert not too_wide
    assert amp == 16.0

    too_small = (1, 4096, payload, 0, b"sha")
    eligible, _ = O._record_is_g04_eligible(shared, too_small, [4096])
    assert not eligible


def test_post_decision_speculation_bound_matches_worker_window():
    assert [O.max_post_decision_outstanding(w) for w in range(5)] == [0, 0, 1, 2, 3]


def test_optimistic_prefix_bound_cannot_prune_a_true_strict_winner():
    rng = random.Random(194_030)
    for _ in range(50_000):
        records = rng.randint(0, 40)
        fixed = rng.randint(0, 500)
        invariant = rng.randint(0, 5000)
        chosen = [rng.randint(0, 50_000) for _ in range(records)]
        metadata = rng.randint(0, 10_000)
        completed_overlay = fixed + invariant + sum(chosen) + metadata
        floor = completed_overlay + rng.randint(1, 10_000)
        order = list(range(records))
        rng.shuffle(order)
        proof = O.ProgressiveFloor(fixed, invariant, floor)
        assert not proof.decisive
        for index in order:
            proof.observe_chosen_payload(chosen[index])
            assert not proof.decisive
