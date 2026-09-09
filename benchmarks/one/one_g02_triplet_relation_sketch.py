"""ONE-G0.2 triplet block relation-sketch rehabilitation.

Rehabilitates the first block-cadence sketch by reducing each completed 64-byte block to
three content-derived probes. A block votes only when all three probes agree on the same
non-zero relation value. Global 7/8 agreement remains required. Exact proof remains a
separate mandatory downstream stage.
"""
from __future__ import annotations

import ctypes
from functools import lru_cache
import json
from pathlib import Path
import statistics
import subprocess
import tempfile
import time

import benchmarks.one.one_g02_native_multi_law_carry as full
from benchmarks.one.one_g02_multi_law_gate import FAMILIES, SIZES, make_case, oracle_expected

REPETITIONS=21
PROBES=3
GLOBAL_NUM=7
GLOBAL_DEN=8
MAX_MEDIAN_OVERHEAD=1.20
MAX_ROW_OVERHEAD=1.35
MIN_1MIB_THROUGHPUT_MIB_S=250.0

_TRIPLET_C=r'''
int one_gate_triplet(const uint8_t *data, size_t n, gate_out *out) {
    if (!out || (n && !data)) return 2;
    memset(out, 0, sizeof(*out)); out->input_bytes=n; out->source_scan_bytes=n;
    if (!n) return 0;
    uint64_t fps[MAX_FP]; size_t fp_count=0; uint64_t chunk_hash=FNV_OFFSET,repeated=0;
    uint8_t run_value=data[0]; uint64_t run_len=0,run_support=0;
    uint64_t add_blocks[HIST]={0},xor_blocks[HIST]={0},add_eligible=0,xor_eligible=0;
    size_t block_start=0; int have_previous=0;
    for (size_t p=0;p<n;++p) {
        const uint8_t v=data[p];
        if (!run_len) {run_value=v;run_len=1;} else if(v==run_value) ++run_len;
        else {if(run_len>=MIN_RUN)run_support+=run_len;run_value=v;run_len=1;}
        chunk_hash^=(uint64_t)v; chunk_hash*=FNV_PRIME;
        if (((p+1)%CHUNK)==0) {
            if (fp_seen_or_insert(fps,&fp_count,chunk_hash)) ++repeated;
            uint8_t ad[3], xv[3];
            for (unsigned k=0;k<3;++k) {
                const size_t lane=1u+(size_t)(((chunk_hash>>(16u*k))&UINT64_C(0xffff))%63u);
                ad[k]=(uint8_t)(data[block_start+lane]-data[block_start+lane-1]);
                xv[k]=have_previous?(uint8_t)(data[block_start+lane]^data[block_start-CHUNK+lane]):0;
            }
            ++add_eligible;
            if (ad[0]!=0 && ad[0]==ad[1] && ad[1]==ad[2]) ++add_blocks[ad[0]];
            if (have_previous) {
                ++xor_eligible;
                if (xv[0]!=0 && xv[0]==xv[1] && xv[1]==xv[2]) ++xor_blocks[xv[0]];
            }
            have_previous=1; chunk_hash=FNV_OFFSET; block_start=p+1;
        }
    }
    if(run_len>=MIN_RUN)run_support+=run_len;
    uint64_t best_add=0,best_xor=0;uint32_t add_idx=0,xor_idx=0;
    for(uint32_t i=1;i<HIST;++i){if(add_blocks[i]>best_add){best_add=add_blocks[i];add_idx=i;}if(xor_blocks[i]>best_xor){best_xor=xor_blocks[i];xor_idx=i;}}
    const int add8=add_eligible>=8 && add_idx && best_add*8>=add_eligible*7;
    const int xor_nom=xor_eligible>=8 && xor_idx && best_xor*8>=xor_eligible*7;
    out->run_support=run_support;out->reuse_support=repeated*CHUNK;out->add8_support=add8?best_add*CHUNK:0;out->xor_support=xor_nom?best_xor*CHUNK:0;out->retained_entries=fp_count;
    out->run=run_support>=MIN_RUN;out->reuse=repeated>0;out->add8=add8;out->xor_nom=xor_nom;return 0;
}
'''
_C_SOURCE=full._C_SOURCE+_TRIPLET_C

