from benchmarks.one.one_g02_generic_execution_plan import FAMILIES, SIZES
from benchmarks.one.one_g02_native_plan_bulk import decide


def rows(arithmetic=0.20, other=1.0):
    return [{"size": size, "family": family, "wall_ratio": arithmetic if family in {"xor2", "add8_3"} else other, "cpu_ratio": arithmetic if family in {"xor2", "add8_3"} else other} for size in SIZES for family in FAMILIES]


def test_green_exact_matrix_advances():
    assert decide(rows(), True) == "ADVANCE_NATIVE_PLAN_BULK"


def test_missing_or_duplicate_cell_invalidates():
    good = rows()
    assert decide(good[:-1], True) == "INVALIDATE_NATIVE_PLAN_BULK"
    assert decide(good[:-1] + [dict(good[0])], True) == "INVALIDATE_NATIVE_PLAN_BULK"


def test_semantic_failure_invalidates():
    assert decide(rows(), False) == "INVALIDATE_NATIVE_PLAN_BULK"


def test_arithmetic_0351_holds():
    data = rows()
    target = next(r for r in data if r["family"] == "xor2")
    target["wall_ratio"] = 0.351
    assert decide(data, True) == "HOLD_NATIVE_PLAN_BULK"


def test_non_arithmetic_1051_holds():
    data = rows()
    target = next(r for r in data if r["family"] == "repeat")
    target["cpu_ratio"] = 1.051
    assert decide(data, True) == "HOLD_NATIVE_PLAN_BULK"
