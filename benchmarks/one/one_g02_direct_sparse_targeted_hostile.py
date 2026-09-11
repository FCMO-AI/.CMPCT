"""ONE-G0.2 hostile transfer: target the public direct-sparse probe set."""
from __future__ import annotations

import ctypes
import json
import os
import random
import subprocess
import tempfile
from pathlib import Path

from benchmarks.one.one_g02_relation_shared_observer_validation import (
    Result, _cross_object_reuse_nominations, _safe_result, _shifted,
)

SIZES=(4*1024,8*1024,16*1024,64*1024,256*1024)
SEEDS=(101,131,163)


def _probe_positions(n:int):
    out=[]
    for s in range(16):
        p=((s+1)*n)//17
        if p<2: p=2
        if p+2>=n: p=n-3
        out.append(p)
    return tuple(out)


def _hostile(source:bytes)->bytes:
    target=bytearray(_shifted(source,spacing=96))
    for p in _probe_positions(len(source)):
        target[p+1] ^= 0x5A
    return bytes(target)


def _build():
    here=Path(__file__).parent
    td=tempfile.TemporaryDirectory(prefix="cmpct-one-direct-sparse-hostile-")
    lib=Path(td.name)/"lib.so"
    subprocess.run([
        os.environ.get("CC","cc"),"-O3","-std=c11","-fPIC","-shared",
        str(here/"one_g02_shift_branch_bound_relation_direct_kernel.c"),
        str(here/"one_g02_shift_branch_bound_relation_restrict_kernel.c"),
        str(here/"one_g02_shift_relation_safe_dispatch_kernel.c"),
        str(here/"one_g02_shift_relation_sparse_gate_kernel.c"),
        "-o",str(lib),
    ],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    c=ctypes.CDLL(str(lib)); p8=ctypes.POINTER(ctypes.c_uint8)
    safe=c.one_g02_shift_relation_safe_dispatch
    safe.argtypes=[p8,p8,ctypes.c_size_t,ctypes.POINTER(Result)]; safe.restype=ctypes.c_int
    sparse=c.one_g02_shift_relation_sparse_gate
    sparse.argtypes=[p8,p8,ctypes.c_size_t,ctypes.POINTER(Result),ctypes.POINTER(ctypes.c_uint64)]
    sparse.restype=ctypes.c_int
    return safe,sparse,td


def run():
    safe,sparse,td=_build(); rows=[]; cold_misses=[]
    try:
        for size in SIZES:
            for seed in SEEDS:
                source=random.Random(91000+size*53+seed*1009).randbytes(size)
                target=_hostile(source)
                exact_on,best_shift,proofs=_safe_result(safe,source,target)
                cross_exact,cross_auditions,peak_queue=_cross_object_reuse_nominations(source,target)
                cold=(cross_exact==0)
                a=(ctypes.c_uint8*size).from_buffer_copy(source)
                b=(ctypes.c_uint8*size).from_buffer_copy(target)
                out=Result(); compared=ctypes.c_uint64()
                fired=int(sparse(a,b,size,ctypes.byref(out),ctypes.byref(compared)))
                if fired<0: raise RuntimeError(f"sparse gate failed rc={fired}")
                gated_on=int(out.exact_proofs)>=4
                retained=exact_on and fired==1 and gated_on and int(out.best_shift)==best_shift
                if exact_on and cold and not retained:
                    cold_misses.append((size,seed,best_shift,proofs,fired,int(out.exact_proofs)))
                rows.append({
                    "relation_bytes":size,"seed":seed,
                    "exact_relation_enabled":exact_on,"exact_best_shift":best_shift,"exact_proofs":proofs,
                    "shared_exact_nominations":cross_exact,"shared_auditions":cross_auditions,
                    "peak_minimizer_queue_entries":peak_queue,"reaches_cold_rescue":cold,
                    "sparse_gate_fired":bool(fired),"sparse_gate_compared_bytes":int(compared.value),
                    "sparse_path_enabled":gated_on,"sparse_path_best_shift":int(out.best_shift),
                    "productive_retained":bool(retained),
                })
        exact_cold=sum(1 for r in rows if r["exact_relation_enabled"] and r["reaches_cold_rescue"])
        passed=exact_cold>0 and not cold_misses
        return {
            "schema":"cmpct-one-g02-direct-sparse-targeted-hostile-v1",
            "experimental_version":"ONE-G0.2",
            "source_sha":os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "sizes":list(SIZES),"seeds":list(SEEDS),
            "exact_shared_silent_rows":exact_cold,
            "cold_rescue_misses":cold_misses,
            "decision":"retain_direct_sparse_after_targeted_hostile" if passed else "retire_direct_sparse_general_cold_rescue",
            "claim_boundary":"hostile opportunity-retention evidence only; no density/reader/format/comparator claim",
            "rows":rows,
        }
    finally:
        td.cleanup()


if __name__=="__main__":
    result=run(); print(json.dumps(result,indent=2,sort_keys=True)); raise SystemExit(0 if result["decision"]=="retain_direct_sparse_after_targeted_hostile" else 2)
