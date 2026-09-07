"""Hostile unit tests for the frozen ONE-G0.2 auth-tree crossover learner.

These tests deliberately avoid native timing.  They pin the decision rule itself so
hosted benchmark noise cannot be confused with a threshold-selection implementation
bug.  The frozen experiment remains authoritative for result-bearing measurements.
"""
from __future__ import annotations

from benchmarks.one.one_g02_auth_tree_multibuffer_resource_crossover import _learn_threshold


def _row(node_count: int, wall: float, cpu: float) -> dict[str, object]:
    return {
        "node_count": node_count,
        "candidate_ratio": wall,
        "candidate_cpu_ratio": cpu,
    }


def test_crossover_selects_smallest_suffix_that_satisfies_all_frozen_gates() -> None:
    rows = [
        _row(10, 1.02, 1.01),
        _row(20, 0.94, 0.89),
        _row(30, 0.90, 0.88),
        _row(40, 0.86, 0.85),
    ]
    assert _learn_threshold(rows) == 20


def test_crossover_rejects_apparent_early_win_when_larger_discovery_row_regresses() -> None:
    rows = [
        _row(10, 0.93, 0.85),
        _row(20, 0.99, 0.84),
        _row(30, 0.90, 0.83),
    ]
    # Node 10 cannot qualify because every larger discovery row must remain <=0.95x.
    # Node 20 fails its own wall gate, so the earliest legal threshold is 30.
    assert _learn_threshold(rows) == 30


def test_crossover_rejects_suffix_when_cpu_median_does_not_pay_for_elapsed_win() -> None:
    rows = [
        _row(10, 0.90, 0.96),
        _row(20, 0.89, 0.94),
        _row(30, 0.88, 0.92),
    ]
    # Wall time alone is insufficient: every possible suffix has CPU median >0.90x.
    assert _learn_threshold(rows) is None


def test_crossover_cpu_gate_is_applied_to_candidate_suffix_not_entire_discovery_set() -> None:
    rows = [
        _row(10, 1.05, 1.50),
        _row(20, 0.94, 0.89),
        _row(30, 0.93, 0.87),
    ]
    # A deliberately bad tiny-root row must not poison a larger valid dispatch region.
    assert _learn_threshold(rows) == 20


def test_crossover_is_order_independent_because_node_count_is_the_dispatch_coordinate() -> None:
    rows = [
        _row(40, 0.88, 0.84),
        _row(10, 1.04, 1.02),
        _row(30, 0.90, 0.86),
        _row(20, 0.94, 0.89),
    ]
    assert _learn_threshold(rows) == 20
