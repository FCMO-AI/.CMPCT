"""ONE-G0.2 native-segment-buffer direct canonical writer V3 falsifier.

Frozen by ONE_G02_ROOT_HASH_WRITER_NATIVE_BUFFER_DIRECT_WIRE_V3_PREREG_2026-09-06.md.
"""
from __future__ import annotations

import ctypes
import gc
from hashlib import sha256
import json
import os
import statistics

import benchmarks.one.one_g02_root_hash_writer_plan_direct_wire as v1
from benchmarks.one.one_g02_end_to_end_direct_emitter_writer import (
    CONTROLS, PRODUCTIVE, ROUNDS, SIZES, Segment, SegmentStats,
    _build_native, _native_plan, _oracle_plan, _plan_signature, _relation_cases,
)
from benchmarks.one.one_g02_root_hash_writer_plan_direct_wire_v2 import (
    _candidate_once_v2, _direct_wire_from_plan_v2,
)
from experiments.one.growable_wire import _append_blob, _append_uvarint
from experiments.one.ir import Limits, OneError
from experiments.one.vm import evaluate
from experiments.one.wire import MAGIC, MAX_NAME_BYTES, MAX_ROOTS, TAGS, WireStats, decode_program

MATURE_MIN = 16 * 1024
PRODUCTIVE_MEDIAN_MAX = 0.90
PRODUCTIVE_GOOD_MAX = 0.95
MIN_PRODUCTIVE_GOOD = 12
PRODUCTIVE_ROW_MAX = 1.03
CONTROL_MEDIAN_MAX = 1.03
CONTROL_ROW_MAX = 1.08


def _append_ref_fields(out: bytearray, node: int, start: int = 0, length: int | None = None) -> None:
    _append_uvarint(out, node)
    _append_uvarint(out, start)
    _append_uvarint(out, 0 if length is None else length + 1)


def _append_blob_view(out: bytearray, view) -> None:
    _append_uvarint(out, len(view))
    out.extend(view)


def _append_surprise_view(out: bytearray, view) -> None:
    out.append(TAGS["surprise"])
    _append_uvarint(out, 0)
    _append_blob_view(out, view)


def _append_concat(out: bytearray, refs, declared: int) -> None:
    out.append(TAGS["concat"])
    _append_uvarint(out, declared + 1)
    _append_uvarint(out, len(refs))
    for node, start, wire_len in refs:
        _append_ref_fields(out, node, start, wire_len)
    _append_uvarint(out, 0)  # empty concat Surprise blob


def _validate_digest(digest: str) -> None:
    if not isinstance(digest, str) or len(digest) != 64:
        raise OneError("root sha256 must be exactly 64 hex characters")
    try:
        raw = bytes.fromhex(digest)
    except ValueError as exc:
        raise OneError("root sha256 is not hexadecimal") from exc
    if len(raw) != 32:
        raise OneError("root sha256 must decode to exactly 32 bytes")


def _direct_wire_from_native_buffer_v3(
    source: bytes,
    target: bytes,
    seg_buf,
    segment_count: int,
    previous_digest: str,
    current_digest: str,
    enabled: bool,
):
    limits = Limits()
    limits.validate()
    _validate_digest(previous_digest)
    _validate_digest(current_digest)
    if not isinstance(source, bytes) or not isinstance(target, bytes):
        raise OneError("native-buffer writer requires immutable byte inputs")
    if len(source) > limits.max_output_bytes or len(target) > limits.max_output_bytes:
        raise OneError("root length exceeds declared output limit")
    if type(segment_count) is not int or segment_count < 0:
        raise OneError("invalid native segment count")
    if enabled and segment_count <= 0:
        raise OneError("enabled relation requires segment plan")
    if segment_count > len(target):
        raise OneError("native segment count exceeds target length")

    target_view = memoryview(target)
    source_view = memoryview(source)
    surprise_spans: list[tuple[int, int]] = []
    intermediate_nodes: list[tuple[tuple[tuple[int, int, int | None], ...], int]] = []
    surprise_bytes = len(source)
    hierarchy_depth = 0

    if enabled:
        # node, start, serialized Ref.length, creator-known reconstructed span
        level: list[tuple[int, int, int | None, int]] = []
        covered = 0
        next_node = 1
        for idx in range(segment_count):
            seg = seg_buf[idx]
            start = int(seg.start)
            length = int(seg.length)
            kind = int(seg.kind)
            if start < 0 or length <= 0:
                raise OneError("invalid native segment start/length")
            if kind == 0:
                if start + length > len(source):
                    raise OneError("native source Ref exceeds previous root")
                level.append((0, start, length, length))
            elif kind == 1:
                if start + length > len(target):
                    raise OneError("native Surprise span exceeds target")
                surprise_spans.append((start, length))
                surprise_bytes += length
                level.append((next_node, 0, None, length))
                next_node += 1
            else:
                raise OneError("unknown native segment kind")
            covered += length
            if covered > len(target):
                raise OneError("native segment plan exceeds target coverage")
        if covered != len(target) or not level:
            raise OneError("native segment plan does not exactly cover target")

        hierarchy_depth = 1
        fanout = limits.max_nodes
        while len(level) > fanout:
            nxt: list[tuple[int, int, int | None, int]] = []
            for off in range(0, len(level), fanout):
                chunk4 = tuple(level[off:off + fanout])
                declared = sum(span for _node, _start, _wire_len, span in chunk4)
                refs = tuple((node, start, wire_len) for node, start, wire_len, _span in chunk4)
                intermediate_nodes.append((refs, declared))
                nxt.append((next_node, 0, None, declared))
                next_node += 1
            level = nxt
            hierarchy_depth += 1
        final_refs = tuple((node, start, wire_len) for node, start, wire_len, _span in level)
        final_node = next_node
        node_count = final_node + 1
    else:
        if segment_count != 0:
            raise OneError("disabled relation must not carry native segments")
        surprise_spans = [(0, len(target))]
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
    for value in (limits.max_nodes, limits.max_output_bytes, limits.max_work_bytes, limits.max_depth, node_count):
        _append_uvarint(out, value)

    _append_surprise_view(out, source_view)
    for start, length in surprise_spans:
        _append_surprise_view(out, target_view[start:start + length])

    if enabled:
        for refs, declared in intermediate_nodes:
            _append_concat(out, refs, declared)
        _append_concat(out, final_refs, len(target))

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


