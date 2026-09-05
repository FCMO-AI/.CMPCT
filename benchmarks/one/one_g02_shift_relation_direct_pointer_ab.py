"""ONE-G0.2 direct-pointer vs carrier-API relation cost diagnostic.

Frozen before result-bearing execution.

The first arbitrary-offset kernel lost 16-28% against the compact half-layout control. Pointer rebasing
recovered roughly 10-13% on many direct old-vs-new rows but still missed the absolute <=1.10x transfer
bound. This experiment isolates the residual carrier/API bill from physical stream placement: the control
is the rebased carrier function; the candidate receives the exact same source/target bytes at the exact
same addresses but as already-validated pointers plus relation length.

Hypothesis: per-call carrier bounds and offset formation remain a material residual owner. The direct-pointer
kernel must produce an identical result struct and be >=5% faster than the rebased carrier API on every
32/64 KiB row. If that fails, retire carrier/API overhead as the dominant residual and investigate physical
stream locality/code generation instead. The 5% gate is frozen before result and may not be lowered.
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
from pathlib import Path

from benchmarks.one.one_g02_shift_branch_bound_relation_transfer import (
    CARRIER_BYTES,
    PLACEMENTS,
    Result,
    _relation_cases,
)

SIZES = (32 * 1024, 64 * 1024)
MIN_SPEEDUP = 0.05


def _build():
    here = Path(__file__).parent
    td = tempfile.TemporaryDirectory(prefix="cmpct-one-g02-directptr-ab-")
    lib = Path(td.name) / "lib.so"
    subprocess.run(
        [os.environ.get("CC", "cc"), "-O3", "-std=c11", "-fPIC", "-shared",
         str(here / "one_g02_shift_branch_bound_relation_rebased_kernel.c"),
         str(here / "one_g02_shift_branch_bound_relation_direct_kernel.c"),
         "-o", str(lib)],
        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    cdll = ctypes.CDLL(str(lib))
    carrier = cdll.one_g02_shift_branch_bound_relation_rebased
    carrier.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t,
                        ctypes.c_size_t, ctypes.c_size_t, ctypes.c_size_t,
                        ctypes.POINTER(Result)]
    carrier.restype = ctypes.c_int
    direct = cdll.one_g02_shift_branch_bound_relation_direct
    direct.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.POINTER(ctypes.c_uint8),
                       ctypes.c_size_t, ctypes.POINTER(Result)]
    direct.restype = ctypes.c_int
    return carrier, direct, td


def _sig(x: Result):
    return tuple(int(getattr(x, name)) for name, _ in Result._fields_)


def _paired(carrier, direct, arr, n, aoff, boff, rlen):
    co = Result(); do = Result()
    base = ctypes.addressof(arr)
    src = ctypes.cast(base + aoff, ctypes.POINTER(ctypes.c_uint8))
    dst = ctypes.cast(base + boff, ctypes.POINTER(ctypes.c_uint8))
    if carrier(arr, n, aoff, boff, rlen, ctypes.byref(co)) != 0: raise RuntimeError("carrier failed")
    if direct(src, dst, rlen, ctypes.byref(do)) != 0: raise RuntimeError("direct failed")
    cvals=[]; dvals=[]
    for _ in range(151):
        t=time.perf_counter_ns(); carrier(arr,n,aoff,boff,rlen,ctypes.byref(co)); c1=time.perf_counter_ns()-t
        t=time.perf_counter_ns(); direct(src,dst,rlen,ctypes.byref(do)); d1=time.perf_counter_ns()-t
        t=time.perf_counter_ns(); direct(src,dst,rlen,ctypes.byref(do)); d2=time.perf_counter_ns()-t
        t=time.perf_counter_ns(); carrier(arr,n,aoff,boff,rlen,ctypes.byref(co)); c2=time.perf_counter_ns()-t
        cvals.append((c1+c2)*0.5); dvals.append((d1+d2)*0.5)
    return float(statistics.median(cvals)), float(statistics.median(dvals)), co, do


def run():
    carrier, direct, td = _build()
    rows=[]
    try:
        passed=True
        for size in SIZES:
            for case,(source,target,_,_) in _relation_cases(size).items():
                for placement,(aoff,boff) in enumerate(PLACEMENTS):
                    buf=bytearray(random.Random(51000+size+placement).randbytes(CARRIER_BYTES))
                    buf[aoff:aoff+size]=source; buf[boff:boff+size]=target
                    arr=(ctypes.c_uint8*len(buf)).from_buffer_copy(buf)
                    cns,dns,co,do=_paired(carrier,direct,arr,len(buf),aoff,boff,size)
                    exact=_sig(co)==_sig(do)
                    speedup=1.0-dns/cns
                    passed &= exact and speedup >= MIN_SPEEDUP
                    rows.append({"relation_bytes":size,"case":case,"placement":placement,
                                 "carrier_median_ns":cns,"direct_median_ns":dns,
                                 "direct_over_carrier":dns/cns,"direct_speedup_fraction":speedup,
                                 "result_struct_exact":exact})
        return {"schema":"cmpct-one-g02-shift-relation-direct-pointer-ab-v1",
                "experimental_version":"ONE-G0.2",
                "source_sha":os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
                "frozen_sizes":list(SIZES),"frozen_min_speedup":MIN_SPEEDUP,
                "decision":"carrier_api_is_material_residual_owner" if passed else "carrier_api_not_dominant_residual_owner",
                "claim_boundary":"writer-side causal compute attribution only; no representation/product/comparator authority",
                "rows":rows}
    finally:
        td.cleanup()


if __name__ == "__main__":
    result=run(); print(json.dumps(result,indent=2,sort_keys=True))
    raise SystemExit(0 if result["decision"]=="carrier_api_is_material_residual_owner" else 1)
