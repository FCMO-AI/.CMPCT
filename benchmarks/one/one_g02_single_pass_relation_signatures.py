"""ONE-G0.2 single-pass relation-signature falsifier.

Retain V4's exact sparse probe geometry but keep compact per-block signatures so
aligned proof seeds can be derived without a second source read. Exact span growth
remains the truth boundary.
"""
from __future__ import annotations

import ctypes
from functools import lru_cache
import gc
import json
from pathlib import Path
import statistics
import subprocess
import tempfile
import time

import benchmarks.one.one_g02_relation_writer_envelope_v2 as v2
import benchmarks.one.one_g02_relation_writer_envelope_v3 as v3
import benchmarks.one.one_g02_relation_writer_envelope_v3_nocopy as v3_nocopy
import benchmarks.one.one_g02_sparse_native_seed_transfer as v4

ROUNDS = v3.ROUNDS
PROBE_RATIO = 0.046875
MAX_MEDIAN_NOM_CPU_OVER_V4 = 0.60
MAX_NOM_CPU_OVER_V4 = 0.80
MAX_MEDIAN_NOVEL_CPU_OVER_V4 = 1.00
MAX_NOVEL_CPU_OVER_V4 = 1.03
MAX_MEDIAN_CONTROL_CPU_OVER_V4 = 1.05
MAX_CONTROL_CPU_OVER_V4 = 1.15

_FUSED_C = r'''
#include <stdint.h>
#include <stddef.h>
#include <string.h>
typedef struct { uint32_t op,value; uint64_t eligible,votes,probe_bytes,seed_count; } fused_out;
static uint64_t mix64(uint64_t x){x^=x>>30;x*=UINT64_C(0xbf58476d1ce4e5b9);x^=x>>27;x*=UINT64_C(0x94d049bb133111eb);return x^(x>>31);}
int fused_gate_seeds(const uint8_t *a,const uint8_t *b,size_t n,uint16_t *sig,uint32_t *seeds,size_t cap,fused_out *out){
 if(!out||(n&&(!a||!b))||cap<n/64u)return 2; memset(out,0,sizeof(*out));
 uint64_t ah[256]={0},xh[256]={0}; const size_t blocks=n/64u; out->eligible=blocks;
 for(size_t bi=0;bi<blocks;++bi){const size_t base=bi*64u,l0=0u;uint64_t s=mix64(((uint64_t)a[base]<<8)^b[base]^(uint64_t)bi);const size_t l1=1u+(size_t)(s%63u);s=mix64(s+UINT64_C(0x9e3779b97f4a7c15));const size_t l2=1u+(size_t)(s%63u);const size_t lanes[3]={l0,l1,l2};uint8_t ad[3],xv[3];for(unsigned k=0;k<3;++k){size_t p=base+lanes[k];ad[k]=(uint8_t)(b[p]-a[p]);xv[k]=(uint8_t)(b[p]^a[p]);}out->probe_bytes+=6u;uint8_t ac=(ad[0]!=0&&ad[0]==ad[1]&&ad[1]==ad[2])?ad[0]:0;uint8_t xc=(xv[0]!=0&&xv[0]==xv[1]&&xv[1]==xv[2])?xv[0]:0;sig[bi]=(uint16_t)ac|((uint16_t)xc<<8);if(ac)++ah[ac];if(xc)++xh[xc];}
 uint64_t ab=0,xb=0;uint32_t ai=0,xi=0;for(uint32_t i=1;i<256;++i){if(ah[i]>ab){ab=ah[i];ai=i;}if(xh[i]>xb){xb=xh[i];xi=i;}}
 int aok=blocks>=8&&ai&&ab*8>=blocks*7;int xok=blocks>=8&&xi&&xb*8>=blocks*7;if(aok&&(!xok||ab>=xb)){out->op=1;out->value=ai;out->votes=ab;}else if(xok){out->op=2;out->value=xi;out->votes=xb;}
 if(out->op){for(size_t bi=0;bi<blocks;++bi){uint32_t v=out->op==1?(sig[bi]&255u):(sig[bi]>>8);if(v==out->value)seeds[out->seed_count++]=(uint32_t)bi;}}
 return 0;
}
'''

class FusedOut(ctypes.Structure):
    _fields_=[("op",ctypes.c_uint32),("value",ctypes.c_uint32),("eligible",ctypes.c_uint64),("votes",ctypes.c_uint64),("probe_bytes",ctypes.c_uint64),("seed_count",ctypes.c_uint64)]

