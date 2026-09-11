"""ONE-G0.2 native one-pass vs two-pass damaged-relation segment-plan construction."""
from __future__ import annotations

import ctypes
import json
import os
import statistics
import subprocess
import tempfile
import time
from pathlib import Path

from benchmarks.one.one_g02_shift_branch_bound_relation_transfer import _relation_cases

SIZES=(4*1024,8*1024,16*1024,32*1024,64*1024,128*1024,256*1024)
CASES=("shift_plus1_damage_quarter","fragmented_every96")
ROUNDS=101
MAX_TRAFFIC_RATIO=0.51
MAX_LARGE_TIME_RATIO=0.70
MAX_ANY_TIME_RATIO=1.03

class Segment(ctypes.Structure):
    _fields_=[("start",ctypes.c_uint32),("length",ctypes.c_uint32),("kind",ctypes.c_uint8)]
class Stats(ctypes.Structure):
    _fields_=[("compared_target_bytes",ctypes.c_uint64),("segments",ctypes.c_uint64)]

def _build():
    td=tempfile.TemporaryDirectory(prefix="cmpct-one-g02-segment-fusion-")
    lib=Path(td.name)/"lib.so"
    src=Path(__file__).with_name("one_g02_native_segment_plan_fusion_kernel.c")
    subprocess.run([os.environ.get("CC","cc"),"-O3","-std=c11","-fPIC","-shared",str(src),"-o",str(lib)],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    cdll=ctypes.CDLL(str(lib))
    sig=[ctypes.POINTER(ctypes.c_uint8),ctypes.POINTER(ctypes.c_uint8),ctypes.c_size_t,ctypes.POINTER(Segment),ctypes.c_size_t,ctypes.POINTER(Stats)]
    one=cdll.one_g02_segment_plan_one_pass; one.argtypes=sig; one.restype=ctypes.c_int
    two=cdll.one_g02_segment_plan_two_pass; two.argtypes=sig; two.restype=ctypes.c_int
    return one,two,td

def _oracle(src:bytes,dst:bytes):
    out=[]; i=0; n=len(dst)
    while i<n:
        ref=i>0 and dst[i]==src[i-1]; begin=i; i+=1
        while i<n and (i>0 and dst[i]==src[i-1])==ref: i+=1
        out.append((0 if ref else 1, begin-1 if ref else begin, i-begin))
    return out

def _snapshot(buf,count):
    return [(int(buf[i].kind),int(buf[i].start),int(buf[i].length)) for i in range(count)]

def run():
    one,two,td=_build(); rows=[]; all_ok=True; timing_ok=True
    try:
        for n in SIZES:
            generated=_relation_cases(n)
            for case in CASES:
                src,dst,expected,shift=generated[case]
                assert expected and shift==1
                a=(ctypes.c_uint8*n).from_buffer_copy(src); b=(ctypes.c_uint8*n).from_buffer_copy(dst)
                cap=n
                bo=(Segment*cap)(); bt=(Segment*cap)(); so=Stats(); st=Stats()
                if one(a,b,n,bo,cap,ctypes.byref(so))!=0 or two(a,b,n,bt,cap,ctypes.byref(st))!=0: raise AssertionError("native segmenter failed")
                oracle=_oracle(src,dst); op=_snapshot(bo,so.segments); tp=_snapshot(bt,st.segments)
                exact=(op==tp==oracle and sum(x[2] for x in op)==n)
                all_ok &= exact
                before_src=bytes(a); before_dst=bytes(b)
                osamp=[]; tsamp=[]
                for r in range(ROUNDS):
                    order=((one,bo,so,osamp),(two,bt,st,tsamp))
                    if r&1: order=tuple(reversed(order))
                    for fn,buf,stats,samples in order:
                        t0=time.perf_counter_ns(); rc=fn(a,b,n,buf,cap,ctypes.byref(stats)); samples.append(time.perf_counter_ns()-t0)
                        if rc!=0: raise AssertionError("timed native segmenter failed")
                if bytes(a)!=before_src or bytes(b)!=before_dst: raise AssertionError("input mutation")
                om=float(statistics.median(osamp)); tm=float(statistics.median(tsamp)); ratio=om/tm
                traffic=int(so.compared_target_bytes)/int(st.compared_target_bytes)
                row_timing=ratio<=MAX_ANY_TIME_RATIO and (n<16*1024 or ratio<=MAX_LARGE_TIME_RATIO)
                timing_ok &= row_timing
                all_ok &= traffic<=MAX_TRAFFIC_RATIO
                rows.append({"relation_bytes":n,"case":case,"segments":len(op),"plan_bytes":len(op)*ctypes.sizeof(Segment),"exact_plan":exact,"one_pass_compared_target_bytes":int(so.compared_target_bytes),"two_pass_compared_target_bytes":int(st.compared_target_bytes),"traffic_ratio":traffic,"one_pass_median_ns":om,"two_pass_median_ns":tm,"one_over_two_elapsed":ratio,"timing_pass":row_timing})
        passed=all_ok and timing_ok
        return {"schema":"cmpct-one-g02-native-segment-plan-fusion-v1","experimental_version":"ONE-G0.2","source_sha":os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound","rounds":ROUNDS,"decision":"advance_native_segment_plan_fusion" if passed else "hold_native_segment_plan_fusion","claim_boundary":"writer-side transient plan construction only; relation admission, Program/wire creation, discovery and comparator authority excluded","rows":rows}
    finally: td.cleanup()

if __name__=="__main__":
    result=run(); print(json.dumps(result,indent=2,sort_keys=True)); raise SystemExit(0 if result["decision"]=="advance_native_segment_plan_fusion" else 1)
