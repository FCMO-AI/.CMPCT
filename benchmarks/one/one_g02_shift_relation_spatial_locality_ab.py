"""ONE-G0.2 physical stream-placement A/B for proof-led relation validation.

Frozen before result-bearing execution.

The arbitrary relation API remained slower than the compact half-layout control even after pointer rebasing.
A direct-pointer kernel removes carrier/offset arithmetic entirely. This A/B holds function, relation bytes,
proof semantics and one 512 KiB carrier constant, and compares two copies of the same source/target pair:
(1) adjacent non-overlapping streams, and (2) widely separated streams. Calls are A-B-B-A paired.

Hypothesis: physical stream separation is a material residual owner. The far pair must be >=5% slower than
the adjacent pair on every 32/64 KiB row, with identical result structs. If this fails, retire spatial
separation as the dominant residual and inspect compact-vs-direct code generation / benchmark ABI instead.
The 5% threshold and placements are frozen before result.
"""
from __future__ import annotations

import ctypes, json, os, random, statistics, subprocess, tempfile, time
from pathlib import Path
from benchmarks.one.one_g02_shift_branch_bound_relation_transfer import Result, _relation_cases

SIZES=(32*1024,64*1024)
CARRIER_BYTES=768*1024
MIN_FAR_SLOWDOWN=0.05
# Adjacent target begins immediately after source relation; far streams are hundreds of KiB apart.
ADJ_SOURCE=4*1024
FAR_SOURCE=256*1024
FAR_TARGET=640*1024


def _build():
    here=Path(__file__).parent
    td=tempfile.TemporaryDirectory(prefix="cmpct-one-g02-spatial-ab-")
    lib=Path(td.name)/"lib.so"
    subprocess.run([os.environ.get("CC","cc"),"-O3","-std=c11","-fPIC","-shared",
                    str(here/"one_g02_shift_branch_bound_relation_direct_kernel.c"),"-o",str(lib)],
                   check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    cdll=ctypes.CDLL(str(lib)); fn=cdll.one_g02_shift_branch_bound_relation_direct
    fn.argtypes=[ctypes.POINTER(ctypes.c_uint8),ctypes.POINTER(ctypes.c_uint8),ctypes.c_size_t,ctypes.POINTER(Result)]
    fn.restype=ctypes.c_int
    return fn,td


def _sig(x): return tuple(int(getattr(x,n)) for n,_ in Result._fields_)


def _ptr(arr,off): return ctypes.cast(ctypes.addressof(arr)+off,ctypes.POINTER(ctypes.c_uint8))


def _paired(fn,arr,size,adj_a,adj_b,far_a,far_b):
    ao=Result(); fo=Result(); ap=_ptr(arr,adj_a); aq=_ptr(arr,adj_b); fp=_ptr(arr,far_a); fq=_ptr(arr,far_b)
    fn(ap,aq,size,ctypes.byref(ao)); fn(fp,fq,size,ctypes.byref(fo))
    av=[]; fv=[]
    for _ in range(151):
        t=time.perf_counter_ns(); fn(ap,aq,size,ctypes.byref(ao)); a1=time.perf_counter_ns()-t
        t=time.perf_counter_ns(); fn(fp,fq,size,ctypes.byref(fo)); f1=time.perf_counter_ns()-t
        t=time.perf_counter_ns(); fn(fp,fq,size,ctypes.byref(fo)); f2=time.perf_counter_ns()-t
        t=time.perf_counter_ns(); fn(ap,aq,size,ctypes.byref(ao)); a2=time.perf_counter_ns()-t
        av.append((a1+a2)*0.5); fv.append((f1+f2)*0.5)
    return float(statistics.median(av)),float(statistics.median(fv)),ao,fo


def run():
    fn,td=_build(); rows=[]
    try:
        passed=True
        for size in SIZES:
            adj_b=ADJ_SOURCE+size
            if adj_b+size>FAR_SOURCE: raise AssertionError("frozen adjacent/far regions overlap")
            if FAR_TARGET+size>CARRIER_BYTES: raise AssertionError("frozen far target exceeds carrier")
            for ci,(case,(source,target,_,_)) in enumerate(_relation_cases(size).items()):
                buf=bytearray(random.Random(61000+size+ci).randbytes(CARRIER_BYTES))
                for off,payload in ((ADJ_SOURCE,source),(adj_b,target),(FAR_SOURCE,source),(FAR_TARGET,target)):
                    buf[off:off+size]=payload
                arr=(ctypes.c_uint8*len(buf)).from_buffer_copy(buf)
                ans,fns,ao,fo=_paired(fn,arr,size,ADJ_SOURCE,adj_b,FAR_SOURCE,FAR_TARGET)
                exact=_sig(ao)==_sig(fo); slowdown=fns/ans-1.0
                passed &= exact and slowdown>=MIN_FAR_SLOWDOWN
                rows.append({"relation_bytes":size,"case":case,"adjacent_median_ns":ans,"far_median_ns":fns,
                             "far_over_adjacent":fns/ans,"far_slowdown_fraction":slowdown,"result_struct_exact":exact})
        return {"schema":"cmpct-one-g02-shift-relation-spatial-locality-ab-v1","experimental_version":"ONE-G0.2",
                "source_sha":os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
                "frozen_sizes":list(SIZES),"frozen_min_far_slowdown":MIN_FAR_SLOWDOWN,
                "decision":"stream_separation_is_material_residual_owner" if passed else "stream_separation_not_dominant_residual_owner",
                "claim_boundary":"writer-side causal compute attribution only; no representation/product/comparator authority","rows":rows}
    finally: td.cleanup()

if __name__=="__main__":
    r=run(); print(json.dumps(r,indent=2,sort_keys=True)); raise SystemExit(0 if r["decision"]=="stream_separation_is_material_residual_owner" else 1)
