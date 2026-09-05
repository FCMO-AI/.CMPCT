"""ONE-G0.2 native carrying-cost A/B for phase witnesses fused into byte observation."""
from __future__ import annotations

import ctypes
import json
import os
import random
import statistics
import subprocess
import tempfile
import time
import zlib
from pathlib import Path

from benchmarks.one.one_g02_gear_replacement_ab import _GEAR
from benchmarks.one.one_g02_bounded_shift_phase_certificate_validation import _source_certificate

REPETITIONS=7
PHASES=(0,1,2,30,31)
K=4
MODELED_INCREMENTAL_STATE_BYTES=248
LARGE_REPS=16


def _c_source()->str:
    gear=",\n".join(f"UINT64_C({v})" for v in _GEAR)
    return f'''#include <stddef.h>
#include <stdint.h>
#define K 4u
#define P 5u
#define MASK UINT64_C(1023)
static const uint64_t G[256]={{ {gear} }};
static volatile uint64_t ESC;
typedef struct {{ uint64_t checksum,anchors,samples,admissions,replacements; }} stats_t;
static inline uint64_t mix64(uint64_t x) {{ x^=x>>30; x*=UINT64_C(0xBF58476D1CE4E5B9); x^=x>>27; x*=UINT64_C(0x94D049BB133111EB); x^=x>>31; return x; }}
static inline int pidx(unsigned p) {{ return p==0?0:p==1?1:p==2?2:p==30?3:p==31?4:-1; }}
static inline int worse(uint64_t ah,uint32_t ap,uint64_t bh,uint32_t bp) {{ return ah>bh || (ah==bh && ap>bp); }}
static inline void sw(uint64_t *ah,uint32_t *ap,uint64_t *bh,uint32_t *bp) {{ uint64_t h=*ah;*ah=*bh;*bh=h;uint32_t p=*ap;*ap=*bp;*bp=p; }}
static inline void offer(uint64_t h,uint32_t pos,uint64_t hs[K],uint32_t ps[K],unsigned *cnt,uint64_t *adm,uint64_t *rep) {{
  if(*cnt<K) {{ unsigned i=(*cnt)++;hs[i]=h;ps[i]=pos;(*adm)++;while(i){{unsigned q=(i-1u)>>1;if(!worse(hs[i],ps[i],hs[q],ps[q]))break;sw(&hs[i],&ps[i],&hs[q],&ps[q]);i=q;}}return; }}
  if(h>=hs[0]) return; hs[0]=h;ps[0]=pos;(*adm)++;(*rep)++;unsigned i=0;for(;;){{unsigned l=i*2u+1u;if(l>=K)break;unsigned r=l+1u,w=l;if(r<K&&worse(hs[r],ps[r],hs[l],ps[l]))w=r;if(!worse(hs[w],ps[w],hs[i],ps[i]))break;sw(&hs[i],&ps[i],&hs[w],&ps[w]);i=w;}}
}}
static inline uint64_t baseline_once(const uint8_t*d,size_t n,uint64_t *anchors) {{ uint64_t pre=0;size_t run=0;uint8_t rv=0;for(size_t i=0;i<n;i++){{uint8_t v=d[i];if(!run||v!=rv){{rv=v;run=1;}}else run++;pre=(pre<<1)+G[v];if(i+1>=64u&&!(pre&MASK))(*anchors)++;}}return pre+run; }}
static inline uint64_t fused_once(const uint8_t*d,size_t n,uint64_t *anchors,uint64_t *samples,uint64_t *adm,uint64_t *rep) {{
  uint64_t pre=0,word=0,hs[P][K]={{{{0}}}};uint32_t ps[P][K]={{{{0}}}};unsigned cnt[P]={{0}};size_t run=0;uint8_t rv=0;
  for(size_t i=0;i<n;i++){{uint8_t v=d[i];if(!run||v!=rv){{rv=v;run=1;}}else run++;pre=(pre<<1)+G[v];if(i+1>=64u&&!(pre&MASK))(*anchors)++;
    if(i<8u) word|=((uint64_t)v)<<(8u*i); else word=(word>>8)|((uint64_t)v<<56);
    if(i>=7u){{uint32_t pos=(uint32_t)(i-7u);int q=pidx(pos&31u);if(q>=0){{uint64_t h=mix64(word^UINT64_C(0x9E3779B97F4A7C15));offer(h,pos,hs[q],ps[q],&cnt[q],adm,rep);(*samples)++;}}}}
  }} uint64_t z=pre+word+run;for(unsigned q=0;q<P;q++)for(unsigned j=0;j<cnt[q];j++)z^=hs[q][j]+((uint64_t)ps[q][j]<<((q+j)&31u));return z;
}}
uint64_t run_baseline(const uint8_t*d,size_t n,unsigned reps,stats_t*out){{uint64_t x=0,a=0;for(unsigned r=0;r<reps;r++)x^=baseline_once(d,n,&a)+(uint64_t)r;ESC^=x;if(out){{out->checksum=x;out->anchors=a;out->samples=out->admissions=out->replacements=0;}}return x;}}
uint64_t run_fused(const uint8_t*d,size_t n,unsigned reps,stats_t*out){{uint64_t x=0,a=0,s=0,m=0,rp=0;for(unsigned r=0;r<reps;r++)x^=fused_once(d,n,&a,&s,&m,&rp)+(uint64_t)r;ESC^=x;if(out){{out->checksum=x;out->anchors=a;out->samples=s;out->admissions=m;out->replacements=rp;}}return x;}}
int phase_exact(const uint8_t*d,size_t n,uint64_t out_h[P*K],uint32_t out_p[P*K],uint8_t out_phase[P*K]){{uint64_t word=0,hs[P][K]={{{{0}}}};uint32_t ps[P][K]={{{{0}}}};unsigned cnt[P]={{0}};uint64_t a=0,r=0;for(size_t i=0;i<n;i++){{uint8_t v=d[i];if(i<8u)word|=((uint64_t)v)<<(8u*i);else word=(word>>8)|((uint64_t)v<<56);if(i>=7u){{uint32_t pos=(uint32_t)(i-7u);int q=pidx(pos&31u);if(q>=0)offer(mix64(word^UINT64_C(0x9E3779B97F4A7C15)),pos,hs[q],ps[q],&cnt[q],&a,&r);}}}}unsigned o=0;static const uint8_t pv[P]={{0,1,2,30,31}};for(unsigned q=0;q<P;q++)for(unsigned j=0;j<cnt[q];j++){{out_h[o]=hs[q][j];out_p[o]=ps[q][j];out_phase[o]=pv[q];o++;}}return (int)o;}}
'''

