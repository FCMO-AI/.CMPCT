#!/usr/bin/env python3
"""Independent J24G61 receipt auditor; Python standard library only, no CMPCT import.

Verifies the archived raw research record and intentionally falsifies eight altered
copies. This is evidence arithmetic/custody, NOT independent physical Reader execution.
"""
from __future__ import annotations
import copy
import hashlib
import json
import math
from pathlib import Path
import statistics
import sys

CASES = [(512, 63), (2048, 1), (2048, 32), (2048, 63)]
PINS = {
 "src/cmpct/builder.py": "a2160a2f6b1ca3ef8cd94897cb68bb2fcb74ebc2",
 "src/cmpct/reader.py": "29a8be64f3acfb027750351c6a567fd82cf7dc97",
 "src/cmpct/transactions.py": "3eef7fdc3f6deca5ddd6d9edf1292c7e2c864f11",
 "src/cmpct/journal_replay.py": "03743ca2a06c022c2ec64243a90fe373cf91e899",
 "src/cmpct/validation.py": "5ea3b8f26058b0983c9686295c73f15472bc3ffe",
}

def require(condition, message):
    if not condition: raise ValueError(message)

def close(a, b, label):
    require(a is not None and b is not None and math.isclose(float(a), float(b), rel_tol=1e-10, abs_tol=0.00001), "changed " + label)

def med(rows, key): return statistics.median(x[key] for x in rows)

def verify(r):
    require(r["status"] == "RESEARCH_ONLY" and r["parent_research_head"] == "fb5d96cdb8855fe3e01868792e65b79d3d61661d", "wrong scope")
    require(r["prereg_commit"] == "8eaa7460825fde317aa7338db3f557a2dd9e45bf", "wrong prereg")
    require(set(r["source"]["sources"]) == set(PINS), "missing source")
    for name, sha in PINS.items():
        require(r["source"]["sources"][name]["git_blob"] == sha, "source drift " + name)
    require(len(r["source"]["head"]) == 40, "missing source HEAD")
    require(set(r["cases"]) == {f"{n}/{d}" for n,d in CASES}, "wrong case family")
    samples = r["raw_samples"]
    require(len(samples) == 72, "missing samples: 64 wrapped, 8 unwrapped expected")
    for n, depth in CASES:
        key = f"{n}/{depth}"; case = r["cases"][key]
        require(case["physical_depth"] == depth and case["index_count"] == n, "wrong case size")
        b = case["archive_bytes"]
        require(b["checkpoint"] - b["chain"] == case["checkpoint_premium_bytes"], "checkpoint byte charge")
        for sha in case["archive_sha256"].values():
            require(len(sha) == 64 and all(c in "0123456789abcdef" for c in sha), "archive SHA format")
        rows = [x for x in samples if x["n"] == n and x["depth"] == depth and x["instrumented"] is True]
        require(len(rows) == 16, "missing instrumented observations")
        for block in range(4):
            ordered = sorted((x for x in rows if x["block"] == block), key=lambda x: x["position"])
            order = ["chain","checkpoint","checkpoint","chain"] if block%2 == 0 else ["checkpoint","chain","chain","checkpoint"]
            require([x["variant"] for x in ordered] == order and [x["position"] for x in ordered] == [0,1,2,3], "broken ABBA")
        for x in rows:
            chained = x["variant"] == "chain"
            require(x["observed_depth"] == (depth if chained else 0) and x["rows"] == n, "observed-depth clobber")
            require(x["replay_calls"] == (depth if chained else 0), "replay call mismatch")
            require(x["footer_calls"] == (depth+1 if chained else 1), "footer call mismatch")
            for field in ("wall_ns","cpu_ns","replay_wall_ns","footer_wall_ns","residual_wall_ns"):
                require(type(x[field]) is int and x[field] >= 0, "invalid timing")
            require(x["replay_wall_ns"]+x["footer_wall_ns"]+x["residual_wall_ns"] == x["wall_ns"], "span sum")
        chains = [x for x in rows if x["variant"] == "chain"]
        checkpoints = [x for x in rows if x["variant"] == "checkpoint"]
        require(len(chains) == len(checkpoints) == 8, "unbalanced A/B")
        expected={}
        fields = {"open_wall_ns":"wall_ns","open_cpu_ns":"cpu_ns",
                  "replay_ns":"replay_wall_ns","footer_ns":"footer_wall_ns",
                  "residual_ns":"residual_wall_ns"}
        for label, subset in (("chain",chains),("checkpoint",checkpoints)):
            for label2, field in fields.items():
                expected[label+"_"+label2] = med(subset, field)
        diff = expected["chain_open_wall_ns"]-expected["checkpoint_open_wall_ns"]
        rdiff = expected["chain_replay_ns"]-expected["checkpoint_replay_ns"]
        expected.update(extra_total_wall_ns=diff, extra_replay_wall_ns=rdiff,
                        extra_replay_fraction=rdiff/diff if diff>0 else None)
        found=r["summaries"][key]
        require(set(found) == set(expected), "missing summary fields")
        for name, value in expected.items():
            if value is None: require(found[name] is None,"invalid missing value")
            else: close(found[name], value, key+"/"+name)
    unwrapped=[x for x in samples if x["instrumented"] is False]
    require(len(unwrapped) == 8 and all(x["n"]==2048 and x["depth"]==63 for x in unwrapped), "unwrapped control")
    for block in (0,1):
        ordered=sorted((x for x in unwrapped if x["block"]==block), key=lambda x:x["position"])
        order=["chain","checkpoint","checkpoint","chain"] if block==0 else ["checkpoint","chain","chain","checkpoint"]
        require([x["variant"] for x in ordered]==order,"unwrapped ABBA")
        require(all(x["replay_calls"] == x["footer_calls"] == 0 for x in ordered),"unwrapped tracing")
    a=[x for x in unwrapped if x["variant"]=="chain"];b=[x for x in unwrapped if x["variant"]=="checkpoint"]
    rawdiff=med(a,"wall_ns")-med(b,"wall_ns")
    wrapped=r["summaries"]["2048/63"]["extra_total_wall_ns"]
    impact=abs(rawdiff-wrapped)/rawdiff if rawdiff>0 else None
    control=r["control"]
    for k, v in {"uninstrumented_chain_ns":med(a,"wall_ns"),
                 "uninstrumented_checkpoint_ns":med(b,"wall_ns"),
                 "uninstrumented_difference_ns":rawdiff,
                 "instrumented_difference_ns":wrapped,
                 "penalty_perturbation_fraction":impact}.items():
        if v is None: require(control[k] is None, "null control")
        else: close(control[k],v,k)
    share=r["summaries"]["2048/63"]["extra_replay_fraction"]
    if impact is None or impact>.15 or wrapped<3_000_000: decision="INCONCLUSIVE_MEASUREMENT_OR_NONMATERIAL_PENALTY"
    elif share is not None and share>=.50: decision="REPLAY_MAJOR_COST_OWNER_ON_MEASURED_WORKLOAD"
    elif share is not None and share<.35: decision="REPLAY_NOT_MAJOR_COST_OWNER_ON_MEASURED_WORKLOAD"
    else: decision="INCONCLUSIVE_REPLAY_SHARE"
    require(r["decision"] == decision, "decision changed")
    require(r["profile"]["chain"]["depth"]==63 and r["profile"]["checkpoint"]["depth"]==0,"independent profile mismatch")
    return {"decision": decision, "raw_samples":len(samples),
            "replay_fraction":share, "wrapped_excess_ms":wrapped/1e6,
            "instrumentation_perturbation":impact}

