from benchmarks.one.one_g02_native_auth_verify_prepacked_boundary import (
    BOUNDARY_MATERIAL_MAX,
    BOUNDARY_WORST_MAX,
    CONTROL_MATERIAL_MAX,
    CONTROL_WORST_MAX,
    LEAVES,
    SIZE,
    _decide,
    _requests,
)


def _green_rows():
    rows=[]
    for leaf in LEAVES:
        for start,length in _requests(SIZE):
            rows.append({
                "leaf_bytes":leaf,"start":start,"length":length,
                "semantic_ok":True,"hostile_ok":True,
                "prepacked_control_wall_ratio":CONTROL_MATERIAL_MAX-0.05,
                "prepacked_control_cpu_ratio":CONTROL_MATERIAL_MAX-0.05,
                "prepacked_charged_wall_ratio":BOUNDARY_MATERIAL_MAX-0.05,
                "prepacked_charged_cpu_ratio":BOUNDARY_MATERIAL_MAX-0.05,
            })
    return rows


def test_complete_green_matrix_advances():
    assert _decide(_green_rows()) == "ADVANCE_PREPACKED_NATIVE_AUTH_VERIFY_BOUNDARY"


def test_control_worst_gate_is_strict():
    rows=_green_rows(); rows[0]["prepacked_control_wall_ratio"]=CONTROL_WORST_MAX+0.001
    assert _decide(rows) == "HOLD_PREPACKED_NATIVE_AUTH_VERIFY_BOUNDARY"


def test_fewer_than_twelve_control_material_rows_holds():
    rows=_green_rows()
    for row in rows[:5]:
        row["prepacked_control_wall_ratio"]=CONTROL_MATERIAL_MAX+0.01
        row["prepacked_control_cpu_ratio"]=CONTROL_MATERIAL_MAX+0.01
    assert _decide(rows) == "HOLD_PREPACKED_NATIVE_AUTH_VERIFY_BOUNDARY"


def test_boundary_worst_gate_is_strict():
    rows=_green_rows(); rows[-1]["prepacked_charged_cpu_ratio"]=BOUNDARY_WORST_MAX+0.001
    assert _decide(rows) == "HOLD_PREPACKED_NATIVE_AUTH_VERIFY_BOUNDARY"


def test_fewer_than_twelve_boundary_material_rows_holds():
    rows=_green_rows()
    for row in rows[:5]:
        row["prepacked_charged_wall_ratio"]=BOUNDARY_MATERIAL_MAX+0.01
        row["prepacked_charged_cpu_ratio"]=BOUNDARY_MATERIAL_MAX+0.01
    assert _decide(rows) == "HOLD_PREPACKED_NATIVE_AUTH_VERIFY_BOUNDARY"


def test_semantic_or_hostile_failure_invalidates():
    rows=_green_rows(); rows[0]["semantic_ok"]=False
    assert _decide(rows) == "INVALIDATE_PREPACKED_NATIVE_AUTH_VERIFY_BOUNDARY"
    rows=_green_rows(); rows[0]["hostile_ok"]=False
    assert _decide(rows) == "INVALIDATE_PREPACKED_NATIVE_AUTH_VERIFY_BOUNDARY"


def test_missing_or_duplicate_matrix_cell_invalidates():
    rows=_green_rows()[:-1]
    assert _decide(rows) == "INVALIDATE_PREPACKED_NATIVE_AUTH_VERIFY_BOUNDARY"
    rows=_green_rows(); rows[-1]=dict(rows[0])
    assert _decide(rows) == "INVALIDATE_PREPACKED_NATIVE_AUTH_VERIFY_BOUNDARY"
