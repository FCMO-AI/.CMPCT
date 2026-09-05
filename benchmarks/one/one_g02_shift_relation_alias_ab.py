"""ONE-G0.2 relation alias-analysis causal discriminator.

Frozen before result-bearing execution.

Native-internal timing falsified Python/ctypes overhead as the dominant residual: the generic direct-pointer
kernel remained materially slower than the compact half-layout kernel. The direct API exposes two source
pointers plus a written result object, so the compiler has weaker non-alias guarantees than the packed-half
control. This experiment changes only that compile-time contract on benchmark inputs that are already
physically non-overlapping.

Hypothesis: conservative alias analysis is the dominant remaining code-generation owner. The `restrict`
variant advances only if result structs are exact, it is >=5% faster than the otherwise identical direct
kernel on every frozen 32/64 KiB case, and it lands within 1.05x of the compact half-layout control on every
row. Failure retires alias uncertainty as a sufficient explanation and moves attribution to instruction /
loop-shape differences. Thresholds are frozen and may not be relaxed after result.
"""
from __future__ import annotations

import ctypes
import json
import os
import statistics
import subprocess
import tempfile
from pathlib import Path

from benchmarks.one.one_g02_shift_branch_bound_relation_transfer import Result, _relation_cases

SIZES=(32*1024,64*1024)
ROUNDS=101
BATCH_CALLS=64
MAX_RESTRICT_OVER_DIRECT=0.95
MAX_RESTRICT_OVER_HALF=1.05

class Measurement(ctypes.Structure):
    _fields_=[
        ("direct_ns_per_call",ctypes.c_double),
        ("restrict_ns_per_call",ctypes.c_double),
        ("half_ns_per_call",ctypes.c_double),
        ("direct_result",Result),("restrict_result",Result),("half_result",Result),
    ]

def _sig(x): return tuple(int(getattr(x,n)) for n,_ in Result._fields_)

def _build():
    here=Path(__file__).parent
    td=tempfile.TemporaryDirectory(prefix="cmpct-one-g02-alias-ab-")
    lib=Path(td.name)/"lib.so"
    subprocess.run([
        os.environ.get("CC","cc"),"-O3","-std=c11","-fPIC","-shared",
        str(here/"one_g02_shift_branch_bound_relation_direct_kernel.c"),
        str(here/"one_g02_shift_branch_bound_relation_restrict_kernel.c"),
        str(here/"one_g02_shift_branch_bound_proof_led_kernel.c"),
        str(here/"one_g02_shift_relation_alias_pair_kernel.c"),"-o",str(lib)],
        check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    cdll=ctypes.CDLL(str(lib)); fn=cdll.one_g02_shift_relation_alias_measure
    fn.argtypes=[ctypes.POINTER(ctypes.c_uint8),ctypes.c_size_t,ctypes.c_size_t,ctypes.POINTER(Measurement)]
    fn.restype=ctypes.c_int
    return fn,td

def run():
    fn,td=_build(); rows=[]
    try:
        passed=True
        for size in SIZES:
            for case,(src,dst,_e,_s) in _relation_cases(size).items():
                packed=src+dst; arr=(ctypes.c_uint8*len(packed)).from_buffer_copy(packed)
                ds=[]; rs=[]; hs=[]; last=Measurement()
                for _ in range(ROUNDS):
                    m=Measurement(); rc=fn(arr,size,BATCH_CALLS,ctypes.byref(m))
                    if rc: raise RuntimeError(f"alias harness failed: {rc}")
                    ds.append(float(m.direct_ns_per_call)); rs.append(float(m.restrict_ns_per_call)); hs.append(float(m.half_ns_per_call)); last=m
                d=float(statistics.median(ds)); r=float(statistics.median(rs)); h=float(statistics.median(hs))
                rd=r/d; rh=r/h
                exact=_sig(last.direct_result)==_sig(last.restrict_result)==_sig(last.half_result)
                ok=exact and rd<=MAX_RESTRICT_OVER_DIRECT and rh<=MAX_RESTRICT_OVER_HALF
                passed &= ok
                rows.append({"relation_bytes":size,"case":case,"direct_ns":d,"restrict_ns":r,"half_ns":h,
                             "restrict_over_direct":rd,"restrict_over_half":rh,"result_struct_exact":exact,"row_pass":ok})
        return {"schema":"cmpct-one-g02-shift-relation-alias-ab-v1","experimental_version":"ONE-G0.2",
                "source_sha":os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
                "frozen_sizes":list(SIZES),"frozen_rounds":ROUNDS,"frozen_batch_calls":BATCH_CALLS,
                "frozen_max_restrict_over_direct":MAX_RESTRICT_OVER_DIRECT,
                "frozen_max_restrict_over_half":MAX_RESTRICT_OVER_HALF,
                "decision":"alias_analysis_is_dominant_residual_owner" if passed else "alias_analysis_not_sufficient_residual_owner",
                "claim_boundary":"writer-side causal compute attribution only; no representation/product/comparator authority","rows":rows}
    finally: td.cleanup()

if __name__=="__main__":
    r=run(); print(json.dumps(r,indent=2,sort_keys=True)); raise SystemExit(0 if r["decision"]=="alias_analysis_is_dominant_residual_owner" else 1)
