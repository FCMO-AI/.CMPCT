"""ONE-G0.2 native writer stage-owner profiler.

Preregistered by ONE_G02_NATIVE_WRITER_STAGE_OWNER_PREREG_2026-09-07.md.
This is a descriptive owner-localization experiment, not a product-speed gate.
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
    CONTROLS,
    PRODUCTIVE,
    SIZES,
    Segment,
    SegmentStats,
    _admit,
    _build_native,
    _native_plan,
    _oracle_plan,
    _plan_signature,
    _relation_cases,
)
from benchmarks.one.one_g02_post_segment_control_cost_owner import (
    _literal_program,
    _program_from_plan,
)
from experiments.one.growable_wire import _encode_program_growable_prevalidated
from experiments.one.ir import Ref, Root
from experiments.one.native_observe import observe_native
from experiments.one.vm import evaluate
from experiments.one.wire import decode_program

REPETITIONS = 15
OWNER_SHARE = 0.20
CLUSTER_SHARE = 0.40
MIN_OWNER_ROWS_1M = 2
STAGES = (
    "root_hash",
    "native_observe",
    "relation_admission",
    "native_segmentation",
    "program_construction",
    "validation",
    "canonical_emission",
)
ADJACENT_CLUSTERS = tuple(zip(STAGES, STAGES[1:]))


def _timed(fn):
    c0 = time.process_time_ns()
    w0 = time.perf_counter_ns()
    value = fn()
    w1 = time.perf_counter_ns()
    c1 = time.process_time_ns()
    return value, w1 - w0, c1 - c0


def _profile_row(admission_fn, segment_fn, source: bytes, target: bytes):
    n = len(source)
    src_arr = (ctypes.c_uint8 * n).from_buffer_copy(source)
    dst_arr = (ctypes.c_uint8 * n).from_buffer_copy(target)
    seg_buf = (Segment * n)()
    wall = {stage: [] for stage in STAGES}
    cpu = {stage: [] for stage in STAGES}
    last = None

    was_enabled = gc.isenabled()
    try:
        if was_enabled:
            gc.disable()
        for _ in range(REPETITIONS):
            hashes, w, c = _timed(lambda: (sha256(source).hexdigest(), sha256(target).hexdigest()))
            wall["root_hash"].append(w)
            cpu["root_hash"].append(c)
            previous_digest, current_digest = hashes
            previous_root = Root(Ref(0), len(source), previous_digest)

            observation, w, c = _timed(lambda: observe_native(target))
            wall["native_observe"].append(w)
            cpu["native_observe"].append(c)

            admitted, w, c = _timed(lambda: _admit(admission_fn, src_arr, dst_arr, n))
            wall["relation_admission"].append(w)
            cpu["relation_admission"].append(c)
            result, gate_reads, gate_used, enabled = admitted

            segment_stats = SegmentStats()
            if enabled:
                plan, w, c = _timed(lambda: _native_plan(segment_fn, src_arr, dst_arr, n, seg_buf, segment_stats))
            else:
                plan = ()
                w = c = 0
            wall["native_segmentation"].append(w)
            cpu["native_segmentation"].append(c)

            if enabled:
                built, w, c = _timed(
                    lambda: _program_from_plan(source, target, plan, previous_root, current_digest)
                )
            else:
                built, w, c = _timed(
                    lambda: _literal_program(source, target, previous_root, current_digest)
                )
            wall["program_construction"].append(w)
            cpu["program_construction"].append(c)
            program, hierarchy_depth = built

            _, w, c = _timed(program.validate_shape)
            wall["validation"].append(w)
            cpu["validation"].append(c)

            emitted, w, c = _timed(lambda: _encode_program_growable_prevalidated(program))
            wall["canonical_emission"].append(w)
            cpu["canonical_emission"].append(c)
            wire, stats = emitted

            last = {
                "observation": observation,
                "result": result,
                "gate_reads": gate_reads,
                "gate_used": gate_used,
                "enabled": enabled,
                "plan": plan,
                "segment_stats": segment_stats,
                "program": program,
                "hierarchy_depth": hierarchy_depth,
                "wire": wire,
                "stats": stats,
                "previous_digest": previous_digest,
                "current_digest": current_digest,
            }
    finally:
        if was_enabled:
            gc.enable()

    assert last is not None
    wall_med = {stage: float(statistics.median(wall[stage])) for stage in STAGES}
    cpu_med = {stage: float(statistics.median(cpu[stage])) for stage in STAGES}
    wall_total = sum(wall_med.values())
    cpu_total = sum(cpu_med.values())
    wall_share = {stage: (wall_med[stage] / wall_total if wall_total else 0.0) for stage in STAGES}
    cpu_share = {stage: (cpu_med[stage] / cpu_total if cpu_total else 0.0) for stage in STAGES}
    return last, wall_med, cpu_med, wall_total, cpu_total, wall_share, cpu_share


def _decision(rows):
    million = [row for row in rows if row["relation_bytes"] == (1 << 20)]
    counts = {
        stage: sum(row["wall_share"][stage] >= OWNER_SHARE for row in million)
        for stage in STAGES
    }
    qualifying = [stage for stage, count in counts.items() if count >= MIN_OWNER_ROWS_1M]
    if qualifying:
        stage = max(
            qualifying,
            key=lambda name: statistics.median(row["wall_share"][name] for row in million),
        )
        return f"OWNER_{stage.upper()}", counts

    cluster_counts = {}
    for a, b in ADJACENT_CLUSTERS:
        key = f"{a}+{b}"
        cluster_counts[key] = sum(
            row["wall_share"][a] + row["wall_share"][b] >= CLUSTER_SHARE
            for row in million
        )
    qualifying_clusters = [key for key, count in cluster_counts.items() if count >= MIN_OWNER_ROWS_1M]
    if qualifying_clusters:
        key = max(
            qualifying_clusters,
            key=lambda name: statistics.median(
                row["wall_share"][name.split("+")[0]] + row["wall_share"][name.split("+")[1]]
                for row in million
            ),
        )
        return "OWNER_CLUSTER_" + key.replace("+", "_").upper(), {**counts, **cluster_counts}
    return "NO_STABLE_OWNER_FUSE_BOUNDARY", {**counts, **cluster_counts}


def run():
    # Compile/load outside result timing so compiler startup cannot own the writer.
    observe_native(b"warmup" * 32)
    admission_fn, segment_fn, td = _build_native()
    rows = []
    semantic_ok = True
    oracle_ok = True
    try:
        for size in SIZES:
            cases = _relation_cases(size)
            for case in PRODUCTIVE + CONTROLS:
                source, target, expected_enable, expected_shift = cases[case]
                profiled = _profile_row(admission_fn, segment_fn, source, target)
                last, wall_med, cpu_med, wall_total, cpu_total, wall_share, cpu_share = profiled

                program = last["program"]
                wire = last["wire"]
                stats = last["stats"]
                result = last["result"]
                enabled = last["enabled"]
                plan = last["plan"]
                observation = last["observation"]
                segment_stats = last["segment_stats"]

                if enabled:
                    this_oracle = _plan_signature(plan) == _plan_signature(_oracle_plan(source, target))
                else:
                    this_oracle = True
                oracle_ok &= this_oracle

                decoded = decode_program(wire)
                outputs, vm_stats = evaluate(decoded)
                roots_exact = (
                    program.roots["previous"].sha256 == sha256(source).hexdigest()
                    and program.roots["current"].sha256 == sha256(target).hexdigest()
                )
                exact = outputs == {"previous": source, "current": target}
                this_semantic = roots_exact and exact and this_oracle
                semantic_ok &= this_semantic
                if not this_semantic:
                    raise AssertionError(f"native writer stage profile changed semantics: {size=} {case=}")

                rows.append({
                    "relation_bytes": size,
                    "case": case,
                    "expected_enable": expected_enable,
                    "expected_shift": expected_shift,
                    "relation_enabled": enabled,
                    "best_shift": int(result.best_shift),
                    "exact_proofs": int(result.exact_proofs),
                    "gate_compared_bytes": last["gate_reads"],
                    "used_sparse_gate": last["gate_used"],
                    "observer_source_scan_bytes": observation.stats.source_scan_bytes,
                    "observer_total_source_read_bytes": observation.stats.total_source_read_bytes,
                    "observer_peak_index_entries": observation.stats.peak_index_entries,
                    "observer_retained_index_payload_bytes": observation.stats.retained_index_payload_bytes,
                    "native_segment_compared_target_bytes": int(segment_stats.compared_target_bytes),
                    "segments": int(segment_stats.segments),
                    "modeled_segment_plan_bytes": int(segment_stats.segments) * ctypes.sizeof(Segment),
                    "native_plan_matches_python_oracle": this_oracle,
                    "hierarchy_depth": last["hierarchy_depth"],
                    "program_nodes": len(program.nodes),
                    "canonical_wire_bytes": stats.total_bytes,
                    "surprise_bytes": stats.surprise_bytes,
                    "control_integrity_bytes": stats.control_integrity_bytes,
                    "reader_work_bytes": vm_stats.work_bytes,
                    "reader_materialized_bytes": vm_stats.materialized_bytes,
                    "stage_wall_median_ns": wall_med,
                    "stage_cpu_median_ns": cpu_med,
                    "profiled_wall_total_ns": wall_total,
                    "profiled_cpu_total_ns": cpu_total,
                    "wall_share": wall_share,
                    "cpu_share": cpu_share,
                    "root_hashes_exact": roots_exact,
                    "exact_reconstruction": exact,
                })

        if not semantic_ok or not oracle_ok:
            decision = "INVALIDATE_PROFILE"
            ownership_counts = {}
        else:
            decision, ownership_counts = _decision(rows)
        return {
            "schema": "cmpct-one-g02-native-writer-stage-owner-v1",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "repetitions": REPETITIONS,
            "owner_share_threshold": OWNER_SHARE,
            "cluster_share_threshold": CLUSTER_SHARE,
            "minimum_qualifying_1m_rows": MIN_OWNER_ROWS_1M,
            "semantic_gates_pass": semantic_ok,
            "native_plan_oracle_pass": oracle_ok,
            "decision": decision,
            "ownership_counts": ownership_counts,
            "claim_boundary": (
                "descriptive stage ownership in the current adjacent-version research-writer envelope; "
                "charges root SHA-256, native fresh observation, relation admission, native segmentation, "
                "generic Program construction, validation and direct canonical emission; does not establish "
                "product writer speed, authenticated placement/durability, full arbitrary discovery, or "
                "v0.29/v0.30 superiority"
            ),
            "rows": rows,
        }
    finally:
        td.cleanup()


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(1 if result["decision"] == "INVALIDATE_PROFILE" else 0)
