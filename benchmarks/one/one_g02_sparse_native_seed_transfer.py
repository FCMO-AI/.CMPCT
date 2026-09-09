"""ONE-G0.2 sparse native relation-seed transfer falsifier.

Frozen by ONE_G02_SPARSE_NATIVE_SEED_TRANSFER_PREREG_2026-09-09.md.
V3's exact zero-copy gate remains the first opportunity decision.  On a positive
nomination only, a second sparse native pass emits aligned seed offsets for the
selected generic relation.  Exact grow_relation_spans() remains the truth boundary.
"""
from __future__ import annotations

import ctypes
from functools import lru_cache
import gc
import json
from pathlib import Path
import statistics
import subprocess
import tempfile
import time

import benchmarks.one.one_g02_relation_writer_envelope_v2 as v2
import benchmarks.one.one_g02_relation_writer_envelope_v3 as v3
# Import side effects install both the corrected three-pair kernel and zero-copy gate.
import benchmarks.one.one_g02_relation_writer_envelope_v3_nocopy as v3_nocopy

MIN_NOVEL_WIRE_SAVING = 0.25
MIN_MEDIAN_MARGINAL_MBIT_PER_CPU_S = 20.0
MAX_MEDIAN_CONTROL_CPU_RATIO = 1.35
MAX_CONTROL_CPU_RATIO = 1.75
MAX_FALSE_PROOF_BYTES = 8192
MAX_STATE_RATIO = 0.60
MAX_MEDIAN_NOVEL_CPU_OVER_V3 = 0.85
MAX_NOVEL_CPU_OVER_V3 = 1.00
MAX_MEDIAN_CONTROL_CPU_OVER_V3 = 1.10
MAX_CONTROL_CPU_OVER_V3 = 1.25
FIRST_PASS_PROBE_RATIO = 0.046875
MAX_POSITIVE_TOTAL_PROBE_RATIO = 0.09375
ROUNDS = v3.ROUNDS

_SEED_C = r'''
#include <stdint.h>
#include <stddef.h>
static uint64_t mix64(uint64_t x) {
    x ^= x >> 30; x *= UINT64_C(0xbf58476d1ce4e5b9);
    x ^= x >> 27; x *= UINT64_C(0x94d049bb133111eb);
    return x ^ (x >> 31);
}
int collect_triplet_seeds(
    const uint8_t *a, const uint8_t *b, size_t n,
    uint32_t op, uint32_t value,
    uint64_t *offsets, size_t cap,
    size_t *out_count, uint64_t *probe_bytes
) {
    if (!out_count || !probe_bytes || (n && (!a || !b))) return 2;
    *out_count = 0; *probe_bytes = 0;
    if (op != 1u && op != 2u) return 3;
    const size_t blocks = n / 64u;
    if (cap < blocks) return 4;
    for (size_t bi = 0; bi < blocks; ++bi) {
        const size_t base = bi * 64u;
        const size_t l0 = 0u;
        uint64_t s = mix64(((uint64_t)a[base] << 8) ^ b[base] ^ (uint64_t)bi);
        const size_t l1 = 1u + (size_t)(s % 63u);
        s = mix64(s + UINT64_C(0x9e3779b97f4a7c15));
        const size_t l2 = 1u + (size_t)(s % 63u);
        const size_t lanes[3] = {l0, l1, l2};
        int match = 1;
        for (unsigned k = 0; k < 3; ++k) {
            const size_t p = base + lanes[k];
            const uint32_t observed = op == 1u
                ? (uint32_t)(uint8_t)(b[p] - a[p])
                : (uint32_t)(uint8_t)(b[p] ^ a[p]);
            if (observed != value) match = 0;
        }
        *probe_bytes += 6u;
        if (match) offsets[(*out_count)++] = (uint64_t)base;
    }
    return 0;
}
'''

@lru_cache(maxsize=1)
def _seed_lib():
    d = Path(tempfile.mkdtemp(prefix="cmpct-one-rel-seeds-"))
    src = d / "seeds.c"
    so = d / "seeds.so"
    src.write_text(_SEED_C)
    subprocess.run(
        ["cc", "-O3", "-std=c11", "-fPIC", "-shared", str(src), "-o", str(so)],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    lib = ctypes.CDLL(str(so))
    fn = lib.collect_triplet_seeds
    fn.argtypes = [
        ctypes.POINTER(ctypes.c_uint8), ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t,
        ctypes.c_uint32, ctypes.c_uint32,
        ctypes.POINTER(ctypes.c_uint64), ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_size_t), ctypes.POINTER(ctypes.c_uint64),
    ]
    fn.restype = ctypes.c_int
    return lib

_pybytes_as_string = ctypes.pythonapi.PyBytes_AsString
_pybytes_as_string.argtypes = [ctypes.py_object]
_pybytes_as_string.restype = ctypes.c_void_p


