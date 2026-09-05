"""ONE-G0.2 native edge-pulse rescue cost falsifier.

Referee freeze before result-bearing execution
==============================================
Semantic edge-pulse replay preserved 35/35 generator-distinct hard opportunities using two
bounded replays per short starvation case. This experiment asks whether eliminating continuous
queue maintenance actually closes the remaining small-input creation debt while keeping the
large-path compute advantage.

Frozen native seed gate:
- emitted pulse positions and final Gear state must exactly match an independent Python
  recurrence on every row;
- reserved state <=0.20x the promoted selector state for every >=8 KiB row;
- median edge/promoted <=0.98x on random and zlib-random 1 MiB;
- median edge/promoted <=1.02x on repeated and shifted large controls;
- any large row >1.05x retires this native scheduling shape;
- hard 8,193-byte edge/promoted <=1.20x and edge/compact <=0.65x to close the localized debt.
No threshold or semantic constant may move after result-bearing execution.

This is encoder-discovery native evidence only. Opportunity equivalence outside the already
frozen 35-row transfer family remains a separate required experiment.
"""
from __future__ import annotations

from collections import deque
import ctypes
import json
import os
from pathlib import Path
import statistics
import subprocess
import tempfile
import time

from benchmarks.one.one_g02_gear_replacement_ab import _GEAR, _U64_MASK, ANCHOR_MASK, WINDOW, MIN_RUN
from benchmarks.one.one_g02_minimizer_native_probe import MINIMIZER_SPAN
from benchmarks.one.one_g02_minimizer_size_dispatch_tail_ab import _bind_dispatch, _call_dispatch
from benchmarks.one.one_g02_starvation_compact_queue_ab import _bind as _bind_compact, _call as _call_compact
from benchmarks.one.one_g02_starvation_byte_history_native_ab import _cases

ROUNDS=13

class _P(ctypes.Structure):
    _fields_=[("emitted",ctypes.c_uint64),("final_state",ctypes.c_uint64),
              ("positions_considered",ctypes.c_uint64),("sparse_anchors",ctypes.c_uint64),
              ("pulses",ctypes.c_uint64),("replayed_history_bytes",ctypes.c_uint64),
              ("reserved_state_bytes",ctypes.c_uint64)]


def _bind_pulse(lib):
    fn=lib.one_g02_starvation_edge_pulse_kernel
    fn.argtypes=[ctypes.POINTER(ctypes.c_uint8),ctypes.c_size_t,
                 ctypes.POINTER(ctypes.c_uint64),ctypes.c_size_t,ctypes.c_size_t,
                 ctypes.POINTER(_P),ctypes.POINTER(ctypes.c_uint64),ctypes.c_size_t]
    fn.restype=ctypes.c_int
    return fn


def _call_pulse(fn,gear,arr,n,trace=None,cap=0):
    out=_P(); ptr=trace if trace is not None else None
    rc=fn(arr,n,gear,WINDOW,MINIMIZER_SPAN,ctypes.byref(out),ptr,cap)
    if rc: raise RuntimeError(f"edge pulse kernel rc={rc}")
    return out


def _oracle(data:bytes):
    states=deque(maxlen=MINIMIZER_SPAN); h=0; last_sparse=None; active=False; last_emit=None
    trace=[]; anchors=0; positions=0; run_value=data[0] if data else 0; run_length=0
    def pulse():
        nonlocal last_emit
        if len(states)<MINIMIZER_SPAN: return
        best_signal,best_pos=states[0]
        for signal,pos in states:
            if signal<=best_signal: best_signal,best_pos=signal,pos
        if best_pos!=last_emit:
            trace.append(best_pos); last_emit=best_pos
    for position,value in enumerate(data):
        if not run_length: run_value=value; run_length=1
        elif value==run_value: run_length+=1
        else: run_value=value; run_length=1
        h=((h<<1)+_GEAR[value])&_U64_MASK
        if position+1<WINDOW: continue
        positions+=1
        rd=run_length>=max(MIN_RUN,WINDOW)
        sparse=not(h&ANCHOR_MASK) and not rd
        if sparse and active:
            pulse(); active=False; last_emit=None
        states.append((h,position))
        if sparse:
            anchors+=1; last_sparse=position; continue
        if rd: continue
        gap=position-last_sparse if last_sparse is not None else position+1-WINDOW
        if gap>=MINIMIZER_SPAN and not active and len(states)==MINIMIZER_SPAN:
            pulse(); active=True
    if active: pulse()
    return trace,h,positions,anchors


