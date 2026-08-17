from __future__ import annotations

import random

import pytest

from experiments import representation_superoptimizer_v030_safe as RSO


def _baseline(target: str, cost: int, name: str = "direct") -> RSO.Plan:
    return RSO.Plan(target, name, cost, representation_kind="direct")


def test_shared_facility_can_be_globally_profitable_when_locally_unprofitable() -> None:
    # Charging the 120-byte base independently makes each 10+120 reference look worse than a 100-byte direct
    # target.  Globally the base opens once: 120 + 10 + 10 = 140 < 200.
    problem = RSO.Problem(
        [RSO.Facility("base", 120, "mosaic-root")],
        [
            _baseline("a", 100),
            _baseline("b", 100),
            RSO.Plan("a", "ref-a", 10, frozenset({"base"}), dependency_depth=1, representation_kind="reference"),
            RSO.Plan("b", "ref-b", 10, frozenset({"base"}), dependency_depth=1, representation_kind="reference"),
        ],
    )
    exact = RSO.exact_extract(problem)
    beam = RSO.beam_extract(problem)
    assert exact.total_bytes == 140
    assert exact.opened == frozenset({"base"})
    assert beam.total_bytes == exact.total_bytes


def test_multi_root_requirement_bundle_can_become_feasible_atomically() -> None:
    problem = RSO.Problem(
        [RSO.Facility("r1", 30), RSO.Facility("r2", 30)],
        [
            _baseline("target", 100),
            RSO.Plan(
                "target", "mosaic-2root", 10, frozenset({"r1", "r2"}),
                dependency_depth=1, read_amplification=3.0, representation_kind="mosaic",
            ),
        ],
    )
    beam = RSO.beam_extract(problem, beam_width=4, max_rounds=2)
    assert beam.total_bytes == 70
    assert beam.opened == frozenset({"r1", "r2"})
    assert beam.selected[0].plan_id == "mosaic-2root"


def test_global_context_can_flip_geometry_to_reference_without_phase_ordering() -> None:
    facilities = [RSO.Facility("shared-root", 80)]
    plans = [
        _baseline("a", 100), _baseline("b", 100),
        RSO.Plan("a", "geometry-a", 60, representation_kind="geometry"),
        RSO.Plan("b", "geometry-b", 60, representation_kind="geometry"),
        RSO.Plan("a", "ref-a", 10, frozenset({"shared-root"}), dependency_depth=1, representation_kind="reference"),
        RSO.Plan("b", "ref-b", 10, frozenset({"shared-root"}), dependency_depth=1, representation_kind="reference"),
    ]
    problem = RSO.Problem(facilities, plans)
    # Per-target local accounting would choose Geometry (60 < 80+10), but shared opening changes the optimum.
    row = RSO.exact_extract(problem)
    assert row.total_bytes == 100
    assert {plan.plan_id for plan in row.selected} == {"ref-a", "ref-b"}


def test_synthetic_atom_facility_amortizes_across_many_targets() -> None:
    facilities = [RSO.Facility("atom:shared-header", 50, "synthetic-atom")]
    plans = []
    for index in range(4):
        target = f"f{index}"
        plans.append(_baseline(target, 40))
        plans.append(RSO.Plan(
            target, f"atom-ref-{index}", 10, frozenset({"atom:shared-header"}),
            dependency_depth=1, read_amplification=2.0, representation_kind="substrate",
        ))
    row = RSO.exact_extract(RSO.Problem(facilities, plans))
    assert row.total_bytes == 90
    assert row.facility_bytes == 50


def test_hard_policy_filters_size_winner_before_optimization() -> None:
    problem = RSO.Problem(
        [RSO.Facility("base", 1)],
        [
            _baseline("x", 100),
            RSO.Plan(
                "x", "unsafe-tiny", 1, frozenset({"base"}), dependency_depth=2,
                read_amplification=100.0, representation_kind="unsafe",
            ),
        ],
        policy=RSO.Policy(max_dependency_depth=1, max_read_amplification=8.0),
    )
    row = RSO.exact_extract(problem)
    assert row.total_bytes == 100
    assert row.opened == frozenset()
    assert row.selected[0].plan_id == "direct"


def test_every_target_requires_facility_free_fallback() -> None:
    with pytest.raises(ValueError, match="fallback"):
        RSO.Problem(
            [RSO.Facility("base", 10)],
            [RSO.Plan("x", "ref", 1, frozenset({"base"}), dependency_depth=1)],
        )


def test_beam_matches_exact_on_random_small_shared_cost_problems() -> None:
    rng = random.Random(20260817)
    for case in range(20):
        facilities = [RSO.Facility(f"f{index}", rng.randrange(5, 40)) for index in range(5)]
        plans = []
        for target_index in range(6):
            target = f"t{target_index}"
            plans.append(_baseline(target, rng.randrange(60, 120)))
            for candidate_index in range(4):
                width = rng.randrange(1, 3)
                req = frozenset(rng.sample([facility.facility_id for facility in facilities], width))
                plans.append(RSO.Plan(
                    target,
                    f"c{case}-{target_index}-{candidate_index}",
                    rng.randrange(5, 80),
                    req,
                    dependency_depth=1,
                    read_amplification=float(rng.randrange(1, 8)),
                    representation_kind="research",
                ))
        problem = RSO.Problem(facilities, plans)
        exact = RSO.exact_extract(problem)
        # Wide beam / generous tiny-case budget should reproduce the exact oracle, giving us a regression
        # detector for future pruning heuristics before they are trusted on real representation candidates.
        beam = RSO.beam_extract(problem, beam_width=128, max_rounds=8, max_expansions=5000)
        assert beam.total_bytes == exact.total_bytes


def test_candidate_input_order_does_not_change_exact_or_beam_result() -> None:
    facilities = [RSO.Facility("a", 20), RSO.Facility("b", 25)]
    plans = [
        _baseline("x", 100), _baseline("y", 90),
        RSO.Plan("x", "xa", 30, frozenset({"a"}), dependency_depth=1),
        RSO.Plan("y", "yb", 25, frozenset({"b"}), dependency_depth=1),
        RSO.Plan("x", "xab", 5, frozenset({"a", "b"}), dependency_depth=1),
    ]
    forward = RSO.Problem(facilities, plans)
    reverse = RSO.Problem(list(reversed(facilities)), list(reversed(plans)))
    assert RSO.exact_extract(forward).total_bytes == RSO.exact_extract(reverse).total_bytes
    assert RSO.beam_extract(forward).total_bytes == RSO.beam_extract(reverse).total_bytes


def test_baseline_audit_surface_works_for_slotted_extraction() -> None:
    problem = RSO.Problem([], [_baseline("x", 17)])
    row = problem.baseline()
    assert row.total_bytes == 17
    assert row.method == "baseline"
    assert RSO.explain(row)["selected"][0]["plan"] == "direct"
