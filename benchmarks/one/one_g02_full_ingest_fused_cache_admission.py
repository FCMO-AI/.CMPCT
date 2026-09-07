"""ONE-G0.2 whole-ingest fused-cache admission rehabilitation falsifier."""
from __future__ import annotations

import ctypes
import gc
from hashlib import sha256
import json
import os
import statistics
import time

from benchmarks.one.one_g02_end_to_end_direct_emitter_writer import (
    Segment,
    _build_native,
    _oracle_plan,
    _plan_signature,
    _writer_once,
)
from benchmarks.one.one_g02_full_ingest_fused_cache import (
    BLOCK_SIZE,
    CHUNK_SIZE,
    MIN_RUN,
    REPETITIONS,
    SIZES,
    _ingest_once,
    _paired_medians,
    _update_cases,
)
from experiments.one.cache_fused_admission import observe_admitted
from experiments.one.cache_fused_observe import observe_incremental
from experiments.one.fused_cache_cost_ledger import audit_integrity_cost
from experiments.one.ir import Ref, Root
from experiments.one.observe import observe
from experiments.one.vm import evaluate
from experiments.one.wire import decode_program

EXPECTED_ADMISSION = {
    "exact_repeat": True,
    "one_block_edit": True,
    "eight_block_edit": True,
    "shift_plus1": False,
    "independent_random": False,
}
LIMITS = {
    "exact_repeat": 0.95,
    "one_block_edit": 0.98,
    "eight_block_edit": 1.02,
    "shift_plus1": 1.05,
    "independent_random": 1.05,
}


def _admitted_once(
    *,
    source: bytes,
    target: bytes,
    seed_cache,
    admission_fn,
    segment_fn,
    src_arr,
    dst_arr,
    seg_buf,
):
    c0 = time.process_time_ns()
    w0 = time.perf_counter_ns()
    observed = observe_admitted(
        target,
        previous=seed_cache,
        min_run=MIN_RUN,
        chunk_size=CHUNK_SIZE,
        block_size=BLOCK_SIZE,
    )
    w1 = time.perf_counter_ns()
    c1 = time.process_time_ns()

    previous_digest = sha256(source).hexdigest()
    current_digest = sha256(target).hexdigest()
    previous_root = Root(Ref(0), len(source), previous_digest)
    w2 = time.perf_counter_ns()
    c2 = time.process_time_ns()

    writer = _writer_once(
        admission_fn,
        segment_fn,
        source,
        target,
        src_arr,
        dst_arr,
        seg_buf,
        previous_root,
        current_digest,
        direct_emit=True,
    )
    w3 = time.perf_counter_ns()
    c3 = time.process_time_ns()
    return {
        "total_wall_ns": w3 - w0,
        "total_cpu_ns": c3 - c0,
        "observe_wall_ns": w1 - w0,
        "observe_cpu_ns": c1 - c0,
        "hash_wall_ns": w2 - w1,
        "hash_cpu_ns": c2 - c1,
        "writer_wall_ns": w3 - w2,
        "writer_cpu_ns": c3 - c2,
        "observation": observed.observation,
        "observed": observed,
        "writer": writer,
    }


