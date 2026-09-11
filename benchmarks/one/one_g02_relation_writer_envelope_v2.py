"""ONE-G0.2 corrected relation writer-envelope falsifier.

Frozen by ONE_G02_RELATION_WRITER_ENVELOPE_V2_PREREG_2026-09-09.md.
The incumbent is the promoted root-hash-charged direct temporal writer. The
candidate pays that incumbent path, then adds generic block relation nomination,
exact maximal-span proof and generic ONE emission only for proved opportunities.
"""
from __future__ import annotations

import ctypes
import gc
from hashlib import sha256
import json
import os
import random
import statistics
import time
import zlib

from benchmarks.one.one_g02_end_to_end_direct_emitter_writer import (
    Segment,
    _build_native,
    _plan_signature,
)
from benchmarks.one.one_g02_root_hash_charged_direct_emitter import _writer_once_hashed
from benchmarks.one.one_g02_relation_witness_transfer import (
    BLOCK,
    EXTENSION_BYTES,
    PROBES,
    SEED_BYTES,
    _group_witnesses,
)
from experiments.one.block_relation_witness import observe_relation_witnesses
from experiments.one.growable_wire import _encode_program_growable_prevalidated
from experiments.one.ir import Limits, Node, Program, Ref, Root
from experiments.one.relation_span_growth import grow_relation_spans
from experiments.one.vm import evaluate
from experiments.one.wire import decode_program

VERSION_SIZES = (32 * 1024, 128 * 1024, 512 * 1024)
NOVEL = ("add8_versioned", "xor_versioned", "add8_sparse_cracks", "xor_sparse_cracks")
PRESERVE = ("plus1_incumbent",)
CONTROLS = ("exact_repeat", "random", "compressed_like", "probe_false_positive")
FAMILIES = NOVEL + PRESERVE + CONTROLS
ROUNDS = 9

MIN_NOVEL_WIRE_SAVING = 0.25
MAX_PRESERVE_WIRE_RATIO = 1.0  # byte-identical is required separately
MIN_MEDIAN_MARGINAL_MBIT_PER_CPU_S = 20.0
MAX_FALSE_PROOF_BYTES = 8192
MAX_PROBE_RATIO = 0.05
MAX_STATE_RATIO = 0.60
MAX_MEDIAN_CONTROL_CPU_RATIO = 1.35
MAX_CONTROL_CPU_RATIO = 1.75


def _rel(b: int, op: str, value: int) -> int:
    return ((b + value) & 255) if op == "add8" else b ^ value


def _compressed_bytes(n: int, seed: int) -> bytes:
    rng = random.Random(seed)
    raw = bytes(rng.randrange(256) for _ in range(n + 4096))
    packed = zlib.compress(raw, level=9)
    if len(packed) < n:
        raise AssertionError("compressed-like generator unexpectedly too short")
    return packed[:n]


def _case(n: int, family: str):
    rng = random.Random(0xE11E0000 ^ n ^ sum(map(ord, family)))
    source = bytes(rng.randrange(256) for _ in range(n))
    if family.startswith("add8") or family.startswith("xor"):
        op = "add8" if family.startswith("add8") else "xor"
        value = 37 if op == "add8" else 0xA7
        target = bytearray(_rel(b, op, value) for b in source)
        if family.endswith("sparse_cracks"):
            for p in range(64 * 1024 - 1, n, 64 * 1024):
                target[p] ^= 1
        return source, bytes(target), op, value, "novel"
    if family == "plus1_incumbent":
        # Existing promoted shift/+1 relation: target[i] == source[i-1] for i>=1.
        return source, bytes([rng.randrange(256)]) + source[:-1], None, None, "preserve"
    if family == "exact_repeat":
        return source, source, None, None, "control"
    if family == "random":
        return source, bytes(rng.randrange(256) for _ in range(n)), None, None, "control"
    if family == "compressed_like":
        return (
            _compressed_bytes(n, 0xC0110000 ^ n),
            _compressed_bytes(n, 0xC0220000 ^ n),
            None,
            None,
            "control",
        )
    if family == "probe_false_positive":
        target = bytearray(rng.randrange(256) for _ in range(n))
        for off in range(0, n - (n % BLOCK), BLOCK):
            for p in PROBES:
                target[off + p] = (source[off + p] + 37) & 255
        return source, bytes(target), None, None, "control"
    raise ValueError(family)


