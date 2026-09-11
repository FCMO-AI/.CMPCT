from benchmarks.one.one_g02_lazy_segment_timing import (
    ADMITTED,
    CASES,
    REJECTED,
    _adjudicate,
)


def _rows(admitted=1.0, rejected=0.90):
    rows = []
    for case in CASES:
        ratio = admitted if case in ADMITTED else rejected
        rows.append(
            {
                "case": case,
                "lazy_over_eager_wall": ratio,
                "lazy_over_eager_cpu": ratio,
                "eager_segment_capacity_bytes": 12 << 20,
                "lazy_segment_capacity_bytes": 12 << 20 if case in ADMITTED else 0,
            }
        )
    return rows


def test_adjudicator_advances_only_when_all_frozen_gates_pass():
    decision, admitted_ok, rejected_ok = _adjudicate(_rows(), True)
    assert decision == "ADVANCE_LAZY_SEGMENT_TIMING"
    assert admitted_ok
    assert rejected_ok


def test_admitted_regression_blocks_advance():
    rows = _rows()
    rows[0]["lazy_over_eager_cpu"] = 1.051
    decision, admitted_ok, rejected_ok = _adjudicate(rows, True)
    assert decision == "HOLD_LAZY_SEGMENT_TIMING"
    assert not admitted_ok
    assert rejected_ok


def test_rejected_speedup_below_five_percent_blocks_advance():
    rows = _rows()
    rejected_case = REJECTED[0]
    row = next(row for row in rows if row["case"] == rejected_case)
    row["lazy_over_eager_wall"] = 0.951
    decision, admitted_ok, rejected_ok = _adjudicate(rows, True)
    assert decision == "HOLD_LAZY_SEGMENT_TIMING"
    assert admitted_ok
    assert not rejected_ok


def test_rejected_allocation_blocks_advance_even_with_speed_win():
    rows = _rows()
    rejected_case = REJECTED[1]
    row = next(row for row in rows if row["case"] == rejected_case)
    row["lazy_segment_capacity_bytes"] = 4096
    decision, admitted_ok, rejected_ok = _adjudicate(rows, True)
    assert decision == "HOLD_LAZY_SEGMENT_TIMING"
    assert admitted_ok
    assert not rejected_ok


def test_semantic_failure_invalidates_even_when_timing_is_green():
    decision, admitted_ok, rejected_ok = _adjudicate(_rows(), False)
    assert decision == "INVALIDATE_LAZY_SEGMENT_TIMING"
    assert admitted_ok
    assert rejected_ok


def test_missing_row_cannot_vacuously_advance():
    rows = _rows()[:-1]
    decision, admitted_ok, rejected_ok = _adjudicate(rows, True)
    assert decision == "HOLD_LAZY_SEGMENT_TIMING"
    assert not admitted_ok
    assert not rejected_ok
