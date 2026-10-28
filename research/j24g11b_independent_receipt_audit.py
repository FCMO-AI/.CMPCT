#!/usr/bin/env python3
"""Independent J24G11b receipt verifier. Standard-library only; no CMPCT import.

Audits recorded real same-head measurements, source identities and hostile
claims; it cannot reconstruct .cmpct bytes absent physical archive artifacts.
"""
import copy,json,statistics,sys
from pathlib import Path
def audit(r):
    assert r["release_credit"]==0
    assert r["prereg"]=="c363ec7dcec370509a8318dae8d5603fe5835808"
    assert r["source_original"]=="19f8d0313a93655af05a365d1777a7a303a550be"
    assert r["old_reader_blob"]=="4bcedb059316171963d258fc93caaa49fec56f12"
    assert r["source_sqlite"]=="da5552d4f74113de1887fdad9683b433bb6e6cf2"
    assert r["sqlite_reader_blob"]=="0a8a7afa036cb4988b80836bcbe550c3b5d0bb40"
    assert r["candidate_reader_blob"]=="f13c5492f5acfa1cfcfec97cdbe0da71e41e327b"
    assert not r["global_RSS_bounded"] and not r["per_chain_bounded"]
    assert not r["same_inode_mutation_supported"]
    o=r["oracle"]
    assert o["small_batch_updates"]==1000 and o["staging_positions"]==2000
    assert o["packed_merge_after_hot_cap"] and o["disk_handoff_copies_hot_and_packed"]
    assert o["independent_db_rows"]==131075 and o["temp_deleted"]
    assert o["small_batch_wall_ms"]>=0
    assert set(r["cases"])=={"independent-pairs","valid-rename"}
    tested=0
    for label,case in r["cases"].items():
        assert case["label"]==label
        assert len(case["archive_sha256"])==64 and case["archive_bytes"]>0
        assert set(case["raw"])=={"old","sqlite","candidate","unbounded"}
        expected=18001 if label=="independent-pairs" else 2
        for k,rows in case["raw"].items():
            assert len(rows)>=3
            for i,row in enumerate(rows):
                assert row["decoder_calls"]==case["decoder_counts"][k][i]==expected
                assert row["physical_bytes"]==case["archive_bytes"]
                assert row["wall_ms"]>0 and row["cpu_ms"]>0
                tested+=1
            assert abs(statistics.median(x["wall_ms"] for x in rows)-case["median_wall_ms"][k])<1e-8
            assert abs(statistics.median(x["cpu_ms"] for x in rows)-case["median_cpu_ms"][k])<1e-8
        m=case["median_wall_ms"]
        assert abs(case["old_to_candidate_wall_ratio"]-m["old"]/m["candidate"])<1e-8
        assert abs(case["sqlite_to_candidate_wall_ratio"]-m["sqlite"]/m["candidate"])<1e-8
        assert abs(case["unbounded_to_candidate_wall_ratio"]-m["unbounded"]/m["candidate"])<1e-8
    a=r["cases"]["independent-pairs"];v=r["cases"]["valid-rename"]
    assert a["old_to_candidate_wall_ratio"]>=2
    assert v["median_wall_ms"]["candidate"]<=1.25*v["median_wall_ms"]["old"]
    assert r["decision"]=="NARROW_STAGED_PRODUCT_SEED"
    return {"raw_samples_checked":tested,"decision":r["decision"],
            "source_bound":True,"output_scope":"receipt consistency, not second physical archive decode"}
def hostile(r):
    cases=[
        lambda q:q.__setitem__("release_credit",1),
        lambda q:q["oracle"].__setitem__("independent_db_rows",131074),
        lambda q:q["cases"]["independent-pairs"]["decoder_counts"]["candidate"].__setitem__(0,42),
        lambda q:q["cases"]["valid-rename"]["median_wall_ms"].__setitem__("candidate",1e8),
        lambda q:q.__setitem__("candidate_reader_blob","fabricated"),
        lambda q:q["cases"]["independent-pairs"]["raw"]["old"][0].__setitem__("cpu_ms",0),
    ]
    for edit in cases:
        q=copy.deepcopy(r);edit(q)
        try:audit(q)
        except AssertionError:pass
        else:raise AssertionError("tampered evidence accepted")
    return len(cases)
def main():
    p=Path(sys.argv[1] if len(sys.argv)>1 else "j24g11b-artifacts/court.json")
    d=json.loads(p.read_text());result=audit(d)
    result["tamper_cases_rejected"]=hostile(d)
    p.with_name("audit.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("J24G11B_INDEPENDENT_AUDIT="+json.dumps(result,sort_keys=True))
if __name__=="__main__":main()
