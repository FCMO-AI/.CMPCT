from benchmarks.one.one_g02_block_relation_sketch import (
    FAMILIES, SIZES, decide,
)


def _rows():
    rows=[]
    for size in SIZES:
        for family in FAMILIES:
            rows.append({
                "size":size,"family":family,"semantic_ok":True,"baseline_common_equal":True,
                "source_scan_ratio":1.0,"wall_ratio":1.0,"cpu_ratio":1.0,
                "candidate_wall_mib_s":300.0,"candidate_cpu_mib_s":300.0,
            })
    return rows


def test_decision_advances_only_complete_green_matrix():
    assert decide(_rows()) == "ADVANCE_BLOCK_RELATION_SKETCH"


def test_semantic_divergence_invalidates():
    rows=_rows(); rows[0]["semantic_ok"]=False
    assert decide(rows) == "INVALIDATE_BLOCK_RELATION_SKETCH"


def test_missing_cell_invalidates():
    assert decide(_rows()[:-1]) == "INVALIDATE_BLOCK_RELATION_SKETCH"


def test_compute_regression_holds():
    rows=_rows(); rows[0]["wall_ratio"]=1.36
    assert decide(rows) == "HOLD_BLOCK_RELATION_SKETCH"


def test_throughput_floor_holds():
    rows=_rows(); row=next(r for r in rows if r["size"]==1024*1024); row["candidate_wall_mib_s"]=249.0
    assert decide(rows) == "HOLD_BLOCK_RELATION_SKETCH"
