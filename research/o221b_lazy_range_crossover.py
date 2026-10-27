#!/usr/bin/env python3
"""O221b preregistered genuine-r24 Reader short-session crossover (SCIENCE ONLY).

Do not edit or monkeypatch the installed production Reader. Reuse exact O221
out-of-tree range implementation, source and fixture; charge all costs.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import random
import resource
import statistics
import subprocess
import sys
import tempfile
import time

KINDS=("fixed","cdc")
QS=(1,2,3,4,8,16)
ARMS=("baseline","eager","lazy")
N=262144
REPS=3
ORIGINAL_SHA="d5b97d8a75707243e49d79c4561ad9e40072939d"
PREREG="748d0dc9ad36c3dad791a1f1fed5084904aad897"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def load_orig(path:Path):
    spec=importlib.util.spec_from_file_location("o221_prior_frozen",path)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def child(a):
    from cmpct.reader import CMPCT
    original=load_orig(Path(a.workspace)/"research/o221_chunk_range_strided_oracle.py")
    ranges=original.queries(a.kind,a.n,a.q)
    start_w=time.perf_counter_ns()
    start_c=time.process_time_ns()
    idx=None
    with CMPCT(Path(a.archive)) as reader:
        assert reader.by[original.NAME[a.kind]][4]==a.n
        if a.arm=="eager":
            idx=original.build_anchors(reader,original.NAME[a.kind])
        streamed=hashlib.sha256()
        count_built=1 if idx is not None else 0
        for i,(start,size) in enumerate(ranges):
            if a.arm=="lazy" and i==1:
                idx=original.build_anchors(reader,original.NAME[a.kind])
                count_built+=1
            if idx is None:
                out=reader.read_range(original.NAME[a.kind],start,size)
            else:
                out=original.indexed_range(reader,original.NAME[a.kind],start,size,idx)
            assert out==b"Q"*size,(a.arm,a.kind,i,start,len(out))
            streamed.update(out)
        end_w=time.perf_counter_ns()
        end_c=time.process_time_ns()
    rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    assert count_built == (1 if a.arm=="eager" or (a.arm=="lazy" and a.q>1) else 0)
    print(json.dumps({"arm":a.arm,"kind":a.kind,"n":a.n,"q":a.q,
                      "index_build_count":count_built,
                      "wall_ms":(end_w-start_w)/1e6,"cpu_ms":(end_c-start_c)/1e6,
                      "peak_rss_kib":rss,
                      "range_starts_sha256":sha(json.dumps(ranges).encode()),
                      "range_result_sha256":streamed.hexdigest()},sort_keys=True))


def run(a):
    from cmpct.reader import CMPCT
    from cmpct.validation import preflight_archive
    workspace=Path(a.workspace).resolve()
    orig=load_orig(workspace/"research/o221_chunk_range_strided_oracle.py")
    samples=[]
    archives=[]
    with tempfile.TemporaryDirectory(prefix="o221b-") as td:
        for kind in KINDS:
            wire=orig.archive_bytes(workspace,kind,N)
            arc=Path(td)/(kind+".cmpct")
            arc.write_bytes(wire)
            assert preflight_archive(arc,verify_blob_headers=True)["files"]==1
            with CMPCT(arc) as reader:
                assert reader.verify()==1
                assert reader.read_range(orig.NAME[kind],N-17,17)==b"Q"*17
            archives.append({"kind":kind,"n":N,"archive_sha256":sha(wire),
                             "archive_bytes":len(wire),"logical_sha256":sha(b"Q"*N)})
            for q in QS:
                for rep in range(a.repeats):
                    order=list(ARMS)
                    random.Random(221021+q*33+rep*7+len(kind)).shuffle(order)
                    matched={}
                    for arm in order:
                        cmd=[sys.executable,__file__,"--child",
                             "--workspace",str(workspace),"--archive",str(arc),
                             "--kind",kind,"--n",str(N),"--q",str(q),"--arm",arm]
                        pstart=time.perf_counter_ns()
                        proc=subprocess.run(cmd,cwd=td,capture_output=True,text=True,check=False)
                        process_wall=(time.perf_counter_ns()-pstart)/1e6
                        if proc.returncode:
                            raise RuntimeError("child failed: "+str(cmd)+"\n"+proc.stdout+"\n"+proc.stderr)
                        obj=json.loads(proc.stdout.strip().splitlines()[-1])
                        assert obj["arm"]==arm and obj["kind"]==kind and obj["q"]==q and obj["n"]==N
                        obj.update({"rep":rep,"archive_sha256":sha(wire),
                                    "process_wall_ms":process_wall})
                        matched[arm]=obj
                        samples.append(obj)
                    assert len({matched[m]["range_starts_sha256"] for m in ARMS})==1
                    assert len({matched[m]["range_result_sha256"] for m in ARMS})==1
                    print("PAIR",kind,q,rep,
                          *(f"{arm}={matched[arm]['wall_ms']:.4f}" for arm in ARMS),flush=True)
    summary=[]
    for kind in KINDS:
        for q in QS:
            rows={arm:[x for x in samples if x["kind"]==kind and x["q"]==q
                        and x["arm"]==arm] for arm in ARMS}
            meds={arm:{key:statistics.median(x[key] for x in rows[arm])
                       for key in ("wall_ms","cpu_ms","peak_rss_kib")}
                  for arm in ARMS}
            baseline=meds["baseline"]
            summary.append({"kind":kind,"q":q,"medians":meds,
                           "lazy_wall_speedup":baseline["wall_ms"]/meds["lazy"]["wall_ms"],
                           "lazy_cpu_speedup":baseline["cpu_ms"]/meds["lazy"]["cpu_ms"],
                           "eager_wall_speedup":baseline["wall_ms"]/meds["eager"]["wall_ms"],
                           "eager_cpu_speedup":baseline["cpu_ms"]/meds["eager"]["cpu_ms"],
                           "lazy_rss_delta_mib":(meds["lazy"]["peak_rss_kib"]-baseline["peak_rss_kib"])/1024})
    q1=[s for s in summary if s["q"]==1]
    q4=[s for s in summary if s["q"]==4]
    passed=all(s["lazy_wall_speedup"]>=1/1.05 and s["lazy_cpu_speedup"]>=1/1.05
               for s in q1) and all(
                   s["lazy_wall_speedup"]>=1.10 and s["lazy_cpu_speedup"]>=1.10
                   and s["lazy_rss_delta_mib"]<=8.0 for s in q4)
    res={"question":"O221b","tier":"installed_reader_scientific_short_session_AB_not_product",
         "pre_registered_before_instrument_commit":PREREG,
         "original_o221_blob":ORIGINAL_SHA,"source_parent":"c5e13bb3fbb4cdade8b64246658ce7c7818de41f",
         "archives":archives,"samples":samples,"summary":summary,
         "decision":"LAZY_SHORT_SESSION_HEADROOM" if passed else "LAZY_SHORT_SESSION_NOT_PROVEN",
         "limits":"Linux only, repeated 1-byte RAW refs, startup excluded, no product changes"}
    Path(a.output).write_text(json.dumps(res,sort_keys=True,indent=2)+"\n")
    print("RESULT",res["decision"],flush=True)
    for s in summary:
        print("MEDIAN",s["kind"],s["q"],json.dumps({
            "lazy":s["lazy_wall_speedup"],"eager":s["eager_wall_speedup"]}),flush=True)


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--child",action="store_true")
    p.add_argument("--workspace",required=True)
    p.add_argument("--archive")
    p.add_argument("--kind",choices=KINDS)
    p.add_argument("--n",type=int,default=N)
    p.add_argument("--q",type=int)
    p.add_argument("--arm",choices=ARMS)
    p.add_argument("--repeats",type=int,default=REPS)
    p.add_argument("--output")
    args=p.parse_args()
    if args.child: child(args)
    else:
        if args.output is None: p.error("--output is required")
        run(args)
