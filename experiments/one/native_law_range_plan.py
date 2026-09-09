"""Cone-proportional native execution for ordinary ONE Law terminals.

This is an experimental lowering layer. It reads the existing Program topology and lowers
only one requested root interval into bounded native execution. Ordinary Law terminals use
the promoted COPY/FILL/ADD8/XOR schedule. A validated direct Repeat(Surprise) cone may use
a bulk periodic-copy kernel that is an execution detail, not a reader-visible ONE operation.
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
from .validated_program import ValidatedProgram
from .vm import _preflight


@dataclass
class NativeLawRangePlan:
    root_name: str
    root_start: int
    length: int
    # Private mutable backing store for ordinary scheduled terminals. It is never exposed
    # to the reader and is not modified after compilation.
    source_blob: bytearray
    source_buffer: object
    commands: object
    command_count: int
    source_read_bytes: int
    source_plan_write_bytes: int
    sink_write_bytes: int
    max_work_bytes: int
    # Optional borrowed immutable source for a validated direct periodic view. Keeping the
    # exact Program bytes object alive lets the bulk kernel read it without a cone-sized
    # source-plan copy.
    periodic_source: bytes | None = None
    periodic_source_offset: int = 0
    periodic_width: int = 0
    periodic_phase: int = 0

    @property
    def packed_source_bytes(self) -> int:
        return len(self.source_blob)

    @property
    def bulk_periodic(self) -> bool:
        return self.periodic_source is not None


def _ref_width(program: Program, ref: Ref) -> int:
    node_len = _node_length(program.nodes[ref.node])
    lo, hi = _ref_bounds(ref, node_len)
    return hi - lo


def _direct_periodic_plan(
    program: Program,
    root_name: str,
    start: int,
    length: int,
) -> NativeLawRangePlan | None:
    """Return a zero-repack plan for a validated direct Repeat(Surprise) root.

    This performs no discovery. The caller has already established complete Program
    validity; this function merely recognizes the explicit stored topology and maps the
    requested root coordinate into the repeated child period.
    """
    if length == 0:
        return None
    root = program.roots[root_name]
    node = program.nodes[root.ref.node]
    if node.op != "repeat" or len(node.refs) != 1:
        return None
    child = node.refs[0]
    child_node = program.nodes[child.node]
    if child_node.op != "surprise":
        return None

    child_len = _node_length(child_node)
    child_lo, child_hi = _ref_bounds(child, child_len)
    period = child_hi - child_lo
    if period == 0:
        raise OneError("non-empty native range requested from empty repeat source")
    node_len = _node_length(node)
    root_lo, _root_hi = _ref_bounds(root.ref, node_len)
    phase = (root_lo + start) % period

    return NativeLawRangePlan(
        root_name=root_name,
        root_start=start,
        length=length,
        source_blob=bytearray(),
        source_buffer=None,
        commands=None,
        # One bounded execution descriptor, independent of cone/period quotient.
        command_count=1,
        # The bulk kernel consumes one source byte per emitted byte. There is no
        # intermediate source-plan write.
        source_read_bytes=length,
        source_plan_write_bytes=0,
        sink_write_bytes=length,
        max_work_bytes=program.limits.max_work_bytes,
        periodic_source=child_node.surprise,
        periodic_source_offset=child_lo,
        periodic_width=period,
        periodic_phase=phase,
    )


def _compile_range_from_valid_snapshot(
    program: Program,
    root_name: str,
    start: int,
    length: int,
) -> NativeLawRangePlan:
    """Lower one range after full Program validation authority has already been established."""
    if root_name not in program.roots:
        raise OneError(f"unknown root {root_name!r}")
    root = program.roots[root_name]
    if type(start) is not int or type(length) is not int or start < 0 or length < 0:
        raise OneError("range start/length must be non-negative integers")
    if start + length > root.length:
        raise OneError("requested range exceeds root")

    periodic = _direct_periodic_plan(program, root_name, start, length)
    if periodic is not None:
        return periodic

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
            payload = memoryview(node.surprise)[src_lo:src_hi]
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

        if node.op == "repeat":
            child = node.refs[0]
            child_width = _ref_width(program, child)
            if child_width == 0:
                raise OneError("non-empty native range requested from empty repeat source")
            node_len = _node_length(node)
            outer_lo, _outer_hi = _ref_bounds(ref, node_len)
            position = outer_lo + rel_start
            remaining = take
            emitted_before = cursor
            while remaining:
                child_rel = position % child_width
                chunk = min(remaining, child_width - child_rel)
                walk(child, child_rel, chunk)
                position += chunk
                remaining -= chunk
            if cursor - emitted_before != take:
                raise OneError("native range repeat coverage mismatch")
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
            raise OneError("concat Surprise tail native range lowering not yet supported")

        if cursor - emitted_before != take:
            raise OneError("native range concat coverage mismatch")

    walk(root.ref, start, length)
    if cursor != length:
        raise OneError("native range plan produced wrong output length")

    for offset, width, src_off, _value, kind in steps:
        if offset + width > length:
            raise OneError("native range command exceeds output")
        if kind in {COPY, ADD8_CONST, XOR_CONST} and src_off + width > len(blob):
            raise OneError("native range command exceeds packed source")

    source_buffer = (
        (ctypes.c_uint8 * len(blob)).from_buffer(blob) if blob else None
    )
    commands = (
        (_LawCmd * len(steps))(*(_LawCmd(*step) for step in steps)) if steps else None
    )
    return NativeLawRangePlan(
        root_name=root_name,
        root_start=start,
        length=length,
        source_blob=blob,
        source_buffer=source_buffer,
        commands=commands,
        command_count=len(steps),
        source_read_bytes=source_reads,
        source_plan_write_bytes=len(blob),
        sink_write_bytes=length,
        max_work_bytes=program.limits.max_work_bytes,
    )


def compile_native_law_range_plan(
    program: Program,
    root_name: str,
    start: int,
    length: int,
) -> NativeLawRangePlan:
    """Lower a range from a raw Program, retaining the inherited full validation boundary."""
    program.validate_shape()
    _preflight(program)
    return _compile_range_from_valid_snapshot(program, root_name, start, length)


def compile_validated_native_law_range_plan(
    validated: ValidatedProgram,
    root_name: str,
    start: int,
    length: int,
) -> NativeLawRangePlan:
    """Lower a range from an immutable Program whose complete graph already passed preflight."""
    if not isinstance(validated, ValidatedProgram):
        raise TypeError("validated must be ValidatedProgram")
    return _compile_range_from_valid_snapshot(validated.program, root_name, start, length)


def execute_native_law_range_plan(plan: NativeLawRangePlan) -> bytes:
    alloc, bytes_ptr = _bytes_api()
    sink = alloc(None, plan.length)
    raw = bytes_ptr(sink)
    sink_ptr = (
        ctypes.cast(raw, ctypes.POINTER(ctypes.c_uint8))
        if plan.length
        else ctypes.POINTER(ctypes.c_uint8)()
    )

    if plan.bulk_periodic:
        source_raw = bytes_ptr(plan.periodic_source)
        source_ptr = ctypes.cast(source_raw, ctypes.POINTER(ctypes.c_uint8))
        rc = _library().one_copy_periodic(
            sink_ptr,
            plan.length,
            source_ptr,
            len(plan.periodic_source),
            plan.periodic_source_offset,
            plan.periodic_width,
            plan.periodic_phase,
        )
        if rc != 0:
            raise OneError(f"native periodic range copy rejected with status {rc}")
    else:
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

    modeled_work = (
        plan.source_read_bytes
        + plan.source_plan_write_bytes
        + plan.sink_write_bytes
    )
    if modeled_work > plan.max_work_bytes:
        raise OneError("native Law range modeled work exceeds declared limit")
    return sink
