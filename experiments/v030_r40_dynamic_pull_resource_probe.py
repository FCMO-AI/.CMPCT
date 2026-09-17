#!/usr/bin/env python3
"""R40 subprocess resource probe for the R39 dynamic worker-pull scheduler."""
from __future__ import annotations
import argparse, concurrent.futures, hashlib, json, resource, threading, time
from contextlib import contextmanager
from pathlib import Path
from cmpct.builder import Builder
_ORIGINAL_MAP=concurrent.futures.ThreadPoolExecutor.map

def _dynamic_map(self,fn,*iterables,timeout=None,chunksize=1,buffersize=None):
    items=list(zip(*iterables));n=len(items)
    if not n:return iter(())
    out=[None]*n;claim=0;lock=threading.Lock()
    def worker():
        nonlocal claim
        while True:
            with lock:
                if claim>=n:return
                i=claim;claim+=1
            out[i]=fn(*items[i])
    futures=[self.submit(worker) for _ in range(min(int(getattr(self,'_max_workers',1)),n))]
    for f in futures:f.result(timeout=timeout)
    if any(x is None for x in out):raise RuntimeError('R40 incomplete result vector')
    return iter(out)

@contextmanager
def scheduler(arm):
    if arm=='dynamic':concurrent.futures.ThreadPoolExecutor.map=_dynamic_map
    try:yield
    finally:concurrent.futures.ThreadPoolExecutor.map=_ORIGINAL_MAP

def _cpu(r):return r.ru_utime+r.ru_stime

def main():
    ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);ap.add_argument('output',type=Path);ap.add_argument('--arm',choices=('baseline','dynamic'),required=True);ap.add_argument('--workers',type=int,default=8);a=ap.parse_args()
    self0=resource.getrusage(resource.RUSAGE_SELF);child0=resource.getrusage(resource.RUSAGE_CHILDREN);t0=time.perf_counter()
    with scheduler(a.arm):Builder(a.source,workers=a.workers,reproducible=True).build(a.output)
    wall=time.perf_counter()-t0;self1=resource.getrusage(resource.RUSAGE_SELF);child1=resource.getrusage(resource.RUSAGE_CHILDREN)
    cpu=(_cpu(self1)-_cpu(self0))+(_cpu(child1)-_cpu(child0))
    # Linux ru_maxrss is KiB. Child processes here are sequential helpers, so max(self, children)
    # is the conservative available process-tree peak rather than silently dropping helper memory.
    peak=max(self1.ru_maxrss,child1.ru_maxrss)
    print(json.dumps({'schema':'cmpct-v030-r40-subprocess-v2','arm':a.arm,'wall_seconds':wall,'cpu_seconds':cpu,'peak_rss_kib':peak,'archive_bytes':a.output.stat().st_size,'archive_sha256':hashlib.sha256(a.output.read_bytes()).hexdigest()},sort_keys=True))
if __name__=='__main__':main()
