"""ONE-G0.2 opportunity-gated relation writer envelope V3.

Frozen by ONE_G02_RELATION_WRITER_ENVELOPE_V3_PREREG_2026-09-09.md.
A tiny native paired-version triplet gate runs after the exact promoted incumbent.
Only nominated inputs pay actionable Python witness discovery and exact Law proof.
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

MIN_NOVEL_WIRE_SAVING = 0.25
MIN_MEDIAN_MARGINAL_MBIT_PER_CPU_S = 20.0
MAX_MEDIAN_CONTROL_CPU_RATIO = 1.35
MAX_CONTROL_CPU_RATIO = 1.75
MAX_FALSE_PROOF_BYTES = 8192
MAX_STATE_RATIO = 0.60
GATE_PROBE_RATIO = 0.046875
ROUNDS = v2.ROUNDS

class GateOut(ctypes.Structure):
    _fields_ = [
        ("op", ctypes.c_uint32),
        ("value", ctypes.c_uint32),
        ("eligible", ctypes.c_uint64),
        ("votes", ctypes.c_uint64),
        ("probe_bytes", ctypes.c_uint64),
    ]

_GATE_C = r'''
#include <stdint.h>
#include <stddef.h>
#include <string.h>
typedef struct { uint32_t op, value; uint64_t eligible, votes, probe_bytes; } gate_out;
static uint64_t mix64(uint64_t x) {
    x ^= x >> 30; x *= UINT64_C(0xbf58476d1ce4e5b9);
    x ^= x >> 27; x *= UINT64_C(0x94d049bb133111eb);
    return x ^ (x >> 31);
}
int paired_triplet_gate(const uint8_t *a,const uint8_t *b,size_t n,gate_out *out) {
    if (!out || (n && (!a || !b))) return 2;
    memset(out,0,sizeof(*out));
    uint64_t ah[256]={0},xh[256]={0};
    const size_t blocks=n/64u;
    out->eligible=blocks;
    for(size_t bi=0;bi<blocks;++bi){
        const size_t base=bi*64u;
        /* First probe is also the content seed, so traffic remains exactly 3 pairs/block. */
        const size_t l0=(size_t)((a[base]^b[base]^((uint8_t)bi))&63u);
        uint64_t s=mix64(((uint64_t)a[base+l0]<<8) ^ b[base+l0] ^ (uint64_t)bi);
        const size_t l1=1u+(size_t)(s%63u); s=mix64(s+UINT64_C(0x9e3779b97f4a7c15));
        const size_t l2=1u+(size_t)(s%63u);
        const size_t lanes[3]={l0,l1,l2};
        uint8_t ad[3],xv[3];
        for(unsigned k=0;k<3;++k){
            const size_t p=base+lanes[k];
            ad[k]=(uint8_t)(b[p]-a[p]); xv[k]=(uint8_t)(b[p]^a[p]);
        }
        out->probe_bytes += 6;
        if(ad[0]!=0 && ad[0]==ad[1] && ad[1]==ad[2]) ++ah[ad[0]];
        if(xv[0]!=0 && xv[0]==xv[1] && xv[1]==xv[2]) ++xh[xv[0]];
    }
    uint64_t ab=0,xb=0; uint32_t ai=0,xi=0;
    for(uint32_t i=1;i<256;++i){if(ah[i]>ab){ab=ah[i];ai=i;} if(xh[i]>xb){xb=xh[i];xi=i;}}
    const int aok=blocks>=8 && ai && ab*8>=blocks*7;
    const int xok=blocks>=8 && xi && xb*8>=blocks*7;
    if(aok && (!xok || ab>=xb)){out->op=1;out->value=ai;out->votes=ab;}
    else if(xok){out->op=2;out->value=xi;out->votes=xb;}
    return 0;
}
'''

@lru_cache(maxsize=1)
def _gate_lib():
    d=Path(tempfile.mkdtemp(prefix="cmpct-one-rel-v3-")); src=d/"gate.c"; so=d/"gate.so"
    src.write_text(_GATE_C)
    subprocess.run(["cc","-O3","-std=c11","-fPIC","-shared",str(src),"-o",str(so)],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    lib=ctypes.CDLL(str(so)); fn=lib.paired_triplet_gate
    fn.argtypes=[ctypes.POINTER(ctypes.c_uint8),ctypes.POINTER(ctypes.c_uint8),ctypes.c_size_t,ctypes.POINTER(GateOut)]; fn.restype=ctypes.c_int
    return lib

def _gate(source:bytes,target:bytes):
    n=len(source); aa=(ctypes.c_uint8*n).from_buffer_copy(source); bb=(ctypes.c_uint8*n).from_buffer_copy(target); out=GateOut()
    rc=_gate_lib().paired_triplet_gate(aa,bb,n,ctypes.byref(out))
    if rc: raise RuntimeError(rc)
    op="add8" if out.op==1 else "xor" if out.op==2 else None
    return op,(int(out.value) if op else None),out

def _candidate_once(ctx):
    admission_fn,segment_fn,source,target,src_arr,dst_arr,seg_buf=ctx
    incumbent=v2._incumbent_once(*ctx)
    iwire,_istats,iprogram,*_=incumbent
    c0=time.process_time_ns(); gop,gvalue,gout=_gate(source,target); gate_cpu=time.process_time_ns()-c0
    if gop is None:
        return incumbent,iwire,iprogram,None,0,0,"incumbent",gate_cpu,0,0,0,0

    c0=time.process_time_ns(); obs=v2.observe_relation_witnesses(source+target); witness_cpu=time.process_time_ns()-c0
    proof=0; accepted=0; chosen=None; best_wire=None; best_program=None; proof_cpu=0; emit_cpu=0
    for (op,value), nominations in v2._group_witnesses(obs,len(source)):
        if op!=gop or value!=gvalue: continue
        c0=time.process_time_ns()
        result=v2.grow_relation_spans(source,target,op=op,value=value,nominations=tuple(nominations),seed_bytes=v2.SEED_BYTES,extension_bytes=v2.EXTENSION_BYTES)
        proof_cpu += time.process_time_ns()-c0; proof += result.compared_bytes
        if not result.runs: continue
        c0=time.process_time_ns(); program=v2._generic_program(source,target,op,value,result.runs,iprogram.roots); program.validate_shape(); wire,_stats=v2._encode_program_growable_prevalidated(program); emit_cpu += time.process_time_ns()-c0
        if best_wire is None or len(wire)<len(best_wire): best_wire,best_program,accepted,chosen=wire,program,result.accepted_bytes,(op,value)
    if best_wire is not None and len(best_wire)<len(iwire): return incumbent,best_wire,best_program,obs,proof,accepted,"generic",gate_cpu,witness_cpu,proof_cpu,emit_cpu,gout.probe_bytes
    return incumbent,iwire,iprogram,obs,proof,accepted,"incumbent",gate_cpu,witness_cpu,proof_cpu,emit_cpu,gout.probe_bytes

def _time_pair(ctx):
    iw=[];ic=[];cw=[];cc=[]; stages=[]; iv=cv=None; enabled=gc.isenabled()
    try:
        if enabled: gc.disable()
        _gate(ctx[2],ctx[3])
        for r in range(ROUNDS):
            order=("i","c") if r%2==0 else ("c","i")
            for arm in order:
                w0=time.perf_counter_ns(); c0=time.process_time_ns()
                val=v2._incumbent_once(*ctx) if arm=="i" else _candidate_once(ctx)
                cpu=time.process_time_ns()-c0; wall=time.perf_counter_ns()-w0
                if arm=="i": iw.append(wall);ic.append(cpu);iv=val
                else: cw.append(wall);cc.append(cpu);cv=val;stages.append(val[7:11])
    finally:
        if enabled: gc.enable()
    med=lambda xs:int(statistics.median(xs))
    stage=[med([s[k] for s in stages]) for k in range(4)]
    return iv,med(iw),med(ic),cv,med(cw),med(cc),stage

def run():
    admission_fn,segment_fn,td=v2._build_native(); rows=[]; novel_yields=[]; control_cpu=[]
    try:
      for n in v2.VERSION_SIZES:
       for family in v2.FAMILIES:
        source,target,expected_op,expected_value,kind=v2._case(n,family)
        src_arr=(ctypes.c_uint8*n).from_buffer_copy(source); dst_arr=(ctypes.c_uint8*n).from_buffer_copy(target); seg_buf=(v2.Segment*n)(); ctx=(admission_fn,segment_fn,source,target,src_arr,dst_arr,seg_buf)
        incumbent,iwall,icpu,candidate,cwall,ccpu,stage=_time_pair(ctx)
        iwire=incumbent[0]; cinc,cwire,cprogram,obs,proof,accepted,selection,gate_cpu,witness_cpu,proof_cpu,emit_cpu,probe_bytes=candidate
        iexact,_=v2._decode_exact(iwire,source,target); cexact,cvm=v2._decode_exact(cwire,source,target)
        gop,gvalue,gout=_gate(source,target); gate_chosen=(gop,gvalue) if gop else None
        expected_gate=(expected_op,expected_value) if kind=="novel" else None
        semantic=iexact and cexact and cinc[0]==iwire and cprogram.roots["previous"].sha256==incumbent[2].roots["previous"].sha256 and cprogram.roots["current"].sha256==incumbent[2].roots["current"].sha256
        saved=len(iwire)-len(cwire); inc_ns=ccpu-icpu; marginal=(saved*8)/(inc_ns/1e9)/1e6 if saved>0 and inc_ns>0 else (1e99 if saved>0 else 0.0); ratio=ccpu/max(icpu,1)
        if kind=="novel": novel_yields.append(marginal)
        elif kind=="control": control_cpu.append(ratio)
        rows.append({"version_bytes":n,"family":family,"kind":kind,"semantic_ok":semantic,"gate_chosen":gate_chosen,"expected_gate":expected_gate,"gate_correct":gate_chosen==expected_gate,"expensive_path_entered":obs is not None,"accepted_relation_bytes":accepted,"proof_bytes":proof,"final_selection":selection,"incumbent_wire_bytes":len(iwire),"candidate_wire_bytes":len(cwire),"wire_saving_fraction":saved/len(iwire),"cpu_ratio":ratio,"wall_ratio":cwall/max(iwall,1),"marginal_mbit_eliminated_per_cpu_s":marginal,"gate_probe_bytes":int(gout.probe_bytes),"gate_probe_ratio":int(gout.probe_bytes)/(2*n),"gate_cpu_ns":stage[0],"witness_cpu_ns":stage[1],"proof_cpu_ns":stage[2],"program_emit_cpu_ns":stage[3],"state_ratio":((obs.modeled_state_bytes if obs is not None else 4096)/(2*n)),"candidate_reader_work_bytes":cvm.work_bytes,"candidate_reader_materialized_bytes":cvm.materialized_bytes})
    finally:
      td.cleanup()
    invalid=any(not r["semantic_ok"] for r in rows) or any(r["kind"]=="novel" and not r["gate_correct"] for r in rows) or any(r["kind"]!="novel" and r["expensive_path_entered"] for r in rows)
    novel=[r for r in rows if r["kind"]=="novel"]; controls=[r for r in rows if r["kind"]=="control"]
    hold=(any(r["wire_saving_fraction"]<MIN_NOVEL_WIRE_SAVING for r in novel) or statistics.median(novel_yields)<MIN_MEDIAN_MARGINAL_MBIT_PER_CPU_S or statistics.median(control_cpu)>MAX_MEDIAN_CONTROL_CPU_RATIO or max(control_cpu)>MAX_CONTROL_CPU_RATIO or any(r["proof_bytes"]>MAX_FALSE_PROOF_BYTES for r in controls) or any(abs(r["gate_probe_ratio"]-GATE_PROBE_RATIO)>1e-12 for r in rows) or any(r["state_ratio"]>MAX_STATE_RATIO for r in rows))
    decision="INVALIDATE_RELATION_WRITER_ENVELOPE_V3" if invalid else "HOLD_RELATION_WRITER_ENVELOPE_V3" if hold else "ADVANCE_RELATION_WRITER_ENVELOPE_V3"
    print(json.dumps({"experiment":"ONE-G0.2 relation writer envelope V3","decision":decision,"source_sha":__import__('os').environ.get('EVIDENCE_HEAD'),"median_novel_marginal_mbit_per_cpu_s":statistics.median(novel_yields),"median_control_cpu_ratio":statistics.median(control_cpu),"worst_control_cpu_ratio":max(control_cpu),"rows":rows},sort_keys=True))
    return 0 if decision=="ADVANCE_RELATION_WRITER_ENVELOPE_V3" else 1

if __name__=="__main__": raise SystemExit(run())
