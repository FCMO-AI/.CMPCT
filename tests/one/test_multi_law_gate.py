from __future__ import annotations

import pytest

from benchmarks.one.one_g02_multi_law_gate import FAMILIES, SIZES, decide, make_case, oracle_expected
from experiments.one.multi_law_gate import observe_multi_law_gate


def test_gate_is_deterministic_and_charges_exactly_one_source_scan() -> None:
    data = make_case("add8_ramp", 64 * 1024)
    first = observe_multi_law_gate(data)
    second = observe_multi_law_gate(data)
    assert first == second
    assert first.stats.source_scan_bytes == len(data)
    assert first.decision.add8


def test_run_and_reuse_are_nominated_without_new_reader_semantics() -> None:
    data = make_case("long_runs", 64 * 1024)
    result = observe_multi_law_gate(data)
    assert result.decision.run
    assert result.decision.reuse
    assert result.decision.run_support_bytes > 0
    assert result.decision.reuse_support_bytes > 0


def test_xor_relation_is_nominated() -> None:
    data = make_case("xor_chain", 64 * 1024)
    result = observe_multi_law_gate(data)
    assert result.decision.xor
    assert result.decision.xor_support_bytes > 0


def test_random_control_does_not_launch_arithmetic_or_xor_search() -> None:
    data = make_case("random", 64 * 1024)
    result = observe_multi_law_gate(data)
    assert not result.decision.add8
    assert not result.decision.xor


def test_type_and_empty_semantics() -> None:
    with pytest.raises(TypeError):
        observe_multi_law_gate(bytearray(b"abc"))  # type: ignore[arg-type]
    empty = observe_multi_law_gate(b"")
    assert empty.stats.source_scan_bytes == 0
    assert not any((empty.decision.run, empty.decision.reuse, empty.decision.add8, empty.decision.xor))


def _green_rows() -> list[dict]:
    rows = []
    for size in SIZES:
        for family in FAMILIES:
            expected = oracle_expected(family)
            rows.append({
                "size": size,
                "family": family,
                "expected": sorted(expected),
                "actual": sorted(expected),
                "false_negatives": 0,
                "unexpected_nominations": 0,
                "source_scan_ratio": 1.0,
                "retained_fraction": 0.01,
            })
    return rows


def test_decision_rejects_missing_or_duplicate_matrix_cells() -> None:
    rows = _green_rows()
    assert decide(rows) == "ADVANCE_MULTI_LAW_GATE"
    assert decide(rows[:-1]) == "INVALIDATE_MULTI_LAW_GATE"
    duplicate = list(rows)
    duplicate[-1] = dict(duplicate[0])
    assert decide(duplicate) == "INVALIDATE_MULTI_LAW_GATE"


def test_decision_holds_false_negative_and_resource_debt() -> None:
    rows = _green_rows()
    rows[0]["false_negatives"] = 1
    assert decide(rows) == "HOLD_MULTI_LAW_GATE"
    rows = _green_rows()
    rows[0]["retained_fraction"] = 0.151
    assert decide(rows) == "HOLD_MULTI_LAW_GATE"
