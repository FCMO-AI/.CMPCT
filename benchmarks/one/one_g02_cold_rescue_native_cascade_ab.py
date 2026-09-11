"""ONE-G0.2 native A/B: eager exact rescue vs sparse cold rescue after shared silence."""
from __future__ import annotations

import ctypes
import json
import os
import statistics
import subprocess
import tempfile
from pathlib import Path

from benchmarks.one.one_g02_relation_shared_observer_validation import _cross_object_reuse_nominations
from benchmarks.one.one_g02_bounded_shift_phase_certificate_validation import _cases, _source_certificate

SIZES=(4*1024,8*1024,16*1024,64*1024,256*1024)
SEEDS=(13,43,67)
REPETITIONS=7
BATCH_BY_SIZE={4096:256,8192:128,16384:64,65536:16,262144:4}
TRANSIENT_STATE_BYTES=240


class Measurement(ctypes.Structure):
    _fields_=[
        ("eager_ns_per_batch",ctypes.c_double),("gated_ns_per_batch",ctypes.c_double),
        ("phase_source_words",ctypes.c_uint64),("phase_target_words",ctypes.c_uint64),
        ("phase_exact_word_compares",ctypes.c_uint64),("phase_nominations",ctypes.c_uint64),
        ("sparse_gate_compared_bytes",ctypes.c_uint64),("sparse_gate_fires",ctypes.c_uint64),
        ("sparse_gate_rejects",ctypes.c_uint64),("eager_exact_pairs",ctypes.c_uint64),
        ("gated_exact_executions",ctypes.c_uint64),("exact_positive_pairs",ctypes.c_uint64),
        ("productive_retained",ctypes.c_uint64),("negative_enabled",ctypes.c_uint64),
    ]


