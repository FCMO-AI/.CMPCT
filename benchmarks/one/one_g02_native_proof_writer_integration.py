"""ONE-G0.2 native exact-proof full-writer integration falsifier.

Frozen by ONE_G02_NATIVE_PROOF_WRITER_INTEGRATION_PREREG_2026-09-09.md.
This changes only V4's exact-proof implementation: promoted gate/seed geometry, generic
ONE Program construction, validation, canonical emission, and incumbent fallback remain.
"""
from __future__ import annotations

import ctypes
import gc
import json
import statistics
import time

import benchmarks.one.one_g02_relation_writer_envelope_v2 as v2
import benchmarks.one.one_g02_relation_writer_envelope_v3 as v3
import benchmarks.one.one_g02_sparse_native_seed_transfer as v4
from experiments.one.native_relation_span_growth import grow_relation_spans_native_metered

MIN_NOVEL_WIRE_SAVING = 0.25
MIN_MEDIAN_MARGINAL_MBIT_PER_CPU_S = 20.0
MAX_MEDIAN_CONTROL_CPU_RATIO = 1.35
MAX_CONTROL_CPU_RATIO = 1.75
MAX_MEDIAN_NOVEL_CPU_OVER_V4 = 0.60
MAX_NOVEL_CPU_OVER_V4 = 0.80
MAX_MEDIAN_CONTROL_CPU_OVER_V4 = 1.10
MAX_CONTROL_CPU_OVER_V4 = 1.25
MAX_PHYSICAL_PROOF_LOAD_AMPLIFICATION = 1.01
MAX_STATE_RATIO = 0.60
MAX_POSITIVE_TOTAL_PROBE_RATIO = 0.09375
ROUNDS = v3.ROUNDS


def _candidate_once(ctx):
    incumbent = v2._incumbent_once(*ctx)
    iwire, _istats, iprogram, *_ = incumbent

    c0 = time.process_time_ns()
    gop, gvalue, gout = v3._gate(ctx[2], ctx[3])
    gate_cpu = time.process_time_ns() - c0
    if gop is None:
        return (
            incumbent, iwire, iprogram, None, 0, 0, "incumbent",
            gate_cpu, 0, 0, 0, int(gout.probe_bytes), 0, 0, 0,
        )

    c0 = time.process_time_ns()
    seeds, seed_probe_bytes = v4._collect_seeds_nocopy(ctx[2], ctx[3], gop, int(gvalue))
    seed_cpu = time.process_time_ns() - c0

    c0 = time.process_time_ns()
    result, loaded_per_input = grow_relation_spans_native_metered(
        ctx[2], ctx[3], op=gop, value=int(gvalue), nominations=seeds,
        seed_bytes=v2.SEED_BYTES, extension_bytes=v2.EXTENSION_BYTES,
    )
    proof_cpu = time.process_time_ns() - c0
    proof = result.compared_bytes
    accepted = result.accepted_bytes

    emit_cpu = 0
    best_wire = None
    best_program = None
    if result.runs:
        c0 = time.process_time_ns()
        program = v2._generic_program(ctx[2], ctx[3], gop, int(gvalue), result.runs, iprogram.roots)
        program.validate_shape()
        wire, _stats = v2._encode_program_growable_prevalidated(program)
        emit_cpu = time.process_time_ns() - c0
        best_wire, best_program = wire, program

    if best_wire is not None and len(best_wire) < len(iwire):
        return (
            incumbent, best_wire, best_program, (gop, int(gvalue)), proof, accepted, "generic",
            gate_cpu, seed_cpu, proof_cpu, emit_cpu, int(gout.probe_bytes), seed_probe_bytes,
            len(seeds), loaded_per_input,
        )
    return (
        incumbent, iwire, iprogram, (gop, int(gvalue)), proof, accepted, "incumbent",
        gate_cpu, seed_cpu, proof_cpu, emit_cpu, int(gout.probe_bytes), seed_probe_bytes,
        len(seeds), loaded_per_input,
    )


