"""ONE-G0.2 broad linear-phase attribution for the ref-fused native writer.

Frozen by ONE_G02_SIMPLE_RELATION_LINEAR_PHASE_ATTRIBUTION_PREREG_2026-09-06.md.
This is diagnostic evidence only; it does not promote a writer.
"""
from __future__ import annotations

import ctypes
import gc
from hashlib import sha256
import json
import os
import statistics
import time

import benchmarks.one.one_g02_shared_native_writer_transfer as seed
from benchmarks.one.one_g02_end_to_end_direct_emitter_writer import (
    Segment,
    SegmentStats,
    _admit,
    _build_native,
)
from benchmarks.one.one_g02_shared_native_writer_ref_fusion import _build_writer_native
from benchmarks.one.one_g02_shift_branch_bound_relation_transfer import _relation_cases
from experiments.one.wire import decode_program
from experiments.one.vm import evaluate

SIZES = (16 * 1024, 32 * 1024, 64 * 1024, 128 * 1024, 256 * 1024)
CASES = (
    "shift_plus1",
    "shift_plus1_damage_quarter",
    "fragmented_every96",
    "independent_random",
)
ROUNDS = 63
OWNER_SHARE = 0.15


def _median_ns(fn):
    samples = []
    last = None
    was_enabled = gc.isenabled()
    try:
        if was_enabled:
            gc.disable()
        for _ in range(ROUNDS):
            t0 = time.perf_counter_ns()
            last = fn()
            samples.append(time.perf_counter_ns() - t0)
    finally:
        if was_enabled:
            gc.enable()
    return float(statistics.median(samples)), last


def _hash_prepare(source: bytes, target: bytes):
    ph = sha256(source).hexdigest()
    ch = sha256(target).hexdigest()
    return seed._digest_array(ph), seed._digest_array(ch)


def _writer_only(writer_fn, free_fn, source, target, src_arr, dst_arr,
                 seg_buf, segment_count: int, enabled: bool, pd, cd):
    out = ctypes.POINTER(ctypes.c_uint8)()
    out_len = ctypes.c_size_t()
    surprise = ctypes.c_size_t()
    allocated = ctypes.c_size_t()
    depth = ctypes.c_size_t()
    nodes = ctypes.c_size_t()
    rc = writer_fn(
        src_arr, len(source), dst_arr, len(target), seg_buf, segment_count,
        pd, cd, int(enabled), ctypes.byref(out), ctypes.byref(out_len),
        ctypes.byref(surprise), ctypes.byref(allocated), ctypes.byref(depth),
        ctypes.byref(nodes),
    )
    if rc != 0:
        raise RuntimeError(f"ref-fused native writer failed: {rc}")
    try:
        wire = ctypes.string_at(out, out_len.value)
    finally:
        free_fn(out)
    return wire, int(out_len.value), int(allocated.value)


