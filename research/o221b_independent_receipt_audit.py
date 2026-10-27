#!/usr/bin/env python3
"""Independent O221b receipt auditor; never imports the subject instrument."""
import json
import math
import statistics
import sys
from pathlib import Path

Q=(1,2,3,4,8,16)
K=("fixed","cdc")
A=("baseline","eager","lazy")
N=262144
def audit(p):
    obj=json.loads(Path(p).read_text())
    assert obj["question"]=="O221b"
    assert obj["pre_registered_before_instrument_commit"]=="748d0dc9ad36c3dad791a1f1fed5084904aad897"
    assert obj["source_parent"]=="c5e13bb3fbb4cdade8b64246658ce7c7818de41f"
    assert obj["original_o221_blob"]=="d5b97d8a75707243e49d79c4561ad9e40072939d"
    archives={a["kind"]:a for a in obj["archives"]}
    assert len(archives)==2 and set(archives)==set(K)
    assert all(a["n"]==N and a["archive_bytes"]>0 and len(a["archive_sha256"])==64 for a in archives.values())
    src=obj["samples"]; assert len(src)==108,len(src)
    seen=set()
    for s in src:
        key=(s["kind"],s["q"],s["rep"],s["arm"])
        assert key not in seen,key
        seen.add(key)
        assert s["kind"] in K and s["q"] in Q and s["rep"] in (0,1,2) and s["arm"] in A
        assert s["n"]==N and s["archive_sha256"]==archives[s["kind"]]["archive_sha256"]
        assert s["index_build_count"]==(int(s["arm"]=="eager" or (s["arm"]=="lazy" and s["q"]>1)))
        for field in ("wall_ms","cpu_ms","peak_rss_kib","process_wall_ms"):
            assert math.isfinite(s[field]) and s[field]>0,(key,field)
        assert s["process_wall_ms"]>=s["wall_ms"]
    for kind in K:
        for q in Q:
            for rep in range(3):
                pair=[s for s in src if s["kind"]==kind and s["q"]==q and s["rep"]==rep]
                assert len(pair)==3 and {s["arm"] for s in pair}==set(A)
                assert len({s["range_starts_sha256"] for s in pair})==1
                assert len({s["range_result_sha256"] for s in pair})==1
    rows={(s["kind"],s["q"]):s for s in obj["summary"]}
    assert len(rows)==12
    for kind in K:
        for q in Q:
            s=rows[(kind,q)]
            groups={arm:[v for v in src if v["kind"]==kind and v["q"]==q and v["arm"]==arm] for arm in A}
            for arm in A:
                for field in ("wall_ms","cpu_ms","peak_rss_kib"):
                    x=statistics.median(v[field] for v in groups[arm])
                    y=s["medians"][arm][field]
                    assert math.isclose(x,y,rel_tol=1e-10,abs_tol=1e-9),(kind,q,arm,field)
            b,c=s["medians"]["baseline"],s["medians"]["lazy"]
            e=s["medians"]["eager"]
            for key,value in {"lazy_wall_speedup":b["wall_ms"]/c["wall_ms"],
                "lazy_cpu_speedup":b["cpu_ms"]/c["cpu_ms"],
                "eager_wall_speedup":b["wall_ms"]/e["wall_ms"],
                "eager_cpu_speedup":b["cpu_ms"]/e["cpu_ms"],
                "lazy_rss_delta_mib":(c["peak_rss_kib"]-b["peak_rss_kib"])/1024}.items():
                assert math.isclose(s[key],value,rel_tol=1e-10,abs_tol=1e-9)
    first=[rows[k,1] for k in K]
    fourth=[rows[k,4] for k in K]
    meets=all(s["lazy_wall_speedup"]>=1/1.05 and s["lazy_cpu_speedup"]>=1/1.05 for s in first) and all(
        s["lazy_wall_speedup"]>=1.10 and s["lazy_cpu_speedup"]>=1.10 and
        s["lazy_rss_delta_mib"]<=8 for s in fourth)
    dec="LAZY_SHORT_SESSION_HEADROOM" if meets else "LAZY_SHORT_SESSION_NOT_PROVEN"
    assert obj["decision"]==dec
    print(json.dumps({"audit":"PASS","samples":len(src),"triples":36,
        "question":obj["question"],"decision":dec,
        "q1":[(s["kind"],s["lazy_wall_speedup"]) for s in first],
        "q4":[(s["kind"],s["lazy_wall_speedup"]) for s in fourth]}))
if __name__=="__main__":
    audit(sys.argv[1])
