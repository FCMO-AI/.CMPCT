"""ONE-G0.2 fused-observation cache whole-ingest falsifier.

Frozen by ONE_G02_FULL_INGEST_FUSED_CACHE_PREREG_2026-09-07.md.

Both arms charge observation, SHA-256 identities for previous/current roots, the promoted
amortization-safe relation gate, native one-pass segmentation when admitted, bounded
Law/Surprise Program construction, full validation and direct final-buffer canonical
emission. The candidate replaces only fresh current observation with the sealed
positional fused-observation cache seeded by the previous version.

This is still a research-writer envelope: authenticated physical placement/durability,
product-native creation and arbitrary-length updates remain outside the claim boundary.
"""
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
from benchmarks.one.one_g02_shift_branch_bound_relation_transfer import _relation_cases
from experiments.one.cache_fused_observe import observe_incremental
from experiments.one.fused_cache_cost_ledger import audit_integrity_cost
from experiments.one.ir import Ref, Root
from experiments.one.observe import observe
from experiments.one.vm import evaluate
from experiments.one.wire import decode_program

SIZES = (64 << 10, 256 << 10)
REPETITIONS = 15
BLOCK_SIZE = 4096
CHUNK_SIZE = 64
MIN_RUN = 8

POSITIONAL_LIMITS = {
    "exact_repeat": 0.95,
    "one_block_edit": 0.98,
    "eight_block_edit": 1.02,
}
HOSTILE_LIMIT = 1.15


