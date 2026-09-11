"""ONE-G0.2 exact-source fused nomination compact-local-SoA A/B.

Preregistered in ONE_G02_NATIVE_FUSED_NOMINATION_LOCAL_SOA_PREREG_2026-09-06.md.
The candidate is mechanically derived from the pinned fused consumer and changes
only the 64-entry local ring storage from AoS to keys/starts SoA.
"""
from __future__ import annotations

import ctypes
import json
import os
import statistics
import subprocess
import tempfile
from pathlib import Path

from benchmarks.one.one_g02_gear_replacement_ab import _GEAR
from benchmarks.one.one_g02_relation_shared_observer_validation import MINIMIZER_SPAN, _cases
from benchmarks.one.one_g02_native_fused_nomination_fp8_ab import (
    FusedResult, SIZES, SEEDS, WINDOW, _batch, _false_pattern, _local_hit_rich, _git_blob_sha,
)

BASELINE_BLOB = "89f25972374c747654ddbf631372929b3f21b970"
PRODUCTIVE = {"shift_plus1", "damage_quarter", "fragmented_every96", "fragmented_every32", "local_hit_rich"}
CONTROLS = {"independent_random", "false_pattern"}


def _candidate_source(src: str) -> str:
    marker = "static size_t extend_left("
    helper = r'''
static int find_local_soa(
    const uint64_t keys[ONE_G02_LOCAL_ENTRIES],
    const size_t starts[ONE_G02_LOCAL_ENTRIES],
    size_t count,
    size_t head,
    uint64_t key,
    size_t *start_out
) {
    for (size_t i = 0; i < count; ++i) {
        const size_t slot = (head + i) & (ONE_G02_LOCAL_ENTRIES - 1u);
        if (keys[slot] == key) {
            *start_out = starts[slot];
            return 1;
        }
    }
    return 0;
}

'''
    if marker not in src:
        raise RuntimeError("helper insertion boundary moved")
    out = src.replace(marker, helper + marker, 1)
    decl = "    one_g02_index_entry local[ONE_G02_LOCAL_ENTRIES] = {{0}};\n"
    repl = "    uint64_t local_keys[ONE_G02_LOCAL_ENTRIES] = {0};\n    size_t local_starts[ONE_G02_LOCAL_ENTRIES] = {0};\n"
    if out.count(decl) != 1:
        raise RuntimeError("local declaration boundary moved")
    out = out.replace(decl, repl, 1)
    old_lookup = """            const int have_prior = find_entry(\n                local, ONE_G02_LOCAL_ENTRIES, local_count, local_head, state, &prior\n            );"""
    new_lookup = """            const int have_prior = find_local_soa(\n                local_keys, local_starts, local_count, local_head, state, &prior\n            );"""
    if out.count(old_lookup) != 1:
        raise RuntimeError("local lookup boundary moved")
    out = out.replace(old_lookup, new_lookup, 1)
    old_insert = """                local[slot].key = state;\n                local[slot].start = start;\n                local[slot].used = 1;\n                if (local_count > out->local_peak_entries) out->local_peak_entries = local_count;"""
    new_insert = """                local_keys[slot] = state;\n                local_starts[slot] = start;\n                if (local_count > out->local_peak_entries) out->local_peak_entries = local_count;"""
    if out.count(old_insert) != 1:
        raise RuntimeError("local insertion boundary moved")
    out = out.replace(old_insert, new_insert, 1)
    old_state = "        sizeof(local) + global_capacity * sizeof(*global);"
    new_state = "        sizeof(local_keys) + sizeof(local_starts) + global_capacity * sizeof(*global);"
    if out.count(old_state) != 1:
        raise RuntimeError("state accounting boundary moved")
    out = out.replace(old_state, new_state, 1)
    if out.count("one_g02_fused_native_nomination(") != 1:
        raise RuntimeError("fused symbol boundary moved")
    return out.replace("one_g02_fused_native_nomination(", "one_g02_fused_native_nomination_soa(", 1)


