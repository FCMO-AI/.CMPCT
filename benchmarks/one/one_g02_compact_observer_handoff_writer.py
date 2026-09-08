"""ONE-G0.2 compact native-observer handoff whole-writer falsifier.

Frozen by ONE_G02_COMPACT_OBSERVER_HANDOFF_WRITER_PREREG_2026-09-08.md.
Only eager Python observer materialization differs between the paired writer arms.
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
    SegmentStats,
    _admit,
    _build_native,
    _native_plan,
    _plan_signature,
)
from benchmarks.one.one_g02_post_segment_control_cost_owner import _literal_program
from experiments.one.bounded_surprise_pool import program_from_plan_pooled
from experiments.one.growable_wire import _encode_program_growable_prevalidated
from experiments.one.ir import Ref, Root
from experiments.one.native_observe import observe_native
from experiments.one.native_observe_view import NativeObservationView, observe_native_view
from experiments.one.vm import evaluate
from experiments.one.wire import decode_program

REPETITIONS = 15
SIZES = (4 * 1024, 256 * 1024, 1 << 20)
FAMILIES = ("structured", "compressed_like", "long_runs", "random", "near_repeats")
RICH = ("structured", "compressed_like", "long_runs")
CONTROLS = ("random", "near_repeats")
RICH_RATIO_MAX = 0.90
NO_REGRESSION_MAX = 1.05
MIN_RICH_WINS = 2


def _repeat_to_size(seed: bytes, size: int) -> bytes:
    if not seed:
        return bytes(size)
    return (seed * ((size + len(seed) - 1) // len(seed)))[:size]


def _target(family: str, size: int) -> bytes:
    if family == "structured":
        record = b"ONE|LAW=repeat|SURPRISE=bounded|" + bytes(range(32))
        body = _repeat_to_size(record, max(0, size - size // 4))
        run = bytes([0xA5]) * (size - len(body))
        return (body + run)[:size]
    if family == "long_runs":
        out = bytearray()
        value = 17
        while len(out) < size:
            span = min(size - len(out), 4096 + ((len(out) // 4096) % 7) * 257)
            out.extend(bytes([value]) * span)
            value = (value + 53) & 0xFF
        return bytes(out)
    if family == "random":
        return random.Random(31000 + size).randbytes(size)
    if family == "near_repeats":
        out = bytearray(_repeat_to_size(bytes(range(64)), size))
        for i in range(31, size, 997):
            out[i] ^= (0x5A + i) & 0xFF
        return bytes(out)
    if family == "compressed_like":
        rng = random.Random(32000 + size)
        chunks = bytearray()
        chunk_id = 0
        while len(chunks) < size:
            raw = bytearray(rng.randbytes(12 * 1024))
            marker = (f"ONE-COMPRESSED-BLOCK-{chunk_id:06d}|".encode("ascii") * 64)
            raw[: min(len(raw), len(marker))] = marker[: len(raw)]
            chunks.extend(zlib.compress(bytes(raw), level=9))
            chunk_id += 1
        return bytes(chunks[:size])
    raise AssertionError(f"unknown family: {family}")


def _case(family: str, size: int) -> tuple[bytes, bytes]:
    target = _target(family, size)
    source = random.Random(33000 + size + FAMILIES.index(family) * 101).randbytes(size)
    return source, target


def _writer_once(admission_fn, segment_fn, source: bytes, target: bytes, src_arr, dst_arr, seg_buf, compact: bool):
    previous_digest = sha256(source).hexdigest()
    current_digest = sha256(target).hexdigest()
    previous_root = Root(Ref(0), len(source), previous_digest)

    observer = observe_native_view(target) if compact else observe_native(target)

    result, gate_reads, gate_used, enabled = _admit(admission_fn, src_arr, dst_arr, len(source))
    segment_stats = SegmentStats()
    if enabled:
        plan = _native_plan(segment_fn, src_arr, dst_arr, len(source), seg_buf, segment_stats)
        program, pool_stats = program_from_plan_pooled(source, target, plan, previous_root, current_digest)
        hierarchy_depth = pool_stats.hierarchy_depth
    else:
        plan = ()
        program, hierarchy_depth = _literal_program(source, target, previous_root, current_digest)
        pool_stats = None
    program.validate_shape()
    wire, wire_stats = _encode_program_growable_prevalidated(program)

    if compact:
        assert isinstance(observer, NativeObservationView)
        observer_counts = (observer.run_count, observer.reuse_count)
        output_capacity_bytes = observer.native_output_capacity_bytes
        output_used_bytes = observer.native_output_used_bytes
    else:
        observer_counts = (len(observer.runs), len(observer.reuse))
        run_capacity = max(1, len(target) // 8 + 2)
        reuse_capacity = max(1, len(target) // 64 + 2)
        output_capacity_bytes = run_capacity * 24 + reuse_capacity * 24
        output_used_bytes = (observer_counts[0] + observer_counts[1]) * 24

    return {
        "wire": wire,
        "wire_stats": wire_stats,
        "program": program,
        "relation_signature": (
            bool(enabled), int(result.best_shift), int(result.exact_proofs), bool(gate_used), int(gate_reads)
        ),
        "plan_signature": _plan_signature(plan),
        "hierarchy_depth": hierarchy_depth,
        "segments": int(segment_stats.segments),
        "segment_compared_target_bytes": int(segment_stats.compared_target_bytes),
        "observer_counts": observer_counts,
        "observer_output_capacity_bytes": output_capacity_bytes,
        "observer_output_used_bytes": output_used_bytes,
        "pooled_groups": pool_stats.groups if pool_stats is not None else 0,
    }


def _time_pair(ctx):
    eager_wall: list[int] = []
    eager_cpu: list[int] = []
    compact_wall: list[int] = []
    compact_cpu: list[int] = []
    eager_value = None
    compact_value = None
    was_enabled = gc.isenabled()
    try:
        if was_enabled:
            gc.disable()
        for round_index in range(REPETITIONS):
            order = (False, True) if round_index % 2 == 0 else (True, False)
            for compact in order:
                # Release the prior same-arm result before the next timer so object-graph
                # teardown cannot be charged to either candidate.
                if compact:
                    compact_value = None
                else:
                    eager_value = None
                c0 = time.process_time_ns()
                w0 = time.perf_counter_ns()
                value = _writer_once(*ctx, compact=compact)
                w1 = time.perf_counter_ns()
                c1 = time.process_time_ns()
                if compact:
                    compact_value = value
                    compact_wall.append(w1 - w0)
                    compact_cpu.append(c1 - c0)
                else:
                    eager_value = value
                    eager_wall.append(w1 - w0)
                    eager_cpu.append(c1 - c0)
    finally:
        if was_enabled:
            gc.enable()
    if eager_value is None or compact_value is None:
        raise AssertionError("missing paired writer result")
    return (
        float(statistics.median(eager_wall)),
        float(statistics.median(eager_cpu)),
        eager_value,
        float(statistics.median(compact_wall)),
        float(statistics.median(compact_cpu)),
        compact_value,
    )


def _same_writer_result(a, b) -> bool:
    return (
        a["wire"] == b["wire"]
        and a["wire_stats"] == b["wire_stats"]
        and a["program"] == b["program"]
        and a["relation_signature"] == b["relation_signature"]
        and a["plan_signature"] == b["plan_signature"]
        and a["observer_counts"] == b["observer_counts"]
    )


def run():
    # Compiler/native-library startup is not writer work.
    observe_native(b"warmup" * 32)
    observe_native_view(b"warmup" * 32)
    admission_fn, segment_fn, td = _build_native()
    rows = []
    semantic_ok = True
    try:
        for size in SIZES:
            for family in FAMILIES:
                source, target = _case(family, size)
                src_arr = (ctypes.c_uint8 * size).from_buffer_copy(source)
                dst_arr = (ctypes.c_uint8 * size).from_buffer_copy(target)
                seg_buf = (Segment * size)()

                # Untimed independent authority: the compact buffer view must carry the
                # exact same observation before whole-writer timing can be interpreted.
                eager_observation = observe_native(target)
                compact_authority = observe_native_view(target)
                observer_exact = compact_authority.materialize() == eager_observation

                eager_authority = _writer_once(
                    admission_fn, segment_fn, source, target, src_arr, dst_arr, seg_buf, False
                )
                compact_authority_writer = _writer_once(
                    admission_fn, segment_fn, source, target, src_arr, dst_arr, seg_buf, True
                )
                writer_exact = _same_writer_result(eager_authority, compact_authority_writer)
                decoded = decode_program(compact_authority_writer["wire"])
                outputs, vm_stats = evaluate(decoded)
                reconstruction_exact = outputs == {"previous": source, "current": target}
                roots_exact = (
                    compact_authority_writer["program"].roots["previous"].sha256 == sha256(source).hexdigest()
                    and compact_authority_writer["program"].roots["current"].sha256 == sha256(target).hexdigest()
                )
                row_semantic = observer_exact and writer_exact and reconstruction_exact and roots_exact
                semantic_ok &= row_semantic
                if not row_semantic:
                    raise AssertionError(f"compact observer handoff changed semantics: {size=} {family=}")

                ctx = (admission_fn, segment_fn, source, target, src_arr, dst_arr, seg_buf)
                ew, ec, ev, cw, cc, cv = _time_pair(ctx)
                timed_exact = _same_writer_result(ev, cv)
                if not timed_exact:
                    raise AssertionError(f"timed compact observer handoff changed writer: {size=} {family=}")

                rows.append({
                    "bytes": size,
                    "family": family,
                    "observer_exact": observer_exact,
                    "writer_exact": writer_exact,
                    "timed_writer_exact": timed_exact,
                    "root_hashes_exact": roots_exact,
                    "exact_reconstruction": reconstruction_exact,
                    "relation_enabled": cv["relation_signature"][0],
                    "best_shift": cv["relation_signature"][1],
                    "exact_proofs": cv["relation_signature"][2],
                    "segments": cv["segments"],
                    "segment_compared_target_bytes": cv["segment_compared_target_bytes"],
                    "program_nodes": len(cv["program"].nodes),
                    "canonical_wire_bytes": cv["wire_stats"].total_bytes,
                    "surprise_bytes": cv["wire_stats"].surprise_bytes,
                    "reader_work_bytes": vm_stats.work_bytes,
                    "reader_materialized_bytes": vm_stats.materialized_bytes,
                    "observer_run_count": cv["observer_counts"][0],
                    "observer_reuse_count": cv["observer_counts"][1],
                    "observer_native_output_capacity_bytes": cv["observer_output_capacity_bytes"],
                    "observer_native_output_used_bytes": cv["observer_output_used_bytes"],
                    "eager_writer_wall_median_ns": ew,
                    "eager_writer_cpu_median_ns": ec,
                    "compact_writer_wall_median_ns": cw,
                    "compact_writer_cpu_median_ns": cc,
                    "compact_over_eager_wall": cw / ew,
                    "compact_over_eager_cpu": cc / ec,
                })

        million = [row for row in rows if row["bytes"] == (1 << 20)]
        rich = [row for row in million if row["family"] in RICH]
        controls = [row for row in million if row["family"] in CONTROLS]
        rich_wall_wins = sum(row["compact_over_eager_wall"] <= RICH_RATIO_MAX for row in rich)
        rich_cpu_wins = sum(row["compact_over_eager_cpu"] <= RICH_RATIO_MAX for row in rich)
        rich_no_regression = all(
            row["compact_over_eager_wall"] <= NO_REGRESSION_MAX
            and row["compact_over_eager_cpu"] <= NO_REGRESSION_MAX
            for row in rich
        )
        control_ok = all(
            row["compact_over_eager_wall"] <= NO_REGRESSION_MAX
            and row["compact_over_eager_cpu"] <= NO_REGRESSION_MAX
            for row in controls
        )
        performance_ok = (
            rich_wall_wins >= MIN_RICH_WINS
            and rich_cpu_wins >= MIN_RICH_WINS
            and rich_no_regression
            and control_ok
        )
        if not semantic_ok:
            decision = "INVALIDATE_COMPACT_OBSERVER_HANDOFF"
        elif performance_ok:
            decision = "ADVANCE_COMPACT_OBSERVER_HANDOFF"
        else:
            decision = "HOLD_COMPACT_OBSERVER_HANDOFF"
        return {
            "schema": "cmpct-one-g02-compact-observer-handoff-writer-v1",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "repetitions": REPETITIONS,
            "sizes": list(SIZES),
            "families": list(FAMILIES),
            "rich_ratio_max": RICH_RATIO_MAX,
            "no_regression_max": NO_REGRESSION_MAX,
            "minimum_rich_wins": MIN_RICH_WINS,
            "semantic_gates_pass": semantic_ok,
            "rich_wall_wins_1m": rich_wall_wins,
            "rich_cpu_wins_1m": rich_cpu_wins,
            "rich_no_regression_1m": rich_no_regression,
            "control_no_regression_1m": control_ok,
            "decision": decision,
            "claim_boundary": (
                "writer-internal handoff only; same native observer kernel/input copy/output capacities, but eager "
                "Python opportunity objects are deferred; current admission/segmentation still consume source/target "
                "directly rather than the compact observation; no stored-format, reader, RSS/product, arbitrary "
                "discovery, durability, recovery, portability, or v0.29/v0.30 authority"
            ),
            "rows": rows,
        }
    finally:
        td.cleanup()


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["decision"] == "ADVANCE_COMPACT_OBSERVER_HANDOFF" else 1)
