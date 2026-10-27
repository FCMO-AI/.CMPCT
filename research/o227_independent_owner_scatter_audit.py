#!/usr/bin/env python3
"""O227 second-root receipt/referee. Never imports experimental code or CMPCT Reader."""
import copy
import hashlib
import json
import math
import statistics
import sys
from pathlib import Path

FAMILIES=("zstd_entropy_twice","deflate_entropy_twice","zstd_pattern_twice",
          "deflate_pattern_twice","zstd_entropy_once","deflate_entropy_once")
KINDS=("fixed","cdc")
ARMS=("eager","serial","scatter")
FIELDS=("session_wall_ms","session_cpu_ms","read_wall_ms","read_cpu_ms","open_wall_ms","VmHWM_kib")


def audit(d):
    assert d["schema"]=="o227-owner-scatter-v1"
    assert d["reader_blob"]=="dbd4ac576a05a47eae97e1e40de89cf1de440516"
    assert d["source_parent"]=="12a8b08a661746653a4af1801dfe89c00a39dd85"
    assert d["prereg_commit"]=="f34fe69211fe07e09a368fda9ade7c7233a77520"
    assert tuple(d["families"])==FAMILIES
    assert tuple(d["kinds"])==KINDS
    assert tuple(d["arms"])==ARMS
    manifests={(x["family"],x["kind"]):x for x in d["archives"]}
    assert len(d["archives"])==len(manifests)==12
    assert set(manifests)=={(f,k) for f in FAMILIES for k in KINDS}
    for (family,kind),m in manifests.items():
        for field in ("archive_sha256","logical_sha256"):
            v=m[field]
            assert len(v)==64 and all(c in "0123456789abcdef" for c in v)
        count=24 if family.endswith("twice") else 12
        assert m["refs"]==count and m["distinct_owners"]==12
        assert m["logical_bytes"]==count*3*1024*1024
        assert m["physical_decoded_request_upper_bytes"]==m["logical_bytes"]
        assert m["physical_unique_decode_bytes"]==12*3*1024*1024
        assert m["archive_bytes"]>0
    keyset={(f,k,a,i) for f in FAMILIES for k in KINDS for a in ARMS for i in range(3)}
    assert len(d["samples"])==108
    seen=set()
    pids=set()
    by_key={}
    for sample in d["samples"]:
        k=(sample["family"],sample["kind"],sample["arm"],sample["rep"])
        assert k in keyset and k not in seen
        seen.add(k)
        m=manifests[k[:2]]
        assert sample["archive_sha256"]==m["archive_sha256"]
        assert sample["logical_sha256"]==m["logical_sha256"]
        assert sample["logical_bytes"]==m["logical_bytes"]
        assert sample["archive_bytes"]==m["archive_bytes"]
        assert isinstance(sample["pid"],int) and sample["pid"]>0
        assert sample["pid"] not in pids, "not a fresh independent child process"
        pids.add(sample["pid"])
        assert sample["python"] and isinstance(sample["python"],str)
        for field in (*FIELDS,"open_cpu_ms","process_wall_ms","VmRSS_kib"):
            val=sample[field]
            assert type(val) in (float,int) and math.isfinite(val) and val>=0,(k,field,val)
        assert sample["VmHWM_kib"]>=sample["VmRSS_kib"]
        assert sample["session_wall_ms"]+0.02>=sample["read_wall_ms"]
        assert sample["session_cpu_ms"]+0.02>=sample["read_cpu_ms"]
        assert sample["process_wall_ms"]+100>=sample["session_wall_ms"]
        count=m["refs"]
        assert sample["requested_blob_calls"]==count
        expected_owners=12 if sample["arm"]=="scatter" else count
        assert sample["unique_physical_owners"]==expected_owners
        by_key[k]=sample
    assert seen==keyset
    assert len(d["heldout_controls"])==6 and len(d["hostile_controls"])==6
    assert {(v["kind"],v["arm"]) for v in d["heldout_controls"]}=={
        (k,a) for k in KINDS for a in ARMS}
    assert {(v["kind"],v["arm"]) for v in d["hostile_controls"]}=={
        (k,a) for k in KINDS for a in ARMS}
    assert all(v["rejected"] is True for v in d["hostile_controls"])
    for kind in KINDS:
        rows=[v for v in d["heldout_controls"] if v["kind"]==kind]
        assert len({v["sha256"] for v in rows})==1
        assert len({v["bytes"] for v in rows})==1
    summaries={(x["family"],x["kind"]):x for x in d["summary"]}
    assert len(summaries)==12
    assert set(summaries)==set(manifests)
    material=[]
    once_penalty=False
    rss_debt=False
    for (family,kind),g in summaries.items():
        assert set(g["arms"])==set(ARMS)
        for arm in ARMS:
            ss=[by_key[(family,kind,arm,r)] for r in range(3)]
            for field in FIELDS:
                expected=statistics.median(v[field] for v in ss)
                assert math.isclose(expected,g["arms"][arm][field],rel_tol=1e-11,abs_tol=1e-7)
        b=g["arms"]
        wall=min(b["eager"]["session_wall_ms"],b["serial"]["session_wall_ms"])/b["scatter"]["session_wall_ms"]
        cpu=min(b["eager"]["session_cpu_ms"],b["serial"]["session_cpu_ms"])/b["scatter"]["session_cpu_ms"]
        rss=b["scatter"]["VmHWM_kib"]-min(b["serial"]["VmHWM_kib"],b["eager"]["VmHWM_kib"])
        assert math.isclose(wall,g["best_control_wall_speedup"],rel_tol=1e-11)
        assert math.isclose(cpu,g["best_control_cpu_speedup"],rel_tol=1e-11)
        assert math.isclose(rss,g["rss_above_best_control_kib"],rel_tol=1e-11,abs_tol=1e-6)
        if family.endswith("twice") and wall>=1.20 and cpu>=1.20:
            material.append((family,kind))
        if family.endswith("once") and wall<1/1.10:
            once_penalty=True
        if rss>8192:
            rss_debt=True
    assert sorted(tuple(q) for q in d["material_cells"])==sorted(material)
    assert d["once_penalty"] is once_penalty
    assert d["rss_debt"] is rss_debt
    verdict="SCATTER_SEED" if len(material)>=2 else "NO_MATERIAL_HEADROOM"
    if verdict=="SCATTER_SEED" and (once_penalty or rss_debt):
        verdict="SCATTER_SEED_WITH_EXPORTED_DEBT"
    assert d["decision"]==verdict
    return {"status":"PASS","decision":verdict,"samples":len(seen),
            "material_cells":material,"once_penalty":once_penalty,"rss_debt":rss_debt}


if __name__=="__main__":
    payload=Path(sys.argv[1]).read_bytes()
    d=json.loads(payload)
    result=audit(d)
    for mutation in ("bad_logical_sha","duplicate_pid","fake_outcome"):
        bad=copy.deepcopy(d)
        if mutation=="bad_logical_sha":
            bad["samples"][0]["logical_sha256"]="0"*64
        elif mutation=="duplicate_pid":
            bad["samples"][1]["pid"]=bad["samples"][0]["pid"]
        else:
            bad["decision"]="SCATTER_SEED" if d["decision"]!="SCATTER_SEED" else "NO_MATERIAL_HEADROOM"
        try:
            audit(bad)
        except AssertionError:
            pass
        else:
            raise AssertionError("mutated evidence falsely accepted: "+mutation)
    result["mutated_receipts_rejected"]=3
    result["json_sha256"]=hashlib.sha256(payload).hexdigest()
    print(json.dumps(result,sort_keys=True))
