from __future__ import annotations

"""Held-out hostile generalization test for the Analytics sparse-DEFLATE locality mechanism.

The frozen Analytics NPY member has an unusually sparse LZ77 dependency closure (~1.01x). That is not
a format guarantee. This diagnostic generates deterministic valid NPY payloads with very different
entropy/repetition structure, raw-DEFLATE compresses them with one fixed codec setting, verifies exact
round-trip, and measures every 4 KiB-aligned output request (plus the final suffix). Closure traversal
stops once the preregistered 8x bound is exceeded, because the question is admission safety, not how
spectacularly a hostile case can fail.

Falsifiable claim: the sparse reader may be unconditional for exact NPY/NPZ relations only if every
held-out case stays <=32,768 unique decoded dependencies per 4 KiB request. Any counterexample forces a
build-time structural locality admission check plus exact fallback; it is not permission to tune the
8x threshold or drop the workload.
"""

import argparse
from io import BytesIO
import json
import os
from pathlib import Path
import time
import zlib

import numpy as np

from benchmarks import v030_r4_deflate_sparse_dependency_oracle as SPARSE

SCHEMA='cmpct-v030-r4-deflate-sparse-hostile-generalization-v1'
REQUEST=4096
LIMIT=8*REQUEST
ROWS=120_000
COLS=8
LEVEL=6


def npy_bytes(a:np.ndarray)->bytes:
    b=BytesIO();np.save(b,a,allow_pickle=False);return b.getvalue()


def cases()->dict[str,bytes]:
    rng=np.random.default_rng(0xC0DEC0DE)
    return {
        'all_zero_f32':npy_bytes(np.zeros((ROWS,COLS),dtype=np.float32)),
        'repeated_row_f32':npy_bytes(np.tile(np.arange(COLS,dtype=np.float32),(ROWS,1))),
        'ramp_f32':npy_bytes(np.arange(ROWS*COLS,dtype=np.float32).reshape(ROWS,COLS)),
        'seeded_normal_f32':npy_bytes(rng.normal(size=(ROWS,COLS)).astype(np.float32)),
    }


def raw_deflate(data:bytes)->bytes:
    c=zlib.compressobj(LEVEL,zlib.DEFLATED,-15);return c.compress(data)+c.flush()


def starts(n:int)->list[int]:
    if n<=REQUEST:return [0]
    s=list(range(0,n-REQUEST+1,REQUEST));tail=n-REQUEST
    if s[-1]!=tail:s.append(tail)
    return s


def bounded_closure(parents,start:int,end:int)->tuple[int,bool]:
    seen=set();stack=list(range(start,end))
    while stack:
        n=stack.pop()
        if n in seen:continue
        seen.add(n)
        if len(seen)>LIMIT:return len(seen),True
        p=parents[n]
        if p>=0 and p not in seen:stack.append(p)
    return len(seen),False


def measure(name:str,raw:bytes)->dict:
    comp=raw_deflate(raw)
    if zlib.decompress(comp,-15)!=raw:raise RuntimeError(f'round-trip failed: {name}')
    t0=time.perf_counter();p=SPARSE.parse_parents(comp);parse_wall=time.perf_counter()-t0
    if len(p['parents'])!=len(raw):raise RuntimeError(f'parser length mismatch: {name}')
    worst={'unique_decoded_closure_bytes':0,'amplification':0.0,'start':0,'capped_after_failure':False};failed_requests=0;t0=time.perf_counter()
    for s in starts(len(raw)):
        e=min(s+REQUEST,len(raw));n,capped=bounded_closure(p['parents'],s,e);amp=n/max(1,e-s)
        if n>worst['unique_decoded_closure_bytes']:worst={'unique_decoded_closure_bytes':n,'amplification':amp,'start':s,'end':e,'capped_after_failure':capped}
        if n>LIMIT:failed_requests+=1
    return {'case':name,'raw_bytes':len(raw),'compressed_bytes':len(comp),'compression_ratio':len(comp)/len(raw),'blocks':p['blocks'],'tokens':p['tokens'],'literal_tokens':p['literal_tokens'],'copy_tokens':p['copy_tokens'],'parse_wall_s':parse_wall,'probe_wall_s':time.perf_counter()-t0,'requests':len(starts(len(raw))),'failed_requests_over_8x':failed_requests,'worst':worst,'passes_8x':worst['unique_decoded_closure_bytes']<=LIMIT}


def run()->dict:
    rows=[measure(k,v) for k,v in cases().items()];safe=all(r['passes_8x'] for r in rows)
    return {'schema':SCHEMA,'source_commit':os.environ.get('EVIDENCE_HEAD'),'request_bytes':REQUEST,'limit_unique_decoded_bytes':LIMIT,'codec':{'zlib_level':LEVEL,'wbits':-15},'cases':rows,'hypothesis':{'unconditional_sparse_reader_safe_on_held_out_hostile_npy':safe,'structural_admission_required':not safe},'contract':{'diagnostic_only':True,'release_credit':False,'held_out_from_genesis':True,'no_threshold_sweep':True,'fixed_codec':True,'exact_round_trip_required':True,'failure_cap_is_limit_plus_one':True},'next_if_counterexample':'add a cheap build-time dependency-locality admission proof and exact fallback before any productization; do not weaken 8x','next_if_all_pass':'broaden held-out families and then implement physical authenticated reader; four synthetic cases are not a universal proof'}


def main()->None:
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=Path('benchmark-artifacts/v030-r4-sparse-hostile.json'));a=p.parse_args();d=run();a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps({'cases':d['cases'],'hypothesis':d['hypothesis']},indent=2))
if __name__=='__main__':main()
