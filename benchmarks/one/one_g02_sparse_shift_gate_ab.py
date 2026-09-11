"""ONE-G0.2 sparse opportunity gate for expensive shifted-reuse discovery.

Referee freeze before result-bearing execution
==============================================
The exact marginal-yield map shows that the promoted minimizer selector adds reuse opportunity only
on the two small-shift temporal falsifiers in the current corpus, while paying ~3-4 ns/input byte on
large random/already-compressed/repetition controls.  This experiment asks whether a tiny writer-only
sparse resemblance probe can identify those cases *after the existing cheap fixed observer has found
zero reuse*, so the expensive selector can remain dormant elsewhere.

The probe samples eight deterministic 64-byte regions in the first half and compares their hashes to
corresponding second-half regions at shifts -2..+2.  It is a gate only, not a Law or reader opcode.

Frozen gate:
- reference labels are recomputed from fixed observer vs existing minimizer opportunity bytes;
- enable iff fixed opportunity == 0 and >=4/8 probe samples match at some tested shift;
- recall every positive-marginal case;
- false-enable zero zero-marginal cases in the complete existing MIY corpus;
- probe median elapsed <=0.05x the promoted selector's incremental cost over Gear on every input >=8KiB;
- probe compared bytes <=25% of input on every input >=8KiB.
Failure preserves a scoped negative; no threshold/shift/sample retuning after execution.

A pass is gating headroom only. It does not yet satisfy the one-fused-observation-pass product law;
the sparse observations would have to be harvested from the fused observer without an extra source pass.
"""
from __future__ import annotations

import ctypes
import json
import os
from pathlib import Path
import random
import statistics
import subprocess
import tempfile
import time

from benchmarks.one.one_g02_gear_replacement_ab import _GEAR, _cases, FIXED_MAX_INDEX_ENTRIES, MIN_RUN, WINDOW
from benchmarks.one.one_g02_minimizer_gear_ab import _minimizer_observe, MINIMIZER_SPAN
from benchmarks.one.one_g02_minimizer_miy import _bind as _bind_cost, _dispatch_call, _gear_call, _paired_cost
from experiments.one.observe import observe

MATCH_THRESHOLD = 4
MAX_COST_RATIO = 0.05
MAX_READ_FRACTION = 0.25

class GateResult(ctypes.Structure):
    _fields_ = [("samples",ctypes.c_uint64),("matched_samples",ctypes.c_uint64),("compared_bytes",ctypes.c_uint64),("best_shift",ctypes.c_int64)]

def _build():
    here=Path(__file__).parent
    td=tempfile.TemporaryDirectory(prefix="cmpct-one-g02-shift-gate-")
    lib=Path(td.name)/"lib.so"
    subprocess.run([os.environ.get("CC","cc"),"-O3","-std=c11","-fPIC","-shared",
        str(here/"one_g02_sparse_shift_gate_kernel.c"),
        str(here/"one_g02_minimizer_kernel.c"),
        str(here/"one_g02_minimizer_segmented_counter_kernel.c"),
        str(here/"one_g02_minimizer_offset_only_kernel.c"),
        str(here/"one_g02_minimizer_size_dispatch_tail_kernel.c"),"-o",str(lib)],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    return ctypes.CDLL(str(lib)),td

def _median_probe(fn, arr, n):
    out=GateResult(); fn(arr,n,ctypes.byref(out))
    vals=[]
    for _ in range(31):
        t=time.perf_counter_ns(); fn(arr,n,ctypes.byref(out)); vals.append(time.perf_counter_ns()-t)
    return float(statistics.median(vals)),out

def run():
    cases=_cases(); starved=random.Random(4876).randbytes(8*1024)
    cases["starved_repeat_basis_8k_16k"]=starved*2
    cases["starved_shifted_basis_8k_insert1"]=starved+b"X"+starved
    lib,td=_build()
    try:
        probe=lib.one_g02_sparse_shift_gate
        probe.argtypes=[ctypes.POINTER(ctypes.c_uint8),ctypes.c_size_t,ctypes.POINTER(GateResult)]; probe.restype=ctypes.c_int
        dispatch,gear_only=_bind_cost(lib); gear=(ctypes.c_uint64*256)(*_GEAR)
        rows=[]; positives=[]; predicted=[]; recall=True; specificity=True; cost_ok=True; reads_ok=True
        for name,data in cases.items():
            fixed=observe(data,min_run=MIN_RUN,chunk_size=WINDOW,max_index_entries=FIXED_MAX_INDEX_ENTRIES)
            minimizer=_minimizer_observe(data)
            marginal=minimizer.reuse_opportunity_bytes-fixed.stats.reuse_opportunity_bytes
            positive=marginal>0
            if positive: positives.append(name)
            arr=(ctypes.c_uint8*len(data)).from_buffer_copy(data)
            pns,pout=_median_probe(probe,arr,len(data))
            enable=(fixed.stats.reuse_opportunity_bytes==0 and int(pout.matched_samples)>=MATCH_THRESHOLD)
            if enable: predicted.append(name)
            recall &= (not positive) or enable
            specificity &= positive or (not enable)
            cost_ratio=None
            if len(data)>=8192:
                _,_,inc=_paired_cost(lambda:_gear_call(gear_only,gear,arr,len(data)),lambda:_dispatch_call(dispatch,gear,arr,len(data)))
                cost_ratio=pns/inc
                cost_ok &= cost_ratio<=MAX_COST_RATIO
                reads_ok &= int(pout.compared_bytes)/len(data)<=MAX_READ_FRACTION
            rows.append({"case":name,"input_bytes":len(data),"fixed_opportunity_bytes":fixed.stats.reuse_opportunity_bytes,
                "minimizer_opportunity_bytes":minimizer.reuse_opportunity_bytes,"marginal_opportunity_bytes":marginal,
                "positive_marginal":positive,"probe_samples":int(pout.samples),"matched_samples":int(pout.matched_samples),
                "best_shift":int(pout.best_shift),"probe_compared_bytes":int(pout.compared_bytes),
                "probe_read_fraction":int(pout.compared_bytes)/len(data),"probe_median_ns":pns,
                "probe_over_incremental_selector":cost_ratio,"gate_enable":enable})
        passed=recall and specificity and cost_ok and reads_ok
        return {"schema":"cmpct-one-g02-sparse-shift-gate-ab-v1","experimental_version":"ONE-G0.2",
            "source_sha":os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "frozen_match_threshold":MATCH_THRESHOLD,"frozen_max_cost_ratio":MAX_COST_RATIO,"frozen_max_read_fraction":MAX_READ_FRACTION,
            "positive_marginal_cases":positives,"gate_enabled_cases":predicted,
            "decision":"advance_sparse_shift_opportunity_gate" if passed else "retire_sparse_shift_opportunity_gate",
            "claim_boundary":"writer opportunity-gating headroom only; sparse probe currently performs extra reads and is not fused-observer/product/comparator/release authority",
            "rows":rows}
    finally: td.cleanup()

if __name__=="__main__":
    r=run(); print(json.dumps(r,indent=2,sort_keys=True)); raise SystemExit(0 if r["decision"]=="advance_sparse_shift_opportunity_gate" else 1)
