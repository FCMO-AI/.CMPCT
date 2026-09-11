"""ONE-G0.2 compact-position rescue queue A/B.

Referee freeze before result-bearing execution
==============================================
The promoted linear activation build preserves exact byte-history rescue semantics and removes
~10% full-rescue elapsed on the entropy controls, but still reserves 71,680 B because every
possible queue slot stores a u64 value plus u64 absolute position. A live 4,096-span queue
never needs an age >=4,096. With modulus 8,192 (>2*max-live-age-1), current_position mod 8192
and entry_position mod 8192 uniquely recover every live age. The candidate therefore keeps
u64 values but stores position modulo 8192 in a separate u16 array and reconstructs emitted
absolute positions from current position minus modular age.

Hypothesis: compact positions preserve the exact full rescue nomination trace and accounting,
reduce reserved state by >=30%, and do not trade that state win for material compute loss.

Frozen promotion:
- exact trace/state/accounting equality on every case;
- candidate reserved state <=0.70 * linear baseline state;
- median compact/linear <=1.03 on both entropy controls and shifted large case;
- no tested median >1.10;
- exact hostile wrap vectors crossing 8192 and 16384 absolute positions are included.
Failure retires compact modulo-position storage as this implementation; no threshold tuning.
No product-speed, stored-byte, reader, comparator, or release authority.
"""
from __future__ import annotations
import ctypes, json, os, random, statistics, subprocess, tempfile, time, zlib
from pathlib import Path
from benchmarks.one.one_g02_gear_replacement_ab import _GEAR, WINDOW
from benchmarks.one.one_g02_minimizer_native_probe import MINIMIZER_SPAN
from benchmarks.one.one_g02_starvation_native_cost_decomposition import ROUNDS, _cases

class _R(ctypes.Structure):
    _fields_=[("emitted",ctypes.c_uint64),("final_state",ctypes.c_uint64),
      ("positions_considered",ctypes.c_uint64),("sparse_anchors",ctypes.c_uint64),
      ("rescue_active_positions",ctypes.c_uint64),("replayed_history_bytes",ctypes.c_uint64),
      ("peak_queue_entries",ctypes.c_uint64),("reserved_state_bytes",ctypes.c_uint64)]

def _build():
    h=Path(__file__).parent; td=tempfile.TemporaryDirectory(prefix="cmpct-one-g02-cq-"); lib=Path(td.name)/"lib.so"
    subprocess.run([os.environ.get("CC","cc"),"-O3","-std=c11","-fPIC","-shared",
      str(h/"one_g02_starvation_linear_build_kernel.c"),str(h/"one_g02_starvation_compact_queue_kernel.c"),"-o",str(lib)],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    return ctypes.CDLL(str(lib)),td

def _bind(lib,name):
    f=getattr(lib,name); f.argtypes=[ctypes.POINTER(ctypes.c_uint8),ctypes.c_size_t,ctypes.POINTER(ctypes.c_uint64),ctypes.c_size_t,ctypes.c_size_t,ctypes.POINTER(_R),ctypes.POINTER(ctypes.c_uint64),ctypes.c_size_t]; f.restype=ctypes.c_int; return f

def _call(f,g,a,n,t=None,c=0):
    o=_R(); rc=f(a,n,g,WINDOW,MINIMIZER_SPAN,ctypes.byref(o),t,c)
    if rc: raise RuntimeError((rc,n))
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

def _all_cases():
    c=dict(_cases())
    # Long shifted controls force absolute anchor positions across multiple modulo epochs.
    for n,seed in [(20000,9911),(40000,9912)]:
      base=random.Random(seed).randbytes(n)
      c[f"wrap_shifted_{n}"]=base+b"X"+base
    return c

def run():
    lib,td=_build()
    try:
      lin=_bind(lib,"one_g02_starvation_linear_build_kernel"); cq=_bind(lib,"one_g02_starvation_compact_queue_kernel"); gear=(ctypes.c_uint64*256)(*_GEAR); rows=[]
      for name,data in _all_cases().items():
        a=(ctypes.c_uint8*len(data)).from_buffer_copy(data); cap=max(1,len(data)); lt=(ctypes.c_uint64*cap)(); ct=(ctypes.c_uint64*cap)()
        l=_call(lin,gear,a,len(data),lt,cap); q=_call(cq,gear,a,len(data),ct,cap)
        trace=[int(lt[i]) for i in range(int(l.emitted))]; qtrace=[int(ct[i]) for i in range(int(q.emitted))]
        equal=(trace==qtrace and l.final_state==q.final_state and l.positions_considered==q.positions_considered and l.sparse_anchors==q.sparse_anchors and l.rescue_active_positions==q.rescue_active_positions and l.replayed_history_bytes==q.replayed_history_bytes and l.peak_queue_entries==q.peak_queue_entries)
        if not equal: raise AssertionError((name,"compact queue semantic/accounting mismatch",trace[:20],qtrace[:20]))
        xs=_rat(lambda:_call(lin,gear,a,len(data)),lambda:_call(cq,gear,a,len(data)))
        rows.append({"case":name,"input_bytes":len(data),"trace_and_accounting_equal":equal,"median_compact_over_linear":statistics.median(xs),"p90_compact_over_linear":sorted(xs)[int(.9*(len(xs)-1))],"linear_reserved_state_bytes":int(l.reserved_state_bytes),"compact_reserved_state_bytes":int(q.reserved_state_bytes),"state_ratio":int(q.reserved_state_bytes)/int(l.reserved_state_bytes),"peak_queue_entries":int(q.peak_queue_entries),"emitted":int(q.emitted)})
      m={x["case"]:x for x in rows}; critical=[m["random_1mib"],m["zlib_random_1mib"],m["shifted_512k_insert1"]]
      promote=all(x["state_ratio"]<=.70 for x in rows) and all(x["median_compact_over_linear"]<=1.03 for x in critical) and all(x["median_compact_over_linear"]<=1.10 for x in rows)
      return {"schema":"cmpct-one-g02-starvation-compact-queue-ab-v1","experimental_version":"ONE-G0.2","source_sha":os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound","rounds":ROUNDS,"position_modulus":8192,"frozen_max_state_ratio":.70,"frozen_critical_elapsed_ratio":1.03,"frozen_max_case_elapsed_ratio":1.10,"hypothesis":"u16 modulo-8192 queue positions preserve exact 4096-span semantics while reducing state >=30% without material elapsed regression","decision":"advance_compact_queue_for_integration_review" if promote else "retire_compact_queue_position_storage","claim_boundary":"native encoder-discovery A/B only; no product/comparator/release authority","rows":rows}
    finally: td.cleanup()
if __name__=="__main__": print(json.dumps(run(),indent=2,sort_keys=True))
