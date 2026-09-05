"""ONE-G0.2 native epoch-min rescue cost falsifier.

Referee freeze before result-bearing execution
==============================================
The scalar epoch-min observer preserved all 35 previously frozen hard shifted/starvation
transfer rows with zero opportunity loss. It removes the two costs that separately failed:
continuous exact queue/hierarchy state and 4,096-state edge replay.

This native test charges the complete per-byte epoch-min recurrence against the promoted 8 KiB
tail-return minimizer selector. It does not move WINDOW=64, starvation/span=4096, sparse Gear
mask, rightmost tie semantics, or the generator-distinct transfer corpus.

Frozen seed gate:
- native emitted epoch positions/final Gear state/accounting exactly match an independent
  Python epoch recurrence on every row;
- reserved state <=0.10x promoted selector state for every >=8 KiB row;
- hard 8,193-byte epoch/promoted median <=1.10x;
- random, zlib-random, repeated and shifted 1 MiB epoch/promoted median <=0.80x each;
- any large row >0.90x retires this native implementation shape.
Passing is only permission for broad opportunity-transfer testing, not promotion.
"""
from __future__ import annotations

import ctypes,json,os
from pathlib import Path
import statistics,subprocess,tempfile,time

from benchmarks.one.one_g02_gear_replacement_ab import _GEAR,_U64_MASK,ANCHOR_MASK,WINDOW,MIN_RUN
from benchmarks.one.one_g02_minimizer_native_probe import MINIMIZER_SPAN
from benchmarks.one.one_g02_minimizer_size_dispatch_tail_ab import _bind_dispatch,_call_dispatch
from benchmarks.one.one_g02_starvation_byte_history_native_ab import _cases

ROUNDS=17

class _E(ctypes.Structure):
    _fields_=[("emitted",ctypes.c_uint64),("final_state",ctypes.c_uint64),
              ("positions_considered",ctypes.c_uint64),("sparse_anchors",ctypes.c_uint64),
              ("pulses",ctypes.c_uint64),("reserved_state_bytes",ctypes.c_uint64)]

def _bind_epoch(lib):
    fn=lib.one_g02_starvation_epoch_min_kernel
    fn.argtypes=[ctypes.POINTER(ctypes.c_uint8),ctypes.c_size_t,ctypes.POINTER(ctypes.c_uint64),
                 ctypes.c_size_t,ctypes.c_size_t,ctypes.POINTER(_E),ctypes.POINTER(ctypes.c_uint64),ctypes.c_size_t]
    fn.restype=ctypes.c_int; return fn

def _call_epoch(fn,gear,arr,n,trace=None,cap=0):
    out=_E(); rc=fn(arr,n,gear,WINDOW,MINIMIZER_SPAN,ctypes.byref(out),trace if trace is not None else None,cap)
    if rc: raise RuntimeError(f"epoch kernel rc={rc}")
    return out

def _oracle(data:bytes):
    if not data:return [],0,0,0
    h=0;last_sparse=None;active=False;min_signal=(1<<64)-1;min_pos=None;epoch_count=0
    trace=[];positions=anchors=0;run_value=data[0];run_length=0
    def reset():
        nonlocal min_signal,min_pos,epoch_count
        min_signal=(1<<64)-1;min_pos=None;epoch_count=0
    def pulse():
        if min_pos is not None:trace.append(min_pos)
        reset()
    for position,value in enumerate(data):
        if not run_length:run_value=value;run_length=1
        elif value==run_value:run_length+=1
        else:run_value=value;run_length=1
        h=((h<<1)+_GEAR[value])&_U64_MASK
        if position+1<WINDOW:continue
        positions+=1;rd=run_length>=max(MIN_RUN,WINDOW);sparse=not(h&ANCHOR_MASK) and not rd
        if sparse:
            if active:pulse()
            anchors+=1;last_sparse=position;active=False;reset();continue
        if rd:continue
        epoch_count+=1
        if h<=min_signal:min_signal=h;min_pos=position
        gap=position-last_sparse if last_sparse is not None else position+1-WINDOW
        if not active and gap>=MINIMIZER_SPAN:pulse();active=True
        elif active and epoch_count>=MINIMIZER_SPAN:pulse()
    if active:pulse()
    return trace,h,positions,anchors

