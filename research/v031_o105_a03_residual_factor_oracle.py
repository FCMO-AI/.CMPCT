#!/usr/bin/env python3
"""O105: deterministic A03 residual-space factorization research oracle.
No CMPCT archive/product/release claims. Follows prereg at Git commit 3527d8d.
"""
from __future__ import annotations
import argparse
import ctypes
import ctypes.util
import hashlib
import json
import platform
import random
import statistics
import time
from dataclasses import dataclass
from pathlib import Path

N=32
S=4096
G=8
REPS=5
MEMBER_B=24
ROOT_B=64
OWNER_B=32
SELECTIONS=(1,7,13,29)
SEEDS={"shared":0x1051, "heldout":0x1052, "hostile":0x1053, "flat":0x1054}

class Zstd:
    def __init__(self, level=9):
        name=ctypes.util.find_library('zstd')
        if not name:raise RuntimeError('libzstd unavailable')
        self.lib=ctypes.CDLL(name)
        u=ctypes.c_size_t
        self.lib.ZSTD_compressBound.argtypes=[u]
        self.lib.ZSTD_compressBound.restype=u
        self.lib.ZSTD_compress.argtypes=[ctypes.c_void_p,u,ctypes.c_void_p,u,ctypes.c_int]
        self.lib.ZSTD_compress.restype=u
        self.lib.ZSTD_decompress.argtypes=[ctypes.c_void_p,u,ctypes.c_void_p,u]
        self.lib.ZSTD_decompress.restype=u
        self.lib.ZSTD_isError.argtypes=[u]
        self.lib.ZSTD_isError.restype=ctypes.c_uint
        self.lib.ZSTD_getErrorName.argtypes=[u]
        self.lib.ZSTD_getErrorName.restype=ctypes.c_char_p
        self.lib.ZSTD_versionNumber.restype=ctypes.c_uint
        self.level=level
    def _checked(self, n):
        if self.lib.ZSTD_isError(n):raise RuntimeError(self.lib.ZSTD_getErrorName(n).decode())
        return int(n)
    def compress(self,data):
        buf=ctypes.create_string_buffer(self.lib.ZSTD_compressBound(len(data)))
        n=self._checked(self.lib.ZSTD_compress(buf,len(buf),data,len(data),self.level))
        return buf.raw[:n]
    def decompress(self,blob,size):
        buf=ctypes.create_string_buffer(size)
        n=self._checked(self.lib.ZSTD_decompress(buf,size,blob,len(blob)))
        if n!=size:raise AssertionError(f'decompressed length {n} != {size}')
        return buf.raw[:n]

def xor(a,b):
    if len(a)!=len(b):raise ValueError('length')
    return bytes(x^y for x,y in zip(a,b))

def mutate(base,positions,rand,unique_positions=()):
    out=bytearray(base)
    for pos,by in positions:
        out[pos:pos+len(by)]=by
    for pos,size in unique_positions:
        out[pos:pos+size]=rand.randbytes(size)
    return bytes(out)

def build_cases():
    results={}
    for regime,seed in SEEDS.items():
        r=random.Random(seed)
        if regime=='flat':
            base=r.randbytes(S)
            ts=[r.randbytes(S) for _ in range(N)]
        elif regime=='heldout':
            rows=[]
            for k in range(64):
                rows.append(f'{k:04d},'+'ABCDFGHH'+'|'+f'{(k*31)%100000:05d}'+':'+('Z'*42)+'\n')
            base=(''.join(rows).encode()+b' ' * S)[:S]
            shared=[]
            for j in (3,11,19,27,35,43,51,59):
                pos=j*64+18
                shared.append((pos,b'CHANGE'+bytes([65+j%26])*5))
            ts=[]
            for i in range(N):
                one=[(i%64)*64+2,((i*11+9)%64)*64+46]
                ts.append(mutate(base,shared,r,[(pos,5) for pos in one]))
        elif regime=='shared':
            base=r.randbytes(S)
            slots=r.sample(range(4,S-25),12)
            shared=[(pos,r.randbytes(12)) for pos in slots]
            ts=[]
            for i in range(N):
                unique_slots=r.sample([p for p in range(0,S-9) if all(not (q-8<=p<q+12) for q,_ in shared)],2)
                ts.append(mutate(base,shared,r,[(p,8) for p in unique_slots]))
        else:
            base=r.randbytes(S)
            ts=[]
            for i in range(N):
                slots=r.sample(range(S-9),14)
                ts.append(mutate(base,[],r,[(p,8) for p in slots]))
        assert len(base)==S and len(ts)==N and all(len(t)==S for t in ts)
        results[regime]=(base,ts)
    return results