class Stats(ctypes.Structure):
    _fields_=[("checksum",ctypes.c_uint64),("anchors",ctypes.c_uint64),("samples",ctypes.c_uint64),("admissions",ctypes.c_uint64),("replacements",ctypes.c_uint64)]

def _build(td:str):
    src=Path(td)/"native.c";so=Path(td)/"native.so";src.write_text(_c_source())
    subprocess.run([os.environ.get("CC","cc"),"-O3","-std=c11","-fPIC","-shared",str(src),"-o",str(so)],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    lib=ctypes.CDLL(str(so));p8=ctypes.POINTER(ctypes.c_uint8)
    for name in ("run_baseline","run_fused"):
        fn=getattr(lib,name);fn.argtypes=[p8,ctypes.c_size_t,ctypes.c_uint,ctypes.POINTER(Stats)];fn.restype=ctypes.c_uint64
    lib.phase_exact.argtypes=[p8,ctypes.c_size_t,ctypes.POINTER(ctypes.c_uint64),ctypes.POINTER(ctypes.c_uint32),ctypes.POINTER(ctypes.c_uint8)];lib.phase_exact.restype=ctypes.c_int
    return lib

def _buf(data:bytes): return (ctypes.c_uint8*len(data)).from_buffer_copy(data)
def _native_cert(lib,data:bytes):
    b=_buf(data);hs=(ctypes.c_uint64*20)();ps=(ctypes.c_uint32*20)();ph=(ctypes.c_uint8*20)();n=lib.phase_exact(b,len(data),hs,ps,ph)
    return sorted((int(hs[i]),int(ps[i]),int(ph[i])) for i in range(n))
def _reference(data:bytes): return sorted(_source_certificate(data)[0])
def _cases():
    r1=random.Random(88001).randbytes(1024*1024);comp=zlib.compress(random.Random(88002).randbytes(1024*1024),9);basis=random.Random(88003).randbytes(4096);v=random.Random(88004).randbytes(512*1024)
    return {"random_1mib":r1,"compressed_like_1mib":comp,"repeated_1mib":basis*256,"shifted_version_1mib":v+b"X"+v[:-1],"zeros_1mib":b"\0"*(1024*1024),"alternating_hostile_1mib":b"\0\xff"*(512*1024),"tiny_4k":random.Random(88005).randbytes(4096),"tiny_64b":random.Random(88006).randbytes(64)}
def _sample(fn,b,n,reps):
    vals=[];last=Stats()
    for _ in range(REPETITIONS):
        st=Stats();t=time.perf_counter_ns();fn(b,n,reps,ctypes.byref(st));vals.append(time.perf_counter_ns()-t);last=st
    return int(statistics.median(vals)),last

def run():
    rows=[];mismatches=[]
    with tempfile.TemporaryDirectory(prefix="one_fused_phase_") as td:
        lib=_build(td);cases=_cases()
        for name,data in cases.items():
            if _native_cert(lib,data)!=_reference(data): mismatches.append(name)
        for name,data in cases.items():
            b=_buf(data);n=len(data);reps=LARGE_REPS if n>=1024*1024-1024 else (1024 if n>=4096 else 65536)
            bt,bs=_sample(lib.run_baseline,b,n,reps);ft,fs=_sample(lib.run_fused,b,n,reps)
            rows.append({"case":name,"input_bytes":n,"internal_repetitions":reps,"baseline_median_ns":bt,"fused_phase_median_ns":ft,"fused_over_baseline":ft/bt,"modeled_incremental_state_bytes":MODELED_INCREMENTAL_STATE_BYTES,"phase_samples_all_reps":int(fs.samples),"witness_admissions_all_reps":int(fs.admissions),"heap_replacements_all_reps":int(fs.replacements),"native_witness_equal_reference":name not in mismatches})
    gate_names={"random_1mib","compressed_like_1mib","repeated_1mib","shifted_version_1mib","zeros_1mib"};large=[r for r in rows if r["case"] in gate_names];ratios=[r["fused_over_baseline"] for r in large]
    by={r["case"]:r for r in rows};all1=[r for r in rows if r["input_bytes"]>=1024*1024-1024]
    ok=(not mismatches and statistics.median(ratios)<=1.12 and by["random_1mib"]["fused_over_baseline"]<=1.15 and by["compressed_like_1mib"]["fused_over_baseline"]<=1.15 and all(r["fused_over_baseline"]<=1.18 for r in all1) and by["tiny_4k"]["fused_over_baseline"]<=1.30 and by["tiny_64b"]["fused_over_baseline"]<=1.50)
    return {"schema":"cmpct-one-g02-fused-phase-witness-native-cost-v1","experimental_version":"ONE-G0.2","source_sha":os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound","modeled_incremental_state_bytes":MODELED_INCREMENTAL_STATE_BYTES,"native_witness_mismatches":mismatches,"large_gate_median_fused_over_baseline":statistics.median(ratios),"decision":"advance_fused_phase_to_combined_coverage" if ok else "retire_unconditional_fused_phase_witness","claim_boundary":"native carrying-cost viability only; no density/reader/format/comparator claim","rows":rows}

if __name__=="__main__":
    result=run();print(json.dumps(result,indent=2,sort_keys=True));raise SystemExit(0 if result["decision"]=="advance_fused_phase_to_combined_coverage" else 2)
