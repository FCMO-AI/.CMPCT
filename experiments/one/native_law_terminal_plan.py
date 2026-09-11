"""ONE-G0.2 generic native Law-terminal execution experiment.

This module lowers an already validated ordinary ONE Program into a bounded native
execution schedule for a deliberately small set of terminal cones. It changes no
stored operation or wire format: unsupported topology fails closed to the incumbent
reader.

The first integration target is the modern relation shape:
  Surprise / Fill / (add8|xor) / Concat
including arbitrary validated ranges of terminal Surprise and Fill operands.
"""
from __future__ import annotations

import ctypes
from dataclasses import dataclass
from functools import lru_cache
from hashlib import sha256
from pathlib import Path
import subprocess
import tempfile

from experiments.one.fused_terminal_reader import FusedTerminalStats, _ref_bounds, _terminal_length
from experiments.one.ir import Node, OneError, Program, Ref
from experiments.one.vm import _preflight

COPY = 0
FILL = 1
ADD8_CONST = 2
XOR_CONST = 3


class _LawCmd(ctypes.Structure):
    _fields_ = [
        ("offset", ctypes.c_uint64),
        ("length", ctypes.c_uint64),
        ("source_offset", ctypes.c_uint64),
        ("value", ctypes.c_uint8),
        ("kind", ctypes.c_uint8),
    ]


