"""ONE-G0.2 result-bearing native carrying-cost A/B for the local Gear certificate.

The frozen numerical gate is in ONE_G02_LOCAL_GEAR_CERTIFICATE_NATIVE_COST_PREREG_2026-09-05.md.
The pre-result implementation correction is documented in the matching IMPLEMENTATION_NOTE.
Each arm has a separately compiled hot loop so runtime benchmark dispatch is not charged as
candidate work.  The certificate uses a fixed max-heap: the common non-replacement path is
one root comparison, while rare replacement pays O(log 8).
"""
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
from benchmarks.one.one_g02_local_gear_certificate_validation import _source_certificate

REPETITIONS = 7
CERT_WINDOW = 32
CERT_K = 8
MODELED_INCREMENTAL_STATE_BYTES = 136
LARGE_REPS = 16


def _c_source() -> str:
    gear = ",\n".join(f"UINT64_C({v})" for v in _GEAR)
    return f'''#include <stddef.h>
#include <stdint.h>
#define W 32u
#define K 8u
#define MASK UINT64_C(1023)
static const uint64_t G[256] = {{ {gear} }};
static volatile uint64_t ESC;
static inline uint64_t rol(uint64_t x, unsigned r) {{ return (x << r) | (x >> (64u-r)); }}
static inline int worse(uint64_t ah,uint32_t ap,uint64_t bh,uint32_t bp) {{
    return ah > bh || (ah == bh && ap > bp);
}}
static inline void swap(uint64_t *ah,uint32_t *ap,uint64_t *bh,uint32_t *bp) {{
    uint64_t h=*ah; *ah=*bh; *bh=h; uint32_t p=*ap; *ap=*bp; *bp=p;
}}
static inline void offer(uint64_t h,uint32_t p,uint64_t hs[K],uint32_t ps[K],unsigned *count,uint64_t *repl) {{
    if (*count < K) {{
        unsigned i=(*count)++; hs[i]=h; ps[i]=p;
        while (i) {{
            unsigned q=(i-1u)>>1;
            if (!worse(hs[i],ps[i],hs[q],ps[q])) break;
            swap(&hs[i],&ps[i],&hs[q],&ps[q]); i=q;
        }}
        return;
    }}
    if (h >= hs[0]) return;
    hs[0]=h; ps[0]=p; (*repl)++;
    unsigned i=0;
    for (;;) {{
        unsigned l=i*2u+1u; if (l>=K) break;
        unsigned r=l+1u, w=l;
        if (r<K && worse(hs[r],ps[r],hs[l],ps[l])) w=r;
        if (!worse(hs[w],ps[w],hs[i],ps[i])) break;
        swap(&hs[i],&ps[i],&hs[w],&ps[w]); i=w;
    }}
}}

typedef struct {{ uint64_t checksum,anchors,updates,outgoing,duplicate,replacements; }} stats_t;

static inline uint64_t baseline_once(const uint8_t*d,size_t n,uint64_t *anchors) {{
    uint64_t pre=0; size_t run=0; uint8_t rv=0;
    for(size_t i=0;i<n;i++) {{
        uint8_t v=d[i]; if(!run||v!=rv){{rv=v;run=1;}} else run++;
        uint64_t in=G[v]; pre=(pre<<1)+in;
        if(i+1>=64u && !(pre&MASK)) (*anchors)++;
    }}
    return pre + run;
}}
static inline uint64_t rolling_once(const uint8_t*d,size_t n,uint64_t *anchors,uint64_t *outgoing) {{
    uint64_t pre=0,roll=0; size_t run=0; uint8_t rv=0;
    for(size_t i=0;i<n;i++) {{
        uint8_t v=d[i]; if(!run||v!=rv){{rv=v;run=1;}} else run++;
        uint64_t in=G[v]; pre=(pre<<1)+in;
        if(i+1>=64u && !(pre&MASK)) (*anchors)++;
        if(i<W) roll=rol(roll,1)^in;
        else {{ roll=rol(roll,1)^rol(G[d[i-W]],W)^in; (*outgoing)++; }}
    }}
    return pre + roll + run;
}}
static inline uint64_t certificate_once(const uint8_t*d,size_t n,uint64_t *anchors,uint64_t *updates,uint64_t *outgoing,uint64_t *repl,int duplicate) {{
    uint64_t pre=0,roll=0,hs[K]={{0}}; uint32_t ps[K]={{0}}; unsigned count=0; size_t run=0; uint8_t rv=0;
    for(size_t i=0;i<n;i++) {{
        uint8_t v=d[i]; if(!run||v!=rv){{rv=v;run=1;}} else run++;
        uint64_t in=G[v]; pre=(pre<<1)+in;
        if(i+1>=64u && !(pre&MASK)) (*anchors)++;
        uint64_t local_in=duplicate ? ((volatile const uint64_t*)G)[v] : in;
        if(i<W) roll=rol(roll,1)^local_in;
        else {{ roll=rol(roll,1)^rol(G[d[i-W]],W)^local_in; (*outgoing)++; }}
        if(i+1>=W) {{ offer(roll,(uint32_t)(i+1-W),hs,ps,&count,repl); (*updates)++; }}
    }}
    uint64_t mix=0; for(unsigned j=0;j<count;j++) mix^=hs[j]+((uint64_t)ps[j]<<(j&31u));
    return pre + roll + mix + run;
}}

uint64_t run_baseline(const uint8_t*d,size_t n,unsigned reps,stats_t*out) {{
    uint64_t x=0,a=0; for(unsigned r=0;r<reps;r++) x^=baseline_once(d,n,&a)+(uint64_t)r; ESC^=x;
    if(out){{out->checksum=x;out->anchors=a;out->updates=out->outgoing=out->duplicate=out->replacements=0;}} return x;
}}
uint64_t run_rolling(const uint8_t*d,size_t n,unsigned reps,stats_t*out) {{
    uint64_t x=0,a=0,o=0; for(unsigned r=0;r<reps;r++) x^=rolling_once(d,n,&a,&o)+(uint64_t)r; ESC^=x;
    if(out){{out->checksum=x;out->anchors=a;out->updates=0;out->outgoing=o;out->duplicate=0;out->replacements=0;}} return x;
}}
uint64_t run_certificate(const uint8_t*d,size_t n,unsigned reps,stats_t*out) {{
    uint64_t x=0,a=0,u=0,o=0,q=0; for(unsigned r=0;r<reps;r++) x^=certificate_once(d,n,&a,&u,&o,&q,0)+(uint64_t)r; ESC^=x;
    if(out){{out->checksum=x;out->anchors=a;out->updates=u;out->outgoing=o;out->duplicate=0;out->replacements=q;}} return x;
}}
uint64_t run_certificate_no_reuse(const uint8_t*d,size_t n,unsigned reps,stats_t*out) {{
    uint64_t x=0,a=0,u=0,o=0,q=0; for(unsigned r=0;r<reps;r++) x^=certificate_once(d,n,&a,&u,&o,&q,1)+(uint64_t)r; ESC^=x;
    if(out){{out->checksum=x;out->anchors=a;out->updates=u;out->outgoing=o;out->duplicate=(uint64_t)n*reps;out->replacements=q;}} return x;
}}
int certificate_exact(const uint8_t*d,size_t n,uint64_t hs[K],uint32_t ps[K]) {{
    if(n<W) return 0; uint64_t roll=0,repl=0; unsigned count=0;
    for(size_t i=0;i<n;i++) {{ uint64_t in=G[d[i]]; if(i<W)roll=rol(roll,1)^in; else roll=rol(roll,1)^rol(G[d[i-W]],W)^in; if(i+1>=W)offer(roll,(uint32_t)(i+1-W),hs,ps,&count,&repl); }}
    return (int)count;
}}
'''


