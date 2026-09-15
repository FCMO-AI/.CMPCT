#!/usr/bin/env python3
"""A01 O1b: fresh same-length causal transfer with strongest observed ownership label."""
from __future__ import annotations
import hashlib, importlib.util, json, random, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('a01_o0',HERE/'a01_synthetic_basis_o0.py'); assert spec and spec.loader
O0=importlib.util.module_from_spec(spec); spec.loader.exec_module(O0)
SEED=0xA01B2026; N=8; SIZE=128*1024; OFFSET=31; STRIDE=257; THRESHOLD=.08

def rb(seed): return O0.random_bytes(seed,SIZE)
def positions_mut(src,pos,seed):
    r=random.Random(seed); b=bytearray(src)
    for p in sorted(set(pos)):
        v=r.randrange(256); b[p]=(v+1)&255 if v==b[p] else v
    return bytes(b)
def scatter(src,count,seed):
    r=random.Random(seed); return positions_mut(src,r.sample(range(SIZE),count),seed+1)
def blocks(src,seed):
    r=random.Random(seed); ps=[]
    for _ in range(24):
        s=r.randrange(SIZE-192); ps.extend(range(s,s+r.randrange(32,192)))
    return positions_mut(src,ps,seed+1)
def families():
    p=rb(SEED)
    burst=[blocks(p,SEED+100+i) for i in range(N)]
    sparse=[scatter(p,2100,SEED+200+i) for i in range(N)]
    shared=scatter(p,12000,SEED+300)
    hist=[scatter(shared,1050,SEED+400+i) for i in range(N)]
    p2=scatter(p,24000,SEED+500); p3=scatter(p,41000,SEED+501)
    clusters=[scatter(p,1300,SEED+600+i) for i in range(3)] + [scatter(p2,1300,SEED+610+i) for i in range(3)] + [scatter(p3,1300,SEED+620+i) for i in range(2)]
    near=[scatter(p,180,SEED+700)] + [scatter(p,2100,SEED+710+i) for i in range(N-1)]
    rnd=[rb(SEED+800+i) for i in range(N)]
    return {'private_block_bursts':burst,'private_sparse_scatter':sparse,'shared_history_plus_private':hist,'three_cluster':clusters,'near_observed_center':near,'independent_random':rnd}
def predictor(ms):
    mode=0; per=[0]*len(ms); samples=0
    for p in range(OFFSET,SIZE,STRIDE):
        vals=[m[p] for m in ms]; c={}
        for v in vals:c[v]=c.get(v,0)+1
        mode += len(vals)-max(c.values())
        for i,v in enumerate(vals): per[i]+=sum(v!=x for x in vals)
        samples+=1
    best=min(per); adv=(best-mode)/max(1,best)
    return {'sample_count':samples,'mode_disagreement':mode,'best_member_disagreement':best,'consensus_advantage':adv,'prediction':'PREDICT_LATENT' if adv>=THRESHOLD else 'PREDICT_OBSERVED_OR_MULTIMODAL'}
def fp(fs):
    h=hashlib.sha256()
    for n in sorted(fs):
        h.update(n.encode()+b'\0')
        for m in fs[n]:h.update(hashlib.sha256(m).digest())
    return h.hexdigest()
def main():
    fs=families(); rows={}; invalid=False
    for name,ms in fs.items():
        sr=O0.synth_root(ms); ok=O0.verify(sr,ms); invalid|=not ok
        br,bri=O0.best_real(ms); bt,bti=O0.best_two_real(ms); sc=O0.one_root_cost(sr,ms); obs=min(br,bt)
        actual=sc<=obs-4096 and sc<=int(obs*.99)
        rows[name]={'predictor':predictor(ms),'best_real':br,'best_real_index':bri,'best_two_real':bt,'best_two_real_indices':bti,'observed_portfolio':obs,'synthetic':sc,'synthetic_vs_observed_bytes':sc-obs,'synthetic_vs_observed_frac':(sc-obs)/obs,'actual_latent_material':actual,'roundtrip':ok}
    if invalid: decision='INSTRUMENT_INVALID'
    else:
        miss=[n for n,r in rows.items() if r['actual_latent_material'] and r['predictor']['prediction']!='PREDICT_LATENT']
        fp_rows=[n for n,r in rows.items() if not r['actual_latent_material'] and r['predictor']['prediction']=='PREDICT_LATENT']
        if miss: decision='PREDICTOR_FALSE_NEGATIVE'
        elif len(fp_rows)>1: decision='PREDICTOR_FALSE_POSITIVE'
        else: decision='CAUSAL_PREDICTOR_SEED'
    print(json.dumps({'schema':'cmpct-a01-o1b-strong-control-v1','seed':SEED,'threshold':THRESHOLD,'sample_offset':OFFSET,'sample_stride':STRIDE,'corpus_fingerprint':fp(fs),'rows':rows,'decision':decision},sort_keys=True,indent=2)); return 2 if invalid else 0
if __name__=='__main__':sys.exit(main())
