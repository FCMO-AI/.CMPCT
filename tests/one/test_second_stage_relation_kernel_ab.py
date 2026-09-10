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
    assert KINDS == ("true", "stage2_collision", "dual_collision")
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
                _row("stage2_collision", 0.05, 0.05),
                _row("dual_collision", 1.25, 1.25),
            ]
        )
    decision, hypotheses = decide(rows)
    assert hypotheses["H2_hostile_benefit"] is True
    assert hypotheses["H3_survivor_debt"] is False
    assert decision == "HOLD_SECOND_STAGE_RELATION_KERNEL"


def test_decision_retires_on_truth_mismatch() -> None:
    rows = [
        _row("true", 1.0, 1.0),
        _row("stage2_collision", 0.1, 0.1),
        _row("dual_collision", 1.0, 1.0),
    ]
    rows[0]["candidate_value"] = False
    decision, hypotheses = decide(rows)
    assert hypotheses["H1_correctness"] is False
    assert decision == "RETIRE_SECOND_STAGE_RELATION_KERNEL"
