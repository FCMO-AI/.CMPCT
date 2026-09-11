"""ONE-G0.2 exact byte-history rescue: linear construction vs generic ring construction.

Referee freeze before result-bearing execution
==============================================
Prior exact-head causal evidence isolates activation-time monotonic-queue construction as the
primary queue-cost owner: +21.1/+21.4% over replay-only on the entropy controls, versus only
+7.1/+7.3% for post-build maintenance. During activation construction the queue head is zero
and no expiry can occur, so ring modulo addressing is semantically unnecessary until build
completion.

Hypothesis: a specialized linear monotonic-stack build preserves the exact full rescue trace
while removing enough construction overhead to reduce full-rescue elapsed by >=5% on both
entropy-dense 1 MiB controls, with no tested-case regression >5% and identical reserved state.
Failure retires this local construction specialization; it does not reopen threshold tuning.
No product-speed, stored-byte, reader, comparator or release authority.
"""
from __future__ import annotations
import ctypes, json, os, statistics, subprocess, tempfile, time
from pathlib import Path
from benchmarks.one.one_g02_gear_replacement_ab import _GEAR, WINDOW
from benchmarks.one.one_g02_minimizer_native_probe import MINIMIZER_SPAN
from benchmarks.one.one_g02_starvation_native_cost_decomposition import ROUNDS, _cases
from benchmarks.one.one_g02_starvation_byte_history_native_ab import _GateResult, _bind_gate, _call_gate

class _LinearResult(ctypes.Structure):
    _fields_=[("emitted",ctypes.c_uint64),("final_state",ctypes.c_uint64),
      ("positions_considered",ctypes.c_uint64),("sparse_anchors",ctypes.c_uint64),
      ("rescue_active_positions",ctypes.c_uint64),("replayed_history_bytes",ctypes.c_uint64),
      ("peak_queue_entries",ctypes.c_uint64),("reserved_state_bytes",ctypes.c_uint64)]

def _build():
    here=Path(__file__).parent; td=tempfile.TemporaryDirectory(prefix="cmpct-one-g02-linear-build-"); lib=Path(td.name)/"lib.so"
    subprocess.run([os.environ.get("CC","cc"),"-O3","-std=c11","-fPIC","-shared",
      str(here/"one_g02_starvation_byte_history_kernel.c"),str(here/"one_g02_starvation_linear_build_kernel.c"),"-o",str(lib)],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    return ctypes.CDLL(str(lib)),td

def _bind_linear(lib):
    f=lib.one_g02_starvation_linear_build_kernel; f.argtypes=[ctypes.POINTER(ctypes.c_uint8),ctypes.c_size_t,ctypes.POINTER(ctypes.c_uint64),ctypes.c_size_t,ctypes.c_size_t,ctypes.POINTER(_LinearResult),ctypes.POINTER(ctypes.c_uint64),ctypes.c_size_t]; f.restype=ctypes.c_int; return f

def _call_linear(f,gear,arr,n,trace=None,capacity=0):
    o=_LinearResult(); rc=f(arr,n,gear,WINDOW,MINIMIZER_SPAN,ctypes.byref(o),trace,capacity)
    if rc: raise RuntimeError(rc)
    return o

def _rat(base,cand):
    xs=[]
    for i in range(ROUNDS):
      if i%2==0:
        t=time.perf_counter_ns(); base(); a=time.perf_counter_ns()-t; t=time.perf_counter_ns(); cand(); b=time.perf_counter_ns()-t
      else:
        t=time.perf_counter_ns(); cand(); b=time.perf_counter_ns()-t; t=time.perf_counter_ns(); base(); a=time.perf_counter_ns()-t
      xs.append(b/a)
    return xs

def run():
    lib,td=_build()
    try:
      base=_bind_gate(lib); cand=_bind_linear(lib); gear=(ctypes.c_uint64*256)(*_GEAR); rows=[]; all_equal=True
      for name,data in _cases().items():
        arr=(ctypes.c_uint8*len(data)).from_buffer_copy(data); cap=max(1,len(data)); bt=(ctypes.c_uint64*cap)(); ct=(ctypes.c_uint64*cap)()
        b=_call_gate(base,gear,arr,len(data),bt,cap); c=_call_linear(cand,gear,arr,len(data),ct,cap)
        trace_equal=int(b.emitted)==int(c.emitted) and [int(bt[i]) for i in range(int(b.emitted))]==[int(ct[i]) for i in range(int(c.emitted))]
        equal=trace_equal and b.final_state==c.final_state and b.positions_considered==c.positions_considered and b.sparse_anchors==c.sparse_anchors and b.rescue_active_positions==c.rescue_active_positions and b.replayed_history_bytes==c.replayed_history_bytes and b.reserved_state_bytes==c.reserved_state_bytes
        if not equal: raise AssertionError((name,"linear build semantic/accounting mismatch"))
        xs=_rat(lambda:_call_gate(base,gear,arr,len(data)),lambda:_call_linear(cand,gear,arr,len(data)))
        rows.append({"case":name,"input_bytes":len(data),"trace_and_accounting_equal":equal,"median_linear_over_generic":statistics.median(xs),"p90_linear_over_generic":sorted(xs)[int(.9*(len(xs)-1))],"generic_reserved_state_bytes":int(b.reserved_state_bytes),"linear_reserved_state_bytes":int(c.reserved_state_bytes),"peak_queue_entries":int(c.peak_queue_entries),"replayed_history_bytes":int(c.replayed_history_bytes)})
      m={x["case"]:x for x in rows}; entropy=[m["random_1mib"],m["zlib_random_1mib"]]
      promote=all(x["median_linear_over_generic"]<=.95 for x in entropy) and all(x["median_linear_over_generic"]<=1.05 for x in rows)
      return {"schema":"cmpct-one-g02-starvation-linear-build-ab-v1","experimental_version":"ONE-G0.2","source_sha":os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound","rounds":ROUNDS,"frozen_promotion_entropy_ratio":.95,"frozen_max_case_ratio":1.05,"hypothesis":"linear activation-time monotonic-stack construction removes >=5% full-rescue elapsed on both entropy controls without semantic/state change","decision":"advance_linear_queue_build_for_integration_review" if promote else "retire_linear_queue_build_specialization","claim_boundary":"native encoder-discovery A/B only; no product/comparator/release authority","rows":rows}
    finally: td.cleanup()
if __name__=="__main__": print(json.dumps(run(),indent=2,sort_keys=True))
