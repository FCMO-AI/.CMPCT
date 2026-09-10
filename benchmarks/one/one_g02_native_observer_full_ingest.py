"""ONE-G0.2 native fresh-observer full-ingest transfer falsifier.

Frozen by ONE_G02_NATIVE_OBSERVER_FULL_INGEST_PREREG_2026-09-09.md.
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
from benchmarks.one.one_g02_full_ingest_fused_cache import _update_cases
from experiments.one.ir import Ref, Root
from experiments.one.native_observe import observe_native
from experiments.one.observe import observe
from experiments.one.vm import evaluate
from experiments.one.wire import decode_program

SIZES = (64 << 10, 256 << 10, 1 << 20)
REPETITIONS = 15
MEDIAN_LIMIT = 0.15
ROW_LIMIT = 0.35


_TIMED_KEYS = (
    "total_wall_ns",
    "total_cpu_ns",
    "observe_wall_ns",
    "observe_cpu_ns",
    "hash_wall_ns",
    "hash_cpu_ns",
    "writer_wall_ns",
    "writer_cpu_ns",
)


def _ingest_once(
    *,
    native_observer: bool,
    source: bytes,
    target: bytes,
    admission_fn,
    segment_fn,
    src_arr,
    dst_arr,
    seg_buf,
):
    c0 = time.process_time_ns()
    w0 = time.perf_counter_ns()
    observation = observe_native(target) if native_observer else observe(target)
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
        "writer": writer,
    }


def _paired_medians(baseline_fn, candidate_fn):
    samples = {
        "baseline": {key: [] for key in _TIMED_KEYS},
        "candidate": {key: [] for key in _TIMED_KEYS},
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
                for key in _TIMED_KEYS:
                    samples[label][key].append(result[key])
    finally:
        if was_enabled:
            gc.enable()
    medians = {
        label: {key: float(statistics.median(values)) for key, values in metrics.items()}
        for label, metrics in samples.items()
    }
    return medians, last


def _semantic_check(source: bytes, target: bytes, baseline: dict, candidate: dict) -> dict:
    if baseline["observation"] != candidate["observation"]:
        raise AssertionError("native observer changed exact Observation")

    bwriter = baseline["writer"]
    cwriter = candidate["writer"]
    (
        bwire, bstats, _bprogram, bresult, _breads, _bused, benabled,
        bplan, _btraffic, _bsegments, _bdepth,
    ) = bwriter
    (
        cwire, cstats, _cprogram, cresult, _creads, _cused, cenabled,
        cplan, _ctraffic, _csegments, _cdepth,
    ) = cwriter

    if bwire != cwire or bstats != cstats:
        raise AssertionError("native observer changed canonical ONE wire/stats")
    if (
        benabled != cenabled
        or int(bresult.best_shift) != int(cresult.best_shift)
        or int(bresult.exact_proofs) != int(cresult.exact_proofs)
    ):
        raise AssertionError("native observer changed downstream relation classification")
    if _plan_signature(bplan) != _plan_signature(cplan):
        raise AssertionError("native observer changed native segment plan")
    if cenabled and _plan_signature(cplan) != _plan_signature(_oracle_plan(source, target)):
        raise AssertionError("native segment plan diverged from independent Python oracle")

    outputs, vm_stats = evaluate(decode_program(cwire))
    if outputs != {"previous": source, "current": target}:
        raise AssertionError("native-observer writer failed exact reconstruction")

    return {
        "canonical_wire_bytes": cstats.total_bytes,
        "surprise_bytes": cstats.surprise_bytes,
        "control_integrity_bytes": cstats.control_integrity_bytes,
        "relation_enabled": cenabled,
        "best_shift": int(cresult.best_shift),
        "exact_proofs": int(cresult.exact_proofs),
        "reader_work_bytes": vm_stats.work_bytes,
        "reader_materialized_bytes": vm_stats.materialized_bytes,
    }


def run():
    # Compile/warm native observation outside timed samples.
    observe_native(b"warmup" * 32)
    admission_fn, segment_fn, td = _build_native()
    rows = []
    semantic_ok = True
    row_timing_ok = True
    try:
        for size in SIZES:
            source, cases = _update_cases(size)
            src_arr = (ctypes.c_uint8 * size).from_buffer_copy(source)
            for case, target in cases.items():
                if len(target) != size:
                    raise AssertionError(f"full-ingest transfer requires equal-sized pair: {case=}")
                dst_arr = (ctypes.c_uint8 * size).from_buffer_copy(target)
                seg_buf = (Segment * size)()

                def baseline_call():
                    return _ingest_once(
                        native_observer=False,
                        source=source,
                        target=target,
                        admission_fn=admission_fn,
                        segment_fn=segment_fn,
                        src_arr=src_arr,
                        dst_arr=dst_arr,
                        seg_buf=seg_buf,
                    )

                def candidate_call():
                    return _ingest_once(
                        native_observer=True,
                        source=source,
                        target=target,
                        admission_fn=admission_fn,
                        segment_fn=segment_fn,
                        src_arr=src_arr,
                        dst_arr=dst_arr,
                        seg_buf=seg_buf,
                    )

                baseline = baseline_call()
                candidate = candidate_call()
                try:
                    semantic = _semantic_check(source, target, baseline, candidate)
                except AssertionError:
                    semantic_ok = False
                    raise

                medians, last = _paired_medians(baseline_call, candidate_call)
                if last["baseline"] is None or last["candidate"] is None:
                    raise AssertionError("missing timed writer result")
                timed_semantic = _semantic_check(source, target, last["baseline"], last["candidate"])
                if timed_semantic != semantic:
                    raise AssertionError("timed writer semantics/accounting changed")

                bwall = medians["baseline"]["total_wall_ns"]
                bcpu = medians["baseline"]["total_cpu_ns"]
                cwall = medians["candidate"]["total_wall_ns"]
                ccpu = medians["candidate"]["total_cpu_ns"]
                wall_ratio = cwall / bwall
                cpu_ratio = ccpu / bcpu
                passed = wall_ratio <= ROW_LIMIT and cpu_ratio <= ROW_LIMIT
                row_timing_ok &= passed

                obs = candidate["observation"]
                rows.append({
                    "size": size,
                    "case": case,
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
                    "baseline_hash_cpu_ns": medians["baseline"]["hash_cpu_ns"],
                    "candidate_hash_cpu_ns": medians["candidate"]["hash_cpu_ns"],
                    "baseline_writer_cpu_ns": medians["baseline"]["writer_cpu_ns"],
                    "candidate_writer_cpu_ns": medians["candidate"]["writer_cpu_ns"],
                    "baseline_observe_share_cpu": medians["baseline"]["observe_cpu_ns"] / bcpu,
                    "candidate_observe_share_cpu": medians["candidate"]["observe_cpu_ns"] / ccpu,
                    "gate_limit": ROW_LIMIT,
                    "gate_pass": passed,
                    "observation_source_read_bytes": obs.stats.total_source_read_bytes,
                    "observation_verification_read_bytes": obs.stats.verification_read_bytes,
                    "observation_retained_index_payload_bytes": obs.stats.retained_index_payload_bytes,
                    **semantic,
                })

        cpu_ratios = [row["cpu_ratio"] for row in rows]
        wall_ratios = [row["wall_ratio"] for row in rows]
        median_cpu = float(statistics.median(cpu_ratios))
        median_wall = float(statistics.median(wall_ratios))
        median_ok = median_cpu <= MEDIAN_LIMIT and median_wall <= MEDIAN_LIMIT

        if not semantic_ok:
            decision = "INVALIDATE_NATIVE_OBSERVER_FULL_INGEST"
        elif row_timing_ok and median_ok:
            decision = "ADVANCE_NATIVE_OBSERVER_FULL_INGEST"
        else:
            decision = "HOLD_NATIVE_OBSERVER_FULL_INGEST"

        return {
            "schema": "cmpct-one-g02-native-observer-full-ingest-v1",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "repetitions": REPETITIONS,
            "timing_order": "paired alternating A/B-B/A",
            "median_limit": MEDIAN_LIMIT,
            "row_limit": ROW_LIMIT,
            "semantic_gates_pass": semantic_ok,
            "row_timing_gates_pass": row_timing_ok,
            "median_timing_gate_pass": median_ok,
            "median_cpu_ratio": median_cpu,
            "median_wall_ratio": median_wall,
            "decision": decision,
            "claim_boundary": (
                "adjacent-version research-writer transfer of exact native fresh observation; "
                "charges root hashes, relation admission, native segmentation, generic Program construction, "
                "full validation and direct canonical emission; no authenticated placement, product-native RSS, "
                "recovery/portability or Genesis comparator supremacy claim"
            ),
            "rows": rows,
        }
    finally:
        td.cleanup()


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["decision"] == "ADVANCE_NATIVE_OBSERVER_FULL_INGEST" else 1)