@dataclass
class Archive:
    arm:str
    owners:dict
    sizes:dict
    target_ordinals:int
    base:bytes | None
    hashes:list
    def charged(self):
        return ROOT_B+self.target_ordinals*MEMBER_B+len(self.owners)*OWNER_B+sum(map(len,self.owners.values()))
    def selected(self,z,idx):
        arm=self.arm; block=idx//G; ordinal=idx%G
        phys=[]; decode=0
        def grab(k):
            nonlocal decode
            blob=self.owners[k]
            phys.append((k,len(blob)))
            size=self.sizes[k]
            decode+=size
            return z.decompress(blob,size)
        if arm=='A':
            target=grab(f't{idx}')
        elif arm=='B':
            target=grab('solid')[idx*S:(idx+1)*S]
        else:
            base=grab('base')
            if arm=='C':
                residual=grab(f'r{idx}')
            elif arm=='D':
                residual=grab(f'g{block}')[ordinal*S:(ordinal+1)*S]
            elif arm=='E':
                stream=grab(f'g{block}')
                residual=stream[ordinal::G]
            elif arm=='F':
                root=grab(f'root{block}')
                residual=root if ordinal==0 else xor(root,grab(f'd{idx}'))
            else:raise ValueError(arm)
            target=xor(base,residual)
        digest=hashlib.sha256(target).digest()
        if digest!=self.hashes[idx]:raise AssertionError(f'{arm} exact reconstruction failed at {idx}')
        return {'decoded_work':decode,'physical_bytes':sum(p[1] for p in phys),
                'owners':tuple(p[0] for p in phys),'reconstruction_depth':(0 if arm in ('A','B') else 2 if arm=='F' else 1)}

def encode(arm,base,ts,z):
    owners={};sizes={}
    def put(k,plain):
        sizes[k]=len(plain);owners[k]=z.compress(plain)
    if arm=='A':
        for i,t in enumerate(ts):put(f't{i}',t)
    elif arm=='B':put('solid',b''.join(ts))
    else:
        put('base',base)
        residuals=[xor(base,t) for t in ts]
        for start in range(0,N,G):
            block=start//G; group=residuals[start:start+G]
            if arm=='C':
                for j,r in enumerate(group):put(f'r{start+j}',r)
            elif arm=='D':put(f'g{block}',b''.join(group))
            elif arm=='E':
                put(f'g{block}',bytes(group[j][p] for p in range(S) for j in range(G)))
            elif arm=='F':
                root=group[0];put(f'root{block}',root)
                for j,r in enumerate(group[1:],start=1):put(f'd{start+j}',xor(r,root))
            else:raise ValueError(arm)
    return Archive(arm,owners,sizes,len(ts),base,
                   [hashlib.sha256(t).digest() for t in ts])

