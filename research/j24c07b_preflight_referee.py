#!/usr/bin/env python3
"""Independent J24C07b raw receipt referee; refuses incomplete or relabeled economics."""
from __future__ import annotations

import argparse
import copy
import json
import math
from pathlib import Path
import statistics


def unique(pairs):
    values={}
    for key,val in pairs:
        if key in values:raise ValueError("duplicate JSON key "+key)
        values[key]=val
    return values


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"),object_pairs_hook=unique)


def check(receipt):
    assert receipt["schema"]=="j24c07b-abba-1"
    assert receipt["source"]=={
        "baseline":"0a128ff55c7ae0f14c6bdf019a81b40f0d894eff",
        "baseline_validation_blob":"fbcf6e9c108799dc8b6f5c19e95bcb0618cf41e8",
        "candidate_validation_blob":"0614723549403f398a43552a7c5ad3f00fbec688",
    }
    assert receipt["cycles"]==2 and receipt["repetitions"]==10
    assert receipt["order"]==["parent","candidate","candidate","parent"]
    assert receipt["release_credit"] is False
    assert receipt["processes"]==48 and receipt["calls"]==480
    assert len(receipt["archives"])==6 and len(receipt["raw"])==48
    keys={(r["mode"],r["count"]) for r in receipt["archives"]}
    expected={(m,n) for m in ("stored","retained") for n in (32,512,4096)}
    assert keys==expected
    by_case={(r["mode"],r["count"]):r for r in receipt["archives"]}
    for rec in receipt["archives"]:
        assert rec["archive_bytes"]>100 and len(rec["sha256"])==64
        assert rec["mode"] in ("stored","retained")
    good=True
    summary={}
    for mode,count in sorted(expected):
        rows=[r for r in receipt["raw"] if (r["mode"],r["count"])==(mode,count)]
        assert len(rows)==8
        assert [(r["cycle"],r["order"],r["arm"]) for r in rows]==[
            (cycle,i,arm) for cycle in (0,1)
            for i,arm in enumerate(("parent","candidate","candidate","parent"))
        ]
        for row in rows:
            assert row["archive_sha256"]==by_case[(mode,count)]["sha256"]
            assert row["archive_bytes"]==by_case[(mode,count)]["archive_bytes"]
            assert row["decision"]=="VALID_SAME_INDEX"
            assert row["blob"]==receipt["source"][("baseline" if row["arm"]=="parent" else "candidate")+"_validation_blob"]
            assert len(row["observations"])==10
            assert row["external_wall_ns"]>0
            assert row["worker_wall_median_ns"]==statistics.median(s["wall_ns"] for s in row["observations"])
            assert row["worker_cpu_median_ns"]==statistics.median(s["cpu_ns"] for s in row["observations"])
            assert all(isinstance(s["wall_ns"],int) and s["wall_ns"]>0 and
                       isinstance(s["cpu_ns"],int) and s["cpu_ns"]>=0
                       for s in row["observations"])
            assert sum(s["wall_ns"] for s in row["observations"])<=row["external_wall_ns"]
        original=[r for r in rows if r["arm"]=="parent"]
        candidate=[r for r in rows if r["arm"]=="candidate"]
        pwall=statistics.median(r["worker_wall_median_ns"] for r in original)
        cwall=statistics.median(r["worker_wall_median_ns"] for r in candidate)
        pcpu=statistics.median(r["worker_cpu_median_ns"] for r in original)
        ccpu=statistics.median(r["worker_cpu_median_ns"] for r in candidate)
        wratio=cwall/pwall
        cratio=ccpu/pcpu if pcpu else None
        key=f"{mode}-{count}"
        exp=receipt["summary"][key]
        numbers={"parent_median_wall_ns":pwall,"candidate_median_wall_ns":cwall,
                 "parent_median_cpu_ns":pcpu,"candidate_median_cpu_ns":ccpu,
                 "candidate_over_parent_wall":wratio,"candidate_over_parent_cpu":cratio}
        for field,value in numbers.items():
            if value is None:assert exp[field] is None
            else:assert math.isclose(exp[field],value,rel_tol=1e-12,abs_tol=1e-4),(key,field)
        passed=bool(wratio<=1.25 and cratio is not None and cratio<=1.25)
        assert exp["economics_screen_pass"]==passed
        if count==4096:good=good and passed
        summary[key]={"candidate_over_parent_wall":wratio,
                      "candidate_over_parent_cpu":cratio,
                      "economics_screen_pass":passed}
    assert set(receipt["summary"])=={f"{m}-{n}" for m,n in expected}
    expected_decision="FOCUSED_ECONOMIC_SCREEN_PASS" if good else "FOCUSED_ECONOMIC_SCREEN_FAIL"
    assert receipt["decision"]==expected_decision
    return expected_decision,summary


def forged_courts(original):
    bad=[]
    a=copy.deepcopy(original);a["raw"].pop();bad.append(a)
    a=copy.deepcopy(original);a["raw"][1]["arm"]="parent";bad.append(a)
    a=copy.deepcopy(original);a["raw"][0]["archive_sha256"]="0"*64;bad.append(a)
    a=copy.deepcopy(original);a["source"]["candidate_validation_blob"]="0"*40;bad.append(a)
    a=copy.deepcopy(original);a["raw"][0]["observations"][0]["wall_ns"]+=1;bad.append(a)
    for index,receipt in enumerate(bad):
        try:check(receipt)
        except (AssertionError,KeyError,TypeError,ValueError,ZeroDivisionError):continue
        raise AssertionError(f"forged receipt {index} accepted")
    return len(bad)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--receipt",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args()
    receipt=load(a.receipt)
    decision,summary=check(receipt)
    blocked=forged_courts(receipt)
    result={"schema":"j24c07b-referee-1","decision":decision,
            "recomputed":summary,"forgeries_rejected":blocked,
            "raw_workers":len(receipt["raw"]),"source_locked":True,
            "release_credit":False}
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print("J24C07B_REFEREE=PASS", "FORGERIES_REJECTED="+str(blocked),
          "DECISION="+decision,flush=True)


if __name__=="__main__":
    main()
