#!/usr/bin/env python3
"""J24I53: source-identical fresh vs prefix-conditioned Builder court.

Research-only. This is NOT the official r24/ZIP parity evaluator or product proof.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import statistics
import subprocess
import sys
import tempfile
from datetime import datetime, timezone


SOURCE = "0b80ecb9b1742a6c20756f4c9e8e097103881cb4"
PREREG = "95134f0470baac94df700c8088c04caabd05c883"
CHILD = r"""
import hashlib, json, os, resource, statistics, sys, time
from pathlib import Path
import cmpct
from cmpct.builder import Builder
from cmpct.native_codec import _library_path

root=Path(sys.argv[1]).resolve()
corpora=Path(sys.argv[2]).resolve()
out=Path(sys.argv[3]).resolve()
context=sys.argv[4]
reps=int(sys.argv[5])
expected=(root/"src").resolve()
loaded=Path(cmpct.__file__).resolve()
if not loaded.is_relative_to(expected):
    raise AssertionError(("wrong package origin",str(loaded),str(expected)))
native=Path(_library_path()).resolve()
native_sha=hashlib.sha256(native.read_bytes()).hexdigest()
if context not in ("FRESH","PREFIX"):
    raise AssertionError("invalid context")
if not 1 <= reps <= 7:
    raise AssertionError("invalid repetition count")
out.parent.mkdir(parents=True,exist_ok=True)
def create(src,dest):
    try: dest.unlink()
    except FileNotFoundError: pass
    Builder(src).build(dest)
prefix=[]
if context=="PREFIX":
    for name in ("tiny","source","media"):
        dest=out.parent/(name+".cmpct")
        t0=time.perf_counter_ns(); c0=time.process_time_ns()
        create(corpora/name,dest)
        prefix.append({"name":name,"wall_ms":(time.perf_counter_ns()-t0)/1e6,
            "cpu_ms":(time.process_time_ns()-c0)/1e6,"archive_bytes":dest.stat().st_size,
            "sha256":hashlib.sha256(dest.read_bytes()).hexdigest()})
        dest.unlink()
src=corpora/"binary"
create(src,out)  # exactly one immediate untimed binary warmup in both contexts
samples=[]
for i in range(reps):
    t0=time.perf_counter_ns(); c0=time.process_time_ns()
    create(src,out)
    c1=time.process_time_ns(); t1=time.perf_counter_ns()
    # Archive SHA and stat are postconditions OUTSIDE the timed Builder closure.
    digest=hashlib.sha256(out.read_bytes()).hexdigest()
    samples.append({"rep":i,"wall_ms":(t1-t0)/1e6,"cpu_ms":(c1-c0)/1e6,
                    "archive_bytes":out.stat().st_size,"archive_sha256":digest})
if len({s["archive_sha256"] for s in samples})!=1 or len({s["archive_bytes"] for s in samples})!=1:
    raise AssertionError("non-deterministic archive in child")
print(json.dumps({"context":context,"module":str(loaded),"native_path":str(native),
    "native_sha256":native_sha,"reps":reps,"samples":samples,"prefix":prefix,
    "rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_max,
    "median_wall_ms":statistics.median(s["wall_ms"] for s in samples),
    "median_cpu_ms":statistics.median(s["cpu_ms"] for s in samples)},sort_keys=True))
