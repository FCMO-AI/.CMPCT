"""ONE-G0.2 native window-block edge-summary falsifier.

Referee freeze before result-bearing execution
==============================================
Full 4,096-state replay at every starvation edge is retired: it preserved transfer and ran
well on large controls, but remained 1.886x slower than promoted on the 8,193-byte hard row.
The successor attacks that exact causal owner rather than moving semantic thresholds.

The block granularity is not tuned: it is the already-canonical ONE observation WINDOW=64.
Each eligible Gear state updates one 64-position rightmost-min block summary. An exact
4,096-position edge query combines full block summaries and reconstructs only its at-most-two
partial boundary blocks from bounded bytes + checkpoints.

Frozen seed gate:
- exact emitted edge trace/final state/accounting vs the independent Python edge oracle;
- reserved state <=0.25x promoted selector state on every >=8 KiB row;
- hard 8,193-byte block/promoted median <=1.20x and block/full-replay-edge <=0.80x;
- random + zlib-random 1 MiB <=0.98x promoted;
- repeated + shifted large <=1.02x promoted;
- any large row >1.05x retires this summary shape.
No semantic constant or block size may move after result-bearing execution.
"""
from __future__ import annotations

import ctypes, json, os
from pathlib import Path
import statistics, subprocess, tempfile, time

from benchmarks.one.one_g02_gear_replacement_ab import _GEAR, WINDOW
from benchmarks.one.one_g02_minimizer_native_probe import MINIMIZER_SPAN
from benchmarks.one.one_g02_minimizer_size_dispatch_tail_ab import _bind_dispatch, _call_dispatch
from benchmarks.one.one_g02_starvation_byte_history_native_ab import _cases
from benchmarks.one.one_g02_starvation_edge_pulse_native_ab import _oracle, _P, _bind_pulse, _call_pulse

ROUNDS=13

class _B(ctypes.Structure):
    _fields_=[("emitted",ctypes.c_uint64),("final_state",ctypes.c_uint64),
              ("positions_considered",ctypes.c_uint64),("sparse_anchors",ctypes.c_uint64),
              ("queries",ctypes.c_uint64),("reconstructed_boundary_states",ctypes.c_uint64),
              ("scanned_block_summaries",ctypes.c_uint64),("reserved_state_bytes",ctypes.c_uint64)]

def _bind_block(lib):
    fn=lib.one_g02_starvation_block_edge_kernel
    fn.argtypes=[ctypes.POINTER(ctypes.c_uint8),ctypes.c_size_t,ctypes.POINTER(ctypes.c_uint64),
                 ctypes.c_size_t,ctypes.c_size_t,ctypes.POINTER(_B),ctypes.POINTER(ctypes.c_uint64),ctypes.c_size_t]
    fn.restype=ctypes.c_int; return fn

def _call_block(fn,gear,arr,n,trace=None,cap=0):
    out=_B(); rc=fn(arr,n,gear,WINDOW,MINIMIZER_SPAN,ctypes.byref(out),trace if trace is not None else None,cap)
    if rc: raise RuntimeError(f"block edge kernel rc={rc}")
    return out

