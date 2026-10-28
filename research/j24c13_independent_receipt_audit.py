"""Second-root audit of J24C13 fresh-process installed source-exact receipts.

The audit never imports the product, generates queries or reruns benchmarks. A
negative performance decision is scientifically valid and must not fail CI.
"""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import statistics

def audit(source):
    data=json.loads(Path(source).read_text(encoding="utf-8"))
    assert data["schema"]=="j24c13-installed-abba-v1"
    head=data["source_head"]
    assert isinstance(head,str) and len(head)==40 and all(x in "0123456789abcdef" for x in head)
    raw=data["raw"]
    reps=data["repetition"]
    assert reps>=3 and len(raw)==20*2*reps, (len(raw),reps)
    groups=defaultdict(list)
    for entry in raw:
        for key in ("session_wall_ns","open_wall_ns","read_wall_ns",
                    "session_cpu_ns","open_cpu_ns","read_cpu_ns","process_wall_ns"):
            assert isinstance(entry[key],int) and entry[key]>0, (entry["case"],key)
        assert entry["open_wall_ns"]+entry["read_wall_ns"]==entry["session_wall_ns"]
        assert entry["open_cpu_ns"]+entry["read_cpu_ns"]==entry["session_cpu_ns"]
        assert entry["source_head"]==head
        assert entry["arm"] in ("native-original","fused")
        assert len(entry["archive_sha256"])==64 and len(entry["digest"])==64
        assert "site-packages" in entry["installed_reader"] or "dist-packages" in entry["installed_reader"]
        assert entry["case"].startswith(("fixed-","hetero-"))
        assert (entry["index_count"]>0)==(entry["arm"]=="fused")
        assert entry["q"] in (1,6,32)
        assert 0<=entry["iteration"]<reps
        groups[(entry["case"],entry["iteration"])].append(entry)
    assert len(groups)==20*reps, len(groups)
    for (case,i),pair in groups.items():
        assert len(pair)==2 and {x["arm"] for x in pair}=={"native-original","fused"}
        assert len({x["archive_sha256"] for x in pair})==1
        assert len({x["digest"] for x in pair})==1
        assert len({x["q"] for x in pair})==1
        assert len({x["python"] for x in pair})==1
        assert len({x["host"] for x in pair})==1
    expected=[]
    keys=("session_wall_ns","session_cpu_ns","open_wall_ns","read_wall_ns","process_wall_ns")
    for case in sorted({x["case"] for x in raw}):
        for key in keys:
            med={}
            for arm in ("native-original","fused"):
                values=[x[key] for x in raw if x["case"]==case and x["arm"]==arm]
                assert len(values)==reps
                med[arm]=statistics.median(values)
            expected.append(dict(case=case,field=key,original_ns=med["native-original"],
                                 fused_ns=med["fused"],
                                 speedup=med["native-original"]/med["fused"]))
    assert len(expected)==len(data["summary"])==100
    for computed,reported in zip(expected,data["summary"]):
        for key in computed:
            if key=="speedup":
                assert abs(computed[key]-reported[key])<1e-9
            else:
                assert computed[key]==reported[key], (key,computed,reported)
    q6=[x for x in expected if x["field"]=="session_wall_ns" and "-q6-" in x["case"]]
    assert len(q6)==4
    q1=[x for x in expected if x["field"]=="session_wall_ns" and "-q1-" in x["case"]]
    assert len(q1)==12
    original_faster=[x for x in q6 if x["speedup"]<1]
    significant_q1_loss=[x for x in q1
                         if x["fused_ns"]>=1.05*x["original_ns"]
                         and x["fused_ns"]-x["original_ns"]>=3_000_000]
    return dict(verdict="J24C13_SOURCE_EXACT_RECEIPT_AUDIT_PASS_RESEARCH_ONLY",
                head=head,processes=len(raw),groups=len(groups),
                q6_speedups={x["case"]:x["speedup"] for x in q6},
                q6_no_gain=[x["case"] for x in original_faster],
                q1_material_losses=[x["case"] for x in significant_q1_loss],
                caveats=["No published Reader A/B in this court",
                         "No full product release gate",
                         "Windows RSS unavailable when returned null"])

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--input",required=True)
    p.add_argument("--output",required=True)
    a=p.parse_args()
    result=audit(a.input)
    Path(a.output).write_text(json.dumps(result,sort_keys=True,indent=2),encoding="utf-8")
    print(json.dumps(result,sort_keys=True))
