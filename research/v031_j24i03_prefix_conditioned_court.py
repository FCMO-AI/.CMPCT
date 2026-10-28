#!/usr/bin/env python3
"""J24I03-P: source-locked prefix-conditioned binary-create court (research only).

Runs the ORIGINAL parity _timed_layer helper on tiny/source/media/binary in
unmodified chronological order (library and CLI). Neither this script nor
its results change the official r24/ZIP release comparator or thresholds.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import statistics
import subprocess
import sys
from datetime import datetime, timezone

BASE = "4de43609046ceaba93902e6680af3b4059aee49f"
CAND = "293aa161a4a13b4c1f4fd0f5089aa62e4dbeedef"
ORDER = {"AA": ["A", "A2", "A2", "A"], "AB": ["A", "B", "B", "A"]}
ROWS = ("tiny", "source", "media", "binary")
CHILD = r"""
import hashlib, json, os, resource, sys, time
from pathlib import Path
engine=Path(sys.argv[1]).resolve()
corpora=Path(sys.argv[2]).resolve()
out=Path(sys.argv[3]).resolve()
reps=int(sys.argv[4])
sys.path.insert(0,str(engine/"benchmarks"))
import cmpct
from cmpct import builder, reader
import zip_parity_bench as parity
assert Path(cmpct.__file__).resolve().is_relative_to(engine/"src"), cmpct.__file__
assert Path(builder.__file__).resolve().is_relative_to(engine/"src"), builder.__file__
assert Path(reader.__file__).resolve().is_relative_to(engine/"src"), reader.__file__
assert Path(parity.__file__).resolve()==engine/"benchmarks"/"zip_parity_bench.py"
parity.OUT=out
parity.CORP=corpora
out.mkdir(parents=True,exist_ok=True)
results={}
t0=time.perf_counter_ns()
for name in ("tiny","source","media","binary"):
    src=corpora/name
    results[name]={}
    for layer in ("library","cli"):
        row=parity._timed_layer(name,src,layer)
        archive=out/(name+"."+layer+".cmpct")
        results[name][layer]={"metrics":row,
            "archive_sha256":hashlib.sha256(archive.read_bytes()).hexdigest(),
            "archive_bytes":archive.stat().st_size}
print(json.dumps({"engine":str(engine),"module":str(Path(cmpct.__file__).resolve()),
                   "parity_helper":str(Path(parity.__file__).resolve()),
                   "repetitions":reps,"prefix":list(results),
                   "results":results,
                   "process_wall_ms":(time.perf_counter_ns()-t0)/1e6,
                   "peak_rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}))
"""

def sha_file(path:Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def head(path:Path)->str:
    return subprocess.check_output(["git","-C",str(path),"rev-parse","HEAD"],text=True).strip()

def require(condition, message):
    if not condition:raise ValueError(message)

def main():
    a=argparse.ArgumentParser()
    a.add_argument("--base-root",type=Path,required=True)
    a.add_argument("--candidate-root",type=Path,required=True)
    a.add_argument("--corpus-root",type=Path,required=True)
    a.add_argument("--output",type=Path,required=True)
    a.add_argument("--reps",type=int,default=3)
    args=a.parse_args()
    base=args.base_root.resolve()
    candidate=args.candidate_root.resolve()
    corp=args.corpus_root.resolve()
    require(head(base)==BASE, "wrong exact base")
    require(subprocess.run(["git","-C",str(candidate),"merge-base","--is-ancestor",CAND,"HEAD"],capture_output=True).returncode==0,"wrong candidate ancestry")
    require(1<=args.reps<=7, "bounded samples")
    require(all((corp/name).is_dir() for name in ROWS),"missing frozen corpus")
    source={}
    for rel in ("src/cmpct/builder.py","src/cmpct/codec.py","benchmarks/zip_parity_bench.py"):
        x,y=sha_file(base/rel),sha_file(candidate/rel)
        require(x==y,"source differs: "+rel)
        source[rel]=x
    args.output.parent.mkdir(parents=True,exist_ok=True)
    traces=[]
    for court,labels in ORDER.items():
        for ordinal,label in enumerate(labels):
            engine=candidate if label=="B" else base
            output=Path("/tmp/cmpct-j24i03-prefix-"+court+"-"+str(ordinal)+"-out")
            env=dict(os.environ)
            env["PYTHONPATH"]=str(engine/"src")
            env["CMPCT_PARITY_REPS"]=str(args.reps)
            env["CMPCT_PARITY_CORPUS_ROOT"]=str(corp)
            call=subprocess.run([sys.executable,"-c",CHILD,str(engine),str(corp),str(output),str(args.reps)],
                                env=env,text=True,capture_output=True)
            if call.returncode:
                raise RuntimeError("child "+court+"/"+label+": "+call.stderr[-10000:])
            data=json.loads(call.stdout)
            require(data["repetitions"]==args.reps and data["prefix"]==list(ROWS),"wrong helper execution")
            traces.append({"court":court,"step":ordinal,"label":label,"source_sha":head(engine),"data":data})
            binary=data["results"]["binary"]["library"]["metrics"]["cmpct"]["create_s_median"]
            print(f"{court} {ordinal} {label} binary_lib_ms={binary*1000:.6f}",flush=True)
            import shutil
            shutil.rmtree(output)
    # All resulting archive sizes and physical bytes must match across engines for every input/layer.
    for name in ROWS:
        for layer in ("library","cli"):
            ids={(t["data"]["results"][name][layer]["archive_sha256"],
                  t["data"]["results"][name][layer]["archive_bytes"]) for t in traces}
            require(len(ids)==1,"archive drift "+name+"/"+layer)
    summary={}
    for court in ORDER:
        x=[v for v in traces if v["court"]==court]
        a=[v["data"]["results"]["binary"]["library"]["metrics"]["cmpct"]["create_s_median"]*1000 for v in x if v["label"]=="A"]
        b=[v["data"]["results"]["binary"]["library"]["metrics"]["cmpct"]["create_s_median"]*1000 for v in x if v["label"]!="A"]
        am,bm=statistics.median(a),statistics.median(b)
        summary[court]={"base_ms":am,"other_ms":bm,"delta_ms":bm-am,"delta_pct":100*(bm/am-1),
                        "base_process_medians_ms":a,"other_process_medians_ms":b,
                        "passes_gate_scale":(bm-am)>3 and 100*(bm/am-1)>5}
    record={"schema":"cmpct-j24i03-prefix-conditioned-v1","claim_boundary":"short-prefix three-sample research; not official parity evidence",
            "preregistered_source":"docs/v031-research/2026-10-28-j24i03-prefix-conditioned-preregistration.md",
            "start_observed_utc":datetime.now(timezone.utc).isoformat(),"exact_base":BASE,"exact_candidate":CAND,
            "research_head":head(candidate),"source_hashes":source,"order":ORDER,"rows":ROWS,
            "reps_per_operation":args.reps,"summary":summary,"raw":traces}
    args.output.write_text(json.dumps(record,sort_keys=True,indent=2)+"\n")
    print("SUMMARY",json.dumps(summary,sort_keys=True),flush=True)

if __name__=="__main__":
    main()