def attack(r):
    rejected=0
    for k in range(8):
        altered=copy.deepcopy(r)
        if k==0: altered["raw_samples"][0]["replay_calls"]=999
        if k==1: altered["raw_samples"][0]["variant"]="checkpoint"
        if k==2: altered["raw_samples"][0]["observed_depth"]=999
        if k==3: altered["raw_samples"][0]["residual_wall_ns"]=-5
        if k==4: altered["summaries"]["2048/63"]["extra_replay_fraction"]=3.1
        if k==5: altered["cases"]["2048/63"]["checkpoint_premium_bytes"]+=1
        if k==6: altered["cases"]["2048/63"]["archive_sha256"]["chain"]="x"*64
        if k==7: altered["decision"]="UNAUTHORIZED_PRODUCT_WIN"
        try: verify(altered)
        except (ValueError,TypeError,KeyError): rejected+=1
    require(rejected==8,"auditor accepted hostile receipt")
    return rejected

if __name__=="__main__":
    if len(sys.argv)!=2: raise SystemExit("usage: j24g61_independent_receipt_audit.py receipt.json")
    payload=Path(sys.argv[1]).read_bytes(); report=json.loads(payload)
    summary=verify(report);summary["hostile_mutations_rejected"]=attack(report)
    summary["receipt_sha256"]=hashlib.sha256(payload).hexdigest()
    print(json.dumps(summary,sort_keys=True))