def _update_cases(size: int):
    relation = _relation_cases(size)
    source = relation["shift_plus1"][0]

    one = bytearray(source)
    one[len(one) // 2 + 17] ^= 0x5A

    eight = bytearray(source)
    block_count = max(1, len(eight) // BLOCK_SIZE)
    for k in range(min(8, block_count)):
        block = (k * max(1, block_count // 8)) % block_count
        pos = min(len(eight) - 1, block * BLOCK_SIZE + 31 + k)
        eight[pos] ^= (0x21 + k)

    return source, {
        "exact_repeat": source,
        "one_block_edit": bytes(one),
        "eight_block_edit": bytes(eight),
        "shift_plus1": relation["shift_plus1"][1],
        "independent_random": relation["independent_random"][1],
    }


def _ingest_once(
    *,
    cached: bool,
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
    if cached:
        observed = observe_incremental(
            target,
            previous=seed_cache,
            min_run=MIN_RUN,
            chunk_size=CHUNK_SIZE,
            block_size=BLOCK_SIZE,
        )
        observation = observed.observation
    else:
        observed = observe(target, min_run=MIN_RUN, chunk_size=CHUNK_SIZE)
        observation = observed
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
        "observation": observation,
        "observed": observed,
        "writer": writer,
    }


def _paired_medians(baseline_fn, candidate_fn):
    samples = {
        "baseline": {key: [] for key in (
            "total_wall_ns", "total_cpu_ns", "observe_wall_ns", "observe_cpu_ns",
            "hash_wall_ns", "hash_cpu_ns", "writer_wall_ns", "writer_cpu_ns",
        )},
        "candidate": {key: [] for key in (
            "total_wall_ns", "total_cpu_ns", "observe_wall_ns", "observe_cpu_ns",
            "hash_wall_ns", "hash_cpu_ns", "writer_wall_ns", "writer_cpu_ns",
        )},
    }
    last = {"baseline": None, "candidate": None}
    was_enabled = gc.isenabled()
    try:
        if was_enabled:
            gc.disable()
        for rep in range(REPETITIONS):
            order = (("baseline", baseline_fn), ("candidate", candidate_fn))
            if rep % 2:
                order = tuple(reversed(order))
            for label, fn in order:
                result = fn()
                last[label] = result
                for key in samples[label]:
                    samples[label][key].append(result[key])
    finally:
        if was_enabled:
            gc.enable()

    medians = {
        label: {key: float(statistics.median(values)) for key, values in metrics.items()}
        for label, metrics in samples.items()
    }
    return medians, last


def run():
    admission_fn, segment_fn, td = _build_native()
    rows = []
    semantic_ok = True
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
                    return _ingest_once(
                        cached=True,
                        source=source,
                        target=target,
                        seed_cache=seed.cache,
                        admission_fn=admission_fn,
                        segment_fn=segment_fn,
                        src_arr=src_arr,
                        dst_arr=dst_arr,
                        seg_buf=seg_buf,
                    )

                # Untimed semantic authority path before consuming timing evidence.
                baseline = baseline_call()
                candidate = candidate_call()
                bobs = baseline["observation"]
                cobs = candidate["observation"]
                c_inc = candidate["observed"]
                if bobs.runs != cobs.runs or bobs.reuse != cobs.reuse:
                    raise AssertionError(f"cached observation divergence: {size=} {case=}")

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
                    raise AssertionError(f"whole-ingest writer semantic divergence: {size=} {case=}")

                integrity = audit_integrity_cost(c_inc, previous=seed.cache)
                medians, last = _paired_medians(baseline_call, candidate_call)
                if last["baseline"] is None or last["candidate"] is None:
                    raise AssertionError("missing timed ingest result")
                # Timing runs must retain identical canonical output too.
                if (
                    last["baseline"]["writer"][0] != last["candidate"]["writer"][0]
                    or last["baseline"]["writer"][1] != last["candidate"]["writer"][1]
                ):
                    raise AssertionError("timed whole-ingest paths changed canonical bytes/stats")

                bwall = medians["baseline"]["total_wall_ns"]
                bcpu = medians["baseline"]["total_cpu_ns"]
                cwall = medians["candidate"]["total_wall_ns"]
                ccpu = medians["candidate"]["total_cpu_ns"]
                wall_ratio = cwall / bwall
                cpu_ratio = ccpu / bcpu
                baseline_observe_share_wall = medians["baseline"]["observe_wall_ns"] / bwall
                baseline_observe_share_cpu = medians["baseline"]["observe_cpu_ns"] / bcpu

                if case in POSITIONAL_LIMITS:
                    limit = POSITIONAL_LIMITS[case]
                    if wall_ratio > limit or cpu_ratio > limit:
                        productive_ok = False
                else:
                    limit = HOSTILE_LIMIT
                    if wall_ratio > limit or cpu_ratio > limit:
                        hostile_ok = False

                rows.append({
                    "size": size,
                    "case": case,
                    "gate_limit": limit,
                    "baseline_total_wall_ns": bwall,
                    "candidate_total_wall_ns": cwall,
                    "baseline_total_cpu_ns": bcpu,
                    "candidate_total_cpu_ns": ccpu,
                    "wall_ratio": wall_ratio,
                    "cpu_ratio": cpu_ratio,
                    "baseline_observe_wall_ns": medians["baseline"]["observe_wall_ns"],
                    "candidate_observe_wall_ns": medians["candidate"]["observe_wall_ns"],
                    "baseline_observe_cpu_ns": medians["baseline"]["observe_cpu_ns"],
                    "candidate_observe_cpu_ns": medians["candidate"]["observe_cpu_ns"],
                    "baseline_hash_wall_ns": medians["baseline"]["hash_wall_ns"],
                    "candidate_hash_wall_ns": medians["candidate"]["hash_wall_ns"],
                    "baseline_writer_wall_ns": medians["baseline"]["writer_wall_ns"],
                    "candidate_writer_wall_ns": medians["candidate"]["writer_wall_ns"],
                    "baseline_observe_share_wall": baseline_observe_share_wall,
                    "baseline_observe_share_cpu": baseline_observe_share_cpu,
                    "candidate_validation_read_bytes": c_inc.stats.validation_read_bytes,
                    "candidate_feature_recompute_bytes": c_inc.stats.feature_recompute_bytes,
                    "candidate_feature_reuse_bytes": c_inc.stats.feature_reuse_bytes,
                    "candidate_recomputed_blocks": c_inc.stats.recomputed_blocks,
                    "candidate_reused_blocks": c_inc.stats.reused_blocks,
                    "candidate_cache_integrity_verify_hash_bytes": integrity.expected_verify_hash_bytes,
                    "candidate_cache_integrity_build_hash_bytes": integrity.expected_build_hash_bytes,
                    "candidate_cache_integrity_charged_hash_bytes": integrity.charged_hash_bytes,
                    "candidate_cache_feature_payload_read_bytes": c_inc.stats.cache_feature_payload_read_bytes,
                    "candidate_verification_read_bytes": c_inc.stats.verification_read_bytes,
                    "candidate_persistent_payload_bytes": c_inc.stats.persistent_payload_bytes,
                    "candidate_persistent_payload_ratio": c_inc.stats.persistent_payload_bytes / max(1, size),
                    "relation_enabled": cenabled,
                    "best_shift": int(cresult.best_shift),
                    "exact_proofs": int(cresult.exact_proofs),
                    "gate_compared_bytes": creads,
                    "used_sparse_gate": cused,
                    "native_segment_compared_target_bytes": ctraffic,
                    "segments": csegments,
                    "hierarchy_depth": cdepth,
                    "canonical_wire_bytes": cstats.total_bytes,
                    "surprise_bytes": cstats.surprise_bytes,
                    "control_integrity_bytes": cstats.control_integrity_bytes,
                    "reader_work_bytes": vm_stats.work_bytes,
                    "reader_materialized_bytes": vm_stats.materialized_bytes,
                    "wire_equal": wire_equal,
                    "native_plan_matches_python_oracle": plan_oracle,
                    "exact_reconstruction": exact,
                })

        if not semantic_ok:
            decision = "INVALIDATE_FULL_INGEST_CACHE"
        elif not productive_ok:
            decision = "REJECT_OR_REFORM_FULL_INGEST_CACHE"
        elif not hostile_ok:
            decision = "OPEN_CACHE_ADMISSION_DEBT"
        else:
            decision = "ADVANCE_FUSED_CACHE_TO_BROADER_INGEST"

        return {
            "schema": "cmpct-one-g02-full-ingest-fused-cache-v1",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "repetitions": REPETITIONS,
            "timing_order": "alternating A/B-B/A",
            "block_size": BLOCK_SIZE,
            "chunk_size": CHUNK_SIZE,
            "min_run": MIN_RUN,
            "semantic_gates_pass": semantic_ok,
            "productive_positional_gates_pass": productive_ok,
            "hostile_carrying_cost_gates_pass": hostile_ok,
            "decision": decision,
            "claim_boundary": (
                "adjacent-version research-writer envelope charging fused/fresh current observation, SHA-256 of both roots, "
                "relation admission, native one-pass segmentation, bounded Law/Surprise Program construction, validation "
                "and direct final-buffer canonical emission; excludes authenticated physical placement/durability, native "
                "product writer authority, arbitrary-length updates and v0.29/v0.30 supremacy"
            ),
            "rows": rows,
        }
    finally:
        td.cleanup()


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    # Admission debt is a valid scientific outcome with useful positional evidence; make
    # the workflow red only for semantic invalidation or failure of the productive thesis.
    raise SystemExit(1 if result["decision"] in {
        "INVALIDATE_FULL_INGEST_CACHE",
        "REJECT_OR_REFORM_FULL_INGEST_CACHE",
    } else 0)