def _build():
    here=Path(__file__).parent;td=tempfile.TemporaryDirectory(prefix="cmpct-one-g02-epoch-native-");lib=Path(td.name)/"lib.so"
    subprocess.run([os.environ.get("CC","cc"),"-O3","-std=c11","-fPIC","-shared",
        str(here/"one_g02_minimizer_segmented_counter_kernel.c"),str(here/"one_g02_minimizer_offset_only_kernel.c"),
        str(here/"one_g02_minimizer_size_dispatch_tail_kernel.c"),str(here/"one_g02_starvation_epoch_min_kernel.c"),
        "-o",str(lib)],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    return ctypes.CDLL(str(lib)),td

def _paired(a,b):
    ratios=[];ans=[];bns=[]
    for i in range(ROUNDS):
        if i%2==0:
            t=time.perf_counter_ns();a();x=time.perf_counter_ns()-t;t=time.perf_counter_ns();b();y=time.perf_counter_ns()-t
        else:
            t=time.perf_counter_ns();b();y=time.perf_counter_ns()-t;t=time.perf_counter_ns();a();x=time.perf_counter_ns()-t
        ratios.append(y/x);ans.append(x);bns.append(y)
    return ratios,ans,bns

def run():
    lib,td=_build()
    try:
        promoted=_bind_dispatch(lib);epoch=_bind_epoch(lib);gear=(ctypes.c_uint64*256)(*_GEAR);rows=[]
        for name,data in _cases().items():
            arr=(ctypes.c_uint8*len(data)).from_buffer_copy(data);cap=max(1,len(data));tr=(ctypes.c_uint64*cap)()
            eo=_call_epoch(epoch,gear,arr,len(data),tr,cap);oracle=_oracle(data);actual=[int(tr[i]) for i in range(int(eo.emitted))]
            exact=(actual==oracle[0] and int(eo.final_state)==oracle[1] and int(eo.positions_considered)==oracle[2] and int(eo.sparse_anchors)==oracle[3])
            if not exact:raise AssertionError((name,"epoch native/oracle mismatch",actual,oracle[0]))
            po=_call_dispatch(promoted,gear,arr,len(data));ratios,pns,ens=_paired(lambda:_call_dispatch(promoted,gear,arr,len(data)),lambda:_call_epoch(epoch,gear,arr,len(data)))
            rows.append({"case":name,"input_bytes":len(data),"exact_epoch_oracle":exact,
                "median_epoch_over_promoted":statistics.median(ratios),"p90_epoch_over_promoted":sorted(ratios)[int(.9*(ROUNDS-1))],
                "median_promoted_ns":statistics.median(pns),"median_epoch_ns":statistics.median(ens),
                "epoch_state_bytes":int(eo.reserved_state_bytes),"promoted_state_bytes":int(po.reserved_state_bytes),
                "state_ratio":int(eo.reserved_state_bytes)/int(po.reserved_state_bytes),"pulses":int(eo.pulses),"emitted":int(eo.emitted)})
        m={r["case"]:r for r in rows};large=("random_1mib","zlib_random_1mib","repeat_64k_basis_1mib","shifted_512k_insert1")
        large_ok=all(m[k]["median_epoch_over_promoted"]<=.80 for k in large) and max(m[k]["median_epoch_over_promoted"] for k in large)<=.90
        state_ok=all(r["state_ratio"]<=.10 for r in rows if r["input_bytes"]>=8192)
        hard_ok=m["transfer_starved_seed10_insert1"]["median_epoch_over_promoted"]<=1.10
        decision="advance_epoch_min_to_broad_opportunity_transfer" if large_ok and state_ok and hard_ok else "retire_native_epoch_min_shape"
        return {"schema":"cmpct-one-g02-starvation-epoch-min-native-ab-v1","experimental_version":"ONE-G0.2",
            "source_sha":os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound","rounds":ROUNDS,
            "frozen_gate":{"state_max":.10,"large_target":.80,"large_retire":.90,"hard_max":1.10},"decision":decision,
            "claim_boundary":"native encoder-discovery seed evidence only; broad opportunity transfer required before promotion","rows":rows}
    finally:td.cleanup()

if __name__=="__main__":print(json.dumps(run(),indent=2,sort_keys=True))
