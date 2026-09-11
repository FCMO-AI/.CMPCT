"""ONE-G0.2 relation writer-envelope falsifier.

Frozen by ONE_G02_RELATION_WRITER_ENVELOPE_PREREG_2026-09-09.md.
The candidate charges shared block observation, witness grouping, exact maximal-span
proof, generic Program construction, validation and direct final-buffer emission.
The baseline is the same generic direct writer with relation discovery disabled.
"""
from __future__ import annotations

import gc
import json
import random
import statistics
import time
import zlib

from benchmarks.one.one_g02_relation_witness_transfer import (
    BLOCK,
    EXTENSION_BYTES,
    PROBES,
    SEED_BYTES,
    _case as witness_case,
    _compile,
    _group_witnesses,
    _literal,
)
from experiments.one.block_relation_witness import observe_relation_witnesses
from experiments.one.growable_wire import _encode_program_growable_prevalidated
from experiments.one.relation_span_growth import grow_relation_spans
from experiments.one.vm import evaluate
from experiments.one.wire import decode_program

SIZES = (64 * 1024, 256 * 1024, 1024 * 1024)
POSITIVES = ("add8_versioned", "xor_versioned", "add8_sparse_cracks", "xor_sparse_cracks")
CONTROLS = ("exact_repeat", "random", "compressed_like", "probe_false_positive")
FAMILIES = POSITIVES + CONTROLS
ROUNDS = 9

MIN_POSITIVE_WIRE_SAVING = 0.25
MIN_MEDIAN_MARGINAL_MBIT_PER_CPU_S = 20.0
MAX_FALSE_PROOF_BYTES = 8192
MAX_PROBE_RATIO = 0.05
MAX_STATE_RATIO = 0.60
MAX_MEDIAN_CONTROL_CPU_RATIO = 1.35
MAX_CONTROL_CPU_RATIO = 1.75


def _compressed_like(size: int) -> bytes:
    rng = random.Random(0xC011A55 ^ size)
    raw = bytes(rng.randrange(256) for _ in range(size + 4096))
    packed = zlib.compress(raw, level=9)
    if len(packed) < size:
        raise AssertionError("compressed-like generator unexpectedly too short")
    return packed[:size]


def _case(size: int, family: str):
    if family == "compressed_like":
        return _compressed_like(size), None, None, False
    return witness_case(size, family)


def _direct_emit(program):
    program.validate_shape()
    return _encode_program_growable_prevalidated(program)


def _baseline_once(data: bytes):
    program = _literal(data)  # includes SHA-256 root identity construction
    wire, stats = _direct_emit(program)
    return program, wire, stats


def _candidate_program(data: bytes):
    half = len(data) // 2
    parent, child = data[:half], data[half:]
    obs = observe_relation_witnesses(data)
    total_proof = 0
    best = None
    best_accepted = 0
    chosen = None

    # Witness count is only nomination evidence. Exact proof owns admission.
    for (op, value), nominations in _group_witnesses(obs, half):
        result = grow_relation_spans(
            parent,
            child,
            op=op,
            value=value,
            nominations=tuple(nominations),
            seed_bytes=SEED_BYTES,
            extension_bytes=EXTENSION_BYTES,
        )
        total_proof += result.compared_bytes
        if not result.runs:
            continue
        if result.accepted_bytes > best_accepted:
            best = _compile(parent, child, op, value, result.runs)
            best_accepted = result.accepted_bytes
            chosen = (op, value)

    if best is None:
        best = _literal(data)
    return obs, best, total_proof, best_accepted, chosen


def _candidate_once(data: bytes):
    obs, program, proof, accepted, chosen = _candidate_program(data)
    wire, stats = _direct_emit(program)
    return obs, program, wire, stats, proof, accepted, chosen


