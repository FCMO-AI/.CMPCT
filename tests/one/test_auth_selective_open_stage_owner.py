from __future__ import annotations

from benchmarks.one.one_g02_auth_selective_open_stage_owner import LEAVES, PIPELINES, SIZE, _decide, _requests


def _rows(proof_share:float=0.25,verify_share:float=0.75)->list[dict[str,object]]:
    rows=[]
    for pipeline in PIPELINES:
        for leaf in LEAVES:
            for start,length in _requests(SIZE):
                rows.append({"pipeline":pipeline,"leaf_bytes":leaf,"start":start,"length":length,"semantic_ok":True,
                             "proof_wall_share":proof_share,"proof_cpu_share":proof_share,
                             "verify_wall_share":verify_share,"verify_cpu_share":verify_share})
    return rows


def test_verifier_owner_advances_classification()->None:
    assert _decide(_rows()) == "OWNER_AUTH_VERIFY"


def test_proof_owner_classifies()->None:
    assert _decide(_rows(0.75,0.25)) == "OWNER_PROOF_EXTRACT"


def test_distributed_classifies()->None:
    assert _decide(_rows(0.50,0.50)) == "DISTRIBUTED_AUTH_SELECTIVE_OPEN"


def test_only_eleven_verifier_owner_rows_per_pipeline_is_distributed()->None:
    rows=_rows(0.50,0.50)
    for pipeline in PIPELINES:
        subset=[r for r in rows if r["pipeline"] == pipeline]
        for r in subset[:11]:
            r["verify_wall_share"]=0.60; r["verify_cpu_share"]=0.60
            r["proof_wall_share"]=0.40; r["proof_cpu_share"]=0.40
    assert _decide(rows) == "DISTRIBUTED_AUTH_SELECTIVE_OPEN"


def test_missing_row_invalidates()->None:
    rows=_rows(); rows.pop()
    assert _decide(rows) == "INVALIDATE_AUTH_SELECTIVE_OPEN_STAGE_OWNER"


def test_duplicate_row_cannot_hide_missing_cell()->None:
    rows=_rows(); rows[-1]=dict(rows[0])
    assert _decide(rows) == "INVALIDATE_AUTH_SELECTIVE_OPEN_STAGE_OWNER"


def test_semantic_failure_invalidates()->None:
    rows=_rows(); rows[0]["semantic_ok"]=False
    assert _decide(rows) == "INVALIDATE_AUTH_SELECTIVE_OPEN_STAGE_OWNER"