def _generic_program(source: bytes, target: bytes, op: str, value: int, runs, roots):
    nodes = [
        Node("surprise", surprise=source, declared_length=len(source)),
        Node("fill", count=len(target), value=value, declared_length=len(target)),
    ]
    child_refs = []
    cursor = 0
    for start, length in runs:
        if start > cursor:
            payload = target[cursor:start]
            lid = len(nodes)
            nodes.append(Node("surprise", surprise=payload, declared_length=len(payload)))
            child_refs.append(Ref(lid))
        rid = len(nodes)
        nodes.append(
            Node(
                op,
                refs=(Ref(0, start, length), Ref(1, start, length)),
                declared_length=length,
            )
        )
        child_refs.append(Ref(rid))
        cursor = start + length
    if cursor < len(target):
        payload = target[cursor:]
        lid = len(nodes)
        nodes.append(Node("surprise", surprise=payload, declared_length=len(payload)))
        child_refs.append(Ref(lid))
    if not child_refs:
        raise AssertionError("generic relation Program requires an accepted span")
    if len(child_refs) == 1:
        current_ref = child_refs[0]
    else:
        cid = len(nodes)
        nodes.append(Node("concat", refs=tuple(child_refs), declared_length=len(target)))
        current_ref = Ref(cid)
    program_roots = {
        "previous": Root(Ref(0), len(source), roots["previous"].sha256),
        "current": Root(current_ref, len(target), roots["current"].sha256),
    }
    return Program(tuple(nodes), program_roots, Limits())


def _incumbent_once(admission_fn, segment_fn, source, target, src_arr, dst_arr, seg_buf):
    return _writer_once_hashed(
        admission_fn,
        segment_fn,
        source,
        target,
        src_arr,
        dst_arr,
        seg_buf,
        direct_emit=True,
    )


def _candidate_once(admission_fn, segment_fn, source, target, src_arr, dst_arr, seg_buf):
    incumbent = _incumbent_once(admission_fn, segment_fn, source, target, src_arr, dst_arr, seg_buf)
    iwire, _istats, iprogram, *_rest = incumbent

    combined = source + target
    obs = observe_relation_witnesses(combined)
    total_proof = 0
    accepted = 0
    chosen = None
    generic_wire = None
    generic_stats = None
    generic_program = None

    for (op, value), nominations in _group_witnesses(obs, len(source)):
        result = grow_relation_spans(
            source,
            target,
            op=op,
            value=value,
            nominations=tuple(nominations),
            seed_bytes=SEED_BYTES,
            extension_bytes=EXTENSION_BYTES,
        )
        total_proof += result.compared_bytes
        if not result.runs:
            continue
        program = _generic_program(source, target, op, value, result.runs, iprogram.roots)
        program.validate_shape()
        wire, stats = _encode_program_growable_prevalidated(program)
        if generic_wire is None or len(wire) < len(generic_wire):
            generic_wire = wire
            generic_stats = stats
            generic_program = program
            accepted = result.accepted_bytes
            chosen = (op, value)

    if generic_wire is not None and len(generic_wire) < len(iwire):
        final_wire = generic_wire
        final_stats = generic_stats
        final_program = generic_program
        final_selection = "generic"
    else:
        final_wire = iwire
        final_stats = incumbent[1]
        final_program = iprogram
        final_selection = "incumbent"

    return (
        incumbent,
        obs,
        final_wire,
        final_stats,
        final_program,
        total_proof,
        accepted,
        chosen,
        final_selection,
    )


def _time_pair(ctx):
    incumbent_wall = []
    incumbent_cpu = []
    candidate_wall = []
    candidate_cpu = []
    incumbent_value = None
    candidate_value = None
    was_enabled = gc.isenabled()
    try:
        if was_enabled:
            gc.disable()
        for round_index in range(ROUNDS):
            order = ("incumbent", "candidate") if round_index % 2 == 0 else ("candidate", "incumbent")
            for arm in order:
                w0 = time.perf_counter_ns()
                c0 = time.process_time_ns()
                if arm == "incumbent":
                    value = _incumbent_once(*ctx)
                else:
                    value = _candidate_once(*ctx)
                cpu = time.process_time_ns() - c0
                wall = time.perf_counter_ns() - w0
                if arm == "incumbent":
                    incumbent_wall.append(wall)
                    incumbent_cpu.append(cpu)
                    incumbent_value = value
                else:
                    candidate_wall.append(wall)
                    candidate_cpu.append(cpu)
                    candidate_value = value
    finally:
        if was_enabled:
            gc.enable()
    return (
        incumbent_value,
        int(statistics.median(incumbent_wall)),
        int(statistics.median(incumbent_cpu)),
        candidate_value,
        int(statistics.median(candidate_wall)),
        int(statistics.median(candidate_cpu)),
    )


def _decode_exact(wire: bytes, source: bytes, target: bytes):
    decoded = decode_program(wire)
    outputs, stats = evaluate(decoded)
    return outputs == {"previous": source, "current": target}, stats