def _collect_seeds_nocopy(source: bytes, target: bytes, op: str, value: int):
    if type(source) is not bytes or type(target) is not bytes or len(source) != len(target):
        raise ValueError("seed transfer requires equal immutable bytes versions")
    op_id = 1 if op == "add8" else 2 if op == "xor" else 0
    if not op_id or not 0 < value < 256:
        raise ValueError("invalid relation seed request")
    blocks = len(source) // 64
    out = (ctypes.c_uint64 * max(blocks, 1))()
    count = ctypes.c_size_t()
    probe = ctypes.c_uint64()
    ap = ctypes.cast(_pybytes_as_string(source), ctypes.POINTER(ctypes.c_uint8))
    bp = ctypes.cast(_pybytes_as_string(target), ctypes.POINTER(ctypes.c_uint8))
    rc = _seed_lib().collect_triplet_seeds(
        ap, bp, len(source), op_id, value, out, blocks,
        ctypes.byref(count), ctypes.byref(probe),
    )
    if rc:
        raise RuntimeError(rc)
    return tuple(int(out[i]) for i in range(count.value)), int(probe.value)


def _candidate_once(ctx):
    incumbent = v2._incumbent_once(*ctx)
    iwire, _istats, iprogram, *_ = incumbent

    c0 = time.process_time_ns()
    gop, gvalue, gout = v3._gate(ctx[2], ctx[3])
    gate_cpu = time.process_time_ns() - c0
    if gop is None:
        return (
            incumbent, iwire, iprogram, None, 0, 0, "incumbent",
            gate_cpu, 0, 0, 0, int(gout.probe_bytes), 0, 0,
        )

    c0 = time.process_time_ns()
    seeds, seed_probe_bytes = _collect_seeds_nocopy(ctx[2], ctx[3], gop, int(gvalue))
    seed_cpu = time.process_time_ns() - c0

    c0 = time.process_time_ns()
    result = v2.grow_relation_spans(
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
            gate_cpu, seed_cpu, proof_cpu, emit_cpu, int(gout.probe_bytes), seed_probe_bytes, len(seeds),
        )
    return (
        incumbent, iwire, iprogram, (gop, int(gvalue)), proof, accepted, "incumbent",
        gate_cpu, seed_cpu, proof_cpu, emit_cpu, int(gout.probe_bytes), seed_probe_bytes, len(seeds),
    )