@lru_cache(maxsize=1)
def _library() -> ctypes.CDLL:
    source = Path(__file__).with_name("native_law_terminal_plan_kernel.c")
    build_dir = Path(tempfile.mkdtemp(prefix="cmpct-one-law-terminal-"))
    output = build_dir / "libone_law_terminal.so"
    subprocess.run(
        ["cc", "-O3", "-std=c11", "-fPIC", "-shared", str(source), "-o", str(output)],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    lib = ctypes.CDLL(str(output))
    fn = lib.one_apply_law_terminal_schedule
    fn.argtypes = [
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.c_size_t,
        ctypes.POINTER(_LawCmd),
        ctypes.c_size_t,
    ]
    fn.restype = ctypes.c_int
    periodic = lib.one_copy_periodic
    periodic.argtypes = [
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.c_size_t,
        ctypes.c_size_t,
        ctypes.c_size_t,
        ctypes.c_size_t,
    ]
    periodic.restype = ctypes.c_int
    return lib


@lru_cache(maxsize=1)
def _bytes_api():
    alloc = ctypes.pythonapi.PyBytes_FromStringAndSize
    alloc.argtypes = [ctypes.c_void_p, ctypes.c_ssize_t]
    alloc.restype = ctypes.py_object
    ptr = ctypes.pythonapi.PyBytes_AsString
    ptr.argtypes = [ctypes.py_object]
    ptr.restype = ctypes.c_void_p
    return alloc, ptr


@dataclass
class NativeLawRoot:
    name: str
    length: int
    sha256_hex: str
    source_blob: bytes
    source_buffer: object
    commands: object
    command_count: int
    source_read_bytes: int
    sink_write_bytes: int


@dataclass
class NativeLawTerminalPlan:
    roots: tuple[NativeLawRoot, ...]
    max_work_bytes: int
    packed_source_bytes: int
    command_count: int


def has_native_law_op(program: Program) -> bool:
    """Cheap static eligibility check; no data discovery or byte scanning."""
    return any(node.op in {"add8", "xor"} for node in program.nodes)


def _node_length(node: Node) -> int:
    if node.op in {"surprise", "fill"}:
        return _terminal_length(node)
    if node.declared_length is None:
        raise OneError("native Law terminal lowering requires statically declared length")
    return node.declared_length


def _constant_law(program: Program, node: Node, ref: Ref) -> tuple[memoryview, int, int]:
    """Return a zero-copy view of the Surprise source plus constant-Law metadata."""
    if node.op not in {"add8", "xor"} or node.surprise or len(node.refs) != 2:
        raise OneError("unsupported Law shape for native terminal lowering")
    node_len = _node_length(node)
    out_lo, out_hi = _ref_bounds(ref, node_len)
    width = out_hi - out_lo
    source_ref = None
    fill_ref = None
    for operand in node.refs:
        operand_node = program.nodes[operand.node]
        if operand_node.op == "surprise" and source_ref is None:
            source_ref = operand
        elif operand_node.op == "fill" and fill_ref is None:
            fill_ref = operand
        else:
            raise OneError("native Law terminal requires one Surprise and one Fill operand")
    if source_ref is None or fill_ref is None:
        raise OneError("native Law terminal requires one Surprise and one Fill operand")
    source_node = program.nodes[source_ref.node]
    fill_node = program.nodes[fill_ref.node]
    src_lo, src_hi = _ref_bounds(source_ref, _node_length(source_node))
    fill_lo, fill_hi = _ref_bounds(fill_ref, _node_length(fill_node))
    if src_hi - src_lo != node_len or fill_hi - fill_lo != node_len:
        raise OneError("Law operands do not cover declared Law output")
    src_lo += out_lo
    src_hi = src_lo + width
    if src_hi > len(source_node.surprise):
        raise OneError("Law source range exceeds Surprise operand")
    kind = ADD8_CONST if node.op == "add8" else XOR_CONST
    return memoryview(source_node.surprise)[src_lo:src_hi], fill_node.value, kind


def compile_native_law_terminal_plan(program: Program) -> NativeLawTerminalPlan:
    program.validate_shape()
    _preflight(program)
    prepared: list[NativeLawRoot] = []
    total_packed = 0
    total_commands = 0
    for name, root in program.roots.items():
        root_node = program.nodes[root.ref.node]
        root_len = _node_length(root_node)
        start, end = _ref_bounds(root.ref, root_len)
        if start != 0 or end != root_len or root.length != root_len:
            raise OneError("native Law terminal reader currently requires complete root references")
        blob = bytearray()
        steps: list[tuple[int, int, int, int, int]] = []
        cursor = source_reads = sink_writes = 0

        def emit(node: Node, ref: Ref) -> None:
            nonlocal cursor, source_reads, sink_writes
            node_len = _node_length(node)
            lo, hi = _ref_bounds(ref, node_len)
            width = hi - lo
            if cursor + width > root.length:
                raise OneError("native Law terminal output exceeds root")
            if node.op == "surprise":
                src_off = len(blob)
                blob.extend(memoryview(node.surprise)[lo:hi])
                steps.append((cursor, width, src_off, 0, COPY))
                source_reads += width
            elif node.op == "fill":
                steps.append((cursor, width, 0, node.value, FILL))
            elif node.op in {"add8", "xor"}:
                payload, value, kind = _constant_law(program, node, ref)
                if len(payload) != width:
                    raise OneError("native Law lowering produced wrong source width")
                src_off = len(blob)
                blob.extend(payload)
                steps.append((cursor, width, src_off, value, kind))
                source_reads += width
            else:
                raise OneError("unsupported child operation for native Law terminal plan")
            sink_writes += width
            cursor += width

        if root_node.op in {"surprise", "fill", "add8", "xor"}:
            emit(root_node, Ref(root.ref.node))
        elif root_node.op == "concat":
            if root_node.surprise:
                raise OneError("native Law terminal concat Surprise tail is not yet lowered")
            for child_ref in root_node.refs:
                emit(program.nodes[child_ref.node], child_ref)
        else:
            raise OneError("unsupported root operation for native Law terminal plan")
        if cursor != root.length:
            raise OneError(f"root {name!r} native Law terminal length mismatch")
        for offset, width, src_off, _value, kind in steps:
            if width < 0 or offset + width > root.length:
                raise OneError("native Law terminal command exceeds root")
            if kind in {COPY, ADD8_CONST, XOR_CONST} and src_off + width > len(blob):
                raise OneError("native Law terminal command exceeds packed source")
        command_array = ((_LawCmd * len(steps))(*(_LawCmd(*step) for step in steps)) if steps else None)
        packed = bytes(blob)
        source_buffer = ((ctypes.c_uint8 * len(packed)).from_buffer_copy(packed) if packed else None)
        prepared.append(NativeLawRoot(name, root.length, root.sha256, packed, source_buffer, command_array, len(steps), source_reads, sink_writes))
        total_packed += len(packed)
        total_commands += len(steps)
    return NativeLawTerminalPlan(tuple(prepared), program.limits.max_work_bytes, total_packed, total_commands)


def _apply_root_direct(root: NativeLawRoot) -> bytes:
    """Execute directly into a newly allocated final immutable bytes object.

    The object is not exposed outside this function until native writes and SHA-256
    verification complete. This removes V1's bytearray -> bytes full-root freeze copy.
    """
    alloc, bytes_ptr = _bytes_api()
    sink = alloc(None, root.length)
    raw = bytes_ptr(sink)
    sink_ptr = ctypes.cast(raw, ctypes.POINTER(ctypes.c_uint8)) if root.length else ctypes.POINTER(ctypes.c_uint8)()
    source_ptr = ctypes.cast(root.source_buffer, ctypes.POINTER(ctypes.c_uint8)) if root.source_buffer is not None else ctypes.POINTER(ctypes.c_uint8)()
    rc = _library().one_apply_law_terminal_schedule(sink_ptr, root.length, source_ptr, len(root.source_blob), root.commands, root.command_count)
    if rc != 0:
        raise OneError(f"native Law terminal schedule rejected with status {rc}")
    if sha256(sink).hexdigest() != root.sha256_hex:
        raise OneError(f"root {root.name!r} sha256 mismatch")
    return sink


def execute_native_law_terminal_plan(plan: NativeLawTerminalPlan) -> tuple[dict[str, bytes], FusedTerminalStats]:
    outputs: dict[str, bytes] = {}
    source_reads = sink_writes = hash_reads = peak_temporary = 0
    for root in plan.roots:
        outputs[root.name] = _apply_root_direct(root)
        source_reads += root.source_read_bytes
        sink_writes += root.sink_write_bytes
        hash_reads += root.length
        peak_temporary = max(peak_temporary, root.length)
    freeze_traffic = 0
    modeled = source_reads + sink_writes + hash_reads
    if modeled > plan.max_work_bytes:
        raise OneError("native Law terminal modeled memory traffic exceeds declared work limit")
    return outputs, FusedTerminalStats(source_reads, sink_writes, hash_reads, freeze_traffic, modeled, peak_temporary, len(outputs))
