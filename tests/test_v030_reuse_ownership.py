from __future__ import annotations

import random

import pytest

from cmpct.reuse_ownership import realized_reuse_fixed_point


def _id(tag: int, size: int):
    return (8, size, bytes([tag]) * 32)


def _slow_fixed_point(graph, hidden, fixed, floor, excluded=()):
    active = (set(hidden) | set(fixed)) - set(excluded)
    while True:
        credit = {o: 0 for o in active}
        identities = {}
        for owner in active:
            for identity in set(graph.get(owner, ())):
                identities.setdefault(identity, set()).add(owner)
        for identity, owners in identities.items():
            if len(owners) >= 2:
                for owner in owners:
                    credit[owner] += identity[1]
        doomed = {o for o in hidden & active if credit[o] < floor}
        if not doomed:
            return frozenset(active), credit
        active -= doomed


def test_three_owner_bridge_cannot_spend_fallback_owners_as_reuse_credit():
    # A--X--B--Y--C. X and Y are each below the floor; naïve one-pass credit
    # admits B from 2,410 B even though A/C cannot survive to realize either
    # supporting stream. Stable ownership must therefore peel all three.
    x = _id(1, 1205)
    y = _id(2, 1205)
    graph = {"A": {x}, "B": {x, y}, "C": {y}}
    active, credit = realized_reuse_fixed_point(
        graph, hidden_owners=graph, min_verified_reuse=2000
    )
    assert active == frozenset()
    assert credit == {}


def test_realized_fixed_owner_can_anchor_hidden_reuse():
    x = _id(3, 2400)
    graph = {"explicit.zip": {x}, "hidden.bin": {x}}
    active, credit = realized_reuse_fixed_point(
        graph,
        hidden_owners={"hidden.bin"},
        fixed_owners={"explicit.zip"},
        min_verified_reuse=2176,
    )
    assert active == frozenset({"explicit.zip", "hidden.bin"})
    assert credit["hidden.bin"] == 2400


def test_failed_hidden_stage_cascades_through_other_tentative_owners():
    # All three initially survive because each shared identity clears the floor.
    # If B later fails actual-output validation/staging, A and C lose their only
    # realized reuse partners and must fall back too. A failed stage may never
    # remain as phantom evidence for another hidden admission.
    x = _id(4, 2400)
    y = _id(5, 2400)
    graph = {"A": {x}, "B": {x, y}, "C": {y}}
    before, _ = realized_reuse_fixed_point(
        graph, hidden_owners=graph, min_verified_reuse=2176
    )
    assert before == frozenset(graph)
    after, credit = realized_reuse_fixed_point(
        graph,
        hidden_owners=graph,
        excluded_owners={"B"},
        min_verified_reuse=2176,
    )
    assert after == frozenset()
    assert credit == {}


def test_exclusion_cannot_remove_a_realized_fixed_owner():
    x = _id(6, 2400)
    with pytest.raises(ValueError, match="fixed realized owner"):
        realized_reuse_fixed_point(
            {"explicit.zip": {x}},
            hidden_owners=(),
            fixed_owners={"explicit.zip"},
            excluded_owners={"explicit.zip"},
            min_verified_reuse=2176,
        )


def test_queue_peeling_matches_simple_recomputation_on_random_graphs():
    rng = random.Random(204)
    for _ in range(1000):
        owners = [f"o{i}" for i in range(rng.randint(1, 10))]
        identities = [_id(i, rng.randint(1, 3000)) for i in range(rng.randint(1, 12))]
        graph = {
            owner: {identity for identity in identities if rng.random() < 0.3}
            for owner in owners
        }
        fixed = {o for o in owners if rng.random() < 0.2}
        hidden = set(owners) - fixed
        excluded = {o for o in hidden if rng.random() < 0.15}
        floor = rng.randint(1, 5000)
        fast_active, fast_credit = realized_reuse_fixed_point(
            graph,
            hidden_owners=hidden,
            fixed_owners=fixed,
            excluded_owners=excluded,
            min_verified_reuse=floor,
        )
        slow_active, slow_credit = _slow_fixed_point(
            graph, hidden, fixed, floor, excluded
        )
        assert fast_active == slow_active
        assert fast_credit == slow_credit
