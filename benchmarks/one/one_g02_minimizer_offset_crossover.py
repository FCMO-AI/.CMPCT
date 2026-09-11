"""ONE-G0.2 exploratory crossover map for offset-only dense suffix state.

This instrument is deliberately not a promotion gate.  The prior exact-head A/B showed a
large-input Pareto signal (less state and lower elapsed) but startup regressions.  To avoid
choosing a size threshold after seeing only two small and five 1 MiB rows, freeze a geometric
size ladder and independent regimes, then map counter-vs-offset elapsed while preserving the
exact anchor oracle.  A later Builder may preregister a dispatch threshold from this evidence;
this instrument itself grants no dispatch or product authority.
"""
from __future__ import annotations
import ctypes, json, os, random, statistics, subprocess, tempfile, zlib
from pathlib import Path
from benchmarks.one.one_g02_gear_replacement_ab import _GEAR
from benchmarks.one.one_g02_minimizer_block_ab import _median_ns, _python_anchor_trace
from benchmarks.one.one_g02_minimizer_counter_ab import _bind_counter, _call_counter
from benchmarks.one.one_g02_minimizer_offset_only_ab import _OffsetOnlyResult, _bind_offset, _call_offset
from benchmarks.one.one_g02_minimizer_native_probe import MINIMIZER_SPAN, WINDOW

SIZES=(4159,4160,8192,16384,32768,65536,131072,262144,524288,1048576)

def _build():
    here=Path(__file__).parent;td=tempfile.TemporaryDirectory(prefix="cmpct-one-g02-offset-cross-");lib=Path(td.name)/"lib.so"
    subprocess.run([os.environ.get("CC","cc"),"-O3","-std=c11","-fPIC","-shared",str(here/"one_g02_minimizer_segmented_counter_kernel.c"),str(here/"one_g02_minimizer_offset_only_kernel.c"),"-o",str(lib)],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE);return ctypes.CDLL(str(lib)),td

def _payloads(size:int):
    rnd=random.Random(0xC0FFEE+size).randbytes(size)
    basis=random.Random(0x51A7).randbytes(4096)
    repeated=(basis*((size+len(basis)-1)//len(basis)))[:size]
    compressed=zlib.compress(random.Random(0xBADC0DE+size).randbytes(size),9)
    return {"random":rnd,"repeated_4k_basis":repeated,"zlib_random":compressed}

def run():
    lib,td=_build()
    try:
        cfn=_bind_counter(lib);ofn=_bind_offset(lib);gear=(ctypes.c_uint64*256)(*_GEAR);rows=[]
        for requested in SIZES:
            for regime,data in _payloads(requested).items():
                arr=(ctypes.c_uint8*len(data)).from_buffer_copy(data);expected,state,considered=_python_anchor_trace(data);cap=max(1,len(data));ct=(ctypes.c_uint64*cap)();ot=(ctypes.c_uint64*cap)();c=_call_counter(cfn,gear,arr,len(data),ct,cap);o=_call_offset(ofn,gear,arr,len(data),ot,cap)
                if [int(ct[i]) for i in range(int(c.emitted))]!=expected or [int(ot[i]) for i in range(int(o.emitted))]!=expected or int(c.final_state)!=state or int(o.final_state)!=state or int(c.positions_considered)!=considered or int(o.positions_considered)!=considered: raise AssertionError((requested,regime))
                cn=_median_ns(lambda:_call_counter(cfn,gear,arr,len(data)));on=_median_ns(lambda:_call_offset(ofn,gear,arr,len(data)));rows.append({"requested_size":requested,"actual_input_bytes":len(data),"regime":regime,"counter_median_ns":cn,"offset_median_ns":on,"offset_over_counter_ratio":on/cn,"counter_reserved_state_bytes":int(c.reserved_state_bytes),"offset_reserved_state_bytes":int(o.reserved_state_bytes),"source_byte_rescans":0})
        by_size={}
        for s in SIZES:
            rr=[r["offset_over_counter_ratio"] for r in rows if r["requested_size"]==s];by_size[str(s)]={"median_ratio":statistics.median(rr),"worst_ratio":max(rr),"all_non_regressing":all(x<=1.0 for x in rr)}
        return {"schema":"cmpct-one-g02-offset-crossover-v1","experimental_version":"ONE-G0.2","source_sha":os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound","frozen_requested_sizes":SIZES,"regimes":["random","repeated_4k_basis","zlib_random"],"purpose":"exploratory crossover map only; no threshold or promotion may be inferred without a new freeze","summary_by_requested_size":by_size,"rows":rows}
    finally:td.cleanup()
if __name__=="__main__":print(json.dumps(run(),sort_keys=True,indent=2))