def _candidate_once_v3(admission_fn, segment_fn, source, target, src_arr, dst_arr, seg_buf):
    previous_digest = sha256(source).hexdigest()
    current_digest = sha256(target).hexdigest()
    result, gate_reads, gate_used, enabled = v1._admit(admission_fn, src_arr, dst_arr, len(source))
    stats = SegmentStats()
    if enabled:
        rc = segment_fn(src_arr, dst_arr, len(source), seg_buf, len(source), ctypes.byref(stats))
        if rc != 0:
            raise RuntimeError(f"native one-pass segmenter failed: {rc}")
        segment_count = int(stats.segments)
    else:
        stats.compared_target_bytes = 0
        stats.segments = 0
        segment_count = 0
    wire, wire_stats, depth, node_count = _direct_wire_from_native_buffer_v3(
        source, target, seg_buf, segment_count, previous_digest, current_digest, enabled
    )
    return (
        wire, wire_stats, result, gate_reads, gate_used, enabled,
        int(stats.compared_target_bytes), segment_count, depth, node_count,
    )


def _time_pair(ctx):
    baseline_samples = []
    candidate_samples = []
    baseline_value = None
    candidate_value = None
    was_enabled = gc.isenabled()
    try:
        if was_enabled:
            gc.disable()
        for r in range(ROUNDS):
            order = (False, True) if r % 2 == 0 else (True, False)
            for candidate in order:
                t0 = __import__("time").perf_counter_ns()
                value = _candidate_once_v3(*ctx) if candidate else _candidate_once_v2(*ctx)
                elapsed = __import__("time").perf_counter_ns() - t0
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


def _audit_native_plan(segment_fn, src_arr, dst_arr, n, seg_buf, source, target):
    stats = SegmentStats()
    plan = _native_plan(segment_fn, src_arr, dst_arr, n, seg_buf, stats)
    return plan, int(stats.compared_target_bytes), int(stats.segments), (
        _plan_signature(plan) == _plan_signature(_oracle_plan(source, target))
    )


def _malformed_native_probes() -> bool:
    source = b"abcdefgh"
    target = b"bcdefghi"
    pd = sha256(source).hexdigest()
    cd = sha256(target).hexdigest()
    buf = (Segment * 8)()

    probes = []
    # zero length
    buf[0].kind, buf[0].start, buf[0].length = 0, 0, 0
    probes.append(([(0,0,0)], 1))
    # out-of-range ref
    probes.append(([(0,7,2)], 1))
    # out-of-range Surprise
    probes.append(([(1,7,2)], 1))
    # unknown kind
    probes.append(([(7,0,8)], 1))
    # incomplete coverage
    probes.append(([(0,0,4)], 1))
    # over coverage
    probes.append(([(0,0,8),(1,0,1)], 2))

    for spec, count in probes:
        for i, (kind, start, length) in enumerate(spec):
            buf[i].kind, buf[i].start, buf[i].length = kind, start, length
        try:
            _direct_wire_from_native_buffer_v3(source, target, buf, count, pd, cd, True)
        except OneError:
            continue
        return False
    try:
        _direct_wire_from_native_buffer_v3(source, target, buf, len(target)+1, pd, cd, True)
    except OneError:
        pass
    else:
        return False
    return True