def _build():
    here=Path(__file__).parent; td=tempfile.TemporaryDirectory(prefix="cmpct-one-g02-blockedge-"); lib=Path(td.name)/"lib.so"
    subprocess.run([os.environ.get("CC","cc"),"-O3","-std=c11","-fPIC","-shared",
        str(here/"one_g02_minimizer_segmented_counter_kernel.c"),str(here/"one_g02_minimizer_offset_only_kernel.c"),
        str(here/"one_g02_minimizer_size_dispatch_tail_kernel.c"),str(here/"one_g02_starvation_edge_pulse_kernel.c"),
        str(here/"one_g02_starvation_block_edge_kernel.c"),"-o",str(lib)],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    return ctypes.CDLL(str(lib)),td

def _paired(a,b):
    ratios=[]
    for i in range(ROUNDS):
        if i%2==0:
            t=time.perf_counter_ns(); a(); x=time.perf_counter_ns()-t; t=time.perf_counter_ns(); b(); y=time.perf_counter_ns()-t
        else:
            t=time.perf_counter_ns(); b(); y=time.perf_counter_ns()-t; t=time.perf_counter_ns(); a(); x=time.perf_counter_ns()-t
        ratios.append(y/x)
    return ratios

def run():
    lib,td=_build()
    try:
        promoted=_bind_dispatch(lib); edge=_bind_pulse(lib); block=_bind_block(lib); gear=(ctypes.c_uint64*256)(*_GEAR); rows=[]
        for name,data in _cases().items():
            arr=(ctypes.c_uint8*len(data)).from_buffer_copy(data); cap=max(1,len(data)); tr=(ctypes.c_uint64*cap)()
            bo=_call_block(block,gear,arr,len(data),tr,cap); oracle=_oracle(data); actual=[int(tr[i]) for i in range(int(bo.emitted))]
            exact=(actual==oracle[0] and int(bo.final_state)==oracle[1] and int(bo.positions_considered)==oracle[2] and int(bo.sparse_anchors)==oracle[3])
            if not exact: raise AssertionError((name,"block-edge/oracle mismatch",actual,oracle[0]))
            po=_call_dispatch(promoted,gear,arr,len(data)); eo=_call_pulse(edge,gear,arr,len(data))
            bp=_paired(lambda:_call_dispatch(promoted,gear,arr,len(data)),lambda:_call_block(block,gear,arr,len(data)))
            be=_paired(lambda:_call_pulse(edge,gear,arr,len(data)),lambda:_call_block(block,gear,arr,len(data)))
            rows.append({"case":name,"input_bytes":len(data),"exact_edge_oracle":exact,
                "median_block_over_promoted":statistics.median(bp),"p90_block_over_promoted":sorted(bp)[int(.9*(ROUNDS-1))],
                "median_block_over_full_replay_edge":statistics.median(be),"block_state_bytes":int(bo.reserved_state_bytes),
                "promoted_state_bytes":int(po.reserved_state_bytes),"full_replay_edge_state_bytes":int(eo.reserved_state_bytes),
                "block_over_promoted_state":int(bo.reserved_state_bytes)/int(po.reserved_state_bytes),
                "queries":int(bo.queries),"reconstructed_boundary_states":int(bo.reconstructed_boundary_states),
                "scanned_block_summaries":int(bo.scanned_block_summaries),"emitted":int(bo.emitted)})
        m={r["case"]:r for r in rows}
        large_ok=(m["random_1mib"]["median_block_over_promoted"]<=.98 and m["zlib_random_1mib"]["median_block_over_promoted"]<=.98
                  and m["repeat_64k_basis_1mib"]["median_block_over_promoted"]<=1.02 and m["shifted_512k_insert1"]["median_block_over_promoted"]<=1.02
                  and max(m[k]["median_block_over_promoted"] for k in ("random_1mib","zlib_random_1mib","repeat_64k_basis_1mib","shifted_512k_insert1"))<=1.05)
        state_ok=all(r["block_over_promoted_state"]<=.25 for r in rows if r["input_bytes"]>=8192)
        hard=m["transfer_starved_seed10_insert1"]; hard_ok=hard["median_block_over_promoted"]<=1.20 and hard["median_block_over_full_replay_edge"]<=.80
        decision="advance_window_block_edge_summary" if large_ok and state_ok and hard_ok else "retire_window_block_edge_summary"
        return {"schema":"cmpct-one-g02-starvation-block-edge-native-ab-v1","experimental_version":"ONE-G0.2",
            "source_sha":os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound","rounds":ROUNDS,
            "block_positions":WINDOW,"frozen_gate":{"state_max":.25,"hard_promoted_max":1.20,"hard_replay_max":.80,"entropy_max":.98,"repeat_shift_max":1.02,"large_retire":1.05},
            "decision":decision,"claim_boundary":"native encoder-discovery sufficient-summary evidence only; broad opportunity transfer remains required","rows":rows}
    finally: td.cleanup()

if __name__=="__main__": print(json.dumps(run(),indent=2,sort_keys=True))