class Stats(ctypes.Structure):
    _fields_=[("checksum",ctypes.c_uint64),("anchors",ctypes.c_uint64),("updates",ctypes.c_uint64),("outgoing",ctypes.c_uint64),("duplicate",ctypes.c_uint64),("replacements",ctypes.c_uint64)]


def _build(td: str):
    src=Path(td)/"native.c"; so=Path(td)/"native.so"; src.write_text(_c_source())
    subprocess.run(["cc","-O3","-std=c11","-fPIC","-shared",str(src),"-o",str(so)],check=True)
    lib=ctypes.CDLL(str(so)); p8=ctypes.POINTER(ctypes.c_uint8)
    for name in ("run_baseline","run_rolling","run_certificate","run_certificate_no_reuse"):
        fn=getattr(lib,name); fn.argtypes=[p8,ctypes.c_size_t,ctypes.c_uint,ctypes.POINTER(Stats)]; fn.restype=ctypes.c_uint64
    lib.certificate_exact.argtypes=[p8,ctypes.c_size_t,ctypes.POINTER(ctypes.c_uint64),ctypes.POINTER(ctypes.c_uint32)];lib.certificate_exact.restype=ctypes.c_int
    return lib


def _buf(data: bytes): return (ctypes.c_uint8*len(data)).from_buffer_copy(data)


def _native_cert(lib,data:bytes):
    b=_buf(data); hs=(ctypes.c_uint64*CERT_K)(); ps=(ctypes.c_uint32*CERT_K)(); n=lib.certificate_exact(b,len(data),hs,ps)
    return sorted((int(hs[i]),int(ps[i])) for i in range(n))