WRAPPER = r'''
#define _POSIX_C_SOURCE 200809L
#include <stddef.h>
#include <stdint.h>
#include <time.h>

typedef struct {
    uint64_t emitted, final_state, positions_considered, reserved_state_bytes;
    uint64_t derived_state_reads, suffix_blocks_built, suffix_blocks_skipped_dead;
    uint64_t suffix_value_indirect_loads, cross_auditions, cross_exact;
    uint64_t local_peak_entries, global_peak_entries, verification_read_bytes, extension_read_bytes;
} fused_result;

int one_g02_fused_native_nomination_baseline(const uint8_t*, size_t, size_t, const uint64_t[256], size_t, size_t, fused_result*, uint64_t*, size_t);
int one_g02_fused_native_nomination_soa(const uint8_t*, size_t, size_t, const uint64_t[256], size_t, size_t, fused_result*, uint64_t*, size_t);
static uint64_t now_ns(void){ struct timespec t; clock_gettime(CLOCK_MONOTONIC_RAW,&t); return (uint64_t)t.tv_sec*UINT64_C(1000000000)+(uint64_t)t.tv_nsec; }
int one_g02_fused_soa_measure(const uint8_t *data,size_t length,size_t boundary,const uint64_t gear[256],size_t window,size_t span,size_t batch,fused_result *b,fused_result *c,uint64_t *bt,uint64_t *ct,size_t trace_capacity,double *bn,double *cn){
    if(!batch||!b||!c||!bn||!cn)return -100; int rc;
    rc=one_g02_fused_native_nomination_baseline(data,length,boundary,gear,window,span,b,bt,trace_capacity); if(rc)return rc;
    rc=one_g02_fused_native_nomination_soa(data,length,boundary,gear,window,span,c,ct,trace_capacity); if(rc)return rc;
    uint64_t t,b1,b2,c1,c2;
    t=now_ns(); for(size_t i=0;i<batch;i++){rc=one_g02_fused_native_nomination_baseline(data,length,boundary,gear,window,span,b,bt,trace_capacity);if(rc)return rc;} b1=now_ns()-t;
    t=now_ns(); for(size_t i=0;i<batch;i++){rc=one_g02_fused_native_nomination_soa(data,length,boundary,gear,window,span,c,ct,trace_capacity);if(rc)return rc;} c1=now_ns()-t;
    t=now_ns(); for(size_t i=0;i<batch;i++){rc=one_g02_fused_native_nomination_soa(data,length,boundary,gear,window,span,c,ct,trace_capacity);if(rc)return rc;} c2=now_ns()-t;
    t=now_ns(); for(size_t i=0;i<batch;i++){rc=one_g02_fused_native_nomination_baseline(data,length,boundary,gear,window,span,b,bt,trace_capacity);if(rc)return rc;} b2=now_ns()-t;
    *bn=((double)b1+(double)b2)/(2.0*(double)batch); *cn=((double)c1+(double)c2)/(2.0*(double)batch); return 0;
}
'''


def _build():
    here=Path(__file__).parent
    path=here/"one_g02_fused_native_nomination_kernel.c"
    raw=path.read_bytes()
    if _git_blob_sha(raw)!=BASELINE_BLOB:
        raise RuntimeError("authoritative fused source blob moved; re-review before benchmarking")
    td=tempfile.TemporaryDirectory(prefix="cmpct-one-g02-fused-soa-"); root=Path(td.name)
    cand=root/"candidate.c"; cand.write_text(_candidate_source(raw.decode()),encoding="utf-8")
    wrap=root/"wrapper.c"; wrap.write_text(WRAPPER,encoding="utf-8")
    cc=os.environ.get("CC","cc"); base_o=root/"base.o"; cand_o=root/"cand.o"; wrap_o=root/"wrap.o"; lib=root/"libab.so"
    common=[cc,"-O3","-std=c11","-fPIC","-c"]
    subprocess.run(common+["-Done_g02_fused_native_nomination=one_g02_fused_native_nomination_baseline",str(path),"-o",str(base_o)],check=True)
    subprocess.run(common+[str(cand),"-o",str(cand_o)],check=True)
    subprocess.run(common+[str(wrap),"-o",str(wrap_o)],check=True)
    subprocess.run([cc,"-shared",str(base_o),str(cand_o),str(wrap_o),"-o",str(lib)],check=True)
    c=ctypes.CDLL(str(lib)); fn=c.one_g02_fused_soa_measure
    fn.argtypes=[ctypes.POINTER(ctypes.c_uint8),ctypes.c_size_t,ctypes.c_size_t,ctypes.POINTER(ctypes.c_uint64),ctypes.c_size_t,ctypes.c_size_t,ctypes.c_size_t,ctypes.POINTER(FusedResult),ctypes.POINTER(FusedResult),ctypes.POINTER(ctypes.c_uint64),ctypes.POINTER(ctypes.c_uint64),ctypes.c_size_t,ctypes.POINTER(ctypes.c_double),ctypes.POINTER(ctypes.c_double)]
    fn.restype=ctypes.c_int
    return fn,td


