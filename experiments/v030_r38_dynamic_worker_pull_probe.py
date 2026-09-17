#!/usr/bin/env python3
"""R38 falsifier: O(W) persistent futures with dynamic candidate claiming.

Research instrumentation only. It holds candidate encoding and canonical ordering fixed,
changing only scheduling ownership. Product credit requires later uninstrumented full-build evidence.
"""
from __future__ import annotations
import argparse, concurrent.futures, hashlib, json, statistics, threading, time
from pathlib import Path
from cmpct.builder import Builder

def prepare(root:Path,workers:int):
    b=Builder(root,workers=workers)
    b.scan(); b._build_micro_packs(); b._prepare_deflate_reuse(); b._train_dictionary()
    return b,[(h,b.cands[h]) for h in sorted(b.cands)]

def encode_one(b,item):
    h,c=item; codec,comp,meta=b._encode_candidate(h,c); return h,codec,comp,meta

def run_itemwise(b,ordered,workers):
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers,thread_name_prefix='cmpct-r38-item') as pool:
        return list(pool.map(lambda item:encode_one(b,item),ordered))

def run_dynamic_pull(b,ordered,workers):
    n=len(ordered); out=[None]*n; claim=0; lock=threading.Lock()
    def worker():
        nonlocal claim
        while True:
            with lock:
                if claim>=n:return
                i=claim; claim+=1
            out[i]=encode_one(b,ordered[i])
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers,thread_name_prefix='cmpct-r38-pull') as pool:
        futures=[pool.submit(worker) for _ in range(min(workers,n))]
        for f in futures:f.result()
    if any(row is None for row in out):raise RuntimeError('R38 incomplete result vector')
    return out

def digest(rows):
    h=hashlib.sha256()
    for key,codec,comp,meta in rows:
        h.update(key);h.update(codec.to_bytes(2,'little'));h.update(len(meta).to_bytes(8,'little'));h.update(meta);h.update(comp)
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('root',type=Path);ap.add_argument('--workers',type=int,default=8);ap.add_argument('--repetitions',type=int,default=9);ap.add_argument('--output',type=Path);args=ap.parse_args()
    if args.workers<2 or args.repetitions<3:raise SystemExit('need workers>=2 and repetitions>=3')
    b,ordered=prepare(args.root,args.workers)
    if len(ordered)<2:raise SystemExit('need at least two candidates')
    oracle=run_itemwise(b,ordered,args.workers); warm=run_dynamic_pull(b,ordered,args.workers)
    if oracle!=warm:raise SystemExit('R38 FAIL: dynamic-pull output differs from itemwise output')
    item=[];pull=[]
    for i in range(args.repetitions):
        arms=(('item',run_itemwise),('pull',run_dynamic_pull)) if i%2==0 else (('pull',run_dynamic_pull),('item',run_itemwise))
        for name,fn in arms:
            t=time.perf_counter();rows=fn(b,ordered,args.workers);dt=time.perf_counter()-t
            if rows!=oracle:raise SystemExit(f'R38 FAIL: {name} output drift')
            (item if name=='item' else pull).append(dt)
    mi=statistics.median(item);mp=statistics.median(pull)
    out={'schema':'cmpct-v030-r38-dynamic-worker-pull-probe-v1','candidate_count':len(ordered),'workers':args.workers,'repetitions':args.repetitions,'identity':True,'encoded_digest':digest(oracle),'itemwise_seconds':item,'dynamic_pull_seconds':pull,'itemwise_median_seconds':mi,'dynamic_pull_median_seconds':mp,'dynamic_pull_over_itemwise_ratio':mp/mi,'median_seconds_saved':mi-mp,'interpretation':'research-only; product credit requires uninstrumented full-build same-archive evidence'}
    text=json.dumps(out,indent=2,sort_keys=True);print(text)
    if args.output:args.output.write_text(text+'\n')
if __name__=='__main__':main()