def _cases():
    random_1m=random.Random(77001).randbytes(1024*1024)
    compressed=zlib.compress(random.Random(77002).randbytes(1024*1024),9)
    basis=random.Random(77003).randbytes(4096); version=random.Random(77004).randbytes(512*1024)
    return {
        "random_1mib":random_1m,
        "compressed_like_1mib":compressed,
        "repeated_1mib":basis*256,
        "shifted_version_1mib":version+b"X"+version[:-1],
        "zeros_1mib":b"\0"*(1024*1024),
        "alternating_hostile_1mib":b"\0\xff"*(512*1024),
        "tiny_4k":random.Random(77005).randbytes(4096),
        "tiny_64b":random.Random(77006).randbytes(64),
    }


def _sample(fn,b,n,reps):
    ss=[]; last=Stats()
    for _ in range(REPETITIONS):
        st=Stats(); t=time.perf_counter_ns(); fn(b,n,reps,ctypes.byref(st)); ss.append(time.perf_counter_ns()-t); last=st
    return int(statistics.median(ss)),last


def run():
    rows=[]; mismatches=[]
    with tempfile.TemporaryDirectory(prefix="one_cert_cost_v2_") as td:
        lib=_build(td); cases=_cases()
        for name,data in cases.items():
            if _native_cert(lib,data)!=_source_certificate(data): mismatches.append(name)
        for name,data in cases.items():
            b=_buf(data); n=len(data); reps=LARGE_REPS if n>=1024*1024-1024 else (1024 if n>=4096 else 65536)
            bt,bs=_sample(lib.run_baseline,b,n,reps); rt,rs=_sample(lib.run_rolling,b,n,reps); ct,cs=_sample(lib.run_certificate,b,n,reps); nt,ns=_sample(lib.run_certificate_no_reuse,b,n,reps)
            rows.append({
                "case":name,"input_bytes":n,"internal_repetitions":reps,
                "baseline_median_ns":bt,"rolling_median_ns":rt,"certificate_median_ns":ct,"certificate_no_reuse_median_ns":nt,
                "rolling_ratio_over_baseline":rt/bt,"certificate_ratio_over_baseline":ct/bt,"certificate_ratio_over_no_reuse":ct/nt,
                "modeled_incremental_state_bytes":MODELED_INCREMENTAL_STATE_BYTES,
                "modeled_extra_outgoing_byte_reads_per_pass":max(0,n-CERT_WINDOW),"baseline_gear_lookups_per_pass":n,
                "fused_extra_gear_lookups_per_pass":max(0,n-CERT_WINDOW),"no_reuse_extra_incoming_gear_lookups_per_pass":n,
                "certificate_updates_all_reps":int(cs.updates),"heap_replacements_all_reps":int(cs.replacements),
                "native_witness_equal_reference":name not in mismatches,"checksum":int(cs.checksum),
            })
    gate_names={"random_1mib","compressed_like_1mib","repeated_1mib","shifted_version_1mib","zeros_1mib"}
    large=[r for r in rows if r["case"] in gate_names]; ratios=[r["certificate_ratio_over_baseline"] for r in large]
    critical=[r for r in rows if r["case"] in {"random_1mib","compressed_like_1mib"}]; all1=[r for r in rows if r["input_bytes"]>=1024*1024-1024]
    fusion=[r["certificate_ratio_over_no_reuse"] for r in large]
    ok=(not mismatches and statistics.median(ratios)<=1.20 and all(r["certificate_ratio_over_baseline"]<=1.25 for r in critical) and all(r["certificate_ratio_over_baseline"]<=1.35 for r in all1) and statistics.median(fusion)<=1.03)
    return {"schema":"cmpct-one-g02-local-gear-certificate-native-cost-v2","experimental_version":"ONE-G0.2","source_sha":os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound","modeled_incremental_state_bytes":MODELED_INCREMENTAL_STATE_BYTES,"native_witness_mismatches":mismatches,"large_gate_median_certificate_ratio_over_baseline":statistics.median(ratios),"large_gate_median_certificate_ratio_over_no_reuse":statistics.median(fusion),"decision":"advance_certificate_to_end_to_end_efficiency_gate" if ok else "retire_unconditional_local_gear_certificate","claim_boundary":"native carrying-cost viability only; no density, reader-speed, or end-to-end writer promotion claim","rows":rows}


if __name__=="__main__":
    result=run(); print(json.dumps(result,indent=2,sort_keys=True)); raise SystemExit(0 if result["decision"]=="advance_certificate_to_end_to_end_efficiency_gate" else 2)