def _same_except_state(b:FusedResult,c:FusedResult)->bool:
    return all(name=="reserved_state_bytes" or int(getattr(b,name))==int(getattr(c,name)) for name,_ in FusedResult._fields_)


def run()->dict[str,object]:
    fn,td=_build(); gear=(ctypes.c_uint64*256)(*_GEAR); rows=[]; failures=[]
    try:
        for size in SIZES:
            for seed in SEEDS:
                cases=dict(_cases(size,seed)); cases["false_pattern"]=_false_pattern(size,seed); cases["local_hit_rich"]=_local_hit_rich(size,seed)
                for name,(source,target) in cases.items():
                    data=source+target; buf=(ctypes.c_uint8*len(data)).from_buffer_copy(data); samples=[]; last=None
                    for _ in range(7):
                        b,c=FusedResult(),FusedResult(); cap=len(data)+1; bt,ct=(ctypes.c_uint64*cap)(),(ctypes.c_uint64*cap)(); bn,cn=ctypes.c_double(),ctypes.c_double()
                        rc=fn(buf,len(data),len(source),gear,WINDOW,MINIMIZER_SPAN,_batch(size),ctypes.byref(b),ctypes.byref(c),bt,ct,cap,ctypes.byref(bn),ctypes.byref(cn))
                        if rc: raise RuntimeError(f"native SoA A/B failed rc={rc} {size=} {seed=} {name=}")
                        btrace=[int(bt[i]) for i in range(int(b.emitted))]; ctrace=[int(ct[i]) for i in range(int(c.emitted))]
                        if not _same_except_state(b,c) or btrace!=ctrace or int(c.reserved_state_bytes)-int(b.reserved_state_bytes)!=-512:
                            failures.append((size,seed,name))
                        samples.append(float(cn.value)/float(bn.value)); last=(b,c,bn.value,cn.value)
                    b,c,bn,cn=last
                    rows.append({"relation_bytes":size,"seed":seed,"case":name,"ratio_median":statistics.median(samples),"ratio_samples":samples,"baseline_ns_last":bn,"candidate_ns_last":cn,"baseline_state_bytes":int(b.reserved_state_bytes),"candidate_state_bytes":int(c.reserved_state_bytes),"state_delta_bytes":int(c.reserved_state_bytes)-int(b.reserved_state_bytes),"cross_exact":int(c.cross_exact)})
        productive=[r for r in rows if r["case"] in PRODUCTIVE and r["relation_bytes"]>=16*1024]; controls=[r for r in rows if r["case"] in CONTROLS]
        pm=statistics.median(r["ratio_median"] for r in productive); pw=max(r["ratio_median"] for r in productive); cm=statistics.median(r["ratio_median"] for r in controls)
        passed=not failures and pm<=0.95 and pw<=1.03 and cm<=1.03 and all(r["state_delta_bytes"]==-512 for r in rows)
        return {"schema":"cmpct-one-g02-native-fused-nomination-local-soa-v1","experimental_version":"ONE-G0.2","source_sha":os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound","baseline_blob":BASELINE_BLOB,"semantic_failures":failures,"productive_median_ratio":pm,"productive_worst_ratio":pw,"control_median_ratio":cm,"decision":"advance_local_soa" if passed else "reject_local_soa_speed","rows":rows}
    finally: td.cleanup()

if __name__=="__main__":
    result=run(); print(json.dumps(result,indent=2,sort_keys=True)); raise SystemExit(0 if result["decision"]=="advance_local_soa" else 1)
