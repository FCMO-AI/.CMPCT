"""ONE-G0.2 corrected plan-direct canonical writer falsifier.

Frozen by ONE_G02_ROOT_HASH_WRITER_PLAN_DIRECT_WIRE_V2_PREREG_2026-09-06.md.
This V2 changes only hierarchy bookkeeping: creator-known reconstructed span is
kept separate from the canonical serialized Ref.length field.
"""
from __future__ import annotations

import ctypes
from hashlib import sha256
import json
import os

import benchmarks.one.one_g02_root_hash_writer_plan_direct_wire as v1
from experiments.one.growable_wire import _append_blob, _append_uvarint
from experiments.one.ir import Limits, OneError
from experiments.one.wire import MAGIC, MAX_NAME_BYTES, MAX_ROOTS, TAGS, WireStats


def _append_ref_fields(out: bytearray, node: int, start: int = 0, length: int | None = None) -> None:
    _append_uvarint(out, node)
    _append_uvarint(out, start)
    _append_uvarint(out, 0 if length is None else length + 1)


def _append_surprise_node(out: bytearray, payload: bytes) -> None:
    out.append(TAGS["surprise"])
    _append_uvarint(out, 0)
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


def _direct_wire_from_plan_v2(
    source: bytes,
    target: bytes,
    plan,
    previous_digest: str,
    current_digest: str,
    enabled: bool,
):
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
        # node, start, canonical serialized Ref.length, creator-only known span
        level: list[tuple[int, int, int | None, int]] = []
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
                level.append((0, offset, length, length))
            elif kind == "surprise":
                if not isinstance(payload, bytes) or len(payload) != length:
                    raise OneError("Surprise payload length mismatch")
                surprise_nodes.append(payload)
                surprise_bytes += len(payload)
                level.append((next_node, 0, None, length))
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
            nxt: list[tuple[int, int, int | None, int]] = []
            for off in range(0, len(level), fanout):
                chunk = tuple(level[off:off + fanout])
                declared = sum(span for _node, _start, _wire_len, span in chunk)
                refs = tuple((node, start, wire_len) for node, start, wire_len, _span in chunk)
                intermediate_nodes.append((refs, declared))
                # Canonical Program uses Ref(node) here: no serialized subrange length.
                # Keep the known span only for the next parent's declared-length arithmetic.
                nxt.append((next_node, 0, None, declared))
                next_node += 1
            level = nxt
            hierarchy_depth += 1
        final_refs = tuple((node, start, wire_len) for node, start, wire_len, _span in level)
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


def _candidate_once_v2(admission_fn, segment_fn, source, target, src_arr, dst_arr, seg_buf):
    previous_digest = sha256(source).hexdigest()
    current_digest = sha256(target).hexdigest()
    result, gate_reads, gate_used, enabled = v1._admit(admission_fn, src_arr, dst_arr, len(source))
    segment_stats = v1.SegmentStats()
    if enabled:
        plan = v1._native_plan(segment_fn, src_arr, dst_arr, len(source), seg_buf, segment_stats)
    else:
        plan = ()
    wire, stats, depth, node_count = _direct_wire_from_plan_v2(
        source, target, plan, previous_digest, current_digest, enabled
    )
    return (
        wire, stats, result, gate_reads, gate_used, enabled, plan,
        int(segment_stats.compared_target_bytes), int(segment_stats.segments), depth, node_count,
    )


def _malformed_plan_probes_v2() -> bool:
    source = b"abcdefgh"
    target = b"bcdefghi"
    pd = sha256(source).hexdigest()
    cd = sha256(target).hexdigest()
    malformed = (
        (("ref", 7, 2, b""),),
        (("surprise", 0, 4, b"abc"), ("surprise", 0, 4, b"defg")),
        (("ref", 0, 4, b""),),
        (("bogus", 0, 8, b""),),
        (("ref", -1, 8, b""),),
    )
    for plan in malformed:
        try:
            _direct_wire_from_plan_v2(source, target, plan, pd, cd, True)
        except OneError:
            continue
        return False
    try:
        _direct_wire_from_plan_v2(source, target, (("ref", 0, 8, b""),), "0" * 63, cd, True)
    except OneError:
        pass
    else:
        return False
    return True


def run():
    original_candidate = v1._candidate_once
    original_malformed = v1._malformed_plan_probes
    try:
        v1._candidate_once = _candidate_once_v2
        v1._malformed_plan_probes = _malformed_plan_probes_v2
        result = v1.run()
    finally:
        v1._candidate_once = original_candidate
        v1._malformed_plan_probes = original_malformed

    decision_map = {
        "invalidate_plan_direct_wire_writer": "invalidate_plan_direct_wire_writer_v2",
        "reject_plan_direct_wire_writer": "reject_plan_direct_wire_writer_v2",
        "advance_plan_direct_wire_writer": "advance_plan_direct_wire_writer_v2",
    }
    result["schema"] = "cmpct-one-g02-root-hash-writer-plan-direct-wire-v2"
    result["source_sha"] = os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound"
    result["predecessor_invalidated_source"] = "9083603dff3cb311340b3c56429e0165cc2ec34e"
    result["causal_repair"] = "separate serialized Ref.length from creator-only known span on intermediate concat refs"
    result["decision"] = decision_map[result["decision"]]
    return result


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["decision"] == "advance_plan_direct_wire_writer_v2" else 1)
