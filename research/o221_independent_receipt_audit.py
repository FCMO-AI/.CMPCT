#!/usr/bin/env python3
"""O221 separate raw-receipt decision auditor. No import from O221 experiment."""
import hashlib
import json
import math
from pathlib import Path
import statistics
import sys

N=(65536,262144)
Q=(1,64)
K=("fixed","cdc")
A=("baseline","stride")

def check(path):
    obj=json.loads(Path(path).read_text(encoding="utf-8"))
    assert obj["question"]=="O221"
    assert obj["prereg_commit"]=="9114674cf217dd8b8b463f4f602fa8b91b825fee"
    assert obj["exact_source_parent"]=="c5e13bb3fbb4cdade8b64246658ce7c7818de41f"
    archives={(x["kind"],x["n"]):x for x in obj["archives"]}
    assert len(archives)==4
    for kind in K:
        for n in N:
            a=archives[(kind,n)]
            assert a["logical_sha256"]==hashlib.sha256(b"Q"*n).hexdigest()
            assert a["archive_bytes"]>0 and len(a["archive_sha256"])==64
    hold={v["kind"]:v for v in obj["held_out_variable_payloads"]}
    assert set(hold)==set(K)
    assert all(hold[k]["case_count"]>1000 and hold[k]["repeated_reference_count"]==173 for k in K)
    s=obj["samples"]
    assert len(s)==48, len(s)
    distinct=set()
    for row in s:
        key=(row["kind"],row["n"],row["q"],row["rep"],row["arm"])
        assert key not in distinct,key
        distinct.add(key)
        assert row["archive_sha256"]==archives[(row["kind"],row["n"])]["archive_sha256"]
        assert row["logical_digest"]==archives[(row["kind"],row["n"])]["logical_sha256"]
        assert row["count"]==row["q"]
        assert row["anchor_count"]==(0 if row["arm"]=="baseline" else
                                     (row["n"]+255)//256)
        assert all(isinstance(row[x],(int,float)) and math.isfinite(row[x])
                   and row[x]>0 for x in ("wall_ms","cpu_ms","process_wall_ms","peak_rss_kib"))
    for kind in K:
        for n in N:
            for q in Q:
                for rep in range(3):
                    pairs=[x for x in s if x["kind"]==kind and x["n"]==n
                           and x["q"]==q and x["rep"]==rep]
                    assert {x["arm"] for x in pairs}==set(A)
                    assert len(pairs)==2
                    assert len({x["ranges_digest"] for x in pairs})==1
                    assert len({x["range_starts_sha256"] for x in pairs})==1
    summaries={(x["kind"],x["n"],x["q"]):x for x in obj["summary"]}
    assert len(summaries)==8
    decisive=[]
    for kind in K:
        for n in N:
            for q in Q:
                r=summaries[(kind,n,q)]
                groups={arm:[x for x in s if x["kind"]==kind and x["n"]==n and
                             x["q"]==q and x["arm"]==arm] for arm in A}
                expected={
                    "baseline_wall_ms":statistics.median(x["wall_ms"] for x in groups["baseline"]),
                    "stride_wall_ms":statistics.median(x["wall_ms"] for x in groups["stride"]),
                    "baseline_cpu_ms":statistics.median(x["cpu_ms"] for x in groups["baseline"]),
                    "stride_cpu_ms":statistics.median(x["cpu_ms"] for x in groups["stride"]),
                }
                for name,value in expected.items():
                    assert math.isclose(r[name],value,rel_tol=1e-10), (name,r[name],value)
                assert math.isclose(r["wall_speedup"],
                    expected["baseline_wall_ms"]/expected["stride_wall_ms"],rel_tol=1e-10)
                assert math.isclose(r["cpu_speedup"],
                    expected["baseline_cpu_ms"]/expected["stride_cpu_ms"],rel_tol=1e-10)
                rss=statistics.median(x["peak_rss_kib"] for x in groups["stride"])-statistics.median(
                    x["peak_rss_kib"] for x in groups["baseline"])
                assert math.isclose(r["peak_rss_delta_mib"],rss/1024,abs_tol=1e-10)
                if q==64 and n==262144:
                    decisive.append(r)
    meets=len(decisive)==2 and all(r["wall_speedup"]>=1.5 and
        r["cpu_speedup"]>=1.5 and r["peak_rss_delta_mib"]<=8 for r in decisive)
    expected="CHARGED_RANDOM_RANGE_HEADROOM" if meets else "CHARGED_RANDOM_RANGE_NOT_PROVEN"
    assert obj["decision"]==expected
    print(json.dumps({"auditor":"o221-independent-v1","decision":expected,
                      "samples":len(s),"signed_archives":len(archives),
                      "variable_heldout_cases":sum(v["case_count"] for v in hold.values()),
                      "decisive":decisive},sort_keys=True))
    return expected

if __name__=="__main__":
    if len(sys.argv)!=2:
        raise SystemExit("usage: o221_independent_receipt_audit.py results.json")
    check(sys.argv[1])
