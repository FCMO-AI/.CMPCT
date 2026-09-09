"""Cone-proportional native execution for ordinary ONE Law terminals.

This is an experimental lowering layer. It reads the existing Program topology and lowers
only one requested root interval into the same native COPY/FILL/ADD8/XOR schedule used by
the promoted whole-root terminal reader. It introduces no reader-visible operation.
Unsupported topology raises OneError so callers can measure fallback explicitly.
"""
from __future__ import annotations

import ctypes
from dataclasses import dataclass

from .fused_terminal_reader import _ref_bounds
from .ir import OneError, Program, Ref
from .native_law_terminal_plan import (
    ADD8_CONST,
    COPY,
    FILL,
    XOR_CONST,
    _LawCmd,
    _bytes_api,
    _constant_law,
    _library,
    _node_length,
)
from .vm import _preflight


@dataclass
class NativeLawRangePlan:
    root_name: str
    root_start: int
    length: int
    source_blob: bytes
    source_buffer: object
    commands: object
    command_count: int
    source_read_bytes: int
    sink_write_bytes: int
    max_work_bytes: int

    @property
    def packed_source_bytes(self) -> int:
        return len(self.source_blob)


def _ref_width(program: Program, ref: Ref) -> int:
    node_len = _node_length(program.nodes[ref.node])
    lo, hi = _ref_bounds(ref, node_len)
    return hi - lo


def compile_native_law_range_plan(
    program: Program,
    root_name: str,
    start: int,
    length: int,
) -> NativeLawRangePlan:
    """Lower exactly ``[start,start+length)`` of one root into a native schedule."""
    program.validate_shape()
    _preflight(program)
    if root_name not in program.roots:
        raise OneError(f"unknown root {root_name!r}")
    root = program.roots[root_name]
    if type(start) is not int or type(length) is not int or start < 0 or length < 0:
        raise OneError("range start/length must be non-negative integers")
    if start + length > root.length:
        raise OneError("requested range exceeds root")

    blob = bytearray()
    steps: list[tuple[int, int, int, int, int]] = []
    cursor = 0
    source_reads = 0

    def emit_terminal(node_ref: Ref, rel_start: int, take: int) -> None:
        nonlocal cursor, source_reads
        if take == 0:
            return
        node = program.nodes[node_ref.node]
        node_len = _node_length(node)
        ref_lo, ref_hi = _ref_bounds(node_ref, node_len)
        if rel_start < 0 or rel_start + take > ref_hi - ref_lo:
            raise OneError("native range request exceeds terminal reference")
        effective = Ref(node_ref.node, ref_lo + rel_start, take)

        if node.op == "surprise":
            src_lo, src_hi = _ref_bounds(effective, node_len)
            payload = node.surprise[src_lo:src_hi]
            if len(payload) != take:
                raise OneError("native range Surprise slice mismatch")
            src_off = len(blob)
            blob.extend(payload)
            steps.append((cursor, take, src_off, 0, COPY))
            source_reads += take
        elif node.op == "fill":
            steps.append((cursor, take, 0, node.value, FILL))
        elif node.op in {"add8", "xor"}:
            payload, value, kind = _constant_law(program, node, effective)
            if len(payload) != take:
                raise OneError("native range Law source mismatch")
            src_off = len(blob)
            blob.extend(payload)
            steps.append((cursor, take, src_off, value, kind))
            source_reads += take
        else:
            raise OneError(f"unsupported native range terminal {node.op!r}")
        cursor += take

    def walk(ref: Ref, rel_start: int, take: int) -> None:
        if take == 0:
            return
        node = program.nodes[ref.node]
        width = _ref_width(program, ref)
        if rel_start < 0 or rel_start + take > width:
            raise OneError("native range request exceeds reference")
        if node.op in {"surprise", "fill", "add8", "xor"}:
            emit_terminal(ref, rel_start, take)
            return
        if node.op != "concat":
            raise OneError(f"unsupported native range topology {node.op!r}")

        ref_node_len = _node_length(node)
        outer_lo, _outer_hi = _ref_bounds(ref, ref_node_len)
        want_lo = outer_lo + rel_start
        want_hi = want_lo + take
        node_cursor = 0
        emitted_before = cursor

        for child in node.refs:
            child_width = _ref_width(program, child)
            child_lo = node_cursor
            child_hi = child_lo + child_width
            lo = max(want_lo, child_lo)
            hi = min(want_hi, child_hi)
            if hi > lo:
                walk(child, lo - child_lo, hi - lo)
            node_cursor = child_hi

        if node.surprise:
            # Keep this first candidate narrow and auditable. A concat Surprise tail is
            # valid ONE but is reported as unsupported rather than reconstructed outside
            # the native schedule or hidden in fallback.
            raise OneError("concat Surprise tail native range lowering not yet supported")

        if cursor - emitted_before != take:
            raise OneError("native range concat coverage mismatch")

    # Root Ref can itself select a subrange from its node.
    walk(root.ref, start, length)
    if cursor != length:
        raise OneError("native range plan produced wrong output length")

    for offset, width, src_off, _value, kind in steps:
        if offset + width > length:
            raise OneError("native range command exceeds output")
        if kind in {COPY, ADD8_CONST, XOR_CONST} and src_off + width > len(blob):
            raise OneError("native range command exceeds packed source")

    packed = bytes(blob)
    source_buffer = (
        (ctypes.c_uint8 * len(packed)).from_buffer_copy(packed) if packed else None
    )
    commands = (
        (_LawCmd * len(steps))(*(_LawCmd(*step) for step in steps)) if steps else None
    )
    return NativeLawRangePlan(
        root_name=root_name,
        root_start=start,
        length=length,
        source_blob=packed,
        source_buffer=source_buffer,
        commands=commands,
        command_count=len(steps),
        source_read_bytes=source_reads,
        sink_write_bytes=length,
        max_work_bytes=program.limits.max_work_bytes,
    )


def execute_native_law_range_plan(plan: NativeLawRangePlan) -> bytes:
    alloc, bytes_ptr = _bytes_api()
    sink = alloc(None, plan.length)
    raw = bytes_ptr(sink)
    sink_ptr = (
        ctypes.cast(raw, ctypes.POINTER(ctypes.c_uint8))
        if plan.length
        else ctypes.POINTER(ctypes.c_uint8)()
    )
    source_ptr = (
        ctypes.cast(plan.source_buffer, ctypes.POINTER(ctypes.c_uint8))
        if plan.source_buffer is not None
        else ctypes.POINTER(ctypes.c_uint8)()
    )
    rc = _library().one_apply_law_terminal_schedule(
        sink_ptr,
        plan.length,
        source_ptr,
        len(plan.source_blob),
        plan.commands,
        plan.command_count,
    )
    if rc != 0:
        raise OneError(f"native Law range schedule rejected with status {rc}")
    modeled_work = plan.source_read_bytes + plan.sink_write_bytes
    if modeled_work > plan.max_work_bytes:
        raise OneError("native Law range modeled work exceeds declared limit")
    return sink
