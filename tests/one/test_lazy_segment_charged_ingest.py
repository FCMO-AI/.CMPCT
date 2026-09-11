from benchmarks.one.one_g02_lazy_segment_charged_ingest import (
    ADMITTED,
    CASES,
    DECISION_SIZE,
    REJECTED,
    SIZES,
    _adjudicate,
)


def _rows(wall=0.90, cpu=0.90):
    rows = []
    for size in SIZES:
        for case in CASES:
            enabled = case in ADMITTED
            rows.append({
                "size": size,
                "case": case,
                "lazy_over_eager_wall": wall,
                "lazy_over_eager_cpu": cpu,
                "eager_segment_capacity_bytes": 123 if enabled else 123,
                "lazy_segment_capacity_bytes": 123 if enabled else 0,
            })
    return rows


def test_green_matrix_advances():
    decision, admitted_ok, rejected_ok, small_ok = _adjudicate(_rows(), True)
    assert decision == "ADVANCE_LAZY_SEGMENT_CHARGED_INGEST"
    assert admitted_ok and rejected_ok and small_ok


def test_semantic_failure_invalidates():
    decision, *_ = _adjudicate(_rows(), False)
    assert decision == "INVALIDATE_LAZY_SEGMENT_CHARGED_INGEST"


def test_missing_row_cannot_vacuously_advance():
    rows = _rows()[:-1]
    decision, *_ = _adjudicate(rows, True)
    assert decision == "HOLD_LAZY_SEGMENT_CHARGED_INGEST"


def test_rejected_decision_row_above_gate_holds():
    rows = _rows()
    for row in rows:
        if row["size"] == DECISION_SIZE and row["case"] == REJECTED[0]:
            row["lazy_over_eager_cpu"] = 0.971
    decision, _, rejected_ok, _ = _adjudicate(rows, True)
    assert decision == "HOLD_LAZY_SEGMENT_CHARGED_INGEST"
    assert not rejected_ok


def test_admitted_decision_row_above_gate_holds():
    rows = _rows()
    for row in rows:
        if row["size"] == DECISION_SIZE and row["case"] == ADMITTED[0]:
            row["lazy_over_eager_wall"] = 1.051
    decision, admitted_ok, _, _ = _adjudicate(rows, True)
    assert decision == "HOLD_LAZY_SEGMENT_CHARGED_INGEST"
    assert not admitted_ok


def test_small_transfer_regression_holds():
    rows = _rows()
    for row in rows:
        if row["size"] == SIZES[0] and row["case"] == CASES[0]:
            row["lazy_over_eager_wall"] = 1.081
    decision, _, _, small_ok = _adjudicate(rows, True)
    assert decision == "HOLD_LAZY_SEGMENT_CHARGED_INGEST"
    assert not small_ok
