"""ONE-G0.2 native A/B: eager exact rescue vs direct sparse rescue after shared silence."""
from __future__ import annotations

import ctypes
import json
import os
import statistics
import subprocess
import tempfile
from pathlib import Path

from benchmarks.one.one_g02_relation_shared_observer_validation import _cross_object_reuse_nominations
from benchmarks.one.one_g02_bounded_shift_phase_certificate_validation import _cases

SIZES=(4*1024,8*1024,16*1024,64*1024,256*1024)
SEEDS=(13,43,67)
REPETITIONS=7
BATCH_BY_SIZE={4096:256,8192:128,16384:64,65536:16,262144:4}
INCREMENTAL_TRANSIENT_GATE_BYTES=24


class Measurement(ctypes.Structure):
    _fields_=[
        ("eager_ns_per_batch",ctypes.c_double),("sparse_ns_per_batch",ctypes.c_double),
        ("sparse_gate_compared_bytes",ctypes.c_uint64),("sparse_gate_fires",ctypes.c_uint64),
        ("sparse_gate_rejects",ctypes.c_uint64),("eager_exact_pairs",ctypes.c_uint64),
        ("sparse_exact_executions",ctypes.c_uint64),("exact_positive_pairs",ctypes.c_uint64),
        ("productive_retained",ctypes.c_uint64),("negative_enabled",ctypes.c_uint64),
    ]


def _build():
    here=Path(__file__).parent
    td=tempfile.TemporaryDirectory(prefix="cmpct-one-cold-rescue-direct-sparse-")
    lib=Path(td.name)/"lib.so"
    subprocess.run([
        os.environ.get("CC","cc"),"-O3","-std=c11","-fPIC","-shared",
        str(here/"one_g02_shift_branch_bound_relation_direct_kernel.c"),
        str(here/"one_g02_shift_branch_bound_relation_restrict_kernel.c"),
        str(here/"one_g02_shift_relation_safe_dispatch_kernel.c"),
        str(here/"one_g02_shift_relation_sparse_gate_kernel.c"),
        str(here/"one_g02_cold_rescue_direct_sparse_kernel.c"),
        "-o",str(lib),
    ],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    c=ctypes.CDLL(str(lib)); p8=ctypes.POINTER(ctypes.c_uint8)
    c.one_g02_direct_sparse_measure.argtypes=[p8,ctypes.c_size_t,ctypes.c_size_t,ctypes.c_size_t,ctypes.POINTER(Measurement)]
    c.one_g02_direct_sparse_measure.restype=ctypes.c_int
    return c,td


def _shared_silent_batches():
    batches={}
    for size in SIZES:
        pairs=[]
        for seed in SEEDS:
            for name,(source,target) in _cases(size,seed).items():
                cross_exact,_,_=_cross_object_reuse_nominations(source,target)
                if cross_exact:
                    continue
                pairs.append((seed,name,source,target))
        batches[size]=pairs
    return batches


def run():
    lib,td=_build(); rows=[]
    try:
        batches=_shared_silent_batches()
        for size in SIZES:
            pairs=batches[size]
            packed=b"".join(source+target for _seed,_name,source,target in pairs)
            buf=(ctypes.c_uint8*len(packed)).from_buffer_copy(packed)
            eager_samples=[]; sparse_samples=[]; ratios=[]; last=None
            for _ in range(REPETITIONS):
                m=Measurement()
                rc=lib.one_g02_direct_sparse_measure(buf,size,len(pairs),BATCH_BY_SIZE[size],ctypes.byref(m))
                if rc: raise RuntimeError(f"native direct-sparse rescue measure failed rc={rc} size={size}")
                eager_samples.append(float(m.eager_ns_per_batch)); sparse_samples.append(float(m.sparse_ns_per_batch)); ratios.append(float(m.sparse_ns_per_batch/m.eager_ns_per_batch)); last=m
            assert last is not None
            rows.append({
                "relation_bytes":size,
                "pair_count":len(pairs),
                "pair_cases":[{"seed":seed,"case":name} for seed,name,_s,_t in pairs],
                "internal_batch_repetitions":BATCH_BY_SIZE[size],
                "eager_median_ns_per_batch":statistics.median(eager_samples),
                "direct_sparse_median_ns_per_batch":statistics.median(sparse_samples),
                "median_direct_sparse_over_eager":statistics.median(ratios),
                "sparse_gate_compared_bytes":int(last.sparse_gate_compared_bytes),
                "sparse_gate_fires":int(last.sparse_gate_fires),
                "sparse_gate_rejects":int(last.sparse_gate_rejects),
                "eager_exact_pairs":int(last.eager_exact_pairs),
                "sparse_exact_executions":int(last.sparse_exact_executions),
                "exact_positive_pairs":int(last.exact_positive_pairs),
                "productive_retained":int(last.productive_retained),
                "negative_enabled":int(last.negative_enabled),
                "incremental_transient_gate_bytes":INCREMENTAL_TRANSIENT_GATE_BYTES,
                "persistent_reader_or_wire_bytes":0,
            })

        timing=[float(r["median_direct_sparse_over_eager"]) for r in rows]
        eager_pairs=sum(int(r["eager_exact_pairs"]) for r in rows)
        sparse_exec=sum(int(r["sparse_exact_executions"]) for r in rows)
        exact_pos=sum(int(r["exact_positive_pairs"]) for r in rows)
        retained=sum(int(r["productive_retained"]) for r in rows)
        negative_enabled=sum(int(r["negative_enabled"]) for r in rows)
        gate=(
            eager_pairs==34 and exact_pos==4 and retained==exact_pos and negative_enabled==0
            and statistics.median(timing)<=0.90 and all(x<=1.05 for x in timing)
            and sparse_exec<=0.60*eager_pairs
        )
        return {
            "schema":"cmpct-one-g02-cold-rescue-direct-sparse-v1",
            "experimental_version":"ONE-G0.2",
            "source_sha":os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "repetitions":REPETITIONS,
            "incremental_transient_gate_bytes":INCREMENTAL_TRANSIENT_GATE_BYTES,
            "persistent_reader_or_wire_bytes":0,
            "total_shared_silent_pairs":eager_pairs,
            "total_exact_positive_pairs":exact_pos,
            "total_productive_retained":retained,
            "total_sparse_exact_executions":sparse_exec,
            "sparse_exact_execution_fraction":sparse_exec/eager_pairs,
            "median_direct_sparse_over_eager_across_sizes":statistics.median(timing),
            "decision":"advance_direct_sparse_toward_writer_integration" if gate else "retire_direct_sparse_cold_rescue",
            "claim_boundary":"conditional rescue efficiency only; shared observer and pair nomination are outside both timed arms; no density/reader/format/comparator claim",
            "rows":rows,
        }
    finally:
        td.cleanup()


if __name__=="__main__":
    result=run(); print(json.dumps(result,indent=2,sort_keys=True)); raise SystemExit(0 if result["decision"]=="advance_direct_sparse_toward_writer_integration" else 2)