def run():
    admission_fn, segment_fn, segment_td = _build_native()
    writer_fn, free_fn, writer_td = _build_writer_native()
    rows = []
    semantic_failures = 0
    try:
        for size in SIZES:
            cases = _relation_cases(size)
            for case in CASES:
                source, target, _expected_enable, _expected_shift = cases[case]
                src_arr = (ctypes.c_uint8 * size).from_buffer_copy(source)
                dst_arr = (ctypes.c_uint8 * size).from_buffer_copy(target)
                seg_buf = (Segment * size)()

                # Freeze the exact state consumed by isolated phases.
                pd, cd = _hash_prepare(source, target)
                result, gate_reads, gate_used, enabled = _admit(
                    admission_fn, src_arr, dst_arr, size
                )
                stats = SegmentStats()
                if enabled:
                    rc = segment_fn(
                        src_arr, dst_arr, size, seg_buf, size, ctypes.byref(stats)
                    )
                    if rc != 0:
                        raise RuntimeError(f"native segmenter failed: {rc}")
                    segment_count = int(stats.segments)
                else:
                    segment_count = 0

                full = seed._candidate_once_native(
                    writer_fn, free_fn, admission_fn, segment_fn,
                    source, target, src_arr, dst_arr, seg_buf,
                )
                wire = full[0]
                outputs, _vm_stats = evaluate(decode_program(wire))
                if outputs != {"previous": source, "current": target}:
                    semantic_failures += 1
                    raise AssertionError(f"full candidate reconstruction mismatch: {case}/{size}")

                writer_check = _writer_only(
                    writer_fn, free_fn, source, target, src_arr, dst_arr,
                    seg_buf, segment_count, enabled, pd, cd,
                )
                if writer_check[0] != wire:
                    semantic_failures += 1
                    raise AssertionError(f"isolated writer changed canonical wire: {case}/{size}")

                hash_ns, _ = _median_ns(lambda: _hash_prepare(source, target))
                admit_ns, admit_last = _median_ns(
                    lambda: _admit(admission_fn, src_arr, dst_arr, size)
                )
                if bool(admit_last[3]) != bool(enabled):
                    raise AssertionError("admission phase changed classification")

                if enabled:
                    def segment_once():
                        local_stats = SegmentStats()
                        rc = segment_fn(
                            src_arr, dst_arr, size, seg_buf, size,
                            ctypes.byref(local_stats),
                        )
                        if rc != 0:
                            raise RuntimeError(f"native segmenter failed: {rc}")
                        return int(local_stats.segments)
                    segment_ns, segment_last = _median_ns(segment_once)
                    if int(segment_last) != segment_count:
                        raise AssertionError("segment phase changed segment count")
                else:
                    segment_ns = 0.0

                writer_ns, writer_last = _median_ns(
                    lambda: _writer_only(
                        writer_fn, free_fn, source, target, src_arr, dst_arr,
                        seg_buf, segment_count, enabled, pd, cd,
                    )
                )
                if writer_last[0] != wire:
                    raise AssertionError("timed writer phase changed canonical wire")

                full_ns, full_last = _median_ns(
                    lambda: seed._candidate_once_native(
                        writer_fn, free_fn, admission_fn, segment_fn,
                        source, target, src_arr, dst_arr, seg_buf,
                    )
                )
                if full_last[0] != wire:
                    raise AssertionError("timed full candidate changed canonical wire")

                phase = {
                    "root_hash_prepare": hash_ns,
                    "admission_proof": admit_ns,
                    "native_segmentation": segment_ns,
                    "native_writer_output": writer_ns,
                }
                shares = {name: value / full_ns for name, value in phase.items()}
                phase_sum = sum(phase.values())
                rows.append({
                    "relation_bytes": size,
                    "case": case,
                    "relation_enabled": enabled,
                    "segments": segment_count,
                    "gate_compared_bytes": gate_reads,
                    "used_sparse_gate": gate_used,
                    "best_shift": int(result.best_shift),
                    "exact_proofs": int(result.exact_proofs),
                    "full_candidate_median_ns": full_ns,
                    "full_candidate_ns_per_input_byte": full_ns / size,
                    "phase_median_ns": phase,
                    "phase_ns_per_input_byte": {
                        name: value / size for name, value in phase.items()
                    },
                    "phase_over_full": shares,
                    "isolated_phase_sum_over_full": phase_sum / full_ns,
                    "canonical_wire_bytes": len(wire),
                    "native_output_capacity_bytes": writer_last[2],
                    "exact_reconstruction": True,
                })

        simple = [row for row in rows if row["case"] == "shift_plus1"]
        owner_summary = {}
        for phase in ("root_hash_prepare", "admission_proof", "native_segmentation", "native_writer_output"):
            vals = [float(row["phase_over_full"][phase]) for row in simple]
            median_share = float(statistics.median(vals))
            qualifying = sum(v >= OWNER_SHARE for v in vals)
            owner_summary[phase] = {
                "median_share": median_share,
                "rows_at_or_above_0_15": qualifying,
                "credible_individual_owner": qualifying >= 4 and median_share >= OWNER_SHARE,
            }
        credible = [
            name for name, summary in owner_summary.items()
            if summary["credible_individual_owner"]
        ]
        credible.sort(key=lambda name: owner_summary[name]["median_share"], reverse=True)

        return {
            "schema": "cmpct-one-g02-simple-relation-linear-phase-attribution-v1",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "frozen_rounds": ROUNDS,
            "semantic_failures": semantic_failures,
            "owner_share_threshold": OWNER_SHARE,
            "simple_shift_owner_summary": owner_summary,
            "credible_individual_owners_ranked": credible,
            "decision": (
                "attack_largest_credible_linear_owner"
                if credible else "move_to_broader_fused_boundary"
            ),
            "claim_boundary": "diagnostic attribution on ref-fused adjacent-version research writer only; no promotion/comparator/product authority",
            "rows": rows,
        }
    finally:
        segment_td.cleanup()
        writer_td.cleanup()


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
