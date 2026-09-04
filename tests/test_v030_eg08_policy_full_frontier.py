from __future__ import annotations

from benchmarks import v030_federated_compact_framing_v8_policy_distill_v3 as V3
from benchmarks import v030_federated_compact_framing_v8_policy_distill_v5 as V5


def test_full_frontier_can_beat_first_feasible_rule_depth(monkeypatch):
    """A first-depth feasible broad rule must not hide a cheaper two-rule policy.

    The synthetic state is intentionally about search mathematics, not benchmark content:
    - A broad one-rule policy selects six packs and already clears the byte ceiling.
    - Two narrow rules each select two packs and do not clear alone.
    - Their union selects only four packs and clears, so it is strictly cheaper under the
      existing modeled-effort objective even though it lives one rule depth deeper.
    """

    broad = (12, 12, 12, 12, 12, 12)
    left = (22, 22, 1, 1, 1, 1)
    right = (1, 1, 22, 22, 1, 1)
    combined = (22, 22, 22, 22, 1, 1)
    rules = {
        broad: {"feature": "raw_bytes", "operator": ">=", "threshold": 1, "level": 12},
        left: {"feature": "raw_bytes", "operator": ">=", "threshold": 2, "level": 22},
        right: {"feature": "raw_bytes", "operator": ">=", "threshold": 3, "level": 22},
    }

    monkeypatch.setattr(V3, "MAX_RULES", 2)
    monkeypatch.setattr(V3, "_deduplicated_atomic_states", lambda _features: list(rules.items()))

    def exact_bytes(_meta, _table, vector):
        vector = tuple(vector)
        if vector == broad:
            return 99
        if vector == left or vector == right:
            return 110
        if vector == combined:
            return 90
        return 120

    monkeypatch.setattr(V3, "_exact_archive_bytes", exact_bytes)
    features = [{} for _ in range(6)]
    payload_table = [{} for _ in range(6)]

    old_rules, old_vector, old_bytes, _old_meta = V3._search(features, b"", payload_table, 100)
    assert old_rules is not None
    assert old_vector == broad
    assert old_bytes == 99

    new_rules, new_vector, new_bytes, meta = V5._search_full_frontier(features, b"", payload_table, 100)
    assert new_rules is not None
    assert new_vector == combined
    assert new_bytes == 90
    assert V5._primary_cost(new_vector) < V5._primary_cost(old_vector)
    assert meta["search_mode"] == "full-depth-branch-and-bound"
    assert len(meta["state_counts_by_depth"]) == 3


def test_pruning_lower_bound_is_monotone():
    best_cost = (4, 84, 22, 2, ())
    assert V5._can_still_beat((22, 22, 1, 1, 1, 1), best_cost)
    assert not V5._can_still_beat((22, 22, 22, 22, 1, 1), best_cost)
    assert not V5._can_still_beat((12, 12, 12, 12, 12, 12), best_cost)