def _time_pair(data: bytes):
    baseline_wall = []
    baseline_cpu = []
    candidate_wall = []
    candidate_cpu = []
    baseline_value = None
    candidate_value = None
    was_enabled = gc.isenabled()
    try:
        if was_enabled:
            gc.disable()
        for round_index in range(ROUNDS):
            order = ("baseline", "candidate") if round_index % 2 == 0 else ("candidate", "baseline")
            for arm in order:
                w0 = time.perf_counter_ns()
                c0 = time.process_time_ns()
                if arm == "baseline":
                    value = _baseline_once(data)
                else:
                    value = _candidate_once(data)
                cpu = time.process_time_ns() - c0
                wall = time.perf_counter_ns() - w0
                if arm == "baseline":
                    baseline_wall.append(wall)
                    baseline_cpu.append(cpu)
                    baseline_value = value
                else:
                    candidate_wall.append(wall)
                    candidate_cpu.append(cpu)
                    candidate_value = value
    finally:
        if was_enabled:
            gc.enable()
    return (
        baseline_value,
        int(statistics.median(baseline_wall)),
        int(statistics.median(baseline_cpu)),
        candidate_value,
        int(statistics.median(candidate_wall)),
        int(statistics.median(candidate_cpu)),
    )


def _exact(wire: bytes, data: bytes) -> tuple[bool, int, int]:
    decoded = decode_program(wire)
    outputs, vm_stats = evaluate(decoded)
    return outputs.get("root") == data, vm_stats.work_bytes, vm_stats.materialized_bytes


