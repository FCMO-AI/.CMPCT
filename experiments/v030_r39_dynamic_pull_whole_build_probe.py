#!/usr/bin/env python3
"""R39 whole-build falsifier for R38's dynamic worker-pull scheduler.

Research only. The candidate arm replaces ThreadPoolExecutor.map *only while Builder.build
runs* with R38's O(W) dynamic-claim implementation. This lets complete archive creation,
not a micro-boundary, decide whether the mechanism deserves a product edit.
"""
from __future__ import annotations
import argparse, concurrent.futures, hashlib, json, statistics, threading, time
from contextlib import contextmanager
from pathlib import Path
from cmpct.builder import Builder

_ORIGINAL_MAP=concurrent.futures.ThreadPoolExecutor.map

def _dynamic_map(self,fn,*iterables,timeout=None,chunksize=1,buffersize=None):
    items=list(zip(*iterables)); n=len(items)
    if not n:return iter(())
    out=[None]*n; claim=0; lock=threading.Lock()
    def worker():
        nonlocal claim
        while True:
            with lock:
                if claim>=n:return
                i=claim; claim+=1
            out[i]=fn(*items[i])
    workers=min(int(getattr(self,'_max_workers',1)),n)
    futures=[self.submit(worker) for _ in range(workers)]
    for f in futures:f.result(timeout=timeout)
    if any(x is None for x in out):raise RuntimeError('R39 incomplete result vector')
    return iter(out)

@contextmanager
def scheduler(candidate:bool):
    if candidate:concurrent.futures.ThreadPoolExecutor.map=_dynamic_map
    try:yield
    finally:concurrent.futures.ThreadPoolExecutor.map=_ORIGINAL_MAP

def build(root:Path,out:Path,workers:int,candidate:bool):
    if out.exists():out.unlink()
    t=time.perf_counter()
    with scheduler(candidate):Builder(root,workers=workers,reproducible=True).build(out)
    return time.perf_counter()-t,hashlib.sha256(out.read_bytes()).hexdigest(),out.stat().st_size

def main():
    ap=argparse.ArgumentParser();ap.add_argument('root',type=Path);ap.add_argument('--workers',type=int,default=8);ap.add_argument('--repetitions',type=int,default=9);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    if a.workers<2 or a.repetitions<5:raise SystemExit('R39 requires workers>=2 and repetitions>=5')
    td=a.output.parent;td.mkdir(parents=True,exist_ok=True)
    # Warm both paths; byte identity is a hard precondition before timing receives meaning.
    _,base_digest,base_size=build(a.root,td/'r39-base.cmpct',a.workers,False)
    _,cand_digest,cand_size=build(a.root,td/'r39-candidate.cmpct',a.workers,True)
    if (base_digest,base_size)!=(cand_digest,cand_size):raise SystemExit('R39 FAIL: complete archive bytes differ')
    base=[];cand=[]
    for i in range(a.repetitions):
        arms=((False,base),(True,cand)) if i%2==0 else ((True,cand),(False,base))
        for candidate,sink in arms:
            dt,digest,size=build(a.root,td/('r39-candidate.cmpct' if candidate else 'r39-base.cmpct'),a.workers,candidate)
            if (digest,size)!=(base_digest,base_size):raise SystemExit('R39 FAIL: archive identity drift')
            sink.append(dt)
    mb=statistics.median(base);mc=statistics.median(cand)
    out={'schema':'cmpct-v030-r39-dynamic-pull-whole-build-v1','workers':a.workers,'repetitions':a.repetitions,'archive_identity':True,'archive_sha256':base_digest,'archive_bytes':base_size,'baseline_seconds':base,'candidate_seconds':cand,'baseline_median_seconds':mb,'candidate_median_seconds':mc,'candidate_over_baseline_ratio':mc/mb,'median_seconds_saved':mb-mc,'interpretation':'research whole-build evidence; no product credit until promoted and whole-system gates pass'}
    a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__':main()
