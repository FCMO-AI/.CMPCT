"""ONE-G0.2 representation-neutral root-sink fusion for generic relation cones.

This is a research execution strategy over the existing six-op ONE Program.  It adds no
reader-visible operation and performs no reader discovery.  After the ordinary reference
preflight validates the complete stored graph, a narrowly supported root Concat can stream
direct Surprise ranges and generic add8/xor(Surprise, Fill(constant)) cones into their final
root positions.  Fill values and relation children are therefore not materialized as full
intermediate byte strings, and the root Concat is not recopied through another full buffer.
Unsupported geometry fails closed.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from hashlib import sha256

from experiments.one.ir import Node, OneError, Program, Ref
from experiments.one.vm import _preflight


@dataclass(frozen=True)
class RelationRootFusionStats:
    stored_source_read_bytes: int
    root_sink_write_bytes: int
    relation_arithmetic_bytes: int
    root_accounting_bytes: int
    modeled_work_bytes: int
    materialized_bytes: int
    peak_temporary_bytes: int
    fused_relations: int
    direct_surprises: int


@lru_cache(maxsize=512)
def _translation(op: str, value: int) -> bytes:
    if op == "add8":
        return bytes((byte + value) & 0xFF for byte in range(256))
    if op == "xor":
        return bytes(byte ^ value for byte in range(256))
    raise OneError(f"unsupported relation op {op!r}")


def _bounds(ref: Ref, length: int) -> tuple[int, int]:
    if ref.start > length:
        raise OneError("fusion range starts past referenced output")
    end = length if ref.length is None else ref.start + ref.length
    if end < ref.start or end > length:
        raise OneError("fusion range exceeds referenced output")
    return ref.start, end


def _surprise_range(program: Program, ref: Ref) -> memoryview:
    node = program.nodes[ref.node]
    if node.op != "surprise":
        raise OneError("relation root fusion requires Surprise source")
    start, end = _bounds(ref, len(node.surprise))
    return memoryview(node.surprise)[start:end]


def _constant_fill(program: Program, ref: Ref, expected: int) -> int:
    node = program.nodes[ref.node]
    if node.op != "fill":
        raise OneError("relation root fusion requires Fill constant")
    start, end = _bounds(ref, node.count)
    if end - start != expected:
        raise OneError("relation Fill width differs from source width")
    return node.value


def _relation(program: Program, node: Node) -> tuple[memoryview, int]:
    if node.op not in {"add8", "xor"} or len(node.refs) != 2 or node.surprise:
        raise OneError("unsupported relation cone for root fusion")
    left, right = node.refs
    left_node = program.nodes[left.node]
    right_node = program.nodes[right.node]
    if left_node.op == "surprise" and right_node.op == "fill":
        source_ref, fill_ref = left, right
    elif left_node.op == "fill" and right_node.op == "surprise":
        source_ref, fill_ref = right, left
    else:
        raise OneError("relation root fusion requires exactly one Surprise and one Fill")
    source = _surprise_range(program, source_ref)
    value = _constant_fill(program, fill_ref, len(source))
    if node.declared_length is not None and node.declared_length != len(source):
        raise OneError("relation declared length differs from operand width")
    return source, value


def evaluate_relation_roots_fused(program: Program) -> tuple[dict[str, bytes], RelationRootFusionStats]:
    """Execute the supported generic relation geometry directly into final root sinks.

    The model charges actual stored-source reads, final-root writes, one byte of arithmetic
    per relation output byte, and two root-length charges matching the reference evaluator's
    root range/hash accounting.  It intentionally does not charge a fictitious materialized
    Fill operand or a second full Concat copy, because neither exists in this execution.
    """
    program.validate_shape()
    _preflight(program)  # validates every stored node, including unreachable nodes

    outputs: dict[str, bytes] = {}
    source_reads = 0
    sink_writes = 0
    arithmetic = 0
    root_accounting = 0
    fused_relations = 0
    direct_surprises = 0
    materialized = 0
    peak_temp = 0

    for name, root in program.roots.items():
        root_node = program.nodes[root.ref.node]
        if root_node.op != "concat" or root_node.surprise:
            raise OneError("relation root fusion requires a pure root Concat")
        if root.ref.start != 0 or root.ref.length not in {None, root.length}:
            raise OneError("relation root fusion requires a complete root reference")
        if root_node.declared_length != root.length:
            raise OneError("root Concat declared length mismatch")

        sink = bytearray(root.length)
        materialized += len(sink)
        peak_temp = max(peak_temp, len(sink))
        cursor = 0
        for child_ref in root_node.refs:
            child = program.nodes[child_ref.node]
            if child.op == "surprise":
                view = _surprise_range(program, child_ref)
                width = len(view)
                if cursor + width > len(sink):
                    raise OneError("direct Surprise exceeds root sink")
                sink[cursor : cursor + width] = view
                source_reads += width
                sink_writes += width
                direct_surprises += 1
                cursor += width
                continue

            if child.op not in {"add8", "xor"}:
                raise OneError("unsupported child below fused root Concat")
            if child_ref.start != 0 or child_ref.length not in {None, child.declared_length}:
                raise OneError("fused relation child must be referenced in full")
            source, value = _relation(program, child)
            width = len(source)
            if cursor + width > len(sink):
                raise OneError("relation output exceeds root sink")
            # bytes.translate executes the existing byte-wise Law in a compact native loop.
            # A block-sized derived temporary exists transiently; it is bounded and counted
            # in peak temporary state, but is not retained as a materialized graph value.
            derived = bytes(source).translate(_translation(child.op, value))
            sink[cursor : cursor + width] = derived
            source_reads += width
            sink_writes += width
            arithmetic += width
            fused_relations += 1
            peak_temp = max(peak_temp, len(sink) + len(derived))
            cursor += width

        if cursor != root.length:
            raise OneError(f"root {name!r} fused length mismatch")
        root_accounting += 2 * len(sink)
        if sha256(sink).hexdigest() != root.sha256:
            raise OneError(f"root {name!r} sha256 mismatch")
        outputs[name] = bytes(sink)

    modeled_work = source_reads + sink_writes + arithmetic + root_accounting
    if modeled_work > program.limits.max_work_bytes:
        raise OneError("fused modeled work exceeds declared limit")
    return outputs, RelationRootFusionStats(
        stored_source_read_bytes=source_reads,
        root_sink_write_bytes=sink_writes,
        relation_arithmetic_bytes=arithmetic,
        root_accounting_bytes=root_accounting,
        modeled_work_bytes=modeled_work,
        materialized_bytes=materialized,
        peak_temporary_bytes=peak_temp,
        fused_relations=fused_relations,
        direct_surprises=direct_surprises,
    )
