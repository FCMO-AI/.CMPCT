from __future__ import annotations

from benchmarks.one.one_g02_native_auth_verify import LEAVES, SIZE, _decide, _requests


def _rows(wall: float=0.40,cpu: float=0.40):
    return [
        {"leaf_bytes":leaf,"start":start,"length":length,"semantic_ok":True,"hostile_ok":True,
         "wall_ratio":wall,"cpu_ratio":cpu}
        for leaf in LEAVES for start,length in _requests(SIZE)
    ]


def test_green_complete_matrix_advances():
    assert _decide(_rows()) == "ADVANCE_NATIVE_AUTH_VERIFY"


def test_worst_wall_0651_holds():
    rows=_rows(); rows[0]["wall_ratio"]=0.651
    assert _decide(rows) == "HOLD_NATIVE_AUTH_VERIFY"


def test_worst_cpu_0651_holds():
    rows=_rows(); rows[0]["cpu_ratio"]=0.651
    assert _decide(rows) == "HOLD_NATIVE_AUTH_VERIFY"


def test_only_eleven_material_rows_holds():
    rows=_rows()
    for row in rows[11:]: row["wall_ratio"]=0.60; row["cpu_ratio"]=0.60
    assert _decide(rows) == "HOLD_NATIVE_AUTH_VERIFY"


def test_semantic_failure_invalidates():
    rows=_rows(); rows[0]["semantic_ok"]=False
    assert _decide(rows) == "INVALIDATE_NATIVE_AUTH_VERIFY"


def test_hostile_failure_invalidates():
    rows=_rows(); rows[0]["hostile_ok"]=False
    assert _decide(rows) == "INVALIDATE_NATIVE_AUTH_VERIFY"


def test_missing_row_invalidates():
    assert _decide(_rows()[:-1]) == "INVALIDATE_NATIVE_AUTH_VERIFY"


def test_duplicate_cannot_replace_missing_row():
    rows=_rows(); rows[-1]=dict(rows[0])
    assert _decide(rows) == "INVALIDATE_NATIVE_AUTH_VERIFY"
