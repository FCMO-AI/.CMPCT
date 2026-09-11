"""ONE-G0.2 plan-direct canonical writer falsifier.

Frozen by ONE_G02_ROOT_HASH_WRITER_PLAN_DIRECT_WIRE_PREREG_2026-09-06.md.
The candidate emits the exact same ONE0 Program as the baseline without first
materializing Python Program/Node/Ref objects.
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
    ROUNDS,
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
from benchmarks.one.one_g02_root_hash_writer_coarse_attribution import (
    _writer_once_direct_unprofiled,
)
from experiments.one.growable_wire import _append_blob, _append_uvarint
from experiments.one.ir import Limits, OneError
from experiments.one.vm import evaluate
from experiments.one.wire import MAGIC, MAX_NAME_BYTES, MAX_ROOTS, TAGS, WireStats, decode_program

MATURE_MIN = 16 * 1024
PRODUCTIVE_MEDIAN_MAX = 0.85
PRODUCTIVE_GOOD_MAX = 0.90
MIN_PRODUCTIVE_GOOD = 12
PRODUCTIVE_ROW_MAX = 1.03
CONTROL_MEDIAN_MAX = 1.03
CONTROL_ROW_MAX = 1.08


def _append_ref_fields(out: bytearray, node: int, start: int = 0, length: int | None = None) -> None:
    _append_uvarint(out, node)
    _append_uvarint(out, start)
    _append_uvarint(out, 0 if length is None else length + 1)


def _append_surprise_node(out: bytearray, payload: bytes) -> None:
    out.append(TAGS["surprise"])
    _append_uvarint(out, 0)  # declared_length=None
    _append_blob(out, payload)


def _append_concat_node(out: bytearray, refs, declared_length: int) -> None:
    out.append(TAGS["concat"])
    _append_uvarint(out, declared_length + 1)
    _append_uvarint(out, len(refs))
    for node, start, length in refs:
        _append_ref_fields(out, node, start, length)
    _append_blob(out, b"")


def _validate_digest(digest: str) -> None:
    if not isinstance(digest, str) or len(digest) != 64:
        raise OneError("root sha256 must be exactly 64 hex characters")
    try:
        raw = bytes.fromhex(digest)
    except ValueError as exc:
        raise OneError("root sha256 is not hexadecimal") from exc
    if len(raw) != 32:
        raise OneError("root sha256 must decode to exactly 32 bytes")


def _direct_wire_from_plan(
    source: bytes,
    target: bytes,
    plan,
    previous_digest: str,
    current_digest: str,
    enabled: bool,
):
    """Validate the frozen plan shape and emit byte-identical canonical ONE0 bytes."""
    limits = Limits()
    limits.validate()
    _validate_digest(previous_digest)
    _validate_digest(current_digest)

    if not isinstance(source, bytes) or not isinstance(target, bytes):
        raise OneError("direct writer requires immutable byte inputs")
    if len(source) > limits.max_output_bytes or len(target) > limits.max_output_bytes:
        raise OneError("root length exceeds declared output limit")

    surprise_nodes: list[bytes] = []
    intermediate_nodes: list[tuple[tuple[tuple[int, int, int | None], ...], int]] = []
    final_refs: tuple[tuple[int, int, int | None], ...]
    surprise_bytes = len(source)
    hierarchy_depth = 0

    if enabled:
        level: list[tuple[int, int, int | None]] = []
        covered = 0
        next_node = 1
        for entry in plan:
            if not isinstance(entry, tuple) or len(entry) != 4:
                raise OneError("invalid segment-plan entry")
            kind, offset, length, payload = entry
            if type(offset) is not int or type(length) is not int or offset < 0 or length <= 0:
                raise OneError("invalid segment offset/length")
            if kind == "ref":
                if payload != b"":
                    raise OneError("ref segment carries Surprise")
                if offset + length > len(source):
                    raise OneError("source reference exceeds previous root")
                level.append((0, offset, length))
            elif kind == "surprise":
                if not isinstance(payload, bytes) or len(payload) != length:
                    raise OneError("Surprise payload length mismatch")
                surprise_nodes.append(payload)
                surprise_bytes += len(payload)
                level.append((next_node, 0, None))
                next_node += 1
            else:
                raise OneError("unknown segment-plan kind")
            covered += length
            if covered > len(target):
                raise OneError("segment plan exceeds target coverage")
        if covered != len(target) or not level:
            raise OneError("segment plan does not exactly cover target")

        hierarchy_depth = 1
        fanout = limits.max_nodes
        while len(level) > fanout:
            nxt: list[tuple[int, int, int | None]] = []
            for off in range(0, len(level), fanout):
                chunk = tuple(level[off:off + fanout])
                declared = 0
                for _node, _start, ref_len in chunk:
                    if ref_len is None:
                        # Surprise refs in the first level have known payload length; recover
                        # it from the referenced node id exactly as the baseline graph does.
                        payload_index = _node - 1
                        if payload_index < 0 or payload_index >= len(surprise_nodes):
                            raise OneError("invalid Surprise ref in hierarchy")
                        declared += len(surprise_nodes[payload_index])
                    else:
                        declared += ref_len
                intermediate_nodes.append((chunk, declared))
                nxt.append((next_node, 0, declared))
                next_node += 1
            level = nxt
            hierarchy_depth += 1
        final_refs = tuple(level)
        final_node = next_node
        node_count = final_node + 1
        if node_count > limits.max_nodes:
            raise OneError("node count exceeds declared limit")
    else:
        if plan not in ((), None):
            raise OneError("disabled relation must not carry a segment plan")
        surprise_nodes = [target]
        surprise_bytes += len(target)
        final_refs = ()
        intermediate_nodes = []
        final_node = 1
        node_count = 2

    if node_count > limits.max_nodes:
        raise OneError("node count exceeds declared limit")
    if MAX_ROOTS < 2:
        raise OneError("root count exceeds experimental wire limit")

    out = bytearray(MAGIC)
    for value in (
        limits.max_nodes,
        limits.max_output_bytes,
        limits.max_work_bytes,
        limits.max_depth,
        node_count,
    ):
        _append_uvarint(out, value)

    _append_surprise_node(out, source)
    for payload in surprise_nodes:
        _append_surprise_node(out, payload)

    if enabled:
        for refs, declared in intermediate_nodes:
            _append_concat_node(out, refs, declared)
        _append_concat_node(out, final_refs, len(target))

    # Canonical root order is lexical: current, previous.
    roots = (
        ("current", final_node, len(target), current_digest),
        ("previous", 0, len(source), previous_digest),
    )
    _append_uvarint(out, len(roots))
    for name, node, length, digest in roots:
        name_bytes = name.encode("utf-8")
        if len(name_bytes) > MAX_NAME_BYTES:
            raise OneError("root name exceeds experimental wire limit")
        if node < 0 or node >= node_count:
            raise OneError("root reference exceeds node table")
        _append_blob(out, name_bytes)
        _append_ref_fields(out, node)
        _append_uvarint(out, length)
        out.extend(bytes.fromhex(digest))

    stats = WireStats(
        total_bytes=len(out),
        surprise_bytes=surprise_bytes,
        control_integrity_bytes=len(out) - surprise_bytes,
    )
    return bytes(out), stats, hierarchy_depth, node_count


def _candidate_once(admission_fn, segment_fn, source, target, src_arr, dst_arr, seg_buf):
    previous_digest = sha256(source).hexdigest()
    current_digest = sha256(target).hexdigest()
    result, gate_reads, gate_used, enabled = _admit(admission_fn, src_arr, dst_arr, len(source))
    segment_stats = SegmentStats()
    if enabled:
        plan = _native_plan(segment_fn, src_arr, dst_arr, len(source), seg_buf, segment_stats)
    else:
        plan = ()
    wire, stats, depth, node_count = _direct_wire_from_plan(
        source, target, plan, previous_digest, current_digest, enabled
    )
    return (
        wire, stats, result, gate_reads, gate_used, enabled, plan,
        int(segment_stats.compared_target_bytes), int(segment_stats.segments), depth, node_count,
    )


def _malformed_plan_probes() -> bool:
    source = b"abcdefgh"
    target = b"bcdefghi"
    pd = sha256(source).hexdigest()
    cd = sha256(target).hexdigest()
    malformed = (
        (("ref", 7, 2, b""),),  # ref out of range
        (("surprise", 0, 4, b"abc"), ("surprise", 0, 4, b"defg")),  # payload mismatch
        (("ref", 0, 4, b""),),  # incomplete coverage
        (("bogus", 0, 8, b""),),
        (("ref", -1, 8, b""),),
    )
    for plan in malformed:
        try:
            _direct_wire_from_plan(source, target, plan, pd, cd, True)
        except OneError:
            continue
        return False
    try:
        _direct_wire_from_plan(source, target, (("ref", 0, 8, b""),), "0" * 63, cd, True)
    except OneError:
        pass
    else:
        return False
    return True


def _time_pair(bctx, cctx):
    baseline_samples = []
    candidate_samples = []
    baseline_value = None
    candidate_value = None
    was_enabled = gc.isenabled()
    try:
        if was_enabled:
            gc.disable()
        for round_index in range(ROUNDS):
            order = (False, True) if round_index % 2 == 0 else (True, False)
            for candidate in order:
                t0 = time.perf_counter_ns()
                if candidate:
                    value = _candidate_once(*cctx)
                else:
                    value = _writer_once_direct_unprofiled(*bctx)
                elapsed = time.perf_counter_ns() - t0
                if candidate:
                    candidate_samples.append(elapsed)
                    candidate_value = value
                else:
                    baseline_samples.append(elapsed)
                    baseline_value = value
    finally:
        if was_enabled:
            gc.enable()
    return (
        float(statistics.median(baseline_samples)), baseline_value,
        float(statistics.median(candidate_samples)), candidate_value,
    )


def run():
    admission_fn, segment_fn, td = _build_native()
    rows = []
    semantic_ok = True
    oracle_ok = True
    malformed_ok = _malformed_plan_probes()
    mature_productive = []
    mature_controls = []
    try:
        for size in SIZES:
            cases = _relation_cases(size)
            for case in PRODUCTIVE + CONTROLS:
                source, target, expected_enable, expected_shift = cases[case]
                src_arr = (ctypes.c_uint8 * size).from_buffer_copy(source)
                dst_arr = (ctypes.c_uint8 * size).from_buffer_copy(target)
                seg_buf = (Segment * size)()
                bctx = (admission_fn, segment_fn, source, target, src_arr, dst_arr, seg_buf)
                cctx = bctx

                baseline = _writer_once_direct_unprofiled(*bctx)
                candidate = _candidate_once(*cctx)
                bwire, bstats, bprogram, bresult, breads, bused, benabled, bplan, btraffic, bsegments, bdepth = baseline
                cwire, cstats, cresult, creads, cused, cenabled, cplan, ctraffic, csegments, cdepth, cnode_count = candidate
                this_semantic = (
                    bwire == cwire
                    and bstats == cstats
                    and benabled == cenabled
                    and int(bresult.best_shift) == int(cresult.best_shift)
                    and int(bresult.exact_proofs) == int(cresult.exact_proofs)
                    and _plan_signature(bplan) == _plan_signature(cplan)
                    and btraffic == ctraffic
                    and bsegments == csegments
                    and bdepth == cdepth
                    and len(bprogram.nodes) == cnode_count
                )
                this_oracle = (not benabled) or (
                    _plan_signature(bplan) == _plan_signature(_oracle_plan(source, target))
                )
                decoded = decode_program(cwire)
                outputs, vm_stats = evaluate(decoded)
                exact = outputs == {"previous": source, "current": target}
                this_semantic = this_semantic and exact
                semantic_ok &= this_semantic
                oracle_ok &= this_oracle
                if not this_semantic or not this_oracle:
                    raise AssertionError("plan-direct writer changed canonical semantics/oracle")

                baseline_ns, btimed, candidate_ns, ctimed = _time_pair(bctx, cctx)
                if btimed is None or ctimed is None or btimed[0] != ctimed[0] or btimed[1] != ctimed[1]:
                    raise AssertionError("timed plan-direct writer changed canonical bytes/stats")
                ratio = candidate_ns / baseline_ns
                is_productive = case in PRODUCTIVE
                if size >= MATURE_MIN:
                    (mature_productive if is_productive else mature_controls).append(ratio)
                rows.append({
                    "relation_bytes": size,
                    "case": case,
                    "productive": is_productive,
                    "relation_enabled": cenabled,
                    "best_shift": int(cresult.best_shift),
                    "exact_proofs": int(cresult.exact_proofs),
                    "segments": csegments,
                    "program_nodes": cnode_count,
                    "hierarchy_depth": cdepth,
                    "canonical_wire_bytes": cstats.total_bytes,
                    "surprise_bytes": cstats.surprise_bytes,
                    "reader_work_bytes": vm_stats.work_bytes,
                    "reader_materialized_bytes": vm_stats.materialized_bytes,
                    "baseline_full_writer_median_ns": baseline_ns,
                    "candidate_plan_direct_full_writer_median_ns": candidate_ns,
                    "candidate_over_baseline": ratio,
                    "wire_exact": bwire == cwire,
                    "native_plan_matches_python_oracle": this_oracle,
                    "exact_reconstruction": exact,
                })

        productive_median = float(statistics.median(mature_productive))
        productive_good = sum(r <= PRODUCTIVE_GOOD_MAX for r in mature_productive)
        worst_productive = max(mature_productive)
        control_median = float(statistics.median(mature_controls))
        worst_control = max(mature_controls)
        perf_ok = (
            productive_median <= PRODUCTIVE_MEDIAN_MAX
            and productive_good >= MIN_PRODUCTIVE_GOOD
            and worst_productive <= PRODUCTIVE_ROW_MAX
            and control_median <= CONTROL_MEDIAN_MAX
            and worst_control <= CONTROL_ROW_MAX
        )
        if not semantic_ok or not oracle_ok or not malformed_ok:
            decision = "invalidate_plan_direct_wire_writer"
        elif perf_ok:
            decision = "advance_plan_direct_wire_writer"
        else:
            decision = "reject_plan_direct_wire_writer"
        return {
            "schema": "cmpct-one-g02-root-hash-writer-plan-direct-wire-v1",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "frozen_rounds": ROUNDS,
            "semantic_gates_pass": semantic_ok,
            "native_plan_oracle_pass": oracle_ok,
            "malformed_plan_rejection_pass": malformed_ok,
            "mature_productive_median_ratio": productive_median,
            "mature_productive_rows_at_or_below_0_90": productive_good,
            "mature_productive_worst_ratio": worst_productive,
            "mature_control_median_ratio": control_median,
            "mature_control_worst_ratio": worst_control,
            "decision": decision,
            "claim_boundary": (
                "writer-compiler optimization only inside the existing adjacent-version root-hash-charged "
                "research writer; exact same ONE0 bytes and reader; excludes arbitrary/fused discovery, "
                "authenticated placement/durability, filesystem semantics, product-native speed and v0.29/v0.30 supremacy"
            ),
            "rows": rows,
        }
    finally:
        td.cleanup()


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["decision"] == "advance_plan_direct_wire_writer" else 1)
