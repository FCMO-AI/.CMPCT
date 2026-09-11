"""ONE-G0.2 diagnostic: re-attribute residual cost after counter promotion.

The old ladder contained runtime q/r division in every post-Gear arm and is now historical.
This ladder uses monotone block counters in both non-semantic ablation arms and compares them
with the exact promoted counter selector.  It chooses no implementation by itself.
"""
from __future__ import annotations
import ctypes, json, os, statistics, subprocess, tempfile
from pathlib import Path
from benchmarks.one.one_g02_gear_replacement_ab import _GEAR
from benchmarks.one.one_g02_minimizer_block_ab import _median_ns, _python_anchor_trace
from benchmarks.one.one_g02_minimizer_counter_ab import _bind_counter, _call_counter
from benchmarks.one.one_g02_minimizer_native_probe import _cases, MINIMIZER_SPAN, WINDOW
from benchmarks.one.one_g02_minimizer_segmented_residual import _bind_gear, _call_gear
from benchmarks.one.one_g02_minimizer_wrap_ab import LARGE_CASES

class _CostResult(ctypes.Structure):
    _fields_=[("final_state",ctypes.c_uint64),("positions_considered",ctypes.c_uint64),("reserved_state_bytes",ctypes.c_uint64),("derived_state_reads",ctypes.c_uint64),("suffix_blocks_built",ctypes.c_uint64),("suffix_blocks_skipped_dead",ctypes.c_uint64),("checksum",ctypes.c_uint64)]

def _build():
    here=Path(__file__).parent; td=tempfile.TemporaryDirectory(prefix="cmpct-one-g02-counter-cost-"); lib=Path(td.name)/"lib.so"
    subprocess.run([os.environ.get("CC","cc"),"-O3","-std=c11","-fPIC","-shared",str(here/"one_g02_minimizer_kernel.c"),str(here/"one_g02_minimizer_counter_cost_ladder.c"),str(here/"one_g02_minimizer_segmented_counter_kernel.c"),"-o",str(lib)],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    return ctypes.CDLL(str(lib)),td

def _bind(lib,name):
    fn=getattr(lib,name);fn.argtypes=[ctypes.POINTER(ctypes.c_uint8),ctypes.c_size_t,ctypes.POINTER(ctypes.c_uint64),ctypes.c_size_t,ctypes.c_size_t,ctypes.POINTER(_CostResult)];fn.restype=ctypes.c_int;return fn

def _call(fn,gear,data,n):
    out=_CostResult();rc=fn(data,n,gear,WINDOW,MINIMIZER_SPAN,ctypes.byref(out));
    if rc: raise RuntimeError(f"counter cost kernel failed: {rc}")
    return out

def run():
    lib,td=_build()
    try:
        gearfn=_bind_gear(lib);buffn=_bind(lib,"one_g02_counter_buffer_prefix_cost_kernel");suffn=_bind(lib,"one_g02_counter_dense_suffix_cost_kernel");exactfn=_bind_counter(lib);gear=(ctypes.c_uint64*256)(*_GEAR);rows=[]
        for name,data in _cases().items():
            if name not in LARGE_CASES: continue
            arr=(ctypes.c_uint8*len(data)).from_buffer_copy(data); trace,state,considered=_python_anchor_trace(data)
            g=_call_gear(gearfn,gear,arr,len(data));b=_call(buffn,gear,arr,len(data));s=_call(suffn,gear,arr,len(data));e=_call_counter(exactfn,gear,arr,len(data))
            if any(int(x.final_state)!=state or int(x.positions_considered)!=considered for x in (g,b,s,e)) or int(e.emitted)!=len(trace): raise AssertionError(name)
            gn=_median_ns(lambda:_call_gear(gearfn,gear,arr,len(data)));bn=_median_ns(lambda:_call(buffn,gear,arr,len(data)));sn=_median_ns(lambda:_call(suffn,gear,arr,len(data)));en=_median_ns(lambda:_call_counter(exactfn,gear,arr,len(data)))
            rows.append({"case":name,"input_bytes":len(data),"gear_only_median_ns":gn,"counter_buffer_prefix_median_ns":bn,"counter_dense_suffix_no_selection_median_ns":sn,"counter_exact_median_ns":en,"buffer_incremental_ns_per_byte":(bn-gn)/len(data),"suffix_incremental_ns_per_byte":(sn-bn)/len(data),"selection_incremental_ns_per_byte":(en-sn)/len(data),"counter_exact_over_gear_ratio":en/gn,"source_byte_rescans":0})
        med={k:statistics.median(r[k] for r in rows) for k in ("buffer_incremental_ns_per_byte","suffix_incremental_ns_per_byte","selection_incremental_ns_per_byte")}
        owner=max(med,key=med.get)
        out=os.environ.get("GITHUB_OUTPUT")
        if out:
            with open(out,"a",encoding="utf-8") as f:f.write(f"dominant_owner={owner}\n");f.write(f"median_exact_over_gear={statistics.median(r['counter_exact_over_gear_ratio'] for r in rows):.6f}\n")
        return {"schema":"cmpct-one-g02-counter-cost-ladder-v1","experimental_version":"ONE-G0.2","source_sha":os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound","median_incremental_ns_per_byte":med,"dominant_owner":owner,"interpretation_rule":"post-counter non-semantic cost ablations; choose next causal Builder only","rows":rows}
    finally:td.cleanup()
if __name__=="__main__":print(json.dumps(run(),sort_keys=True,indent=2))
