#!/usr/bin/env python3
"""Independent J24G15 stdlib-only referee for source-locked Reader receipts.

Does not import the candidate, CMPCT, MessagePack, or performance comparator.
It recomputes raw medians and rejects corrupted evidence without changing gates.
"""
import copy
import json
import os
from pathlib import Path
import statistics
import subprocess

EXPECTED_READER="f13c5492f5acfa1cfcfec97cdbe0da71e41e327b"
EXPECTED_PREREG="3f6dcb04422af2090917f6d421f343b6d7d5656a"
ARMS=("eager","guarded","adaptive")
CASES=("empty","opaque","nested")
KEYS=("cpu_ns","wall_ns","rss_kib","adaptive_switches","max_retained_raw_bytes")
checks=0

def require(condition,msg):
    global checks
    checks+=1
    assert condition,msg

def audit(obj):
    require(obj["reader_blob"]==EXPECTED_READER,"Reader identity")
    require(obj["prereg"]==EXPECTED_PREREG,"prereg identity")
    require(obj["raw_budget"]==1048576,"unchanged raw limit")
    require(obj["product_credit"] is False and obj["release_credit"]==0,"misattributed promotion")
    require(set(obj["cases"])==set(CASES),"missing or extra cases")
    require(set(obj["payloads"])==set(CASES),"payload names")
    require(obj["payloads"]["nested"]["maps"]==200000,"signed object count")
    require(obj["payloads"]["opaque"]["maps"]==0,"opaque control")
    require(abs(obj["payloads"]["nested"]["bytes"]-obj["payloads"]["opaque"]["bytes"])<100,"charged size parity")
    for name in CASES:
        case=obj["cases"][name]
        payload=obj["payloads"][name]
        require(payload["bytes"]<=obj["raw_budget"],"admission budget")
        require(len(payload["sha256"])==64,"SHA length")
        require(case["case"]==name and case["repetitions"]==3,"case identity")
        require(set(case["raw"])==set(ARMS),"arm set")
        require(case["expected_footer"]==obj["checkpoint"],"fallback checkpoint")
        for arm in ARMS:
            rows=case["raw"][arm]
            require(len(rows)==3,"three real repetitions")
            for row in rows:
                require(row["arm"]==arm,"arm label")
                require(row["reader_blob"]==EXPECTED_READER,"row Reader blob")
                require(row["archive_sha256"]==case["sha256"],"same physical bytes")
                require(row["archive_bytes"]==case["archive_bytes"],"physical length")
                require(row["failure"] is None,"successful recovery")
                require(row["max_retained_raw_bytes"]<=obj["raw_budget"],"raw budget")
                require(row["adaptive_switches"]==0,"no deferred switch under budget")
                require(row["rss_kib"]>0 and row["cpu_ns"]>0 and row["wall_ns"]>0,"positive measures")
            for key in KEYS:
                require(statistics.median(row[key] for row in rows)==case["median"][arm][key],
                        "median mismatch "+name+" "+arm+" "+key)
            require(abs(case["median"]["adaptive"]["cpu_ns"]/case["median"]["eager"]["cpu_ns"]-
                        case["adaptive_cpu_ratio_to_eager"])<1e-12,"CPU ratio")
            require(abs(case["median"]["adaptive"]["rss_kib"]/case["median"]["eager"]["rss_kib"]-
                        case["adaptive_rss_ratio_to_eager"])<1e-12,"RSS ratio")
    extra=obj["cases"]["nested"]["median"]["adaptive"]["rss_kib"]-obj["cases"]["opaque"]["median"]["adaptive"]["rss_kib"]
    near=sum(abs(obj["cases"]["nested"]["median"][arm]["rss_kib"]-
                 obj["cases"]["nested"]["median"]["adaptive"]["rss_kib"])<=4096 for arm in ARMS)
    require(extra==obj["nested_extra_rss_kib"],"delta recomputation")
    require(near==obj["nested_arms_within_4mib"],"equivalence recomputation")
    require(obj["decision"]==("H1_CONFIRMED" if extra>=12288 and near>=2 else "H1_NOT_CONFIRMED"),"decision recomputation")

def main():
    root=Path(os.environ.get("J24G15_ARTIFACTS","j24g15-artifacts"))
    obj=json.loads((root/"court.json").read_text())
    require(obj["source_head"]==subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip(),"exact commit")
    audit(obj)
    baseline=checks
    mutators=[
       lambda o:o["cases"]["nested"]["median"]["adaptive"].__setitem__("rss_kib",1),
       lambda o:o["cases"]["opaque"]["raw"]["guarded"][0].__setitem__("archive_sha256","0"*64),
       lambda o:o["cases"]["nested"]["raw"]["adaptive"][1].__setitem__("reader_blob","fake"),
       lambda o:o["payloads"]["nested"].__setitem__("bytes",1048577),
       lambda o:o.__setitem__("decision","H1_CONFIRMED" if obj["decision"]!="H1_CONFIRMED" else "H1_NOT_CONFIRMED")
    ]
    rejected=0
    for mutate in mutators:
        altered=copy.deepcopy(obj);mutate(altered)
        try: audit(altered)
        except AssertionError: rejected+=1
    assert rejected==len(mutators),("altered evidence not rejected",rejected)
    result={"source_head":obj["source_head"],"checked":baseline,"forged_rejected":rejected,
            "referee":"stdlib-independent","archive_bytes_embedded":False,
            "product_credit":False}
    (root/"referee.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("J24G15_REFEREE="+json.dumps(result,sort_keys=True))
if __name__=="__main__": main()
