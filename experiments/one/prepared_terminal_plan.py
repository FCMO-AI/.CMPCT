"""ONE-G0.2 prepared terminal execution plan experiment.

Compilation validates the unchanged ONE Program once and lowers the supported terminal
Surprise/Fill/Concat shape into a bounded replay plan. Replay performs no graph walk or
schedule construction. This is execution preparation, not discovery and not a new opcode.
"""
from __future__ import annotations

import ctypes
from dataclasses import dataclass
from hashlib import sha256

from experiments.one.fused_terminal_reader import FusedTerminalStats, _ref_bounds, _terminal_length
from experiments.one.ir import OneError, Program, Ref
from experiments.one.native_terminal_fill import _FillCmd, _library
from experiments.one.vm import _preflight


@dataclass
class PreparedRoot:
    name: str
    length: int
    sha256_hex: str
    surprise_steps: tuple[tuple[int, bytes, int, int], ...]
    fill_commands: object
    fill_count: int
    stored_surprise_read_bytes: int
    sink_write_bytes: int


@dataclass
class PreparedTerminalPlan:
    roots: tuple[PreparedRoot, ...]
    max_work_bytes: int


def compile_terminal_plan(program: Program) -> PreparedTerminalPlan:
    """Validate and lower a bounded terminal graph into deterministic replay state."""
    program.validate_shape()
    _preflight(program)
    prepared: list[PreparedRoot] = []
    for name, root in program.roots.items():
        root_node = program.nodes[root.ref.node]
        root_len = _terminal_length(root_node) if root_node.op in {"surprise", "fill"} else root_node.declared_length
        if root_len is None:
            raise OneError("prepared terminal root requires statically declared length")
        start, end = _ref_bounds(root.ref, root_len)
        if start != 0 or end != root_len or root.length != root_len:
            raise OneError("prepared terminal reader currently requires complete root references")

        cursor = 0
        surprises: list[tuple[int, bytes, int, int]] = []
        fills: list[tuple[int, int, int]] = []
        stored_reads = 0
        sink_writes = 0

        def emit(node, ref: Ref) -> None:
            nonlocal cursor, stored_reads, sink_writes
            length = _terminal_length(node)
            lo, hi = _ref_bounds(ref, length)
            width = hi - lo
            if cursor + width > root.length:
                raise OneError("terminal output exceeds prepared root")
            if node.op == "surprise":
                surprises.append((cursor, node.surprise, lo, hi))
                stored_reads += width
            elif width:
                fills.append((cursor, width, node.value))
            sink_writes += width
            cursor += width

        if root_node.op in {"surprise", "fill"}:
            emit(root_node, Ref(root.ref.node))
        elif root_node.op == "concat":
            for child_ref in root_node.refs:
                child = program.nodes[child_ref.node]
                if child.op not in {"surprise", "fill"}:
                    raise OneError("prepared terminal concat contains non-terminal child")
                emit(child, child_ref)
            if root_node.surprise:
                width = len(root_node.surprise)
                if cursor + width > root.length:
                    raise OneError("concat Surprise exceeds prepared root")
                surprises.append((cursor, root_node.surprise, 0, width))
                stored_reads += width
                sink_writes += width
                cursor += width
        else:
            raise OneError("unsupported root operation for prepared terminal plan")

        if cursor != root.length:
            raise OneError(f"root {name!r} prepared length mismatch")
        commands = (_FillCmd * len(fills))(*(_FillCmd(off, width, value) for off, width, value in fills)) if fills else None
        prepared.append(PreparedRoot(name, root.length, root.sha256, tuple(surprises), commands, len(fills), stored_reads, sink_writes))
    return PreparedTerminalPlan(tuple(prepared), program.limits.max_work_bytes)


def execute_prepared_terminal_plan(plan: PreparedTerminalPlan) -> tuple[dict[str, bytes], FusedTerminalStats]:
    outputs: dict[str, bytes] = {}
    stored_reads = sink_writes = hash_reads = freeze_traffic = peak_temporary = 0
    fn = _library().one_apply_fill_schedule
    for root in plan.roots:
        sink = bytearray(root.length)
        peak_temporary = max(peak_temporary, root.length)
        for offset, payload, lo, hi in root.surprise_steps:
            sink[offset : offset + (hi - lo)] = memoryview(payload)[lo:hi]
        if root.fill_count:
            sink_ptr = ctypes.cast((ctypes.c_uint8 * len(sink)).from_buffer(sink), ctypes.POINTER(ctypes.c_uint8))
            rc = fn(sink_ptr, len(sink), root.fill_commands, root.fill_count)
            if rc != 0:
                raise OneError(f"prepared Fill schedule rejected with status {rc}")
        if sha256(sink).hexdigest() != root.sha256_hex:
            raise OneError(f"root {root.name!r} sha256 mismatch")
        value = bytes(sink)
        outputs[root.name] = value
        stored_reads += root.stored_surprise_read_bytes
        sink_writes += root.sink_write_bytes
        hash_reads += root.length
        freeze_traffic += 2 * root.length
    modeled = stored_reads + sink_writes + hash_reads + freeze_traffic
    if modeled > plan.max_work_bytes:
        raise OneError("prepared terminal modeled memory traffic exceeds declared work limit")
    return outputs, FusedTerminalStats(stored_reads, sink_writes, hash_reads, freeze_traffic, modeled, peak_temporary, len(outputs))
