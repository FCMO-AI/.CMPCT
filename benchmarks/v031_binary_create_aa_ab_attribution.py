#!/usr/bin/env python3
"""Read-only v0.31 binary/library/create attribution court.

Research-only, not a replacement for the r24 release/ZIP ABBA gate. Uses the
candidate harness's exact frozen binary input tree, independently verifies
archive identity, and measures A/A sham alongside A/B interleaved creation.
Python process startup and import are excluded from individual create samples.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import statistics
import subprocess
import sys
from datetime import datetime, timezone

# A fresh subprocess per group ensures different source roots load independently.
CHILD = r'''
import hashlib, json, os, resource, statistics, sys, time
from pathlib import Path
import cmpct
from cmpct.builder import Builder
src=Path(sys.argv[1]); out=Path(sys.argv[2]); reps=int(sys.argv[3])
source_root=Path(sys.argv[4]).resolve()
loaded=Path(cmpct.__file__).resolve()
if not loaded.is_relative_to(source_root):
    raise RuntimeError(f"wrong cmpct module: {loaded} not under {source_root}")
def create():
    try: out.unlink()
    except FileNotFoundError: pass
    Builder(src).build(out)
create()  # untimed warm-up; same input and native path
wall=[]; cpu=[]; hashes=[]; sizes=[]
for i in range(reps):
    t0=time.perf_counter_ns(); c0=time.process_time_ns()
    create()
    cpu.append((time.process_time_ns()-c0)/1e6)
    wall.append((time.perf_counter_ns()-t0)/1e6)
    hashes.append(hashlib.sha256(out.read_bytes()).hexdigest())
    sizes.append(out.stat().st_size)
print(json.dumps({
  "wall_ms":wall,"cpu_ms":cpu,"hashes":hashes,"bytes":sizes,
  "rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
  "module":str(loaded),"python":platform.python_version() if False else sys.version.split()[0]
}))
'''

def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def git_head(root: Path) -> str:
    return subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()

def median(values):
    return statistics.median(values)

def main() -> None:
    p=argparse.ArgumentParser()
    p.add_argument("--base-root", type=Path, required=True)
    p.add_argument("--candidate-root", type=Path, required=True)
    p.add_argument("--corpus-root", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--reps", type=int, default=7)
    args=p.parse_args()
    base=args.base_root.resolve(); candidate=args.candidate_root.resolve()
    src=(args.corpus_root.resolve()/"binary")
    assert src.is_dir() and (src/"random16m.bin").is_file() and (src/"pattern32m.bin").is_file()
    assert 1 <= args.reps <= 100
    expected_base="88cf80d7f1f2f3ece7e83eefa78beece0bd4cc22"
    expected_candidate="8e25363c7bdcafb5a3bd2074b18ec29b84a91799"
    assert git_head(base)==expected_base, ("wrong exact base",git_head(base))
    # workflow-only commits are permitted after the candidate source HEAD.
    assert subprocess.run(["git","-C",str(candidate),"merge-base","--is-ancestor",expected_candidate,"HEAD"]).returncode==0
    expected_code={
       "src/cmpct/builder.py":(digest(base/"src/cmpct/builder.py"),digest(candidate/"src/cmpct/builder.py")),
       "src/cmpct/codec.py":(digest(base/"src/cmpct/codec.py"),digest(candidate/"src/cmpct/codec.py")),
       "src/cmpct/transactions.py":(digest(base/"src/cmpct/transactions.py"),digest(candidate/"src/cmpct/transactions.py")),
    }
    assert expected_code["src/cmpct/builder.py"][0]==expected_code["src/cmpct/builder.py"][1]
    assert expected_code["src/cmpct/codec.py"][0]==expected_code["src/cmpct/codec.py"][1]
    tree_bytes=[(str(p.relative_to(src)),p.stat().st_size,digest(p)) for p in sorted(src.iterdir()) if p.is_file()]
    assert len(tree_bytes)==2
    labels={"A":base,"A2":base,"B":candidate}
    # Two identical-source A/A blocks and two A/B blocks; reverses order
    # to test temporal drift instead of silently treating it as a code effect.
    sequences={
      "AA":["A","A2","A2","A","A2","A","A","A2"],
      "AB":["A","B","B","A","B","A","A","B"],
    }
    root=args.output.parent.resolve();root.mkdir(parents=True,exist_ok=True)
    raw=[]
    for court,order in sequences.items():
        for idx,label in enumerate(order):
            engine=labels[label]
            out=root/f"{court}-{idx}-{label}.cmpct"
            env=dict(os.environ)
            env["PYTHONPATH"]=str(engine/"src")
            x=subprocess.run([sys.executable,"-c",CHILD,str(src),str(out),str(args.reps),str(engine/"src")],
                             env=env,text=True,capture_output=True,check=True)
            v=json.loads(x.stdout)
            if len(set(v["hashes"]))!=1 or len(set(v["bytes"]))!=1:
                raise RuntimeError(f"non-deterministic archive: {court}/{idx}/{label}")
            v.update({"court":court,"order":idx,"label":label,"source_commit":git_head(engine)})
            raw.append(v)
            print(f"{court} step={idx} engine={label} wall_med_ms={median(v['wall_ms']):.4f} cpu_med_ms={median(v['cpu_ms']):.4f} bytes={v['bytes'][0]}",flush=True)
            out.unlink()
    sizes=set(x["bytes"][0] for x in raw)
    hashes=set(x["hashes"][0] for x in raw)
    # Both tested source revisions have identical Builder and codec sources.
    # Archive divergence would invalidate same-semantics attribution.
    assert len(sizes)==1 and len(hashes)==1,(sizes,hashes)
    summary={}
    for court in sequences:
        subsets={
          "base":[x for x in raw if x["court"]==court and x["label"]=="A"],
          "comparison":[x for x in raw if x["court"]==court and x["label"]!="A"],
        }
        a,b=([v for x in subsets[k] for v in x["wall_ms"]] for k in ["base","comparison"])
        ca,cb=([v for x in subsets[k] for v in x["cpu_ms"]] for k in ["base","comparison"])
        am,bm=median(a),median(b)
        summary[court]={
            "base_median_wall_ms":am,"comparison_median_wall_ms":bm,
            "delta_wall_ms":bm-am,"delta_wall_pct":100*(bm/am-1),
            "base_median_cpu_ms":median(ca),"comparison_median_cpu_ms":median(cb),
            "delta_cpu_ms":median(cb)-median(ca),
            "samples_per_side":len(a),
        }
    record={
      "schema":"cmpct-v031-binary-create-aa-ab-attribution-v1",
      "claim_scope":"diagnostic independent same-corpus same-runner A/A vs A/B; not release credit, not a parity-gate override",
      "started_utc":datetime.now(timezone.utc).isoformat(),
      "candidate_repo_head":git_head(candidate),
      "base_source_head":git_head(base),"candidate_engine_head":expected_candidate,
      "python":platform.python_version(),"platform":platform.platform(),
      "source_file_hashes":expected_code,
      "binary_source_files":tree_bytes,
      "archive_bytes":next(iter(sizes)),"archive_sha256":next(iter(hashes)),
      "sequence":sequences,"repetitions_per_group":args.reps,
      "summary":summary,"samples":raw,
    }
    args.output.write_text(json.dumps(record,sort_keys=True,indent=2)+"\n")
    print("COURT_SUMMARY "+json.dumps(summary,sort_keys=True))
    print("DIAGNOSTIC_ONLY: release threshold and frozen comparator unchanged")
if __name__=="__main__":
    main()