def run(reps=REPS):
    z=Zstd(9); cases=build_cases(); raw=[]
    arms=list('ABCDEF')
    for cidx,(case,(base,targets)) in enumerate(cases.items()):
        fingerprint=hashlib.sha256(base+b''.join(targets)).hexdigest()
        for rep in range(reps):
            order=arms[(rep+cidx)%6:]+arms[:(rep+cidx)%6]
            for arm in order:
                cpu0=time.process_time_ns(); wall0=time.perf_counter_ns()
                archive=encode(arm,base,targets,z)
                wall=time.perf_counter_ns()-wall0;cpu=time.process_time_ns()-cpu0
                ts=[];selected=[]
                for i in range(N):
                    result=archive.selected(z,i)
                    if i in SELECTIONS:selected.append(result)
                for i in SELECTIONS:
                    t0=time.perf_counter_ns(); archive.selected(z,i)
                    ts.append(time.perf_counter_ns()-t0)
                raw.append({'case':case,'input_sha256':fingerprint,'rep':rep,'arm':arm,
                            'complete_charged_bytes':archive.charged(),
                            'encoded_payload_bytes':sum(map(len,archive.owners.values())),
                            'owners':len(archive.owners),'create_wall_ns':wall,'create_cpu_ns':cpu,
                            'selected_read_ns':ts,'selected_work':selected,
                            'max_selected_decode_bytes':max(q['decoded_work'] for q in selected),
                            'max_selected_physical_bytes':max(q['physical_bytes'] for q in selected),
                            'max_dependency_depth':max(q['reconstruction_depth'] for q in selected)})
    results={}
    for c in cases:
        rows=[row for row in raw if row['case']==c]
        scores={}
        for arm in arms:
            v=[r for r in rows if r['arm']==arm]
            keys=['complete_charged_bytes','encoded_payload_bytes','create_wall_ns',
                  'create_cpu_ns','max_selected_decode_bytes','max_selected_physical_bytes']
            scores[arm]={k:statistics.median(q[k] for q in v) for k in keys}
            scores[arm]['selected_read_ns_median']=statistics.median(t for q in v for t in q['selected_read_ns'])
            scores[arm]['max_dependency_depth']=v[0]['max_dependency_depth']
            scores[arm]['owners']=v[0]['owners']
        simpler=min(scores[a]['complete_charged_bytes'] for a in 'ABCD')
        best=min('EF',key=lambda a:scores[a]['complete_charged_bytes'])
        relative=(scores[best]['complete_charged_bytes']-simpler)/simpler
        results[c]={'scores':scores,'simpler_min_bytes':simpler,
                    'winner_factor_arm':best,'factor_relative_to_strong_control':relative,
                    'positive_10pc_size':relative<=-0.1,
                    'decoder_selected_amplification_vs_C':scores[best]['max_selected_decode_bytes']/scores['C']['max_selected_decode_bytes']}
    return {'schema':'o105-a03-residual-factors-v1','source':'2026-10-25 prereg 3527d8d',
            'zstd_version':z.lib.ZSTD_versionNumber(),'zstd_level':z.level,
            'platform':platform.platform(),'python':platform.python_version(),
            'settings':{'N':N,'S':S,'G':G,'repetitions':reps,'owner_bytes':OWNER_B,
                        'member_bytes':MEMBER_B,'root_bytes':ROOT_B,'selections':SELECTIONS,
                        'seeds':SEEDS},'results':results,'raw':raw}

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',default='o105-evidence/raw.json');p.add_argument('--repetitions',type=int,default=REPS)
    a=p.parse_args();t=time.time()
    doc=run(a.repetitions)
    dest=Path(a.output);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(doc,indent=2,sort_keys=True)+'\n')
    print('RESULT:',a.output,'wall_s',time.time()-t)
    for k,c in doc['results'].items():
        print(k,'simpler',c['simpler_min_bytes'],'factor',c['winner_factor_arm'],
              c['scores'][c['winner_factor_arm']]['complete_charged_bytes'],
              'delta',f"{c['factor_relative_to_strong_control']:+.2%}",
              'decode_amp',c['decoder_selected_amplification_vs_C'])
        for arm,s in c['scores'].items():
            print(' ',arm,'bytes',s['complete_charged_bytes'],'wallms',round(s['create_wall_ns']/1e6,3),'decoded',s['max_selected_decode_bytes'])
if __name__=='__main__':main()
