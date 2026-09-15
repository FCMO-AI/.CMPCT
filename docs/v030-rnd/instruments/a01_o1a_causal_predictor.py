#!/usr/bin/env python3
"""Frozen A01 O1a causal-predictor transfer instrument."""
from __future__ import annotations
import hashlib, importlib.util, json, random, sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
O0_PATH=HERE/'v030_foundry_a01_synthetic_basis_o0.py'
spec=importlib.util.spec_from_file_location('a01_o0',O0_PATH)
assert spec and spec.loader
O0=importlib.util.module_from_spec(spec); spec.loader.exec_module(O0)

SEED=0xA01CA551
N=8; SIZE=128*1024
SAMPLE_OFFSET=31; SAMPLE_STRIDE=257
THRESHOLD=0.08


def rb(seed,n=SIZE): return O0.random_bytes(seed,n)

def mutate_positions(src, positions, seed):
    rng=random.Random(seed); b=bytearray(src)
    for p in positions:
        v=rng.randrange(256)
        if v==b[p]: v=(v+1)&255
        b[p]=v
    return bytes(b)

def scatter(src,count,seed):
    rng=random.Random(seed); return mutate_positions(src,rng.sample(range(len(src)),count),seed+1)

def bursts(src,seed):
    rng=random.Random(seed); pos=set()
    for _ in range(18):
        start=rng.randrange(0,len(src)-256); ln=rng.randrange(48,224)
        pos.update(range(start,start+ln))
    return mutate_positions(src,sorted(pos),seed+1)


def families():
    proto=rb(SEED)
    ib=[bursts(proto,SEED+100+i) for i in range(N)]
    isc=[scatter(proto,2300,SEED+200+i) for i in range(N)]
    # Shared historical patch is present in every member, then private edits.
    shared=scatter(proto,9000,SEED+300)
    corr=[scatter(shared,900,SEED+400+i) for i in range(N)]
    p2=scatter(proto,26000,SEED+500)
    clu=[scatter(proto,1700,SEED+600+i) for i in range(N//2)] + [scatter(p2,1700,SEED+700+i) for i in range(N//2)]
    near=[scatter(proto,250,SEED+800)] + [scatter(proto,2300,SEED+810+i) for i in range(N-1)]
    rnd=[rb(SEED+900+i) for i in range(N)]
    return {'independent_bursts':ib,'independent_scatter':isc,'shared_correlated_patch':corr,'two_cluster':clu,'near_medoid':near,'independent_random':rnd}


def predictor(ms):
    coords=range(SAMPLE_OFFSET,len(ms[0]),SAMPLE_STRIDE)
    mode_dis=0; member_dis=[0]*len(ms); samples=0
    for p in coords:
        vals=[m[p] for m in ms]; counts={}
        for v in vals: counts[v]=counts.get(v,0)+1
        mode_count=max(counts.values()); mode_dis += len(vals)-mode_count
        for i,v in enumerate(vals): member_dis[i] += sum(v!=x for x in vals)
        samples += 1
    best=min(member_dis); adv=(best-mode_dis)/max(1,best)
    return {'sample_count':samples,'mode_disagreement':mode_dis,'best_member_disagreement':best,'consensus_advantage':adv,'prediction':'PREDICT_LATENT' if adv>=THRESHOLD else 'PREDICT_OBSERVED_OR_MULTIMODAL'}


def fp(fs):
    h=hashlib.sha256()
    for n in sorted(fs):
        h.update(n.encode()+b'\0')
        for m in fs[n]: h.update(hashlib.sha256(m).digest())
    return h.hexdigest()


def main():
    fs=families(); rows={}; invalid=False
    for name,ms in fs.items():
        sr=O0.synth_root(ms); ok=O0.verify(sr,ms); invalid |= not ok
        br,bri=O0.best_real(ms); bt,bti=O0.best_two_real(ms); sc=O0.one_root_cost(sr,ms,0); d=O0.direct_cost(ms)
        actual=(sc<=br-4096 and sc<=int(br*.99))
        rows[name]={'predictor':predictor(ms),'direct':d,'best_real':br,'best_real_index':bri,'best_two_real':bt,'best_two_real_indices':bti,'synthetic':sc,'synthetic_vs_real_bytes':sc-br,'synthetic_vs_real_frac':(sc-br)/br,'synthetic_vs_two_real_bytes':sc-bt,'actual_latent_material':actual,'roundtrip':ok}
    if invalid: decision='INSTRUMENT_INVALID'
    elif rows['two_cluster']['synthetic'] <= int(rows['two_cluster']['best_two_real']*.99): decision='MULTIMODAL_CAUSAL_SURPRISE'
    else:
        misses=[n for n,r in rows.items() if r['actual_latent_material'] and r['predictor']['prediction']!='PREDICT_LATENT']
        nonmat=[r for r in rows.values() if not r['actual_latent_material']]
        fps=[r for r in nonmat if r['predictor']['prediction']=='PREDICT_LATENT']
        if misses: decision='PREDICTOR_FALSE_NEGATIVE'
        elif len(fps)*3>max(1,len(nonmat)): decision='PREDICTOR_FALSE_POSITIVE'
        else: decision='CAUSAL_PREDICTOR_SEED'
    out={'schema':'cmpct-v030-foundry-a01-o1a-causal-predictor-v1','seed':SEED,'size':SIZE,'n':N,'sample_offset':SAMPLE_OFFSET,'sample_stride':SAMPLE_STRIDE,'threshold':THRESHOLD,'corpus_fingerprint':fp(fs),'rows':rows,'decision':decision}
    print(json.dumps(out,sort_keys=True,indent=2)); return 2 if invalid else 0

if __name__=='__main__': sys.exit(main())