def run():
    admission_fn, segment_fn, td = _build_native()
    rows = []
    semantic_failures = 0
    oracle_failures = 0
    mature_productive = []
    mature_controls = []
    malformed_ok = _malformed_native_probes()
    try:
        for size in SIZES:
            cases = _relation_cases(size)
            for case in PRODUCTIVE + CONTROLS:
                source, target, expected_enable, expected_shift = cases[case]
                src_arr = (ctypes.c_uint8 * size).from_buffer_copy(source)
                dst_arr = (ctypes.c_uint8 * size).from_buffer_copy(target)
                seg_buf = (Segment * size)()
                ctx = (admission_fn, segment_fn, source, target, src_arr, dst_arr, seg_buf)

                baseline = _candidate_once_v2(*ctx)
                candidate = _candidate_once_v3(*ctx)
                bwire, bstats, bresult, breads, bused, benabled, bplan, btraffic, bsegments, bdepth, bnodes = baseline
                cwire, cstats, cresult, creads, cused, cenabled, ctraffic, csegments, cdepth, cnodes = candidate
                audit_plan, audit_traffic, audit_segments, this_oracle = _audit_native_plan(
                    segment_fn, src_arr, dst_arr, size, seg_buf, source, target
                ) if benabled else ((), 0, 0, True)
                this_semantic = (
                    bwire == cwire and bstats == cstats and benabled == cenabled
                    and int(bresult.best_shift) == int(cresult.best_shift)
                    and int(bresult.exact_proofs) == int(cresult.exact_proofs)
                    and breads == creads and bused == cused
                    and btraffic == ctraffic == audit_traffic
                    and bsegments == csegments == audit_segments
                    and bdepth == cdepth and bnodes == cnodes
                    and ((not benabled) or _plan_signature(bplan) == _plan_signature(audit_plan))
                )
                outputs, vm_stats = evaluate(decode_program(cwire))
                exact = outputs == {"previous": source, "current": target}
                this_semantic = this_semantic and exact
                if not this_semantic:
                    semantic_failures += 1
                    raise AssertionError(f"native-buffer V3 semantic mismatch: {case}/{size}")
                if not this_oracle:
                    oracle_failures += 1
                    raise AssertionError(f"native-buffer V3 plan oracle mismatch: {case}/{size}")

                baseline_ns, bt, candidate_ns, ct = _time_pair(ctx)
                if bt is None or ct is None or bt[0] != ct[0] or bt[1] != ct[1]:
                    raise AssertionError("timed native-buffer V3 changed canonical bytes/stats")
                ratio = candidate_ns / baseline_ns
                productive = case in PRODUCTIVE
                if size >= MATURE_MIN:
                    (mature_productive if productive else mature_controls).append(ratio)
                rows.append({
                    "relation_bytes": size,
                    "case": case,
                    "productive": productive,
                    "relation_enabled": cenabled,
                    "best_shift": int(cresult.best_shift),
                    "exact_proofs": int(cresult.exact_proofs),
                    "segments": csegments,
                    "hierarchy_depth": cdepth,
                    "node_count": cnodes,
                    "canonical_wire_bytes": cstats.total_bytes,
                    "surprise_bytes": cstats.surprise_bytes,
                    "reader_work_bytes": vm_stats.work_bytes,
                    "reader_materialized_bytes": vm_stats.materialized_bytes,
                    "baseline_v2_median_ns": baseline_ns,
                    "candidate_v3_median_ns": candidate_ns,
                    "candidate_over_baseline": ratio,
                    "canonical_wire_exact": bwire == cwire,
                    "native_plan_oracle_exact": this_oracle,
                    "exact_reconstruction": exact,
                })

        pmed = float(statistics.median(mature_productive))
        pgood = sum(r <= PRODUCTIVE_GOOD_MAX for r in mature_productive)
        pworst = max(mature_productive)
        cmed = float(statistics.median(mature_controls))
        cworst = max(mature_controls)
        perf_ok = (
            pmed <= PRODUCTIVE_MEDIAN_MAX and pgood >= MIN_PRODUCTIVE_GOOD
            and pworst <= PRODUCTIVE_ROW_MAX and cmed <= CONTROL_MEDIAN_MAX
            and cworst <= CONTROL_ROW_MAX
        )
        if semantic_failures or oracle_failures or not malformed_ok:
            decision = "invalidate_native_buffer_direct_wire_v3"
        elif perf_ok:
            decision = "advance_native_buffer_direct_wire_v3"
        else:
            decision = "reject_native_buffer_direct_wire_v3"
        return {
            "schema": "cmpct-one-g02-root-hash-writer-native-buffer-direct-wire-v3",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "frozen_rounds": ROUNDS,
            "semantic_failures": semantic_failures,
            "oracle_failures": oracle_failures,
            "malformed_native_buffer_probes_pass": malformed_ok,
            "mature_productive_median_ratio": pmed,
            "mature_productive_rows_at_or_below_0_95": pgood,
            "mature_productive_worst_ratio": pworst,
            "mature_control_median_ratio": cmed,
            "mature_control_worst_ratio": cworst,
            "decision": decision,
            "claim_boundary": "root-hash-charged adjacent-version V2 writer compiler fusion only; arbitrary/fused discovery, RSS/native peak, filesystem/product and comparator authority excluded",
            "rows": rows,
        }
    finally:
        td.cleanup()


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["decision"] == "advance_native_buffer_direct_wire_v3" else 1)