def _time_three(ctx):
    values = {"i": None, "v4": None, "native": None}
    walls = {k: [] for k in values}
    cpus = {k: [] for k in values}
    stage_rows = []
    enabled = gc.isenabled()
    try:
        if enabled:
            gc.disable()
        # Warm both native helper libraries and Python/ctypes allocation paths outside timing.
        v4._candidate_once(ctx)
        _candidate_once(ctx)
        for r in range(ROUNDS):
            base = ("i", "v4", "native")
            order = base[r % 3:] + base[:r % 3]
            for arm in order:
                w0 = time.perf_counter_ns(); c0 = time.process_time_ns()
                if arm == "i":
                    val = v2._incumbent_once(*ctx)
                elif arm == "v4":
                    val = v4._candidate_once(ctx)
                else:
                    val = _candidate_once(ctx)
                cpu = time.process_time_ns() - c0
                wall = time.perf_counter_ns() - w0
                values[arm] = val
                cpus[arm].append(cpu); walls[arm].append(wall)
                if arm == "native":
                    stage_rows.append(val[7:11])
    finally:
        if enabled:
            gc.enable()
    med = lambda xs: int(statistics.median(xs))
    stage = [med([s[k] for s in stage_rows]) for k in range(4)]
    return values, {k: med(v) for k, v in walls.items()}, {k: med(v) for k, v in cpus.items()}, stage