"""


def sha_file(p: Path) -> str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        while chunk:=f.read(1024*1024):
            h.update(chunk)
    return h.hexdigest()


def git(*args: str) -> str:
    return subprocess.check_output(["git",*args],text=True).strip()


def tree_fingerprint(root: Path) -> dict:
    h=hashlib.sha256()
    total=0
    files=0
    for p in sorted(root.rglob("*")):
        if p.is_dir():
            continue
        st=p.lstat()
        rel=p.relative_to(root).as_posix()
        kind="link" if p.is_symlink() else "regular"
        digest=hashlib.sha256(os.readlink(p).encode()).hexdigest() if p.is_symlink() else sha_file(p)
        line=json.dumps([rel,kind,st.st_mode,st.st_size,st.st_mtime_ns,digest],separators=(",",":"))
        h.update((line+"\n").encode())
        files+=1
        if not p.is_symlink():
            total+=st.st_size
    return {"sha256":h.hexdigest(),"file_count":files,"logical_file_bytes":total}


def sign_group(rows, k: str) -> dict:
    a=[r[k] for r in rows if r["context"]=="FRESH"]
    b=[r[k] for r in rows if r["context"]=="PREFIX"]
    if len(a)!=2 or len(b)!=2:
        raise AssertionError("unbalanced group")
    return {"fresh_median":statistics.median(a),"prefix_median":statistics.median(b),
            "delta_ms":statistics.median(b)-statistics.median(a),
            "ratio":statistics.median(b)/statistics.median(a)}


def main() -> None:
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",type=Path,required=True)
    ap.add_argument("--reps",type=int,default=3)
    args=ap.parse_args()
    assert 1<=args.reps<=7
    root=Path(__file__).resolve().parents[1]
    head=git("rev-parse","HEAD")
    if head!=os.environ.get("EVIDENCE_HEAD"):
        raise AssertionError(("exact-head mismatch",head,os.environ.get("EVIDENCE_HEAD")))
    for ancestor in (PREREG,SOURCE,"1c073d024111be00a1246e67b1138a3d4232b3b9"):
        subprocess.run(["git","merge-base","--is-ancestor",ancestor,head],check=True)
    import universal_bench as universal
    scratch=Path(tempfile.mkdtemp(prefix="cmpct-j24i53-"))
    try:
        universal.WORK=scratch
        universal.CORP=scratch/"corpora"
        universal.OUT=scratch/"outputs"
        universal.CORP.mkdir()
        universal.OUT.mkdir()
        universal.make_corpora()
        corp=universal.CORP
        manifest=tree_fingerprint(corp)
        binaries={p.name:{"size":p.stat().st_size,"sha256":sha_file(p)}
                  for p in sorted((corp/"binary").iterdir())}
        source_paths=("src/cmpct/builder.py","src/cmpct/codec.py",
                      "src/cmpct/native_codec.py","benchmarks/zip_parity_bench.py",
                      "benchmarks/universal_bench.py")
        code_shas={p:sha_file(root/p) for p in source_paths}
        groups=[
          ("CONTEXT",["FRESH","PREFIX","PREFIX","FRESH"]),
          ("CONTEXT",["PREFIX","FRESH","FRESH","PREFIX"]),
          ("SHAM",["FRESH","FRESH","FRESH","FRESH"]),
          ("SHAM",["FRESH","FRESH","FRESH","FRESH"]),
        ]
        observations=[]
        physical_archive=args.out.parent/"j24i53-binary-final.cmpct"
        args.out.parent.mkdir(parents=True,exist_ok=True)
        for group,(court,order) in enumerate(groups):
            for slot,context in enumerate(order):
                outfile=scratch/"outputs"/("binary-"+str(group)+"-"+str(slot)+".cmpct")
                env=dict(os.environ)
                env["PYTHONPATH"]=str(root/"src")
                cmd=[sys.executable,"-c",CHILD,str(root),str(corp),str(outfile),
                     context,str(args.reps)]
                run=subprocess.run(cmd,text=True,capture_output=True,env=env,check=True)
                # Non-JSON tool chatter would make the experiment invalid, not get silently ignored.
                entry=json.loads(run.stdout)
                entry.update({"court":court,"group":group,"slot":slot,
                              "sequence":order,"label":"A" if slot in (0,3) else "B"})
                observations.append(entry)
                if not physical_archive.exists():
                    shutil.copy2(outfile,physical_archive)
                outfile.unlink()
                print("COURT",court,"group",group,"slot",slot,context,
                      "wall",entry["median_wall_ms"],"cpu",entry["median_cpu_ms"],flush=True)
        archives={s["archive_sha256"] for e in observations for s in e["samples"]}
        sizes={s["archive_bytes"] for e in observations for s in e["samples"]}
        nsha={e["native_sha256"] for e in observations}
        modules={e["module"] for e in observations}
        if len(archives)!=1 or len(sizes)!=1 or len(nsha)!=1 or len(modules)!=1:
            raise AssertionError(("source/archive identity divergence",archives,sizes,nsha,modules))
        if sha_file(physical_archive)!=next(iter(archives)):
            raise AssertionError("retained physical archive mismatch")
        if tree_fingerprint(corp)!=manifest:
            raise AssertionError("input tree changed during court")
        scoped=[x for x in observations if x["court"]=="CONTEXT"]
        sham=[x for x in observations if x["court"]=="SHAM"]
        per_group=[{"group":g,"wall":sign_group(scoped[i:i+4],"median_wall_ms"),
                    "cpu":sign_group(scoped[i:i+4],"median_cpu_ms")} for i,g in ((0,0),(4,1))]
        def aggregate(k):
            a=[s[k] for x in scoped if x["context"]=="FRESH" for s in x["samples"]]
            b=[s[k] for x in scoped if x["context"]=="PREFIX" for s in x["samples"]]
            av,bv=statistics.median(a),statistics.median(b)
            return {"fresh_median":av,"prefix_median":bv,
                    "delta_ms":bv-av,"ratio":bv/av,"samples_each":len(a)}
        wall=aggregate("wall_ms")
        cpu=aggregate("cpu_ms")
        # The sham uses label/order, not context. Same source and same FRESH semantics.
        def sham_effect(k):
            a=[s[k] for x in sham if x["label"]=="A" for s in x["samples"]]
            b=[s[k] for x in sham if x["label"]=="B" for s in x["samples"]]
            av,bv=statistics.median(a),statistics.median(b)
            return {"A_median":av,"B_median":bv,"delta_ms":bv-av,"ratio":bv/av}
        sw=scam_wall=sham_effect("wall_ms")
        sc=sham_effect("cpu_ms")
        def big(x):
            return x["ratio"]>1.05 and x["delta_ms"]>3
        ok_sign=all(g["wall"]["delta_ms"]>0 and g["cpu"]["delta_ms"]>0 for g in per_group)
        if big(sw) or big(sc):
            decision="AMBIGUOUS_SHAM_DRIFT"
        elif big(wall) and big(cpu) and ok_sign:
            decision="CONTEXT_COST_SUPPORTED"
        elif not ok_sign or (big(wall)!=big(cpu)):
            decision="AMBIGUOUS_SIGN_OR_CPU"
        else:
            decision="CONTEXT_COST_NOT_REPRODUCED"
        result={"schema":"cmpct-j24i53-context-court-v1","evidence_head":head,
          "preregistered_at_commit":PREREG,"source_root":str(root),
          "source_code_sha256":code_shas,"python":sys.version,"platform":platform.platform(),
          "tree_fingerprint_before_after":manifest,"binary_inputs":binaries,
          "native_sha256":next(iter(nsha)),
          "physical_archive":{"file":physical_archive.name,"sha256":next(iter(archives)),
                              "size":next(iter(sizes))},
          "contexts":["FRESH","PREFIX"],"repetitions_per_invocation":args.reps,
          "groups":per_group,"context_wall":wall,"context_cpu":cpu,
          "sham_wall":sw,"sham_cpu":sc,"decision":decision,"observations":observations,
          "claim_scope":"same-source Builder context-vs-fresh research only; historical release reds stay binding",
          "at_utc":datetime.now(timezone.utc).isoformat()}
        args.out.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
        print("J24I53_RESULT",json.dumps({"decision":decision,"context_wall":wall,
             "context_cpu":cpu,"sham_wall":sw,"sham_cpu":sc,
             "physical_archive":result["physical_archive"]},sort_keys=True),flush=True)
    finally:
        shutil.rmtree(scratch,ignore_errors=True)


if __name__=="__main__":
    main()
