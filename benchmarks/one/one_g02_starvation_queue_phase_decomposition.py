"""ONE-G0.2 queue construction-vs-maintenance decomposition.

Referee freeze: the previous immutable result established queue work as the dominant exported
cost over bounded replay. This experiment asks whether that cost is primarily activation-time
construction or active-run maintenance/emission bookkeeping.

Disproof/decision freeze on both entropy-dense controls:
- semantic accounting mismatch rejects the instrument;
- build-only/replay-only >=1.10 and full/build-only <1.10 => construction-primary;
- build-only/replay-only <1.10 and full/build-only >=1.10 => maintenance-primary;
- both >=1.10 => co-dominant;
- both <1.10 => decomposition inconclusive.
No product-speed, stored-byte, reader, comparator, or release authority.
"""
from __future__ import annotations
import ctypes, json, os, statistics, subprocess, tempfile, time
from pathlib import Path
from benchmarks.one.one_g02_gear_replacement_ab import _GEAR, WINDOW
from benchmarks.one.one_g02_minimizer_native_probe import MINIMIZER_SPAN
from benchmarks.one.one_g02_starvation_native_cost_decomposition import ROUNDS, _cases
from benchmarks.one.one_g02_starvation_replay_queue_decomposition import _ReplayResult
from benchmarks.one.one_g02_starvation_byte_history_native_ab import _bind_gate, _call_gate

class _BuildResult(ctypes.Structure):
    _fields_=[("final_state",ctypes.c_uint64),("positions_considered",ctypes.c_uint64),
      ("sparse_anchors",ctypes.c_uint64),("rescue_active_positions",ctypes.c_uint64),
      ("activation_events",ctypes.c_uint64),("replayed_history_bytes",ctypes.c_uint64),
      ("built_queue_entries",ctypes.c_uint64),("peak_queue_entries",ctypes.c_uint64),
      ("build_checksum",ctypes.c_uint64),("reserved_state_bytes",ctypes.c_uint64)]

def _buildlib():
    here=Path(__file__).parent; td=tempfile.TemporaryDirectory(prefix="cmpct-one-g02-qphase-"); lib=Path(td.name)/"lib.so"
    subprocess.run([os.environ.get("CC","cc"),"-O3","-std=c11","-fPIC","-shared",
      str(here/"one_g02_starvation_replay_only_kernel.c"),str(here/"one_g02_starvation_queue_build_only_kernel.c"),
      str(here/"one_g02_starvation_byte_history_kernel.c"),"-o",str(lib)],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    return ctypes.CDLL(str(lib)),td

def _bind_replay(lib):
    f=lib.one_g02_starvation_replay_only_kernel; f.argtypes=[ctypes.POINTER(ctypes.c_uint8),ctypes.c_size_t,ctypes.POINTER(ctypes.c_uint64),ctypes.c_size_t,ctypes.c_size_t,ctypes.POINTER(_ReplayResult)]; f.restype=ctypes.c_int; return f

def _bind_build(lib):
    f=lib.one_g02_starvation_queue_build_only_kernel; f.argtypes=[ctypes.POINTER(ctypes.c_uint8),ctypes.c_size_t,ctypes.POINTER(ctypes.c_uint64),ctypes.c_size_t,ctypes.c_size_t,ctypes.POINTER(_BuildResult)]; f.restype=ctypes.c_int; return f

def _call(f, typ, gear, arr, n):
    out=typ(); rc=f(arr,n,gear,WINDOW,MINIMIZER_SPAN,ctypes.byref(out));
    if rc: raise RuntimeError((f,rc))
    return out

def _rat(a,b):
    xs=[]
    for i in range(ROUNDS):
      if i%2==0:
        t=time.perf_counter_ns(); a(); ta=time.perf_counter_ns()-t; t=time.perf_counter_ns(); b(); tb=time.perf_counter_ns()-t
      else:
        t=time.perf_counter_ns(); b(); tb=time.perf_counter_ns()-t; t=time.perf_counter_ns(); a(); ta=time.perf_counter_ns()-t
      xs.append(tb/ta)
    return xs

def run():
    lib,td=_buildlib()
    try:
      rf=_bind_replay(lib); bf=_bind_build(lib); ff=_bind_gate(lib); gear=(ctypes.c_uint64*256)(*_GEAR); rows=[]
      for name,data in _cases().items():
        arr=(ctypes.c_uint8*len(data)).from_buffer_copy(data); r=_call(rf,_ReplayResult,gear,arr,len(data)); b=_call(bf,_BuildResult,gear,arr,len(data)); f=_call_gate(ff,gear,arr,len(data))
        equal=(r.final_state==b.final_state==f.final_state and r.positions_considered==b.positions_considered==f.positions_considered and r.sparse_anchors==b.sparse_anchors==f.sparse_anchors and r.rescue_active_positions==b.rescue_active_positions==f.rescue_active_positions and r.replayed_history_bytes==b.replayed_history_bytes==f.replayed_history_bytes)
        if not equal: raise AssertionError((name,"phase accounting mismatch"))
        br=_rat(lambda:_call(rf,_ReplayResult,gear,arr,len(data)),lambda:_call(bf,_BuildResult,gear,arr,len(data)))
        fb=_rat(lambda:_call(bf,_BuildResult,gear,arr,len(data)),lambda:_call_gate(ff,gear,arr,len(data)))
        rows.append({"case":name,"input_bytes":len(data),"semantic_accounting_equal":equal,
          "median_build_only_over_replay_only":statistics.median(br),"p90_build_only_over_replay_only":sorted(br)[int(.9*(len(br)-1))],
          "median_full_over_build_only":statistics.median(fb),"p90_full_over_build_only":sorted(fb)[int(.9*(len(fb)-1))],
          "activation_events":int(b.activation_events),"built_queue_entries":int(b.built_queue_entries),"peak_queue_entries_after_build":int(b.peak_queue_entries),"full_peak_queue_entries":int(f.peak_queue_entries),"reserved_state_bytes":int(b.reserved_state_bytes)})
      m={x["case"]:x for x in rows}; es=[m["random_1mib"],m["zlib_random_1mib"]]
      c=all(x["median_build_only_over_replay_only"]>=1.10 for x in es); maint=all(x["median_full_over_build_only"]>=1.10 for x in es)
      decision="queue_construction_and_maintenance_codominant" if c and maint else "advance_queue_construction_owner_attack" if c else "advance_queue_maintenance_owner_attack" if maint else "queue_phase_decomposition_inconclusive"
      return {"schema":"cmpct-one-g02-starvation-queue-phase-decomposition-v1","experimental_version":"ONE-G0.2","source_sha":os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound","rounds":ROUNDS,"hypothesis":"queue work can be causally partitioned into activation-time construction and active-run maintenance","decision":decision,"claim_boundary":"native encoder-discovery causal decomposition only; no product/comparator/release authority","rows":rows}
    finally: td.cleanup()
if __name__=="__main__": print(json.dumps(run(),indent=2,sort_keys=True))
