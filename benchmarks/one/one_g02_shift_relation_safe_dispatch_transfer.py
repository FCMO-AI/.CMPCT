"""ONE-G0.2 structural transfer of the overlap-safe no-alias relation dispatch.

Frozen before result-bearing execution.

The overlap-safe dispatch advanced at 32/64 KiB: it charged its range proof, preserved overlap fallback,
and recovered 10.1-14.3% versus the alias-conservative generic relation kernel while remaining near the
compact-half control. This experiment asks whether that causal win transfers across a broader relation-size
ladder rather than being a two-size compiler accident.

Frozen sizes: 4, 8, 16, 32, 64, 128 and 256 KiB. Cases are the unchanged relation-transfer cases. Advance
requires exact result structs, disjoint fast-path selection, dispatch/direct <=0.97 and dispatch/half <=1.08
on every row. The wider gate is intentionally slightly looser than the discovery gate because very small
relations charge fixed dynamic range checks and very large relations may expose different code-cache or
frequency regimes. No aggregate may hide a losing row. Hostile overlapping layouts remain covered by the
source experiment and are not gifted away by this transfer.
"""
from __future__ import annotations
import ctypes,json,os,statistics,subprocess,tempfile
from pathlib import Path
from benchmarks.one.one_g02_shift_branch_bound_relation_transfer import Result,_relation_cases

SIZES=(4*1024,8*1024,16*1024,32*1024,64*1024,128*1024,256*1024)
ROUNDS=61
BATCH_CALLS=64
MAX_DISPATCH_DIRECT=0.97
MAX_DISPATCH_HALF=1.08

class M(ctypes.Structure):
    _fields_=[("dispatch_ns_per_call",ctypes.c_double),("direct_ns_per_call",ctypes.c_double),("half_ns_per_call",ctypes.c_double),("dispatch_path",ctypes.c_int),("dispatch_result",Result),("direct_result",Result),("half_result",Result)]

def sig(x):return tuple(int(getattr(x,n)) for n,_ in Result._fields_)

def build():
    h=Path(__file__).parent;td=tempfile.TemporaryDirectory(prefix="cmpct-one-g02-safe-transfer-");lib=Path(td.name)/"lib.so"
    subprocess.run([os.environ.get("CC","cc"),"-O3","-std=c11","-fPIC","-shared",str(h/"one_g02_shift_branch_bound_relation_direct_kernel.c"),str(h/"one_g02_shift_branch_bound_relation_restrict_kernel.c"),str(h/"one_g02_shift_branch_bound_proof_led_kernel.c"),str(h/"one_g02_shift_relation_safe_dispatch_kernel.c"),str(h/"one_g02_shift_relation_safe_dispatch_pair_kernel.c"),"-o",str(lib)],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    c=ctypes.CDLL(str(lib));fn=c.one_g02_shift_relation_safe_dispatch_measure;fn.argtypes=[ctypes.POINTER(ctypes.c_uint8),ctypes.c_size_t,ctypes.c_size_t,ctypes.POINTER(M)];fn.restype=ctypes.c_int
    return fn,td

def run():
    fn,td=build();rows=[]
    try:
        passed=True
        for size in SIZES:
            for case,(src,dst,_e,_s) in _relation_cases(size).items():
                packed=src+dst;arr=(ctypes.c_uint8*len(packed)).from_buffer_copy(packed);sv=[];dv=[];hv=[];last=M()
                for _ in range(ROUNDS):
                    m=M();rc=fn(arr,size,BATCH_CALLS,ctypes.byref(m))
                    if rc:raise RuntimeError(f"measure failed: {rc}")
                    sv.append(float(m.dispatch_ns_per_call));dv.append(float(m.direct_ns_per_call));hv.append(float(m.half_ns_per_call));last=m
                s=float(statistics.median(sv));d=float(statistics.median(dv));h=float(statistics.median(hv));sd=s/d;sh=s/h
                exact=sig(last.dispatch_result)==sig(last.direct_result)==sig(last.half_result)
                ok=exact and last.dispatch_path==1 and sd<=MAX_DISPATCH_DIRECT and sh<=MAX_DISPATCH_HALF
                passed &= ok
                rows.append({"relation_bytes":size,"case":case,"dispatch_ns":s,"direct_ns":d,"half_ns":h,"dispatch_over_direct":sd,"dispatch_over_half":sh,"dispatch_path":last.dispatch_path,"result_struct_exact":exact,"row_pass":ok})
        return {"schema":"cmpct-one-g02-shift-relation-safe-dispatch-transfer-v1","experimental_version":"ONE-G0.2","source_sha":os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound","frozen_sizes":list(SIZES),"frozen_rounds":ROUNDS,"frozen_batch_calls":BATCH_CALLS,"frozen_max_dispatch_over_direct":MAX_DISPATCH_DIRECT,"frozen_max_dispatch_over_half":MAX_DISPATCH_HALF,"decision":"advance_safe_dispatch_structural_transfer" if passed else "safe_dispatch_transfer_incomplete","claim_boundary":"writer-side structural transfer only; no product/comparator authority","rows":rows}
    finally:td.cleanup()
if __name__=="__main__":
    r=run();print(json.dumps(r,indent=2,sort_keys=True));raise SystemExit(0 if r["decision"]=="advance_safe_dispatch_structural_transfer" else 1)
