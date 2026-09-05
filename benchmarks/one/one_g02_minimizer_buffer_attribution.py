"""ONE-G0.2 diagnostic: split derived-state storage from prefix/block-minimum cost.

Non-semantic ablation only. No promotion decision or compression/product claim.
"""
from __future__ import annotations
import ctypes, json, os, subprocess, tempfile
from pathlib import Path
from benchmarks.one.one_g02_gear_replacement_ab import _GEAR
from benchmarks.one.one_g02_minimizer_block_ab import _median_ns, _python_anchor_trace
from benchmarks.one.one_g02_minimizer_native_probe import _cases, MINIMIZER_SPAN, WINDOW
from benchmarks.one.one_g02_minimizer_segmented_residual import _bind_gear, _call_gear
from benchmarks.one.one_g02_minimizer_wrap_ab import LARGE_CASES
from benchmarks.one.one_g02_minimizer_cost_ladder import _CostResult, _bind_cost, _call_cost

class _AttrResult(ctypes.Structure):
    _fields_=[("final_state",ctypes.c_uint64),("positions_considered",ctypes.c_uint64),("reserved_state_bytes",ctypes.c_uint64),("checksum",ctypes.c_uint64)]

def _build():
    here=Path(__file__).parent
    td=tempfile.TemporaryDirectory(prefix="cmpct-one-g02-buffer-attr-")
    so=Path(td.name)/"lib.so"
    subprocess.run([os.environ.get("CC","cc"),"-O3","-std=c11","-fPIC","-shared",
        str(here/"one_g02_minimizer_kernel.c"),str(here/"one_g02_minimizer_cost_ladder.c"),str(here/"one_g02_minimizer_buffer_attribution.c"),"-o",str(so)],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    return ctypes.CDLL(str(so)),td

def _bind(lib,name):
    fn=getattr(lib,name); fn.argtypes=[ctypes.POINTER(ctypes.c_uint8),ctypes.c_size_t,ctypes.POINTER(ctypes.c_uint64),ctypes.c_size_t,ctypes.c_size_t,ctypes.POINTER(_AttrResult)]; fn.restype=ctypes.c_int; return fn

def _call(fn,gear,data,n):
    out=_AttrResult(); rc=fn(data,n,gear,WINDOW,MINIMIZER_SPAN,ctypes.byref(out))
    if rc: raise RuntimeError(f"buffer-attribution kernel failed: {rc}")
    return out

def run():
    lib,td=_build()
    try:
        gear_fn=_bind_gear(lib); store_fn=_bind(lib,"one_g02_store_only_cost_kernel"); prefix_fn=_bind(lib,"one_g02_prefix_only_cost_kernel"); both_fn=_bind_cost(lib,"one_g02_buffer_prefix_cost_kernel")
        gear=(ctypes.c_uint64*256)(*_GEAR); rows=[]
        for name,data in _cases().items():
            if name not in LARGE_CASES: continue
            arr=(ctypes.c_uint8*len(data)).from_buffer_copy(data); _,state,considered=_python_anchor_trace(data)
            arms=[_call_gear(gear_fn,gear,arr,len(data)),_call(store_fn,gear,arr,len(data)),_call(prefix_fn,gear,arr,len(data)),_call_cost(both_fn,gear,arr,len(data))]
            if any(int(x.final_state)!=state or int(x.positions_considered)!=considered for x in arms): raise AssertionError(f"recurrence/count mismatch for {name}")
            g=_median_ns(lambda:_call_gear(gear_fn,gear,arr,len(data))); s=_median_ns(lambda:_call(store_fn,gear,arr,len(data))); p=_median_ns(lambda:_call(prefix_fn,gear,arr,len(data))); b=_median_ns(lambda:_call_cost(both_fn,gear,arr,len(data)))
            rows.append({"case":name,"input_bytes":len(data),"gear_ns":g,"store_only_ns":s,"prefix_only_ns":p,"store_plus_prefix_ns":b,"store_incremental_ns_per_byte":(s-g)/len(data),"prefix_incremental_ns_per_byte":(p-g)/len(data),"combined_incremental_ns_per_byte":(b-g)/len(data),"combined_over_gear_ratio":b/g,"source_byte_rescans":0})
        return {"schema":"cmpct-one-g02-minimizer-buffer-attribution-v1","experimental_version":"ONE-G0.2","source_sha":os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound","purpose":"same-run split of derived-state store traffic versus prefix/block-minimum bookkeeping; diagnostic only","rows":rows}
    finally: td.cleanup()
if __name__=="__main__": print(json.dumps(run(),sort_keys=True,indent=2))