def _time_three(ctx):
    values = {"i": None, "v3": None, "v4": None}
    walls = {k: [] for k in values}
    cpus = {k: [] for k in values}
    stage_rows = []
    enabled = gc.isenabled()
    try:
        if enabled:
            gc.disable()
        v3._gate(ctx[2], ctx[3])
        _seed_lib()
        for r in range(ROUNDS):
            base = ("i", "v3", "v4")
            order = base[r % 3:] + base[:r % 3]
            for arm in order:
                w0 = time.perf_counter_ns(); c0 = time.process_time_ns()
                if arm == "i":
                    val = v2._incumbent_once(*ctx)
                elif arm == "v3":
                    val = v3._candidate_once(ctx)
                else:
                    val = _candidate_once(ctx)
                cpu = time.process_time_ns() - c0
                wall = time.perf_counter_ns() - w0
                values[arm] = val
                cpus[arm].append(cpu); walls[arm].append(wall)
                if arm == "v4":
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
    control_abs = []
    novel_over_v3 = []
    control_over_v3 = []
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
                v3c = vals["v3"]
                v4c = vals["v4"]
                if incumbent is None or v3c is None or v4c is None:
                    raise AssertionError("missing timed arm")

                iwire = incumbent[0]
                v3wire = v3c[1]
                v3program = v3c[2]
                v3chosen = None if v3c[3] is None or not getattr(v3c[3], "witnesses", ()) else None
                v4inc, v4wire, v4program, gate_choice, proof, accepted, selection, gate_cpu, seed_cpu, proof_cpu, emit_cpu, gate_probe, seed_probe, seed_count = v4c

                iexact, _ = v2._decode_exact(iwire, source, target)
                v3exact, _ = v2._decode_exact(v3wire, source, target)
                v4exact, vm = v2._decode_exact(v4wire, source, target)
                semantic = (
                    iexact and v3exact and v4exact
                    and v4wire == v3wire
                    and v4program.roots["previous"].sha256 == v3program.roots["previous"].sha256
                    and v4program.roots["current"].sha256 == v3program.roots["current"].sha256
                    and v4inc[0] == iwire
                )

                expected_gate = (expected_op, expected_value) if kind == "novel" else None
                gate_correct = gate_choice == expected_gate
                bytes_saved = len(iwire) - len(v4wire)
                inc_ns = cpu["v4"] - cpu["i"]
                marginal = (
                    (bytes_saved * 8.0) / (inc_ns / 1e9) / 1e6
                    if bytes_saved > 0 and inc_ns > 0
                    else (1.0e99 if bytes_saved > 0 else 0.0)
                )
                abs_ratio = cpu["v4"] / max(cpu["i"], 1)
                over_v3 = cpu["v4"] / max(cpu["v3"], 1)
                combined = 2 * n
                total_probe_ratio = (gate_probe + seed_probe) / combined
                state_ratio = (4096 + 8 * seed_count) / combined

                if kind == "novel":
                    novel_yields.append(marginal)
                    novel_over_v3.append(over_v3)
                elif kind == "control":
                    control_abs.append(abs_ratio)
                    control_over_v3.append(over_v3)

                rows.append({
                    "version_bytes": n,
                    "family": family,
                    "kind": kind,
                    "semantic_ok": semantic,
                    "gate_choice": gate_choice,
                    "expected_gate": expected_gate,
                    "gate_correct": gate_correct,
                    "seed_count": seed_count,
                    "accepted_relation_bytes": accepted,
                    "proof_bytes": proof,
                    "selection": selection,
                    "incumbent_wire_bytes": len(iwire),
                    "v3_wire_bytes": len(v3wire),
                    "v4_wire_bytes": len(v4wire),
                    "wire_saving_fraction": bytes_saved / len(iwire),
                    "v4_over_incumbent_cpu": abs_ratio,
                    "v4_over_v3_cpu": over_v3,
                    "v4_over_v3_wall": wall["v4"] / max(wall["v3"], 1),
                    "marginal_mbit_eliminated_per_cpu_s": marginal,
                    "gate_probe_bytes": gate_probe,
                    "seed_probe_bytes": seed_probe,
                    "total_relation_probe_ratio": total_probe_ratio,
                    "modeled_relation_state_ratio": state_ratio,
                    "gate_cpu_ns": stages[0],
                    "seed_transfer_cpu_ns": stages[1],
                    "proof_cpu_ns": stages[2],
                    "program_emit_cpu_ns": stages[3],
                    "candidate_reader_work_bytes": vm.work_bytes,
                    "candidate_reader_materialized_bytes": vm.materialized_bytes,
                })
    finally:
        td.cleanup()

    invalid = (
        any(not r["semantic_ok"] for r in rows)
        or any(r["kind"] == "novel" and not r["gate_correct"] for r in rows)
        or any(r["kind"] != "novel" and r["gate_choice"] is not None for r in rows)
    )
    novel = [r for r in rows if r["kind"] == "novel"]
    controls = [r for r in rows if r["kind"] == "control"]
    hold = (
        any(r["wire_saving_fraction"] < MIN_NOVEL_WIRE_SAVING for r in novel)
        or statistics.median(novel_yields) < MIN_MEDIAN_MARGINAL_MBIT_PER_CPU_S
        or statistics.median(control_abs) > MAX_MEDIAN_CONTROL_CPU_RATIO
        or max(control_abs) > MAX_CONTROL_CPU_RATIO
        or any(r["proof_bytes"] > MAX_FALSE_PROOF_BYTES for r in controls)
        or any(r["modeled_relation_state_ratio"] > MAX_STATE_RATIO for r in rows)
        or statistics.median(novel_over_v3) > MAX_MEDIAN_NOVEL_CPU_OVER_V3
        or max(novel_over_v3) > MAX_NOVEL_CPU_OVER_V3
        or statistics.median(control_over_v3) > MAX_MEDIAN_CONTROL_CPU_OVER_V3
        or max(control_over_v3) > MAX_CONTROL_CPU_OVER_V3
        or any(r["kind"] == "novel" and r["total_relation_probe_ratio"] > MAX_POSITIVE_TOTAL_PROBE_RATIO + 1e-12 for r in rows)
        or any(r["kind"] != "novel" and abs(r["total_relation_probe_ratio"] - FIRST_PASS_PROBE_RATIO) > 1e-12 for r in rows)
    )
    decision = (
        "INVALIDATE_SPARSE_NATIVE_SEED_TRANSFER" if invalid
        else "HOLD_SPARSE_NATIVE_SEED_TRANSFER" if hold
        else "ADVANCE_SPARSE_NATIVE_SEED_TRANSFER"
    )
    print(json.dumps({
        "experiment": "ONE-G0.2 sparse native seed transfer",
        "decision": decision,
        "source_sha": __import__("os").environ.get("EVIDENCE_HEAD"),
        "median_novel_marginal_mbit_per_cpu_s": statistics.median(novel_yields),
        "median_v4_over_v3_novel_cpu": statistics.median(novel_over_v3),
        "worst_v4_over_v3_novel_cpu": max(novel_over_v3),
        "median_control_cpu_ratio": statistics.median(control_abs),
        "worst_control_cpu_ratio": max(control_abs),
        "rows": rows,
    }, sort_keys=True))
    return 0 if decision == "ADVANCE_SPARSE_NATIVE_SEED_TRANSFER" else 1


if __name__ == "__main__":
    raise SystemExit(run())