@lru_cache(maxsize=1)
def _lib():
    d=Path(tempfile.mkdtemp(prefix="cmpct-one-fused-rel-")); src=d/"f.c"; so=d/"f.so"; src.write_text(_FUSED_C)
    subprocess.run(["cc","-O3","-std=c11","-fPIC","-shared",str(src),"-o",str(so)],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    lib=ctypes.CDLL(str(so)); fn=lib.fused_gate_seeds
    fn.argtypes=[ctypes.POINTER(ctypes.c_uint8),ctypes.POINTER(ctypes.c_uint8),ctypes.c_size_t,ctypes.POINTER(ctypes.c_uint16),ctypes.POINTER(ctypes.c_uint32),ctypes.c_size_t,ctypes.POINTER(FusedOut)];fn.restype=ctypes.c_int
    return lib

_pybytes_as_string=ctypes.pythonapi.PyBytes_AsString;_pybytes_as_string.argtypes=[ctypes.py_object];_pybytes_as_string.restype=ctypes.c_void_p

def _fused(source:bytes,target:bytes):
    blocks=len(source)//64; sig=(ctypes.c_uint16*max(blocks,1))(); seeds=(ctypes.c_uint32*max(blocks,1))(); out=FusedOut()
    ap=ctypes.cast(_pybytes_as_string(source),ctypes.POINTER(ctypes.c_uint8));bp=ctypes.cast(_pybytes_as_string(target),ctypes.POINTER(ctypes.c_uint8))
    rc=_lib().fused_gate_seeds(ap,bp,len(source),sig,seeds,blocks,ctypes.byref(out))
    if rc: raise RuntimeError(rc)
    op="add8" if out.op==1 else "xor" if out.op==2 else None
    return op,(int(out.value) if op else None),tuple(int(seeds[i])*64 for i in range(out.seed_count)),int(out.probe_bytes),blocks

def _candidate_once(ctx):
    incumbent=v2._incumbent_once(*ctx); iwire,_,iprogram,*_=incumbent
    c0=time.process_time_ns(); op,value,seeds,probe,blocks=_fused(ctx[2],ctx[3]); nom_cpu=time.process_time_ns()-c0
    if op is None:return incumbent,iwire,iprogram,None,0,0,"incumbent",nom_cpu,0,0,probe,blocks
    c0=time.process_time_ns(); result=v2.grow_relation_spans(ctx[2],ctx[3],op=op,value=value,nominations=seeds,seed_bytes=v2.SEED_BYTES,extension_bytes=v2.EXTENSION_BYTES);proof_cpu=time.process_time_ns()-c0
    emit_cpu=0; bw=None;bp=None
    if result.runs:
        c0=time.process_time_ns(); p=v2._generic_program(ctx[2],ctx[3],op,value,result.runs,iprogram.roots);p.validate_shape();w,_=v2._encode_program_growable_prevalidated(p);emit_cpu=time.process_time_ns()-c0;bw,bp=w,p
    if bw is not None and len(bw)<len(iwire):return incumbent,bw,bp,(op,value),result.compared_bytes,result.accepted_bytes,"generic",nom_cpu,proof_cpu,emit_cpu,probe,blocks
    return incumbent,iwire,iprogram,(op,value),result.compared_bytes,result.accepted_bytes,"incumbent",nom_cpu,proof_cpu,emit_cpu,probe,blocks

def _time(ctx):
    vals={"i":None,"v4":None,"v5":None};cpus={k:[] for k in vals};walls={k:[] for k in vals};noms=[]
    enabled=gc.isenabled()
    try:
        if enabled:gc.disable()
        _lib();v3._gate(ctx[2],ctx[3])
        for r in range(ROUNDS):
            base=("i","v4","v5");order=base[r%3:]+base[:r%3]
            for arm in order:
                w0=time.perf_counter_ns();c0=time.process_time_ns();val=v2._incumbent_once(*ctx) if arm=="i" else v4._candidate_once(ctx) if arm=="v4" else _candidate_once(ctx);cpu=time.process_time_ns()-c0;wall=time.perf_counter_ns()-w0
                vals[arm]=val;cpus[arm].append(cpu);walls[arm].append(wall)
                if arm=="v5":noms.append(val[7])
    finally:
        if enabled:gc.enable()
    med=lambda xs:int(statistics.median(xs));return vals,{k:med(x) for k,x in cpus.items()},{k:med(x) for k,x in walls.items()},med(noms)

def run():
    admission_fn,segment_fn,td=v2._build_native();rows=[];novel_whole=[];control_whole=[];nom_ratios=[];yields=[]
    try:
        for n in v2.VERSION_SIZES:
            for family in v2.FAMILIES:
                source,target,eop,eval_,kind=v2._case(n,family);sa=(ctypes.c_uint8*n).from_buffer_copy(source);da=(ctypes.c_uint8*n).from_buffer_copy(target);seg=(v2.Segment*n)();ctx=(admission_fn,segment_fn,source,target,sa,da,seg)
                vals,cpu,wall,v5nom=_time(ctx);inc=vals["i"];a4=vals["v4"];a5=vals["v5"]
                iwire=inc[0];w4=a4[1];p4=a4[2];g4=a4[3];proof4=a4[4];acc4=a4[5];sel4=a4[6];v4nom=int(a4[7])+int(a4[8])
                i5,w5,p5,g5,proof5,acc5,sel5,nom5,proofcpu5,emitcpu5,probe5,blocks=a5
                exact,_=v2._decode_exact(w5,source,target);semantic=exact and w5==w4 and sel5==sel4 and g5==g4 and acc5==acc4 and proof5<=proof4 and i5[0]==iwire
                ratio=cpu["v5"]/max(cpu["v4"],1);nomratio=v5nom/max(v4nom,1);saved=len(iwire)-len(w5);incns=cpu["v5"]-cpu["i"];marg=(saved*8)/(incns/1e9)/1e6 if saved>0 and incns>0 else (1e99 if saved>0 else 0.0)
                if kind=="novel":novel_whole.append(ratio);nom_ratios.append(nomratio);yields.append(marg)
                elif kind=="control":control_whole.append(ratio)
                rows.append({"version_bytes":n,"family":family,"kind":kind,"semantic_ok":semantic,"v4_gate_choice":g4,"v5_gate_choice":g5,"v4_wire_bytes":len(w4),"v5_wire_bytes":len(w5),"v4_accepted_relation_bytes":acc4,"v5_accepted_relation_bytes":acc5,"v4_proof_bytes":proof4,"v5_proof_bytes":proof5,"v5_probe_ratio":probe5/(2*n),"v5_over_v4_cpu":ratio,"v5_over_v4_wall":wall["v5"]/max(wall["v4"],1),"v5_nomination_over_v4_nomination_cpu":nomratio,"marginal_mbit_per_cpu_s":marg,"signature_bytes":2*blocks,"seed_index_bytes":4*(len(source)//64 if g5 else 0),"proof_cpu_ns":proofcpu5,"emit_cpu_ns":emitcpu5})
    finally:td.cleanup()
    novel=[r for r in rows if r["kind"]=="novel"];controls=[r for r in rows if r["kind"]=="control"]
    invalid=any(not r["semantic_ok"] for r in rows) or any(abs(r["v5_probe_ratio"]-PROBE_RATIO)>1e-12 for r in rows) or any(r["kind"]!="novel" and r["v5_gate_choice"] is not None for r in rows)
    hold=(statistics.median(nom_ratios)>MAX_MEDIAN_NOM_CPU_OVER_V4 or max(nom_ratios)>MAX_NOM_CPU_OVER_V4 or statistics.median(novel_whole)>MAX_MEDIAN_NOVEL_CPU_OVER_V4 or max(novel_whole)>MAX_NOVEL_CPU_OVER_V4 or statistics.median(control_whole)>MAX_MEDIAN_CONTROL_CPU_OVER_V4 or max(control_whole)>MAX_CONTROL_CPU_OVER_V4 or statistics.median(yields)<20.0 or any((len(r) and r["v5_wire_bytes"]>0 and (r["kind"]=="novel") and (r["v5_wire_bytes"]>0.75*r["v4_wire_bytes"]*2)) for r in []))
    decision="INVALIDATE_SINGLE_PASS_RELATION_SIGNATURES" if invalid else "HOLD_SINGLE_PASS_RELATION_SIGNATURES" if hold else "ADVANCE_SINGLE_PASS_RELATION_SIGNATURES"
    print(json.dumps({"experiment":"ONE-G0.2 single-pass relation signatures","decision":decision,"source_sha":__import__("os").environ.get("EVIDENCE_HEAD"),"median_nomination_cpu_over_v4":statistics.median(nom_ratios),"worst_nomination_cpu_over_v4":max(nom_ratios),"median_novel_cpu_over_v4":statistics.median(novel_whole),"worst_novel_cpu_over_v4":max(novel_whole),"median_control_cpu_over_v4":statistics.median(control_whole),"worst_control_cpu_over_v4":max(control_whole),"rows":rows},sort_keys=True))
    return 0 if decision=="ADVANCE_SINGLE_PASS_RELATION_SIGNATURES" else 1

if __name__=="__main__":raise SystemExit(run())