def run():
    rows = []
    positive_yields = []
    control_cpu_ratios = []
    semantic_ok = True

    for size in SIZES:
        for family in FAMILIES:
            data, expected_op, expected_value, positive = _case(size, family)
            (
                baseline,
                baseline_wall_ns,
                baseline_cpu_ns,
                candidate,
                candidate_wall_ns,
                candidate_cpu_ns,
            ) = _time_pair(data)
            if baseline is None or candidate is None:
                raise AssertionError("missing timed writer value")

            bprogram, bwire, bstats = baseline
            obs, cprogram, cwire, cstats, proof, accepted, chosen = candidate
            bexact, bwork, bmaterialized = _exact(bwire, data)
            cexact, cwork, cmaterialized = _exact(cwire, data)
            this_semantic = bexact and cexact
            semantic_ok &= this_semantic
            if not this_semantic:
                raise AssertionError("relation writer envelope changed reconstruction semantics")

            saved = len(bwire) - len(cwire)
            saving_fraction = saved / len(bwire)
            incremental_cpu_ns = candidate_cpu_ns - baseline_cpu_ns
            if saved > 0 and incremental_cpu_ns <= 0:
                marginal_mbit = 1.0e99
            elif saved > 0:
                marginal_mbit = (saved * 8.0) / (incremental_cpu_ns / 1e9) / 1e6
            else:
                marginal_mbit = 0.0

            expected_relation = (
                chosen is not None
                and chosen[0] == expected_op
                and chosen[1] == expected_value
            ) if positive else chosen is None

            cpu_ratio = candidate_cpu_ns / max(baseline_cpu_ns, 1)
            wall_ratio = candidate_wall_ns / max(baseline_wall_ns, 1)
            if positive:
                positive_yields.append(marginal_mbit)
            else:
                control_cpu_ratios.append(cpu_ratio)

            rows.append({
                "size": size,
                "family": family,
                "positive": positive,
                "semantic_ok": this_semantic,
                "chosen": chosen,
                "correct_relation": expected_relation,
                "baseline_wire_bytes": len(bwire),
                "candidate_wire_bytes": len(cwire),
                "wire_saving_fraction": saving_fraction,
                "bytes_saved": saved,
                "baseline_writer_wall_ns": baseline_wall_ns,
                "baseline_writer_cpu_ns": baseline_cpu_ns,
                "candidate_writer_wall_ns": candidate_wall_ns,
                "candidate_writer_cpu_ns": candidate_cpu_ns,
                "candidate_over_baseline_wall": wall_ratio,
                "candidate_over_baseline_cpu": cpu_ratio,
                "incremental_cpu_ns": incremental_cpu_ns,
                "marginal_mbit_eliminated_per_cpu_s": marginal_mbit,
                "source_scan_bytes": obs.source_scan_bytes,
                "source_scan_ratio": obs.source_scan_bytes / len(data),
                "probe_bytes": obs.probe_bytes,
                "probe_ratio": obs.probe_bytes / len(data),
                "modeled_observation_state_bytes": obs.modeled_state_bytes,
                "state_ratio": obs.modeled_state_bytes / len(data),
                "retained_records": obs.retained_records,
                "witnesses": len(obs.witnesses),
                "proof_bytes": proof,
                "accepted_relation_bytes": accepted,
                "baseline_program_nodes": len(bprogram.nodes),
                "candidate_program_nodes": len(cprogram.nodes),
                "baseline_reader_work_bytes": bwork,
                "candidate_reader_work_bytes": cwork,
                "baseline_reader_materialized_bytes": bmaterialized,
                "candidate_reader_materialized_bytes": cmaterialized,
                "baseline_wire_stats_bytes": bstats.total_bytes,
                "candidate_wire_stats_bytes": cstats.total_bytes,
            })

    if not semantic_ok or any(not r["correct_relation"] for r in rows if not r["positive"]):
        decision = "INVALIDATE_RELATION_WRITER_ENVELOPE"
    else:
        positives = [r for r in rows if r["positive"]]
        controls = [r for r in rows if not r["positive"]]
        structural_ok = (
            all(r["correct_relation"] for r in positives)
            and all(r["accepted_relation_bytes"] > 0 for r in positives)
            and all(r["wire_saving_fraction"] >= MIN_POSITIVE_WIRE_SAVING for r in positives)
            and all(r["accepted_relation_bytes"] == 0 for r in controls)
        )
        resource_ok = (
            all(r["source_scan_ratio"] == 1.0 for r in rows)
            and all(r["probe_ratio"] <= MAX_PROBE_RATIO for r in rows)
            and all(r["state_ratio"] <= MAX_STATE_RATIO for r in rows)
            and all(
                r["proof_bytes"] <= MAX_FALSE_PROOF_BYTES
                for r in controls if r["family"] == "probe_false_positive"
            )
        )
        median_yield = float(statistics.median(positive_yields))
        median_control_cpu = float(statistics.median(control_cpu_ratios))
        worst_control_cpu = max(control_cpu_ratios)
        economic_ok = (
            median_yield >= MIN_MEDIAN_MARGINAL_MBIT_PER_CPU_S
            and median_control_cpu <= MAX_MEDIAN_CONTROL_CPU_RATIO
            and worst_control_cpu <= MAX_CONTROL_CPU_RATIO
        )
        decision = (
            "ADVANCE_RELATION_WRITER_ENVELOPE"
            if structural_ok and resource_ok and economic_ok
            else "HOLD_RELATION_WRITER_ENVELOPE"
        )

    return {
        "schema": "cmpct-one-g02-relation-writer-envelope-v1",
        "experimental_version": "ONE-G0.2",
        "repetitions": ROUNDS,
        "timing_order": "alternating A/B-B/A",
        "semantic_gates_pass": semantic_ok,
        "decision": decision,
        "frozen_thresholds": {
            "min_positive_wire_saving": MIN_POSITIVE_WIRE_SAVING,
            "min_median_marginal_mbit_per_cpu_s": MIN_MEDIAN_MARGINAL_MBIT_PER_CPU_S,
            "max_false_proof_bytes": MAX_FALSE_PROOF_BYTES,
            "max_probe_ratio": MAX_PROBE_RATIO,
            "max_state_ratio": MAX_STATE_RATIO,
            "max_median_control_cpu_ratio": MAX_MEDIAN_CONTROL_CPU_RATIO,
            "max_control_cpu_ratio": MAX_CONTROL_CPU_RATIO,
        },
        "claim_boundary": (
            "Python research writer charging whole-object SHA-256 root construction, one relation observation pass, "
            "bounded witness transfer, exact maximal-span proof, generic Program construction, validation and direct "
            "final-buffer ONE emission; excludes arbitrary archive segmentation, authenticated placement/durability, "
            "filesystem fidelity, product-native RSS/throughput and Genesis comparator authority"
        ),
        "rows": rows,
    }


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["decision"] == "ADVANCE_RELATION_WRITER_ENVELOPE" else 1)
