"""ONE-G0.2 overlap-safe no-alias relation dispatch A/B.

Frozen before result-bearing execution.

The no-alias generic relation kernel recovered 7.8-17.5% versus the alias-conservative direct kernel and
beat the compact-half control on every frozen row, but `restrict` is invalid when relation spans overlap.
This experiment productizes the causal win without borrowing correctness: an overflow-safe range test uses
the no-alias kernel only when source, target and result storage are proven disjoint; all other layouts fall
back to the existing safe direct kernel.

Advance gate, frozen before result: all result structs exact; every disjoint row must select the fast path,
have dispatch/direct <=0.95 and dispatch/compact-half <=1.05; hostile overlapping layouts must select the
fallback and exactly match direct-kernel accounting. Failure retires this dispatch shape without relaxing
thresholds.
"""
from __future__ import annotations
import ctypes,json,os,statistics,subprocess,tempfile
from pathlib import Path
from benchmarks.one.one_g02_shift_branch_bound_relation_transfer import Result,_relation_cases
SIZES=(32*1024,64*1024);ROUNDS=101;BATCH_CALLS=64;MAX_DISPATCH_DIRECT=0.95;MAX_DISPATCH_HALF=1.05
class M(ctypes.Structure):
    _fields_=[("dispatch_ns_per_call",ctypes.c_double),("direct_ns_per_call",ctypes.c_double),("half_ns_per_call",ctypes.c_double),("dispatch_path",ctypes.c_int),("dispatch_result",Result),("direct_result",Result),("half_result",Result)]
def sig(x):return tuple(int(getattr(x,n)) for n,_ in Result._fields_)
def build():
    h=Path(__file__).parent;td=tempfile.TemporaryDirectory(prefix="cmpct-one-g02-safe-dispatch-");lib=Path(td.name)/"lib.so"
    subprocess.run([os.environ.get("CC","cc"),"-O3","-std=c11","-fPIC","-shared",str(h/"one_g02_shift_branch_bound_relation_direct_kernel.c"),str(h/"one_g02_shift_branch_bound_relation_restrict_kernel.c"),str(h/"one_g02_shift_branch_bound_proof_led_kernel.c"),str(h/"one_g02_shift_relation_safe_dispatch_kernel.c"),str(h/"one_g02_shift_relation_safe_dispatch_pair_kernel.c"),"-o",str(lib)],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    c=ctypes.CDLL(str(lib));measure=c.one_g02_shift_relation_safe_dispatch_measure;measure.argtypes=[ctypes.POINTER(ctypes.c_uint8),ctypes.c_size_t,ctypes.c_size_t,ctypes.POINTER(M)];measure.restype=ctypes.c_int
    dispatch=c.one_g02_shift_relation_safe_dispatch;dispatch.argtypes=[ctypes.POINTER(ctypes.c_uint8),ctypes.POINTER(ctypes.c_uint8),ctypes.c_size_t,ctypes.POINTER(Result)];dispatch.restype=ctypes.c_int
    direct=c.one_g02_shift_branch_bound_relation_direct;direct.argtypes=dispatch.argtypes;direct.restype=ctypes.c_int
    return measure,dispatch,direct,td
def overlap_checks(dispatch,direct):
    rows=[];n=4096;base=bytes(((i*131+17)^(i>>3))&255 for i in range(n+1));arr=(ctypes.c_uint8*len(base)).from_buffer_copy(base);addr=ctypes.addressof(arr)
    layouts=(("same",0,0),("forward_overlap",0,1),("backward_overlap",1,0))
    for name,so,doff in layouts:
        sp=ctypes.cast(addr+so,ctypes.POINTER(ctypes.c_uint8));dp=ctypes.cast(addr+doff,ctypes.POINTER(ctypes.c_uint8));a=Result();b=Result();path=dispatch(sp,dp,n,ctypes.byref(a));rc=direct(sp,dp,n,ctypes.byref(b));rows.append({"layout":name,"dispatch_path":path,"direct_rc":rc,"result_struct_exact":sig(a)==sig(b),"pass":path==0 and rc==0 and sig(a)==sig(b)})
    return rows
def run():
    measure,dispatch,direct,td=build();rows=[]
    try:
        passed=True
        for size in SIZES:
            for case,(src,dst,_e,_s) in _relation_cases(size).items():
                packed=src+dst;arr=(ctypes.c_uint8*len(packed)).from_buffer_copy(packed);sv=[];dv=[];hv=[];last=M()
                for _ in range(ROUNDS):
                    m=M();rc=measure(arr,size,BATCH_CALLS,ctypes.byref(m));
                    if rc:raise RuntimeError(f"measure failed: {rc}")
                    sv.append(float(m.dispatch_ns_per_call));dv.append(float(m.direct_ns_per_call));hv.append(float(m.half_ns_per_call));last=m
                s=float(statistics.median(sv));d=float(statistics.median(dv));h=float(statistics.median(hv));sd=s/d;sh=s/h;exact=sig(last.dispatch_result)==sig(last.direct_result)==sig(last.half_result);ok=exact and last.dispatch_path==1 and sd<=MAX_DISPATCH_DIRECT and sh<=MAX_DISPATCH_HALF;passed &= ok
                rows.append({"relation_bytes":size,"case":case,"dispatch_ns":s,"direct_ns":d,"half_ns":h,"dispatch_over_direct":sd,"dispatch_over_half":sh,"dispatch_path":last.dispatch_path,"result_struct_exact":exact,"row_pass":ok})
        hostile=overlap_checks(dispatch,direct);passed &= all(x["pass"] for x in hostile)
        return {"schema":"cmpct-one-g02-shift-relation-safe-dispatch-ab-v1","experimental_version":"ONE-G0.2","source_sha":os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound","frozen_sizes":list(SIZES),"frozen_rounds":ROUNDS,"frozen_batch_calls":BATCH_CALLS,"frozen_max_dispatch_over_direct":MAX_DISPATCH_DIRECT,"frozen_max_dispatch_over_half":MAX_DISPATCH_HALF,"decision":"advance_overlap_safe_noalias_dispatch" if passed else "retire_overlap_safe_noalias_dispatch","claim_boundary":"writer-side relation discovery implementation only; no representation/product/comparator authority","rows":rows,"hostile_overlap":hostile}
    finally:td.cleanup()
if __name__=="__main__":
    r=run();print(json.dumps(r,indent=2,sort_keys=True));raise SystemExit(0 if r["decision"]=="advance_overlap_safe_noalias_dispatch" else 1)