def run():
    admission_fn, segment_fn, td = _build_native()
    rows = []
    novel_yields = []
    control_cpu_ratios = []
    semantic_ok = True
    try:
        for n in VERSION_SIZES:
            for family in FAMILIES:
                source, target, expected_op, expected_value, kind = _case(n, family)
                src_arr = (ctypes.c_uint8 * n).from_buffer_copy(source)
                dst_arr = (ctypes.c_uint8 * n).from_buffer_copy(target)
                seg_buf = (Segment * n)()
                ctx = (admission_fn, segment_fn, source, target, src_arr, dst_arr, seg_buf)

                (
                    incumbent,
                    incumbent_wall_ns,
                    incumbent_cpu_ns,
                    candidate,
                    candidate_wall_ns,
                    candidate_cpu_ns,
                ) = _time_pair(ctx)
                if incumbent is None or candidate is None:
                    raise AssertionError("missing timed writer result")

                iwire, istats, iprogram, iresult, ireads, iused, ienabled, iplan, itraffic, isegments, idepth = incumbent
                (
                    candidate_incumbent,
                    obs,
                    cwire,
                    cstats,
                    cprogram,
                    proof,
                    accepted,
                    chosen,
                    final_selection,
                ) = candidate
                ciwire, _cistats, _ciprogram, ciresult, _cireads, _ciused, cienabled, ciplan, *_ = candidate_incumbent

                iexact, ivm = _decode_exact(iwire, source, target)
                cexact, cvm = _decode_exact(cwire, source, target)
                roots_exact = (
                    iprogram.roots["previous"].sha256 == sha256(source).hexdigest()
                    and iprogram.roots["current"].sha256 == sha256(target).hexdigest()
                    and cprogram.roots["previous"].sha256 == iprogram.roots["previous"].sha256
                    and cprogram.roots["current"].sha256 == iprogram.roots["current"].sha256
                )
                this_semantic = iexact and cexact and roots_exact
                semantic_ok &= this_semantic
                if not this_semantic:
                    raise AssertionError("corrected relation writer changed root semantics")

                bytes_saved = len(iwire) - len(cwire)
                incremental_cpu_ns = candidate_cpu_ns - incumbent_cpu_ns
                if bytes_saved > 0 and incremental_cpu_ns <= 0:
                    marginal_mbit = 1.0e99
                elif bytes_saved > 0:
                    marginal_mbit = (bytes_saved * 8.0) / (incremental_cpu_ns / 1e9) / 1e6
                else:
                    marginal_mbit = 0.0
                cpu_ratio = candidate_cpu_ns / max(incumbent_cpu_ns, 1)
                wall_ratio = candidate_wall_ns / max(incumbent_wall_ns, 1)

                correct_generic = (
                    chosen is not None and chosen[0] == expected_op and chosen[1] == expected_value
                ) if kind == "novel" else chosen is None
                incumbent_plan_preserved = (
                    cienabled == ienabled
                    and int(ciresult.best_shift) == int(iresult.best_shift)
                    and int(ciresult.exact_proofs) == int(iresult.exact_proofs)
                    and _plan_signature(ciplan) == _plan_signature(iplan)
                    and ciwire == iwire
                )

                if kind == "novel":
                    novel_yields.append(marginal_mbit)
                elif kind == "control":
                    control_cpu_ratios.append(cpu_ratio)

                rows.append({
                    "version_bytes": n,
                    "combined_input_bytes": len(source) + len(target),
                    "family": family,
                    "kind": kind,
                    "semantic_ok": this_semantic,
                    "generic_chosen": chosen,
                    "correct_generic_relation": correct_generic,
                    "accepted_generic_relation_bytes": accepted,
                    "final_selection": final_selection,
                    "incumbent_wire_bytes": len(iwire),
                    "candidate_wire_bytes": len(cwire),
                    "candidate_over_incumbent_wire": len(cwire) / len(iwire),
                    "bytes_saved": bytes_saved,
                    "wire_saving_fraction": bytes_saved / len(iwire),
                    "incumbent_writer_wall_ns": incumbent_wall_ns,
                    "incumbent_writer_cpu_ns": incumbent_cpu_ns,
                    "candidate_writer_wall_ns": candidate_wall_ns,
                    "candidate_writer_cpu_ns": candidate_cpu_ns,
                    "candidate_over_incumbent_wall": wall_ratio,
                    "candidate_over_incumbent_cpu": cpu_ratio,
                    "incremental_cpu_ns": incremental_cpu_ns,
                    "marginal_mbit_eliminated_per_cpu_s": marginal_mbit,
                    "source_scan_bytes": obs.source_scan_bytes,
                    "source_scan_ratio": obs.source_scan_bytes / (len(source) + len(target)),
                    "probe_bytes": obs.probe_bytes,
                    "probe_ratio": obs.probe_bytes / (len(source) + len(target)),
                    "modeled_observation_state_bytes": obs.modeled_state_bytes,
                    "state_ratio": obs.modeled_state_bytes / (len(source) + len(target)),
                    "witnesses": len(obs.witnesses),
                    "proof_bytes": proof,
                    "incumbent_relation_enabled": ienabled,
                    "incumbent_best_shift": int(iresult.best_shift),
                    "incumbent_exact_proofs": int(iresult.exact_proofs),
                    "incumbent_gate_compared_bytes": ireads,
                    "incumbent_used_sparse_gate": iused,
                    "incumbent_segment_compared_target_bytes": itraffic,
                    "incumbent_segments": isegments,
                    "incumbent_hierarchy_depth": idepth,
                    "candidate_internal_incumbent_preserved": incumbent_plan_preserved,
                    "incumbent_program_nodes": len(iprogram.nodes),
                    "candidate_program_nodes": len(cprogram.nodes),
                    "incumbent_reader_work_bytes": ivm.work_bytes,
                    "candidate_reader_work_bytes": cvm.work_bytes,
                    "incumbent_reader_materialized_bytes": ivm.materialized_bytes,
                    "candidate_reader_materialized_bytes": cvm.materialized_bytes,
                    "incumbent_wire_stats_bytes": istats.total_bytes,
                    "candidate_wire_stats_bytes": cstats.total_bytes,
                })

        controls = [r for r in rows if r["kind"] == "control"]
        novel = [r for r in rows if r["kind"] == "novel"]
        preserve = [r for r in rows if r["kind"] == "preserve"]

        invalid = (
            not semantic_ok
            or any(r["accepted_generic_relation_bytes"] > 0 for r in controls)
        )
        structural_ok = (
            all(r["correct_generic_relation"] for r in novel)
            and all(r["accepted_generic_relation_bytes"] > 0 for r in novel)
            and all(r["wire_saving_fraction"] >= MIN_NOVEL_WIRE_SAVING for r in novel)
            and all(r["candidate_wire_bytes"] == r["incumbent_wire_bytes"] for r in preserve)
            and all(r["candidate_internal_incumbent_preserved"] for r in preserve)
            and all(r["candidate_wire_bytes"] == r["incumbent_wire_bytes"] for r in controls)
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
        median_yield = float(statistics.median(novel_yields))
        median_control_cpu = float(statistics.median(control_cpu_ratios))
        worst_control_cpu = max(control_cpu_ratios)
        economic_ok = (
            median_yield >= MIN_MEDIAN_MARGINAL_MBIT_PER_CPU_S
            and median_control_cpu <= MAX_MEDIAN_CONTROL_CPU_RATIO
            and worst_control_cpu <= MAX_CONTROL_CPU_RATIO
        )

        if invalid:
            decision = "INVALIDATE_RELATION_WRITER_ENVELOPE_V2"
        elif structural_ok and resource_ok and economic_ok:
            decision = "ADVANCE_RELATION_WRITER_ENVELOPE_V2"
        else:
            decision = "HOLD_RELATION_WRITER_ENVELOPE_V2"

        return {
            "schema": "cmpct-one-g02-relation-writer-envelope-v2",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "repetitions": ROUNDS,
            "timing_order": "alternating incumbent/candidate-candidate/incumbent",
            "semantic_gates_pass": semantic_ok,
            "decision": decision,
            "median_novel_marginal_mbit_per_cpu_s": median_yield,
            "median_control_cpu_ratio": median_control_cpu,
            "worst_control_cpu_ratio": worst_control_cpu,
            "frozen_thresholds": {
                "min_novel_wire_saving": MIN_NOVEL_WIRE_SAVING,
                "min_median_marginal_mbit_per_cpu_s": MIN_MEDIAN_MARGINAL_MBIT_PER_CPU_S,
                "max_false_proof_bytes": MAX_FALSE_PROOF_BYTES,
                "max_probe_ratio": MAX_PROBE_RATIO,
                "max_state_ratio": MAX_STATE_RATIO,
                "max_median_control_cpu_ratio": MAX_MEDIAN_CONTROL_CPU_RATIO,
                "max_control_cpu_ratio": MAX_CONTROL_CPU_RATIO,
            },
            "claim_boundary": (
                "Python research writer adding generic block relation observation/proof to the exact incumbent root-hash-"
                "charged direct temporal writer; candidate pays the incumbent path first and may pay a second generic "
                "emission on proved opportunities; excludes arbitrary archive geometry, product-native RSS/throughput, "
                "auth/durability/filesystem fidelity and Genesis comparator authority"
            ),
            "rows": rows,
        }
    finally:
        td.cleanup()


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["decision"] == "ADVANCE_RELATION_WRITER_ENVELOPE_V2" else 1)
