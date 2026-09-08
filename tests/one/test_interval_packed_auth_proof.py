from __future__ import annotations

from benchmarks.one.one_g02_interval_packed_auth_proof import DECISION_SIZE, LEAVES, REQUESTS, SIZES, _decide


def _rows(ratio:float=0.95)->list[dict[str,object]]:
    rows=[]
    for size in SIZES:
        for leaf in LEAVES:
            for req in range(len(REQUESTS)):
                rows.append({"size":size,"leaf_bytes":leaf,"start":req,"length":4096,"semantic_ok":True,
                             "tree_digest_bytes_read":320,"proof_hash_bytes":320,
                             "candidate_over_ref_wall":ratio,"candidate_over_ref_cpu":ratio})
    return rows


def test_green_matrix_advances()->None:
    assert _decide(_rows()) == "ADVANCE_INTERVAL_PACKED_AUTH_PROOF"


def test_missing_row_invalidates()->None:
    rows=_rows(); rows.pop()
    assert _decide(rows) == "INVALIDATE_INTERVAL_PACKED_AUTH_PROOF"


def test_semantic_failure_invalidates()->None:
    rows=_rows(); rows[0]["semantic_ok"]=False
    assert _decide(rows) == "INVALIDATE_INTERVAL_PACKED_AUTH_PROOF"


def test_digest_overread_invalidates()->None:
    rows=_rows(); rows[0]["tree_digest_bytes_read"]=352
    assert _decide(rows) == "INVALIDATE_INTERVAL_PACKED_AUTH_PROOF"


def test_large_1_101_blocks()->None:
    rows=_rows(); row=next(r for r in rows if r["size"] == DECISION_SIZE); row["candidate_over_ref_wall"]=1.101
    assert _decide(rows) == "HOLD_INTERVAL_PACKED_AUTH_PROOF"


def test_small_1_151_blocks()->None:
    rows=_rows(); row=next(r for r in rows if r["size"] != DECISION_SIZE); row["candidate_over_ref_cpu"]=1.151
    assert _decide(rows) == "HOLD_INTERVAL_PACKED_AUTH_PROOF"


def test_only_thirteen_decisive_nonregressions_blocks()->None:
    rows=_rows(ratio=1.01); large=[r for r in rows if r["size"] == DECISION_SIZE]
    for r in large[:13]: r["candidate_over_ref_wall"]=0.99; r["candidate_over_ref_cpu"]=0.99
    assert _decide(rows) == "HOLD_INTERVAL_PACKED_AUTH_PROOF"