def _build():
    here=Path(__file__).parent
    td=tempfile.TemporaryDirectory(prefix="cmpct-one-cold-rescue-native-")
    lib=Path(td.name)/"lib.so"
    subprocess.run([
        os.environ.get("CC","cc"),"-O3","-std=c11","-fPIC","-shared",
        str(here/"one_g02_shift_branch_bound_relation_direct_kernel.c"),
        str(here/"one_g02_shift_branch_bound_relation_restrict_kernel.c"),
        str(here/"one_g02_shift_relation_safe_dispatch_kernel.c"),
        str(here/"one_g02_shift_relation_sparse_gate_kernel.c"),
        str(here/"one_g02_cold_rescue_native_cascade_kernel.c"),
        "-o",str(lib),
    ],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    c=ctypes.CDLL(str(lib)); p8=ctypes.POINTER(ctypes.c_uint8)
    c.one_g02_cold_rescue_measure.argtypes=[p8,ctypes.c_size_t,ctypes.c_size_t,ctypes.c_size_t,ctypes.POINTER(Measurement)]
    c.one_g02_cold_rescue_measure.restype=ctypes.c_int
    c.one_g02_phase_certificate_extract.argtypes=[p8,ctypes.c_size_t,ctypes.POINTER(ctypes.c_uint64),ctypes.POINTER(ctypes.c_uint32)]
    c.one_g02_phase_certificate_extract.restype=ctypes.c_int
    return c,td


def _native_certificate(lib,source:bytes):
    buf=(ctypes.c_uint8*len(source)).from_buffer_copy(source)
    hs=(ctypes.c_uint64*20)(); ps=(ctypes.c_uint32*20)()
    count=lib.one_g02_phase_certificate_extract(buf,len(source),hs,ps)
    if count<0: raise RuntimeError("native phase extraction failed")
    return sorted((int(hs[i]),int(ps[i])) for i in range(count))


def _python_certificate(source:bytes):
    cert,_=_source_certificate(source)
    return sorted((int(h),int(pos)) for h,pos,_phase in cert)


def _shared_silent_batches():
    batches={}; semantic_sources=[]
    for size in SIZES:
        pairs=[]
        for seed in SEEDS:
            cases=_cases(size,seed)
            for name,(source,target) in cases.items():
                cross_exact,_,_=_cross_object_reuse_nominations(source,target)
                if cross_exact:
                    continue
                pairs.append((seed,name,source,target))
                semantic_sources.append((size,seed,name,source))
        batches[size]=pairs
    return batches,semantic_sources


def run():
    lib,td=_build(); rows=[]; witness_mismatches=[]
    try:
        batches,semantic_sources=_shared_silent_batches()
        # Exact native-vs-reference witness equality is required before timing can promote.
        seen=set()
        for size,seed,name,source in semantic_sources:
            key=(size,seed)
            if key in seen: continue
            seen.add(key)
            if _native_certificate(lib,source)!=_python_certificate(source):
                witness_mismatches.append((size,seed,name))

        for size in SIZES:
            pairs=batches[size]
            packed=b"".join(source+target for _seed,_name,source,target in pairs)
            buf=(ctypes.c_uint8*len(packed)).from_buffer_copy(packed)
            eager_samples=[]; gated_samples=[]; ratios=[]; last=None
            for _ in range(REPETITIONS):
                m=Measurement()
                rc=lib.one_g02_cold_rescue_measure(buf,size,len(pairs),BATCH_BY_SIZE[size],ctypes.byref(m))
                if rc: raise RuntimeError(f"native rescue measure failed rc={rc} size={size}")
                eager_samples.append(float(m.eager_ns_per_batch)); gated_samples.append(float(m.gated_ns_per_batch)); ratios.append(float(m.gated_ns_per_batch/m.eager_ns_per_batch)); last=m
            assert last is not None
            rows.append({
                "relation_bytes":size,
                "pair_count":len(pairs),
                "pair_cases":[{"seed":seed,"case":name} for seed,name,_s,_t in pairs],
                "internal_batch_repetitions":BATCH_BY_SIZE[size],
                "eager_median_ns_per_batch":statistics.median(eager_samples),
                "gated_median_ns_per_batch":statistics.median(gated_samples),
                "median_gated_over_eager":statistics.median(ratios),
                "phase_source_words":int(last.phase_source_words),
                "phase_target_words":int(last.phase_target_words),
                "phase_exact_word_compares":int(last.phase_exact_word_compares),
                "phase_nominations":int(last.phase_nominations),
                "phase_modeled_sampled_bytes":8*(int(last.phase_source_words)+int(last.phase_target_words)),
                "sparse_gate_compared_bytes":int(last.sparse_gate_compared_bytes),
                "sparse_gate_fires":int(last.sparse_gate_fires),
                "sparse_gate_rejects":int(last.sparse_gate_rejects),
                "eager_exact_pairs":int(last.eager_exact_pairs),
                "gated_exact_executions":int(last.gated_exact_executions),
                "exact_positive_pairs":int(last.exact_positive_pairs),
                "productive_retained":int(last.productive_retained),
                "negative_enabled":int(last.negative_enabled),
                "transient_state_bytes":TRANSIENT_STATE_BYTES,
            })

        timing=[float(r["median_gated_over_eager"]) for r in rows]
        eager_pairs=sum(int(r["eager_exact_pairs"]) for r in rows)
        gated_exec=sum(int(r["gated_exact_executions"]) for r in rows)
        exact_pos=sum(int(r["exact_positive_pairs"]) for r in rows)
        retained=sum(int(r["productive_retained"]) for r in rows)
        negative_enabled=sum(int(r["negative_enabled"]) for r in rows)
        gate=(
            not witness_mismatches and exact_pos==4 and retained==exact_pos and negative_enabled==0
            and statistics.median(timing)<=0.90 and all(x<=1.05 for x in timing)
            and gated_exec<=0.60*eager_pairs
        )
        return {
            "schema":"cmpct-one-g02-cold-rescue-native-cascade-v1",
            "experimental_version":"ONE-G0.2",
            "source_sha":os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "repetitions":REPETITIONS,
            "transient_phase_state_bytes":TRANSIENT_STATE_BYTES,
            "native_witness_mismatches":witness_mismatches,
            "total_shared_silent_pairs":eager_pairs,
            "total_exact_positive_pairs":exact_pos,
            "total_productive_retained":retained,
            "total_gated_exact_executions":gated_exec,
            "gated_exact_execution_fraction":gated_exec/eager_pairs,
            "median_gated_over_eager_across_sizes":statistics.median(timing),
            "decision":"advance_cold_rescue_toward_writer_integration" if gate else "retire_native_cold_rescue_cascade",
            "claim_boundary":"conditional rescue efficiency only; shared observer and pair nomination are outside both timed arms; no density/reader/format/comparator claim",
            "rows":rows,
        }
    finally:
        td.cleanup()


if __name__=="__main__":
    result=run(); print(json.dumps(result,indent=2,sort_keys=True)); raise SystemExit(0 if result["decision"]=="advance_cold_rescue_toward_writer_integration" else 2)
