"""ONE-G0.2 hostile transfer for fixed proof-attempt topology.

Frozen before this transfer executes. The branch-and-bound gate passed its first matrix by combining
whole-relation byte coverage with up to sixteen exact 64-byte proof attempts starting from the relation
front. This test damages only those first sixteen proof cells while preserving the rest of a global +1
relation.

Disproof: if the full minimizer retains positive marginal reuse but the gate produces fewer than four
proofs, retire the fixed-front sixteen-attempt topology. This does not retire cheap-coverage -> exact-proof
branch-and-bound as a principle. Do not increase the cap or move the fixed proof sites after result.
"""
from __future__ import annotations
import ctypes, json, os, random, subprocess, tempfile
from pathlib import Path
from benchmarks.one.one_g02_gear_replacement_ab import FIXED_MAX_INDEX_ENTRIES, MIN_RUN, WINDOW
from benchmarks.one.one_g02_minimizer_gear_ab import _minimizer_observe
from benchmarks.one.one_g02_shift_branch_bound_gate_ab import Result
from experiments.one.observe import observe


def _front_damaged_shift(seed:int,n:int)->bytes:
    a=random.Random(seed).randbytes(n); b=bytearray(b'X'+a[:-1])
    # Corrupt exactly the first 16 64-byte proof cells in the shifted half.
    # Coverage samples are at another phase and the remainder of the relation is untouched.
    for cell in range(16):
        lo=cell*64; hi=min(n,lo+64)
        for j in range(lo,hi): b[j]^=(0x5D+cell*11+j)&0xFF
    return a+bytes(b)


def run():
    data=_front_damaged_shift(9901,64*1024)
    fixed=observe(data,min_run=MIN_RUN,chunk_size=WINDOW,max_index_entries=FIXED_MAX_INDEX_ENTRIES)
    mini=_minimizer_observe(data); marginal=mini.reuse_opportunity_bytes-fixed.stats.reuse_opportunity_bytes
    here=Path(__file__).parent; td=tempfile.TemporaryDirectory(prefix='cmpct-one-g02-bb-phase-')
    try:
        so=Path(td.name)/'lib.so'; subprocess.run([os.environ.get('CC','cc'),'-O3','-std=c11','-fPIC','-shared',
            str(here/'one_g02_shift_branch_bound_gate_kernel.c'),'-o',str(so)],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        fn=ctypes.CDLL(str(so)).one_g02_shift_branch_bound_gate
        fn.argtypes=[ctypes.POINTER(ctypes.c_uint8),ctypes.c_size_t,ctypes.POINTER(Result)]; fn.restype=ctypes.c_int
        arr=(ctypes.c_uint8*len(data)).from_buffer_copy(data); out=Result(); rc=fn(arr,len(data),ctypes.byref(out))
        if rc: raise RuntimeError(rc)
        enabled=fixed.stats.reuse_opportunity_bytes==0 and int(out.exact_proofs)>=4
        should_enable=marginal>0
        passed=enabled==should_enable
        return {'schema':'cmpct-one-g02-shift-branch-bound-phase-transfer-v1','experimental_version':'ONE-G0.2',
            'source_sha':os.environ.get('EVIDENCE_HEAD') or os.environ.get('GITHUB_SHA') or 'local-unbound',
            'decision':'advance_fixed_front_proof_topology' if passed else 'retire_fixed_front_proof_topology',
            'claim_boundary':'hostile writer-discovery topology test only; no product/comparator/release authority',
            'row':{'input_bytes':len(data),'fixed_opportunity_bytes':fixed.stats.reuse_opportunity_bytes,
                'minimizer_opportunity_bytes':mini.reuse_opportunity_bytes,'marginal_opportunity_bytes':marginal,
                'best_hits':int(out.best_hits),'best_shift':int(out.best_shift),'proof_attempts':int(out.proof_attempts),
                'exact_proofs':int(out.exact_proofs),'gate_enable':enabled,'positive_marginal':should_enable}}
    finally: td.cleanup()

if __name__=='__main__':
    r=run(); print(json.dumps(r,indent=2,sort_keys=True)); raise SystemExit(0 if r['decision']=='advance_fixed_front_proof_topology' else 1)
