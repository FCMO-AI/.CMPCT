"""ONE-G0.2 research reader: one native bulk call for terminal Fill spans.

The stored Program is unchanged. Surprise bytes still move through Python memoryviews;
only the repeated Fill writes are collected into a bounded schedule and executed through
one native call per root. Schedule construction remains inside the evaluated call.
"""
from __future__ import annotations

import ctypes
from functools import lru_cache
from hashlib import sha256
from pathlib import Path
import subprocess
import tempfile

from experiments.one.fused_terminal_reader import FusedTerminalStats, _ref_bounds, _terminal_length
from experiments.one.ir import OneError, Program, Ref
from experiments.one.vm import _preflight


class _FillCmd(ctypes.Structure):
    _fields_ = [
        ("offset", ctypes.c_uint64),
        ("length", ctypes.c_uint64),
        ("value", ctypes.c_uint8),
    ]


@lru_cache(maxsize=1)
def _library() -> ctypes.CDLL:
    source = Path(__file__).with_name("native_terminal_fill_kernel.c")
    build_dir = Path(tempfile.mkdtemp(prefix="cmpct-one-terminal-fill-"))
    output = build_dir / "libone_terminal_fill.so"
    subprocess.run(
        ["cc", "-O3", "-std=c11", "-fPIC", "-shared", str(source), "-o", str(output)],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    lib = ctypes.CDLL(str(output))
    fn = lib.one_apply_fill_schedule
    fn.argtypes = [
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.c_size_t,
        ctypes.POINTER(_FillCmd),
        ctypes.c_size_t,
    ]
    fn.restype = ctypes.c_int
    return lib


def _apply_fill_schedule(sink: bytearray, fills: list[tuple[int, int, int]]) -> None:
    if not fills:
        return
    commands = (_FillCmd * len(fills))(*(_FillCmd(off, width, value) for off, width, value in fills))
    if sink:
        sink_ptr = ctypes.cast((ctypes.c_uint8 * len(sink)).from_buffer(sink), ctypes.POINTER(ctypes.c_uint8))
    else:
        sink_ptr = ctypes.POINTER(ctypes.c_uint8)()
    rc = _library().one_apply_fill_schedule(sink_ptr, len(sink), commands, len(fills))
    if rc != 0:
        raise OneError(f"native terminal Fill schedule rejected with status {rc}")


def evaluate_terminal_roots_bulk_fill(program: Program) -> tuple[dict[str, bytes], FusedTerminalStats]:
    """Evaluate the same bounded terminal graph with one Fill dispatch per root."""
    program.validate_shape()
    _preflight(program)

    outputs: dict[str, bytes] = {}
    stored_reads = 0
    sink_writes = 0
    hash_reads = 0
    freeze_traffic = 0
    peak_temporary = 0

    for name, root in program.roots.items():
        root_node = program.nodes[root.ref.node]
        root_node_length = _terminal_length(root_node) if root_node.op in {"surprise", "fill"} else root_node.declared_length
        if root_node_length is None:
            raise OneError("bulk terminal root requires statically declared root length")
        root_start, root_end = _ref_bounds(root.ref, root_node_length)
        if root_start != 0 or root_end != root_node_length or root.length != root_node_length:
            raise OneError("bulk terminal reader currently requires complete root references")

        sink = bytearray(root.length)
        peak_temporary = max(peak_temporary, len(sink))
        cursor = 0
        fills: list[tuple[int, int, int]] = []

        def emit_terminal(node, ref: Ref) -> None:
            nonlocal cursor, stored_reads, sink_writes
            length = _terminal_length(node)
            start, end = _ref_bounds(ref, length)
            width = end - start
            if cursor + width > len(sink):
                raise OneError("terminal output exceeds root sink")
            if node.op == "surprise":
                sink[cursor : cursor + width] = memoryview(node.surprise)[start:end]
                stored_reads += width
            elif width:
                fills.append((cursor, width, node.value))
            sink_writes += width
            cursor += width

        if root_node.op in {"surprise", "fill"}:
            emit_terminal(root_node, Ref(root.ref.node))
        elif root_node.op == "concat":
            for child_ref in root_node.refs:
                child = program.nodes[child_ref.node]
                if child.op not in {"surprise", "fill"}:
                    raise OneError("bulk terminal concat contains non-terminal child")
                emit_terminal(child, child_ref)
            if root_node.surprise:
                end = cursor + len(root_node.surprise)
                if end > len(sink):
                    raise OneError("concat Surprise exceeds root sink")
                sink[cursor:end] = memoryview(root_node.surprise)
                stored_reads += len(root_node.surprise)
                sink_writes += len(root_node.surprise)
                cursor = end
        else:
            raise OneError("unsupported root operation for bulk terminal reader")

        if cursor != root.length:
            raise OneError(f"root {name!r} reconstructed length mismatch")
        _apply_fill_schedule(sink, fills)
        hash_reads += len(sink)
        if sha256(sink).hexdigest() != root.sha256:
            raise OneError(f"root {name!r} sha256 mismatch")
        value = bytes(sink)
        freeze_traffic += 2 * len(value)
        outputs[name] = value

    modeled = stored_reads + sink_writes + hash_reads + freeze_traffic
    if modeled > program.limits.max_work_bytes:
        raise OneError("bulk fused modeled memory traffic exceeds declared work limit")
    return outputs, FusedTerminalStats(
        stored_surprise_read_bytes=stored_reads,
        root_sink_write_bytes=sink_writes,
        root_hash_read_bytes=hash_reads,
        output_freeze_traffic_bytes=freeze_traffic,
        modeled_memory_traffic_bytes=modeled,
        peak_temporary_bytes=peak_temporary,
        roots_reconstructed=len(outputs),
    )