def _build():
    here=Path(__file__).parent; td=tempfile.TemporaryDirectory(prefix="cmpct-one-g02-edgepulse-")
    lib=Path(td.name)/"lib.so"
    subprocess.run([os.environ.get("CC","cc"),"-O3","-std=c11","-fPIC","-shared",
        str(here/"one_g02_minimizer_segmented_counter_kernel.c"),
        str(here/"one_g02_minimizer_offset_only_kernel.c"),
        str(here/"one_g02_minimizer_size_dispatch_tail_kernel.c"),
        str(here/"one_g02_starvation_compact_queue_kernel.c"),
        str(here/"one_g02_starvation_edge_pulse_kernel.c"),"-o",str(lib)],check=True,
        stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    return ctypes.CDLL(str(lib)),td


def _paired(a,b):
    ratios=[]; ans=[]; bns=[]
    for i in range(ROUNDS):
        if i%2==0:
            t=time.perf_counter_ns(); a(); x=time.perf_counter_ns()-t
            t=time.perf_counter_ns(); b(); y=time.perf_counter_ns()-t
        else:
            t=time.perf_counter_ns(); b(); y=time.perf_counter_ns()-t
            t=time.perf_counter_ns(); a(); x=time.perf_counter_ns()-t
        ans.append(x); bns.append(y); ratios.append(y/x)
    return ratios,ans,bns


def run():
    lib,td=_build()
    try:
        promoted=_bind_dispatch(lib); compact=_bind_compact(lib,"one_g02_starvation_compact_queue_kernel")
        pulse=_bind_pulse(lib); gear=(ctypes.c_uint64*256)(*_GEAR); rows=[]
        for name,data in _cases().items():
            arr=(ctypes.c_uint8*len(data)).from_buffer_copy(data); cap=max(1,len(data)); tr=(ctypes.c_uint64*cap)()
            po=_call_pulse(pulse,gear,arr,len(data),tr,cap); oracle=_oracle(data)
            actual=[int(tr[i]) for i in range(int(po.emitted))]
            exact=(actual==oracle[0] and int(po.final_state)==oracle[1]
                   and int(po.positions_considered)==oracle[2] and int(po.sparse_anchors)==oracle[3])
            if not exact: raise AssertionError((name,"edge-pulse native/oracle mismatch",actual,oracle[0]))
            bo=_call_dispatch(promoted,gear,arr,len(data)); co=_call_compact(compact,gear,arr,len(data))
            ep,_,_= _paired(lambda:_call_dispatch(promoted,gear,arr,len(data)),lambda:_call_pulse(pulse,gear,arr,len(data)))
            ec,_,_= _paired(lambda:_call_compact(compact,gear,arr,len(data)),lambda:_call_pulse(pulse,gear,arr,len(data)))
            rows.append({"case":name,"input_bytes":len(data),"exact_native_oracle":exact,
                "median_edge_over_promoted":statistics.median(ep),"p90_edge_over_promoted":sorted(ep)[int(.9*(ROUNDS-1))],
                "median_edge_over_compact":statistics.median(ec),
                "edge_state_bytes":int(po.reserved_state_bytes),"promoted_state_bytes":int(bo.reserved_state_bytes),
                "compact_state_bytes":int(co.reserved_state_bytes),"edge_over_promoted_state":int(po.reserved_state_bytes)/int(bo.reserved_state_bytes),
                "pulses":int(po.pulses),"replayed_history_bytes":int(po.replayed_history_bytes),"emitted":int(po.emitted)})
        m={r["case"]:r for r in rows}
        large_ok=(m["random_1mib"]["median_edge_over_promoted"]<=.98 and m["zlib_random_1mib"]["median_edge_over_promoted"]<=.98
                  and m["repeat_64k_basis_1mib"]["median_edge_over_promoted"]<=1.02 and m["shifted_512k_insert1"]["median_edge_over_promoted"]<=1.02
                  and max(m[k]["median_edge_over_promoted"] for k in ("random_1mib","zlib_random_1mib","repeat_64k_basis_1mib","shifted_512k_insert1"))<=1.05)
        state_ok=all(r["edge_over_promoted_state"]<=.20 for r in rows if r["input_bytes"]>=8192)
        hard=m["transfer_starved_seed10_insert1"]
        hard_ok=hard["median_edge_over_promoted"]<=1.20 and hard["median_edge_over_compact"]<=.65
        decision="advance_edge_pulse_to_broad_opportunity_transfer" if large_ok and state_ok and hard_ok else "retire_native_edge_pulse_scheduling_shape"
        return {"schema":"cmpct-one-g02-starvation-edge-pulse-native-ab-v1","experimental_version":"ONE-G0.2",
            "source_sha":os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound","rounds":ROUNDS,
            "frozen_gate":{"entropy_max":.98,"repeat_shift_max":1.02,"large_retire":1.05,"state_max":.20,"hard_promoted_max":1.20,"hard_compact_max":.65},
            "decision":decision,"claim_boundary":"native encoder-discovery scheduling evidence only; broad opportunity transfer remains required","rows":rows}
    finally: td.cleanup()

if __name__=="__main__": print(json.dumps(run(),indent=2,sort_keys=True))