def run():
    admission_fn, segment_fn, td = v2._build_native()
    rows = []
    novel_yields = []
    novel_over_v4 = []
    control_abs = []
    control_over_v4 = []
    try:
        for n in v2.VERSION_SIZES:
            for family in v2.FAMILIES:
                source, target, expected_op, expected_value, kind = v2._case(n, family)
                src_arr = (ctypes.c_uint8 * n).from_buffer_copy(source)
                dst_arr = (ctypes.c_uint8 * n).from_buffer_copy(target)
                seg_buf = (v2.Segment * n)()
                ctx = (admission_fn, segment_fn, source, target, src_arr, dst_arr, seg_buf)
                vals, wall, cpu, stages = _time_three(ctx)
                incumbent = vals["i"]
                v4c = vals["v4"]
                native = vals["native"]
                if incumbent is None or v4c is None or native is None:
                    raise AssertionError("missing timed arm")

                iwire = incumbent[0]
                v4wire = v4c[1]
                v4program = v4c[2]
                v4gate = v4c[3]
                v4proof = int(v4c[4])
                v4accepted = int(v4c[5])
                v4selection = v4c[6]
                v4gate_probe = int(v4c[11])
                v4seed_probe = int(v4c[12])
                v4seed_count = int(v4c[13])

                ninc, nwire, nprogram, gate_choice, proof, accepted, selection, gate_cpu, seed_cpu, proof_cpu, emit_cpu, gate_probe, seed_probe, seed_count, loaded_per_input = native

                iexact, _ = v2._decode_exact(iwire, source, target)
                v4exact, _ = v2._decode_exact(v4wire, source, target)
                nexact, nm = v2._decode_exact(nwire, source, target)
                semantic = (
                    iexact and v4exact and nexact
                    and ninc[0] == iwire
                    and nwire == v4wire
                    and selection == v4selection
                    and accepted == v4accepted
                    and proof == v4proof
                    and gate_choice == v4gate
                    and gate_probe == v4gate_probe
                    and seed_probe == v4seed_probe
                    and seed_count == v4seed_count
                    and nprogram.roots["previous"].sha256 == v4program.roots["previous"].sha256
                    and nprogram.roots["current"].sha256 == v4program.roots["current"].sha256
                )

                expected_gate = (expected_op, expected_value) if kind == "novel" else None
                gate_correct = gate_choice == expected_gate
                bytes_saved = len(iwire) - len(nwire)
                inc_ns = cpu["native"] - cpu["i"]
                marginal = (
                    (bytes_saved * 8.0) / (inc_ns / 1e9) / 1e6
                    if bytes_saved > 0 and inc_ns > 0
                    else (1.0e99 if bytes_saved > 0 else 0.0)
                )
                abs_ratio = cpu["native"] / max(cpu["i"], 1)
                over_v4 = cpu["native"] / max(cpu["v4"], 1)
                combined = 2 * n
                total_probe_ratio = (gate_probe + seed_probe) / combined
                state_ratio = (4096 + 8 * seed_count) / combined
                load_amp = loaded_per_input / max(proof, 1)

                if kind == "novel":
                    novel_yields.append(marginal)
                    novel_over_v4.append(over_v4)
                elif kind == "control":
                    control_abs.append(abs_ratio)
                    control_over_v4.append(over_v4)

                rows.append({
                    "version_bytes": n,
                    "family": family,
                    "kind": kind,
                    "semantic_ok": semantic,
                    "gate_choice": gate_choice,
                    "expected_gate": expected_gate,
                    "gate_correct": gate_correct,
                    "selection": selection,
                    "accepted_relation_bytes": accepted,
                    "proof_compared_bytes": proof,
                    "native_loaded_bytes_per_input": loaded_per_input,
                    "native_loaded_bytes_parent_plus_child": 2 * loaded_per_input,
                    "native_load_amplification_over_semantic": load_amp,
                    "incumbent_wire_bytes": len(iwire),
                    "v4_wire_bytes": len(v4wire),
                    "native_wire_bytes": len(nwire),
                    "wire_saving_fraction": bytes_saved / len(iwire),
                    "native_over_incumbent_cpu": abs_ratio,
                    "native_over_v4_cpu": over_v4,
                    "native_over_v4_wall": wall["native"] / max(wall["v4"], 1),
                    "marginal_mbit_eliminated_per_cpu_s": marginal,
                    "gate_probe_bytes": gate_probe,
                    "seed_probe_bytes": seed_probe,
                    "total_relation_probe_ratio": total_probe_ratio,
                    "modeled_relation_state_ratio": state_ratio,
                    "gate_cpu_ns": stages[0],
                    "seed_transfer_cpu_ns": stages[1],
                    "native_proof_cpu_ns": stages[2],
                    "program_emit_cpu_ns": stages[3],
                    "candidate_reader_work_bytes": nm.work_bytes,
                    "candidate_reader_materialized_bytes": nm.materialized_bytes,
                })
    finally:
        td.cleanup()

    novel = [r for r in rows if r["kind"] == "novel"]
    controls = [r for r in rows if r["kind"] == "control"]
    proof_rows = [r for r in rows if r["proof_compared_bytes"] > 0]
    invalid = (
        any(not r["semantic_ok"] for r in rows)
        or any(r["kind"] == "novel" and not r["gate_correct"] for r in rows)
        or any(r["kind"] != "novel" and r["gate_choice"] is not None for r in rows)
        or any(r["kind"] == "control" and r["proof_compared_bytes"] != 0 for r in rows)
        or any(r["native_loaded_bytes_per_input"] < r["proof_compared_bytes"] for r in proof_rows)
    )
    hold = (
        any(r["wire_saving_fraction"] < MIN_NOVEL_WIRE_SAVING for r in novel)
        or statistics.median(novel_yields) < MIN_MEDIAN_MARGINAL_MBIT_PER_CPU_S
        or statistics.median(control_abs) > MAX_MEDIAN_CONTROL_CPU_RATIO
        or max(control_abs) > MAX_CONTROL_CPU_RATIO
        or statistics.median(novel_over_v4) > MAX_MEDIAN_NOVEL_CPU_OVER_V4
        or max(novel_over_v4) > MAX_NOVEL_CPU_OVER_V4
        or statistics.median(control_over_v4) > MAX_MEDIAN_CONTROL_CPU_OVER_V4
        or max(control_over_v4) > MAX_CONTROL_CPU_OVER_V4
        or any(r["native_load_amplification_over_semantic"] > MAX_PHYSICAL_PROOF_LOAD_AMPLIFICATION for r in proof_rows)
        or any(r["modeled_relation_state_ratio"] > MAX_STATE_RATIO for r in rows)
        or any(r["kind"] == "novel" and r["total_relation_probe_ratio"] > MAX_POSITIVE_TOTAL_PROBE_RATIO for r in rows)
    )
    decision = (
        "INVALIDATE_NATIVE_PROOF_WRITER_INTEGRATION" if invalid else
        "HOLD_NATIVE_PROOF_WRITER_INTEGRATION" if hold else
        "ADVANCE_NATIVE_PROOF_WRITER_INTEGRATION"
    )
    payload = {
        "experiment": "ONE-G0.2 native exact-proof writer integration",
        "decision": decision,
        "source_sha": __import__("os").environ.get("EVIDENCE_HEAD"),
        "median_novel_marginal_mbit_per_cpu_s": statistics.median(novel_yields),
        "median_novel_cpu_over_v4": statistics.median(novel_over_v4),
        "worst_novel_cpu_over_v4": max(novel_over_v4),
        "median_control_cpu_over_incumbent": statistics.median(control_abs),
        "worst_control_cpu_over_incumbent": max(control_abs),
        "median_control_cpu_over_v4": statistics.median(control_over_v4),
        "worst_control_cpu_over_v4": max(control_over_v4),
        "worst_native_load_amplification": max((r["native_load_amplification_over_semantic"] for r in proof_rows), default=0.0),
        "rows": rows,
    }
    print(json.dumps(payload, sort_keys=True))
    return 0 if decision == "ADVANCE_NATIVE_PROOF_WRITER_INTEGRATION" else 1


if __name__ == "__main__":
    raise SystemExit(run())