@lru_cache(maxsize=1)
def _library():
    d=Path(tempfile.mkdtemp(prefix="cmpct-one-triplet-relation-")); src=d/"kernel.c"; so=d/"libgate.so";src.write_text(_C_SOURCE)
    subprocess.run(["cc","-O3","-std=c11","-fPIC","-shared",str(src),"-o",str(so)],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    lib=ctypes.CDLL(str(so))
    for name in ("one_gate_baseline","one_gate_triplet"):
        fn=getattr(lib,name);fn.argtypes=[ctypes.POINTER(ctypes.c_uint8),ctypes.c_size_t,ctypes.POINTER(full._GateOut)];fn.restype=ctypes.c_int
    return lib

def _call(name,data):
    n=len(data);buf=(ctypes.c_uint8*n).from_buffer_copy(data) if n else None;ptr=ctypes.cast(buf,ctypes.POINTER(ctypes.c_uint8)) if n else ctypes.POINTER(ctypes.c_uint8)();out=full._GateOut();rc=getattr(_library(),name)(ptr,n,ctypes.byref(out));
    if rc: raise RuntimeError(rc)
    return out

def _decision(out): return {n for n,v in (("run",out.run),("reuse",out.reuse),("add8",out.add8),("xor",out.xor_nom)) if v}

def _measure(data):
    names=("one_gate_baseline","one_gate_triplet");latest={n:_call(n,data) for n in names};w={n:[] for n in names};c={n:[] for n in names}
    for rep in range(REPETITIONS):
        order=names if rep%2==0 else names[::-1]
        for name in order:
            w0,c0=time.perf_counter_ns(),time.process_time_ns();latest[name]=_call(name,data);w[name].append(time.perf_counter_ns()-w0);c[name].append(time.process_time_ns()-c0)
    med=lambda xs:statistics.median(xs)/1e9
    return latest,{n:med(w[n]) for n in names},{n:med(c[n]) for n in names}

def decide(rows):
    expected=len(SIZES)*len(FAMILIES)
    if len(rows)!=expected or len({(r['size'],r['family']) for r in rows})!=expected:return 'INVALIDATE_TRIPLET_RELATION_SKETCH'
    if any(not r['semantic_ok'] or not r['baseline_common_equal'] or r['source_scan_ratio']!=1.0 for r in rows):return 'INVALIDATE_TRIPLET_RELATION_SKETCH'
    wr=[r['wall_ratio'] for r in rows];cr=[r['cpu_ratio'] for r in rows]
    if statistics.median(wr)>MAX_MEDIAN_OVERHEAD or statistics.median(cr)>MAX_MEDIAN_OVERHEAD or max(wr)>MAX_ROW_OVERHEAD or max(cr)>MAX_ROW_OVERHEAD:return 'HOLD_TRIPLET_RELATION_SKETCH'
    mib=[r for r in rows if r['size']==1024*1024]
    if any(r['wall_mib_s']<MIN_1MIB_THROUGHPUT_MIB_S or r['cpu_mib_s']<MIN_1MIB_THROUGHPUT_MIB_S for r in mib):return 'HOLD_TRIPLET_RELATION_SKETCH'
    return 'ADVANCE_TRIPLET_RELATION_SKETCH'

def main():
    rows=[]
    for size in SIZES:
      for family in FAMILIES:
        data=make_case(family,size);latest,w,c=_measure(data);b,x=latest['one_gate_baseline'],latest['one_gate_triplet'];actual=_decision(x);expected=oracle_expected(family)
        common=bool(b.run)==bool(x.run) and bool(b.reuse)==bool(x.reuse) and int(b.run_support)==int(x.run_support) and int(b.reuse_support)==int(x.reuse_support) and int(b.retained_entries)==int(x.retained_entries)
        bw,cw=w['one_gate_baseline'],w['one_gate_triplet'];bc,cc=c['one_gate_baseline'],c['one_gate_triplet'];mib=size/(1024*1024)
        rows.append({'size':size,'family':family,'expected':sorted(expected),'actual':sorted(actual),'semantic_ok':actual==expected,'baseline_common_equal':common,'source_scan_ratio':x.source_scan_bytes/max(1,x.input_bytes),'wall_ratio':cw/bw,'cpu_ratio':cc/bc,'wall_mib_s':mib/cw,'cpu_mib_s':mib/cc})
    d=decide(rows);print(json.dumps({'experiment':'ONE-G0.2 triplet block relation sketch','decision':d,'repetitions':REPETITIONS,'probes':PROBES,'global_support':'7/8','rows':rows},sort_keys=True));return 0 if d=='ADVANCE_TRIPLET_RELATION_SKETCH' else 1

if __name__=='__main__':raise SystemExit(main())
