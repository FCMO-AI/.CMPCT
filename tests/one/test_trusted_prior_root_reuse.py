from benchmarks.one.one_g02_trusted_prior_root_reuse import (
    CASES,
    DECISION_SIZE,
    SIZES,
    _adjudicate,
)


def _rows(wall=0.94, cpu=0.94):
    rows = []
    for size in SIZES:
        for case in CASES:
            rows.append({
                "size": size,
                "case": case,
                "trusted_over_rehash_wall": wall,
                "trusted_over_rehash_cpu": cpu,
            })
    return rows


def test_green_matrix_advances():
    decision, target_ok, guard_ok, small_ok = _adjudicate(_rows(), True)
    assert decision == "ADVANCE_TRUSTED_PRIOR_ROOT_REUSE"
    assert target_ok and guard_ok and small_ok


def test_only_three_material_wins_hold():
    rows = _rows(0.94, 0.94)
    touched = 0
    for row in rows:
        if row["size"] == DECISION_SIZE and touched < 2:
            row["trusted_over_rehash_wall"] = 0.99
            row["trusted_over_rehash_cpu"] = 0.99
            touched += 1
    assert _adjudicate(rows, True)[0] == "HOLD_TRUSTED_PRIOR_ROOT_REUSE"


def test_single_decision_regression_blocks():
    rows = _rows()
    for row in rows:
        if row["size"] == DECISION_SIZE:
            row["trusted_over_rehash_wall"] = 1.021
            break
    assert _adjudicate(rows, True)[0] == "HOLD_TRUSTED_PRIOR_ROOT_REUSE"


def test_small_transfer_regression_blocks():
    rows = _rows()
    for row in rows:
        if row["size"] == SIZES[0]:
            row["trusted_over_rehash_cpu"] = 1.051
            break
    assert _adjudicate(rows, True)[0] == "HOLD_TRUSTED_PRIOR_ROOT_REUSE"


def test_semantic_failure_invalidates():
    assert _adjudicate(_rows(), False)[0] == "INVALIDATE_TRUSTED_PRIOR_ROOT_REUSE"


def test_missing_row_cannot_vacuously_advance():
    rows = _rows()[:-1]
    assert _adjudicate(rows, True)[0] == "HOLD_TRUSTED_PRIOR_ROOT_REUSE"
