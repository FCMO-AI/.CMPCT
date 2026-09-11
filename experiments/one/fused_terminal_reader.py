"""Research reader that fuses terminal ONE Law pieces into a root sink.

This is an execution strategy over the existing ONE IR, not a reader-visible opcode.
It intentionally supports only direct terminal roots and a root-level concat whose
references point at terminal ``surprise``/``fill`` nodes. Unsupported graphs fail
closed so semantic coverage cannot silently expand during the experiment.
"""
from __future__ import annotations

import ctypes
from dataclasses import dataclass
from hashlib import sha256

from experiments.one.ir import Node, OneError, Program, Ref
from experiments.one.vm import _preflight


@dataclass(frozen=True)
class FusedTerminalStats:
    stored_surprise_read_bytes: int
    root_sink_write_bytes: int
    root_hash_read_bytes: int
    output_freeze_traffic_bytes: int
    modeled_memory_traffic_bytes: int
    peak_temporary_bytes: int
    roots_reconstructed: int


def _ref_bounds(ref: Ref, length: int) -> tuple[int, int]:
    if ref.start > length:
        raise OneError("range starts past referenced output")
    end = length if ref.length is None else ref.start + ref.length
    if end < ref.start or end > length:
        raise OneError("range exceeds referenced output")
    return ref.start, end


def _terminal_length(node: Node) -> int:
    if node.op == "surprise":
        return len(node.surprise)
    if node.op == "fill":
        return node.count
    raise OneError("fused terminal reader requires surprise/fill terminal")


def _write_terminal(node: Node, ref: Ref, sink: bytearray, offset: int) -> tuple[int, int]:
    """Write one terminal range directly into ``sink``.

    Returns ``(written, stored_surprise_reads)``. Fill uses ``ctypes.memset`` against
    the already allocated root sink so the Python semantic vector does not manufacture
    a second run-sized payload merely to copy it into the destination. Surprise uses a
    memoryview slice so it likewise avoids manufacturing an uncharged payload copy.
    These are execution implementation details; the stored ONE graph and reader
    ontology remain ordinary ``fill``/``surprise``/``concat``.
    """
    length = _terminal_length(node)
    start, end = _ref_bounds(ref, length)
    width = end - start
    if offset + width > len(sink):
        raise OneError("terminal output exceeds root sink")
    if node.op == "surprise":
        sink[offset : offset + width] = memoryview(node.surprise)[start:end]
        return width, width
    if width:
        address = ctypes.addressof(ctypes.c_ubyte.from_buffer(sink, offset))
        ctypes.memset(address, node.value, width)
    return width, 0


def evaluate_terminal_roots_fused(program: Program) -> tuple[dict[str, bytes], FusedTerminalStats]:
    """Reconstruct supported roots without materializing terminal concat children.

    The generic reference preflight runs first and proves the unchanged graph/range/
    depth/output/work envelope before any output byte is written. Every reconstructed
    root is independently SHA-256 checked against the Program commitment.
    """
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
            raise OneError("fused root requires statically declared root length")
        root_start, root_end = _ref_bounds(root.ref, root_node_length)
        if root_start != 0 or root_end != root_node_length or root.length != root_node_length:
            raise OneError("fused terminal reader currently requires complete root references")

        sink = bytearray(root.length)
        peak_temporary = max(peak_temporary, len(sink))
        cursor = 0

        if root_node.op in {"surprise", "fill"}:
            written, reads = _write_terminal(root_node, Ref(root.ref.node), sink, 0)
            cursor += written
            stored_reads += reads
            sink_writes += written
        elif root_node.op == "concat":
            for child_ref in root_node.refs:
                child = program.nodes[child_ref.node]
                if child.op not in {"surprise", "fill"}:
                    raise OneError("fused terminal concat contains non-terminal child")
                written, reads = _write_terminal(child, child_ref, sink, cursor)
                cursor += written
                stored_reads += reads
                sink_writes += written
            if root_node.surprise:
                end = cursor + len(root_node.surprise)
                if end > len(sink):
                    raise OneError("concat Surprise exceeds root sink")
                sink[cursor:end] = memoryview(root_node.surprise)
                stored_reads += len(root_node.surprise)
                sink_writes += len(root_node.surprise)
                cursor = end
        else:
            raise OneError("unsupported root operation for fused terminal reader")

        if cursor != root.length:
            raise OneError(f"root {name!r} reconstructed length mismatch")
        hash_reads += len(sink)
        if sha256(sink).hexdigest() != root.sha256:
            raise OneError(f"root {name!r} sha256 mismatch")

        value = bytes(sink)
        freeze_traffic += 2 * len(value)
        outputs[name] = value

    modeled = stored_reads + sink_writes + hash_reads + freeze_traffic
    if modeled > program.limits.max_work_bytes:
        raise OneError("fused modeled memory traffic exceeds declared work limit")
    return outputs, FusedTerminalStats(
        stored_surprise_read_bytes=stored_reads,
        root_sink_write_bytes=sink_writes,
        root_hash_read_bytes=hash_reads,
        output_freeze_traffic_bytes=freeze_traffic,
        modeled_memory_traffic_bytes=modeled,
        peak_temporary_bytes=peak_temporary,
        roots_reconstructed=len(outputs),
    )
