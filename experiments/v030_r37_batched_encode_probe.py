#!/usr/bin/env python3
"""R37 falsifier for the R36 scheduling-owner result.

This is research instrumentation, not product credit.  It holds candidate encoding and
canonical ordering fixed and changes only ThreadPoolExecutor scheduling granularity.
The experiment answers one narrow question: can deterministic coarse batches remove
meaningful scheduler overhead without changing a single encoded candidate result?
"""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import statistics
import tempfile
import time
from pathlib import Path

from cmpct.builder import Builder


def prepare(root: Path, workers: int):
    b=Builder(root, workers=workers)
    b.scan(); b._build_micro_packs(); b._prepare_deflate_reuse(); b._train_dictionary()
    ordered=[(h,b.cands[h]) for h in sorted(b.cands)]
    return b, ordered


def encode_one(b, item):
    h,c=item; codec,comp,meta=b._encode_candidate(h,c)
    return h,codec,comp,meta


def run_itemwise(b, ordered, workers):
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers,thread_name_prefix='cmpct-r37-item') as pool:
        return list(pool.map(lambda item: encode_one(b,item), ordered))


def run_batched(b, ordered, workers):
    # Contiguous deterministic slices preserve the global sorted-hash order after flattening.
    # At most one future per worker makes scheduling granularity independent of candidate count.
    n=len(ordered); batches=min(workers,n)
    q,r=divmod(n,batches); chunks=[]; start=0
    for i in range(batches):
        stop=start+q+(1 if i<r else 0); chunks.append(ordered[start:stop]); start=stop
    def encode_batch(chunk): return [encode_one(b,item) for item in chunk]
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers,thread_name_prefix='cmpct-r37-batch') as pool:
        parts=list(pool.map(encode_batch,chunks))
    return [row for part in parts for row in part]


def digest(rows):
    h=hashlib.sha256()
    for key,codec,comp,meta in rows:
        h.update(key); h.update(codec.to_bytes(2,'little')); h.update(len(meta).to_bytes(8,'little')); h.update(meta); h.update(comp)
    return h.hexdigest()


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('root',type=Path)
    ap.add_argument('--workers',type=int,default=8)
    ap.add_argument('--repetitions',type=int,default=7)
    ap.add_argument('--output',type=Path)
    args=ap.parse_args()
    if args.workers<2 or args.repetitions<3: raise SystemExit('need workers>=2 and repetitions>=3')
    b,ordered=prepare(args.root,args.workers)
    if len(ordered)<2: raise SystemExit('need at least two candidates')
    # Warm both arms once; only repeated same-process measurements enter the comparison.
    a=run_itemwise(b,ordered,args.workers); z=run_batched(b,ordered,args.workers)
    if a!=z: raise SystemExit('R37 FAIL: batched output differs from itemwise output')
    item=[]; batch=[]
    # Alternate arm order to avoid systematically gifting the second arm warmer caches.
    for i in range(args.repetitions):
        arms=(('item',run_itemwise),('batch',run_batched)) if i%2==0 else (('batch',run_batched),('item',run_itemwise))
        for name,fn in arms:
            t=time.perf_counter(); rows=fn(b,ordered,args.workers); dt=time.perf_counter()-t
            if rows!=a: raise SystemExit(f'R37 FAIL: {name} output drift')
            (item if name=='item' else batch).append(dt)
    mi=statistics.median(item); mb=statistics.median(batch)
    out={'schema':'cmpct-v030-r37-batched-encode-probe-v1','candidate_count':len(ordered),'workers':args.workers,'repetitions':args.repetitions,'identity':True,'encoded_digest':digest(a),'itemwise_seconds':item,'batched_seconds':batch,'itemwise_median_seconds':mi,'batched_median_seconds':mb,'batched_over_itemwise_ratio':mb/mi,'median_seconds_saved':mi-mb,'interpretation':'research-only; product credit requires uninstrumented full-build same-archive evidence'}
    text=json.dumps(out,indent=2,sort_keys=True); print(text)
    if args.output: args.output.write_text(text+'\n')

if __name__=='__main__': main()
