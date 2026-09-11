from __future__ import annotations

from benchmarks.one.one_g02_observer_run_fill_law import FAMILIES, SIZES, adjudicate


def _green_rows():
    rows = []
    for size in SIZES:
        for family in FAMILIES:
            wire = 1.0
            if family == "structured" and size == (1 << 20):
                wire = 0.89
            if family == "long_runs" and size == (1 << 20):
                wire = 0.54
            rows.append(
                {
                    "bytes": size,
                    "family": family,
                    "semantic_ok": True,
                    "bounded": True,
                    "control_wire_bytes": 1000,
                    "candidate_wire_bytes": int(1000 * wire),
                    "control_surprise_bytes": 1000,
                    "candidate_surprise_bytes": int(1000 * wire),
                    "candidate_over_control_reader_work": 1.0,
                    "candidate_over_control_wire": wire,
                    "candidate_over_control_wall": 1.0,
                    "candidate_over_control_cpu": 1.0,
                }
            )
    return rows


def test_complete_green_matrix_advances():
    assert adjudicate(_green_rows()) == "ADVANCE_OBSERVER_RUN_FILL_LAW"


def test_missing_or_duplicate_cell_invalidates():
    rows = _green_rows()
    assert adjudicate(rows[:-1]) == "INVALIDATE_OBSERVER_RUN_FILL_LAW"
    duplicate = list(rows)
    duplicate[-1] = dict(duplicate[0])
    assert adjudicate(duplicate) == "INVALIDATE_OBSERVER_RUN_FILL_LAW"


def test_semantic_or_bound_failure_invalidates():
    rows = _green_rows()
    rows[0]["semantic_ok"] = False
    assert adjudicate(rows) == "INVALIDATE_OBSERVER_RUN_FILL_LAW"
    rows = _green_rows()
    rows[0]["bounded"] = False
    assert adjudicate(rows) == "INVALIDATE_OBSERVER_RUN_FILL_LAW"


def test_density_thresholds_are_strictly_enforced():
    rows = _green_rows()
    target = next(row for row in rows if row["bytes"] == (1 << 20) and row["family"] == "long_runs")
    target["candidate_over_control_wire"] = 0.551
    target["candidate_wire_bytes"] = 551
    assert adjudicate(rows) == "HOLD_OBSERVER_RUN_FILL_LAW"

    rows = _green_rows()
    target = next(row for row in rows if row["bytes"] == (1 << 20) and row["family"] == "structured")
    target["candidate_over_control_wire"] = 0.901
    target["candidate_wire_bytes"] = 901
    assert adjudicate(rows) == "HOLD_OBSERVER_RUN_FILL_LAW"


def test_control_and_run_rich_time_vetoes_are_enforced():
    rows = _green_rows()
    control = next(row for row in rows if row["family"] == "random")
    control["candidate_over_control_wall"] = 1.051
    assert adjudicate(rows) == "HOLD_OBSERVER_RUN_FILL_LAW"

    rows = _green_rows()
    rich = next(row for row in rows if row["family"] == "long_runs")
    rich["candidate_over_control_cpu"] = 1.101
    assert adjudicate(rows) == "HOLD_OBSERVER_RUN_FILL_LAW"


def test_wire_surprise_and_reader_regressions_cannot_hide():
    rows = _green_rows()
    rows[0]["candidate_wire_bytes"] = 1001
    assert adjudicate(rows) == "HOLD_OBSERVER_RUN_FILL_LAW"

    rows = _green_rows()
    rows[0]["candidate_surprise_bytes"] = 1001
    assert adjudicate(rows) == "HOLD_OBSERVER_RUN_FILL_LAW"

    rows = _green_rows()
    rows[0]["candidate_over_control_reader_work"] = 1.051
    assert adjudicate(rows) == "HOLD_OBSERVER_RUN_FILL_LAW"
