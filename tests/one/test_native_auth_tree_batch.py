from __future__ import annotations

from benchmarks.one.one_g02_native_auth_tree_batch import DECISION_SIZE, LEAVES, SIZES, _decide


def _rows(wall=0.4,cpu=0.4):
    return [
        {"size":size,"leaf_bytes":leaf,"semantic_ok":True,
         "native_over_ref_wall":wall,"native_over_ref_cpu":cpu}
        for size in SIZES for leaf in LEAVES
    ]


def test_green_matrix_advances() -> None:
    assert _decide(_rows()) == "ADVANCE_NATIVE_AUTH_TREE_BATCH"


def test_large_wall_boundary_blocks() -> None:
    rows=_rows(); rows[-1]["native_over_ref_wall"]=0.501
    assert _decide(rows) == "HOLD_NATIVE_AUTH_TREE_BATCH"


def test_large_cpu_boundary_blocks() -> None:
    rows=_rows(); rows[-1]["native_over_ref_cpu"]=0.501
    assert _decide(rows) == "HOLD_NATIVE_AUTH_TREE_BATCH"


def test_small_regression_boundary_blocks() -> None:
    rows=_rows(); rows[0]["native_over_ref_wall"]=0.751
    assert _decide(rows) == "HOLD_NATIVE_AUTH_TREE_BATCH"


def test_semantic_failure_invalidates() -> None:
    rows=_rows(); rows[-1]["semantic_ok"]=False
    assert _decide(rows) == "INVALIDATE_NATIVE_AUTH_TREE_BATCH"


def test_missing_row_invalidates() -> None:
    assert _decide(_rows()[:-1]) == "INVALIDATE_NATIVE_AUTH_TREE_BATCH"


def test_frozen_decision_scale() -> None:
    assert DECISION_SIZE == 256 << 10
    assert tuple(SIZES) == (64 << 10,256 << 10)
    assert tuple(LEAVES) == (80,96,112,192)
