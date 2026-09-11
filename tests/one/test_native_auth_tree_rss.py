from __future__ import annotations

from benchmarks.one.one_g02_native_auth_tree_rss import DECISION_SIZE, LEAVES, SIZES, _decide


def _rows(ratio:float=0.80)->list[dict[str,object]]:
    rows=[]
    for size in SIZES:
        for leaf in LEAVES:
            rows.append({
                "size":size,"leaf_bytes":leaf,"semantic_ok":True,
                "reference_incremental_peak_kib_median":1000,
                "candidate_incremental_peak_kib_median":1000*ratio,
                "candidate_over_reference_incremental_rss":ratio,
            })
    return rows


def test_green_matrix_advances()->None:
    assert _decide(_rows()) == "ADVANCE_NATIVE_AUTH_TREE_RSS"


def test_missing_row_invalidates()->None:
    rows=_rows(); rows.pop()
    assert _decide(rows) == "INVALIDATE_NATIVE_AUTH_TREE_RSS"


def test_semantic_failure_invalidates()->None:
    rows=_rows(); rows[0]["semantic_ok"]=False
    assert _decide(rows) == "INVALIDATE_NATIVE_AUTH_TREE_RSS"


def test_zero_reference_delta_invalidates()->None:
    rows=_rows(); rows[0]["reference_incremental_peak_kib_median"]=0
    assert _decide(rows) == "INVALIDATE_NATIVE_AUTH_TREE_RSS"


def test_large_1_051_blocks()->None:
    rows=_rows()
    row=next(r for r in rows if r["size"] == DECISION_SIZE)
    row["candidate_over_reference_incremental_rss"]=1.051
    assert _decide(rows) == "HOLD_NATIVE_AUTH_TREE_RSS"


def test_only_one_large_material_win_blocks()->None:
    rows=_rows(ratio=0.95)
    large=[r for r in rows if r["size"] == DECISION_SIZE]
    large[0]["candidate_over_reference_incremental_rss"]=0.89
    assert _decide(rows) == "HOLD_NATIVE_AUTH_TREE_RSS"


def test_small_1_101_blocks()->None:
    rows=_rows()
    row=next(r for r in rows if r["size"] != DECISION_SIZE)
    row["candidate_over_reference_incremental_rss"]=1.101
    assert _decide(rows) == "HOLD_NATIVE_AUTH_TREE_RSS"
