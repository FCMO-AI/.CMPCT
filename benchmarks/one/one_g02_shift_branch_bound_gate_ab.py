"""ONE-G0.2 branch-and-bound shift gate falsifier.

Frozen before result-bearing execution. The cheap coverage stage may nominate coherent resemblance but
one-byte evidence is not exact reuse. This Builder keeps the frozen 64-byte coverage stride, signed shift
set and majority rule, then pays for exact 64-byte proof only after a displacement is nominated. It stops
after four successful exact proofs or sixteen proof attempts.

Hypothesis: on the combined original, phase-damaged, periodic and fragmented false-pattern matrix, four
exact proofs after coverage nomination retain every minimizer-positive marginal case, reject every zero-
marginal case, and keep total gate elapsed <=5% of promoted selector incremental cost on fixed-zero inputs
>=8 KiB. Modeled extra read traffic must stay <=25% of input.

Disproof retires this two-stage testbed. Do not tune proof count, attempt cap, stride, majority or shifts
after execution. Even a pass is causal writer headroom only; half-to-half layout is not a general ONE
product policy.
"""
from __future__ import annotations

import ctypes, json, os, random, statistics, subprocess, tempfile, time
from pathlib import Path
from benchmarks.one.one_g02_exclusive_shift_gate_transfer import _cases as hostile_cases
from benchmarks.one.one_g02_shift_coverage_false_pattern_transfer import _fragmented_shift
from benchmarks.one.one_g02_gear_replacement_ab import _GEAR, _cases, FIXED_MAX_INDEX_ENTRIES, MIN_RUN, WINDOW
from benchmarks.one.one_g02_minimizer_gear_ab import _minimizer_observe
from benchmarks.one.one_g02_minimizer_miy import _bind as _bind_cost, _dispatch_call, _gear_call, _paired_cost
from experiments.one.observe import observe

MAX_COST_RATIO=0.05
MAX_READ_FRACTION=0.25

class Result(ctypes.Structure):
    _fields_=[('samples',ctypes.c_uint64),('zero_shift_matches',ctypes.c_uint64),
              ('coverage_compared_bytes',ctypes.c_uint64),('best_hits',ctypes.c_uint64),
              ('best_shift',ctypes.c_int64),('proof_attempts',ctypes.c_uint64),
              ('exact_proofs',ctypes.c_uint64),('proof_compared_bytes',ctypes.c_uint64)]

def _build():
    here=Path(__file__).parent; td=tempfile.TemporaryDirectory(prefix='cmpct-one-g02-bb-shift-')
    lib=Path(td.name)/'lib.so'
    subprocess.run([os.environ.get('CC','cc'),'-O3','-std=c11','-fPIC','-shared',
        str(here/'one_g02_shift_branch_bound_gate_kernel.c'),
        str(here/'one_g02_minimizer_kernel.c'),str(here/'one_g02_minimizer_segmented_counter_kernel.c'),
        str(here/'one_g02_minimizer_offset_only_kernel.c'),str(here/'one_g02_minimizer_size_dispatch_tail_kernel.c'),
        '-o',str(lib)],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    return ctypes.CDLL(str(lib)),td

def _median(fn,arr,n):
    out=Result(); fn(arr,n,ctypes.byref(out)); vals=[]
    for _ in range(51):
        t=time.perf_counter_ns(); fn(arr,n,ctypes.byref(out)); vals.append(time.perf_counter_ns()-t)
    return float(statistics.median(vals)),out

def run():
    cases=_cases(); basis=random.Random(4876).randbytes(8192)
    cases['starved_repeat_basis_8k_16k']=basis*2
    cases['starved_shifted_basis_8k_insert1']=basis+b'X'+basis
    for k,v in hostile_cases().items(): cases['hostile_'+k]=v
    cases['false_fragmented_shift_every32']=_fragmented_shift(8101,65536,32)
    cases['fragmented_shift_every96_control']=_fragmented_shift(8102,65536,96)
    lib,td=_build()
    try:
        fn=lib.one_g02_shift_branch_bound_gate
        fn.argtypes=[ctypes.POINTER(ctypes.c_uint8),ctypes.c_size_t,ctypes.POINTER(Result)]; fn.restype=ctypes.c_int
        dispatch,gear_only=_bind_cost(lib); gear=(ctypes.c_uint64*256)(*_GEAR)
        rows=[]; ok=True; cost_ok=True; reads_ok=True
        for name,data in cases.items():
            fixed=observe(data,min_run=MIN_RUN,chunk_size=WINDOW,max_index_entries=FIXED_MAX_INDEX_ENTRIES)
            mini=_minimizer_observe(data); marginal=mini.reuse_opportunity_bytes-fixed.stats.reuse_opportunity_bytes
            positive=marginal>0; arr=(ctypes.c_uint8*len(data)).from_buffer_copy(data)
            ns,out=_median(fn,arr,len(data)); enabled=fixed.stats.reuse_opportunity_bytes==0 and int(out.exact_proofs)>=4
            ok &= enabled==positive
            ratio=read_fraction=None
            if len(data)>=8192 and fixed.stats.reuse_opportunity_bytes==0:
                _,_,inc=_paired_cost(lambda:_gear_call(gear_only,gear,arr,len(data)),lambda:_dispatch_call(dispatch,gear,arr,len(data)))
                ratio=ns/inc; read_fraction=(int(out.coverage_compared_bytes)+int(out.proof_compared_bytes))/len(data)
                cost_ok &= ratio<=MAX_COST_RATIO; reads_ok &= read_fraction<=MAX_READ_FRACTION
            rows.append({'case':name,'input_bytes':len(data),'fixed_opportunity_bytes':fixed.stats.reuse_opportunity_bytes,
                'minimizer_opportunity_bytes':mini.reuse_opportunity_bytes,'marginal_opportunity_bytes':marginal,
                'positive_marginal':positive,'best_hits':int(out.best_hits),'best_shift':int(out.best_shift),
                'proof_attempts':int(out.proof_attempts),'exact_proofs':int(out.exact_proofs),
                'coverage_compared_bytes':int(out.coverage_compared_bytes),'proof_compared_bytes':int(out.proof_compared_bytes),
                'read_fraction':read_fraction,'gate_median_ns':ns,'gate_over_incremental_selector':ratio,
                'gate_enable':enabled,'classification_correct':enabled==positive})
        passed=ok and cost_ok and reads_ok
        return {'schema':'cmpct-one-g02-shift-branch-bound-gate-ab-v1','experimental_version':'ONE-G0.2',
            'source_sha':os.environ.get('EVIDENCE_HEAD') or os.environ.get('GITHUB_SHA') or 'local-unbound',
            'frozen_exact_proofs':4,'frozen_max_proof_attempts':16,'frozen_max_cost_ratio':MAX_COST_RATIO,
            'frozen_max_read_fraction':MAX_READ_FRACTION,
            'decision':'advance_shift_branch_bound_gate' if passed else 'retire_shift_branch_bound_gate',
            'claim_boundary':'causal half-to-half writer testbed only; not a general ONE dispatch/product/comparator authority','rows':rows}
    finally: td.cleanup()

if __name__=='__main__':
    r=run(); print(json.dumps(r,indent=2,sort_keys=True)); raise SystemExit(0 if r['decision']=='advance_shift_branch_bound_gate' else 1)
