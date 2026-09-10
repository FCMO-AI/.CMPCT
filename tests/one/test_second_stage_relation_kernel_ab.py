from __future__ import annotations

import benchmarks.one.one_g02_second_stage_relation_kernel_ab as kernel
from benchmarks.one.one_g02_second_stage_relation_kernel_ab import (
    KINDS,
    LENGTHS,
    RELATIONS,
    REPETITIONS,
    _baseline,
    _baseline_prepared,
    _candidate,
    _candidate_prepared,
    _make_case,
    _nomination_constant,
    _primary_pass,
    _second_positions,
    decide,
)
from experiments.one.general_law_archive import _sample_positions as writer_sample_positions


def test_kernel_contract_is_frozen() -> None:
    assert REPETITIONS == 101
    assert LENGTHS == (256, 4096, 16384, 65536, 262144)
    assert RELATIONS == ("add8", "xor")
    assert KINDS == ("true", "stage2_collision_first", "stage2_collision_last", "dual_collision_early")
    for length in LENGTHS:
        assert len(_second_positions(length)) == 15
        assert not (set(_second_positions(length)) & set(writer_sample_positions(length)))


def test_kernel_candidate_is_rejection_only_and_truth_equivalent() -> None:
    for relation in RELATIONS:
        for length in (256, 4096):
            for kind in KINDS:
                source, target = _make_case(relation, length, kind)
                assert _primary_pass(relation, source, target) is True
                expected = kind == "true"
                assert _baseline(relation, source, target) is expected
                assert _candidate(relation, source, target) is expected


def test_prepared_timing_boundary_does_not_resample_primary(monkeypatch) -> None:
    for relation in RELATIONS:
        for kind in KINDS:
            source, target = _make_case(relation, 4096, kind)
            primary = tuple(writer_sample_positions(len(source)))
            constant = _nomination_constant(relation, source, target, primary)
            expected = kind == "true"

            def fail_resample(_length: int):
                raise AssertionError("prepared timing arm must not resample primary positions")

            monkeypatch.setattr(kernel, "_sample_positions", fail_resample)
            assert _baseline_prepared(relation, source, target, constant, primary) is expected
            assert _candidate_prepared(relation, source, target, constant, primary) is expected
            monkeypatch.undo()


def test_first_and_last_collisions_hit_distinct_second_stage_positions() -> None:
    for relation in RELATIONS:
        for length in (4096, 16384):
            source_first, target_first = _make_case(relation, length, "stage2_collision_first")
            source_last, target_last = _make_case(relation, length, "stage2_collision_last")
            assert source_first == source_last
            diffs_first = [i for i, (a, b) in enumerate(zip(_candidate_truth(relation, source_first), target_first, strict=True)) if a != b]
            diffs_last = [i for i, (a, b) in enumerate(zip(_candidate_truth(relation, source_last), target_last, strict=True)) if a != b]
            second = _second_positions(length)
            assert diffs_first == [second[0]]
            assert diffs_last == [second[-1]]


def _candidate_truth(relation: str, source: bytes) -> bytes:
    if relation == "add8":
        return bytes((b + 37) & 0xFF for b in source)
    if relation == "xor":
        return bytes(b ^ 0xA5 for b in source)
    raise KeyError(relation)


def _row(kind: str, cpu_ratio: float, wall_ratio: float, *, length: int = 4096) -> dict:
    baseline = 1_000_000
    return {
        "kind": kind,
        "length": length,
        "primary_pass": True,
        "baseline_value": kind == "true",
        "candidate_value": kind == "true",
        "expected": kind == "true",
        "baseline_cpu_ns": baseline,
        "candidate_cpu_ns": int(baseline * cpu_ratio),
        "baseline_wall_ns": baseline,
        "candidate_wall_ns": int(baseline * wall_ratio),
        "cpu_ratio": cpu_ratio,
        "wall_ratio": wall_ratio,
    }


def test_decision_refuses_survivor_debt_even_with_large_kill_win() -> None:
    rows = []
    for _relation in RELATIONS:
        rows.extend(
            [
                _row("true", 1.25, 1.25),
                _row("stage2_collision_first", 0.05, 0.05),
                _row("stage2_collision_last", 0.10, 0.10),
                _row("dual_collision_early", 1.25, 1.25),
            ]
        )
    decision, hypotheses = decide(rows)
    assert hypotheses["H2_hostile_benefit"] is True
    assert hypotheses["H3_survivor_debt"] is False
    assert hypotheses["H5_geometry_sensitivity"] is True
    assert decision == "HOLD_SECOND_STAGE_RELATION_KERNEL"


def test_decision_refuses_late_collision_even_if_first_collision_is_fast() -> None:
    rows = []
    for _relation in RELATIONS:
        rows.extend(
            [
                _row("true", 1.0, 1.0),
                _row("stage2_collision_first", 0.05, 0.05),
                _row("stage2_collision_last", 0.80, 0.80),
                _row("dual_collision_early", 1.0, 1.0),
            ]
        )
    decision, hypotheses = decide(rows)
    assert hypotheses["H2_hostile_benefit"] is False
    assert hypotheses["H5_geometry_sensitivity"] is False
    assert decision == "HOLD_SECOND_STAGE_RELATION_KERNEL"


def test_decision_retires_on_truth_mismatch() -> None:
    rows = [
        _row("true", 1.0, 1.0),
        _row("stage2_collision_first", 0.1, 0.1),
        _row("stage2_collision_last", 0.1, 0.1),
        _row("dual_collision_early", 1.0, 1.0),
    ]
    rows[0]["candidate_value"] = False
    decision, hypotheses = decide(rows)
    assert hypotheses["H1_correctness"] is False
    assert decision == "RETIRE_SECOND_STAGE_RELATION_KERNEL"