def run():
    admission_fn, segment_fn, td = _build_native()
    rows = []
    semantic_ok = True
    classifier_ok = True
    productive_ok = True
    hostile_ok = True
    try:
        for size in SIZES:
            source, cases = _update_cases(size)
            seed = observe_incremental(
                source,
                min_run=MIN_RUN,
                chunk_size=CHUNK_SIZE,
                block_size=BLOCK_SIZE,
            )
            seed_oracle = observe(source, min_run=MIN_RUN, chunk_size=CHUNK_SIZE)
            if seed.observation.runs != seed_oracle.runs or seed.observation.reuse != seed_oracle.reuse:
                raise AssertionError("seed fused observation diverged from fresh oracle")

            src_arr = (ctypes.c_uint8 * size).from_buffer_copy(source)
            for case, target in cases.items():
                dst_arr = (ctypes.c_uint8 * size).from_buffer_copy(target)
                seg_buf = (Segment * size)()

                def baseline_call():
                    return _ingest_once(
                        cached=False,
                        source=source,
                        target=target,
                        seed_cache=seed.cache,
                        admission_fn=admission_fn,
                        segment_fn=segment_fn,
                        src_arr=src_arr,
                        dst_arr=dst_arr,
                        seg_buf=seg_buf,
                    )

                def candidate_call():
                    return _admitted_once(
                        source=source,
                        target=target,
                        seed_cache=seed.cache,
                        admission_fn=admission_fn,
                        segment_fn=segment_fn,
                        src_arr=src_arr,
                        dst_arr=dst_arr,
                        seg_buf=seg_buf,
                    )

                baseline = baseline_call()
                candidate = candidate_call()
                admitted = candidate["observed"].admission.admitted
                if admitted != EXPECTED_ADMISSION[case]:
                    classifier_ok = False

                if (
                    baseline["observation"].runs != candidate["observation"].runs
                    or baseline["observation"].reuse != candidate["observation"].reuse
                ):
                    raise AssertionError(f"admitted observation divergence: {size=} {case=}")

                bwriter = baseline["writer"]
                cwriter = candidate["writer"]
                bwire, bstats, bprogram, bresult, breads, bused, benabled, bplan, btraffic, bsegments, bdepth = bwriter
                cwire, cstats, cprogram, cresult, creads, cused, cenabled, cplan, ctraffic, csegments, cdepth = cwriter
                wire_equal = bwire == cwire and bstats == cstats
                classification_equal = (
                    benabled == cenabled
                    and int(bresult.best_shift) == int(cresult.best_shift)
                    and int(bresult.exact_proofs) == int(cresult.exact_proofs)
                )
                plan_equal = _plan_signature(bplan) == _plan_signature(cplan)
                plan_oracle = (
                    _plan_signature(cplan) == _plan_signature(_oracle_plan(source, target))
                    if cenabled else True
                )
                decoded = decode_program(cwire)
                outputs, vm_stats = evaluate(decoded)
                exact = outputs == {"previous": source, "current": target}
                this_semantic = wire_equal and classification_equal and plan_equal and plan_oracle and exact
                semantic_ok &= this_semantic
                if not this_semantic:
                    raise AssertionError(f"admitted whole-ingest semantic divergence: {size=} {case=}")

                medians, last = _paired_medians(baseline_call, candidate_call)
                if last["baseline"] is None or last["candidate"] is None:
                    raise AssertionError("missing timed admission result")
                if (
                    last["baseline"]["writer"][0] != last["candidate"]["writer"][0]
                    or last["baseline"]["writer"][1] != last["candidate"]["writer"][1]
                ):
                    raise AssertionError("timed admission paths changed canonical bytes/stats")

                bwall = medians["baseline"]["total_wall_ns"]
                bcpu = medians["baseline"]["total_cpu_ns"]
                cwall = medians["candidate"]["total_wall_ns"]
                ccpu = medians["candidate"]["total_cpu_ns"]
                wall_ratio = cwall / bwall
                cpu_ratio = ccpu / bcpu
                limit = LIMITS[case]
                row_perf = wall_ratio <= limit and cpu_ratio <= limit
                if case in ("exact_repeat", "one_block_edit", "eight_block_edit"):
                    productive_ok &= row_perf
                else:
                    hostile_ok &= row_perf

                admitted_result = candidate["observed"]
                inc = admitted_result.incremental
                if inc is not None:
                    integrity = audit_integrity_cost(inc, previous=seed.cache)
                    cache_fields = {
                        "candidate_validation_read_bytes": inc.stats.validation_read_bytes,
                        "candidate_feature_recompute_bytes": inc.stats.feature_recompute_bytes,
                        "candidate_feature_reuse_bytes": inc.stats.feature_reuse_bytes,
                        "candidate_recomputed_blocks": inc.stats.recomputed_blocks,
                        "candidate_reused_blocks": inc.stats.reused_blocks,
                        "candidate_cache_integrity_charged_hash_bytes": integrity.charged_hash_bytes,
                        "candidate_cache_feature_payload_read_bytes": inc.stats.cache_feature_payload_read_bytes,
                        "candidate_verification_read_bytes": inc.stats.verification_read_bytes,
                        "candidate_persistent_payload_bytes": inc.stats.persistent_payload_bytes,
                    }
                else:
                    cache_fields = {
                        "candidate_validation_read_bytes": 0,
                        "candidate_feature_recompute_bytes": 0,
                        "candidate_feature_reuse_bytes": 0,
                        "candidate_recomputed_blocks": 0,
                        "candidate_reused_blocks": 0,
                        "candidate_cache_integrity_charged_hash_bytes": 0,
                        "candidate_cache_feature_payload_read_bytes": 0,
                        "candidate_verification_read_bytes": 0,
                        "candidate_persistent_payload_bytes": 0,
                    }

                rows.append({
                    "size": size,
                    "case": case,
                    "expected_admitted": EXPECTED_ADMISSION[case],
                    "candidate_admitted": admitted,
                    "sampled_blocks": admitted_result.admission.sampled_blocks,
                    "matching_blocks": admitted_result.admission.matching_blocks,
                    "sample_match_fraction": admitted_result.admission.match_fraction,
                    "probe_read_bytes": admitted_result.admission.probe_read_bytes,
                    "probe_hash_bytes": admitted_result.admission.probe_hash_bytes,
                    "gate_limit": limit,
                    "baseline_total_wall_ns": bwall,
                    "candidate_total_wall_ns": cwall,
                    "baseline_total_cpu_ns": bcpu,
                    "candidate_total_cpu_ns": ccpu,
                    "wall_ratio": wall_ratio,
                    "cpu_ratio": cpu_ratio,
                    "baseline_observe_wall_ns": medians["baseline"]["observe_wall_ns"],
                    "candidate_observe_wall_ns": medians["candidate"]["observe_wall_ns"],
                    "baseline_hash_wall_ns": medians["baseline"]["hash_wall_ns"],
                    "candidate_hash_wall_ns": medians["candidate"]["hash_wall_ns"],
                    "baseline_writer_wall_ns": medians["baseline"]["writer_wall_ns"],
                    "candidate_writer_wall_ns": medians["candidate"]["writer_wall_ns"],
                    "baseline_observe_share_wall": medians["baseline"]["observe_wall_ns"] / bwall,
                    "relation_enabled": cenabled,
                    "best_shift": int(cresult.best_shift),
                    "exact_proofs": int(cresult.exact_proofs),
                    "gate_compared_bytes": creads,
                    "native_segment_compared_target_bytes": ctraffic,
                    "segments": csegments,
                    "canonical_wire_bytes": cstats.total_bytes,
                    "surprise_bytes": cstats.surprise_bytes,
                    "control_integrity_bytes": cstats.control_integrity_bytes,
                    "reader_work_bytes": vm_stats.work_bytes,
                    "reader_materialized_bytes": vm_stats.materialized_bytes,
                    "wire_equal": wire_equal,
                    "native_plan_matches_python_oracle": plan_oracle,
                    "exact_reconstruction": exact,
                    **cache_fields,
                })

        if not semantic_ok:
            decision = "INVALIDATE_CACHE_ADMISSION"
        elif not classifier_ok:
            decision = "REJECT_CACHE_ADMISSION_CLASSIFIER"
        elif not productive_ok:
            decision = "REJECT_CACHE_ADMISSION_PRODUCTIVE_DEBT"
        elif not hostile_ok:
            decision = "HOLD_CACHE_ADMISSION_CARRYING_COST"
        else:
            decision = "ADVANCE_CACHE_ADMISSION_REHABILITATION"

        return {
            "schema": "cmpct-one-g02-full-ingest-fused-cache-admission-v1",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "repetitions": REPETITIONS,
            "timing_order": "alternating A/B-B/A",
            "sample_blocks": 8,
            "minimum_match_fraction": 0.25,
            "semantic_gates_pass": semantic_ok,
            "classifier_gates_pass": classifier_ok,
            "productive_gates_pass": productive_ok,
            "hostile_gates_pass": hostile_ok,
            "decision": decision,
            "claim_boundary": (
                "bounded writer-side admission for the positional fused observation cache in the frozen adjacent-version "
                "research-writer envelope; rejected rows use fresh observation and intentionally produce no next cache; "
                "excludes re-seeding policy, arbitrary-shift cache reuse, authenticated placement, native product writer, "
                "RSS and v0.29/v0.30 supremacy"
            ),
            "rows": rows,
        }
    finally:
        td.cleanup()


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["decision"] == "ADVANCE_CACHE_ADMISSION_REHABILITATION" else 1)
