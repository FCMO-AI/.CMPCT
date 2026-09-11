from __future__ import annotations

from benchmarks.one.one_g02_second_stage_dual_collision_tail import (
    LENGTHS,
    RELATIONS,
    _last_outside_sparse,
    _make_case,
    _oracle_second_positions,
    decide,
)
from experiments.one.general_law_archive import _sample_positions


def test_dual_collision_tail_geometry_is_outside_both_sparse_sets() -> None:
    for relation in RELATIONS:
        for length in LENGTHS:
            _source, _target, poison, primary, second = _make_case(relation, length)
            assert primary == tuple(_sample_positions(length))
            assert second == _oracle_second_positions(primary)
            assert poison == max(set(range(length)) - set(primary) - set(second))
            assert poison not in primary
            assert poison not in second


def test_last_outside_sparse_is_near_tail_for_all_rows() -> None:
    for length in LENGTHS:
        primary = tuple(_sample_positions(length))
        poison, _second = _last_outside_sparse(length, primary)
        # The hostile case must force a late exact-proof failure rather than
        # accidentally degenerating into the already-covered early collision.
        assert poison >= length - 3


def test_decision_fails_closed_on_each_gate() -> None:
    base = {
        "primary_pass": True,
        "baseline_value": False,
        "candidate_value": False,
        "poison_index": 4094,
        "length": 4096,
        "cpu_ratio": 1.00,
        "wall_ratio": 1.00,
        "baseline_modeled_remaining_bytes": 8192,
        "candidate_modeled_remaining_bytes": 8222,
        "modeled_extra_sparse_bytes": 30,
        "second_stage_positions": 15,
    }

    decision, hypotheses = decide([dict(base)])
    assert decision == "ADVANCE_SECOND_STAGE_DUAL_COLLISION_TAIL_SAFETY_ONLY"
    assert all(hypotheses.values())

    for field, bad in (
        ("primary_pass", False),
        ("candidate_value", True),
        ("cpu_ratio", 1.21),
        ("wall_ratio", 1.21),
        ("candidate_modeled_remaining_bytes", 8223),
    ):
        row = dict(base)
        row[field] = bad
        decision, hypotheses = decide([row])
        assert decision != "ADVANCE_SECOND_STAGE_DUAL_COLLISION_TAIL_SAFETY_ONLY"
        assert not all(hypotheses.values())


def test_broad_median_gate_cannot_be_averaged_away() -> None:
    rows = []
    for ratio in (1.049, 1.051, 1.051):
        row = {
            "primary_pass": True,
            "baseline_value": False,
            "candidate_value": False,
            "poison_index": 4094,
            "length": 4096,
            "cpu_ratio": ratio,
            "wall_ratio": ratio,
            "baseline_modeled_remaining_bytes": 8192,
            "candidate_modeled_remaining_bytes": 8222,
            "modeled_extra_sparse_bytes": 30,
            "second_stage_positions": 15,
        }
        rows.append(row)
    decision, hypotheses = decide(rows)
    assert hypotheses["H2_per_row_survivor_debt"] is True
    assert hypotheses["H3_broad_survivor_debt"] is False
    assert decision == "HOLD_SECOND_STAGE_DUAL_COLLISION_TAIL"
