"""Sized single-buffer ONE canonical emitter experiment.

Research-only ONE-G0.2 implementation. The normal entrypoint preserves the exact
validation obligation of experiments.one.wire.encode_program; the private
prevalidated entrypoint exists only for causal emission-cost measurement.
"""
from __future__ import annotations

from .ir import Node, OneError, Program, Ref
from .wire import MAGIC, MAX_NAME_BYTES, MAX_ROOTS, MAX_U64, TAGS, WireStats


def _uvarint_size(value: int) -> int:
    if not isinstance(value, int) or value < 0 or value > MAX_U64:
        raise OneError("uvarint requires unsigned 64-bit integer")
    size = 1
    while value >= 0x80:
        value >>= 7
        size += 1
    return size


def _write_uvarint(out: bytearray, pos: int, value: int) -> int:
    if not isinstance(value, int) or value < 0 or value > MAX_U64:
        raise OneError("uvarint requires unsigned 64-bit integer")
    while value >= 0x80:
        out[pos] = (value & 0x7F) | 0x80
        pos += 1
        value >>= 7
    out[pos] = value
    return pos + 1


def _ref_size(ref: Ref) -> int:
    length_code = 0 if ref.length is None else ref.length + 1
    return _uvarint_size(ref.node) + _uvarint_size(ref.start) + _uvarint_size(length_code)


def _write_ref(out: bytearray, pos: int, ref: Ref) -> int:
    length_code = 0 if ref.length is None else ref.length + 1
    pos = _write_uvarint(out, pos, ref.node)
    pos = _write_uvarint(out, pos, ref.start)
    return _write_uvarint(out, pos, length_code)


def _blob_size(value: bytes) -> int:
    return _uvarint_size(len(value)) + len(value)


def _write_blob(out: bytearray, pos: int, value: bytes) -> int:
    pos = _write_uvarint(out, pos, len(value))
    end = pos + len(value)
    out[pos:end] = value
    return end


def _node_size(node: Node) -> int:
    size = 1 + _uvarint_size(0 if node.declared_length is None else node.declared_length + 1)
    if node.op == "surprise":
        return size + _blob_size(node.surprise)
    if node.op == "concat":
        return size + _uvarint_size(len(node.refs)) + sum(_ref_size(ref) for ref in node.refs) + _blob_size(node.surprise)
    if node.op == "repeat":
        return size + _ref_size(node.refs[0]) + _uvarint_size(node.count)
    if node.op == "fill":
        return size + 1 + _uvarint_size(node.count)
    if node.op in {"xor", "add8"}:
        return size + _uvarint_size(len(node.refs)) + sum(_ref_size(ref) for ref in node.refs) + _blob_size(node.surprise)
    raise OneError(f"unknown operation {node.op!r}")


def _write_node(out: bytearray, pos: int, node: Node) -> int:
    out[pos] = TAGS[node.op]
    pos += 1
    pos = _write_uvarint(out, pos, 0 if node.declared_length is None else node.declared_length + 1)
    if node.op == "surprise":
        return _write_blob(out, pos, node.surprise)
    if node.op == "concat":
        pos = _write_uvarint(out, pos, len(node.refs))
        for ref in node.refs:
            pos = _write_ref(out, pos, ref)
        return _write_blob(out, pos, node.surprise)
    if node.op == "repeat":
        pos = _write_ref(out, pos, node.refs[0])
        return _write_uvarint(out, pos, node.count)
    if node.op == "fill":
        out[pos] = node.value
        return _write_uvarint(out, pos + 1, node.count)
    if node.op in {"xor", "add8"}:
        pos = _write_uvarint(out, pos, len(node.refs))
        for ref in node.refs:
            pos = _write_ref(out, pos, ref)
        return _write_blob(out, pos, node.surprise)
    raise OneError(f"unknown operation {node.op!r}")


def _encode_program_bulk_prevalidated(program: Program) -> tuple[bytes, WireStats]:
    """Emit exact canonical bytes for a Program whose shape was already validated."""
    roots = sorted(program.roots.items())
    if len(roots) > MAX_ROOTS:
        raise OneError("root count exceeds experimental wire limit")

    root_material: list[tuple[bytes, object]] = []
    total = len(MAGIC)
    for value in (
        program.limits.max_nodes,
        program.limits.max_output_bytes,
        program.limits.max_work_bytes,
        program.limits.max_depth,
        len(program.nodes),
    ):
        total += _uvarint_size(value)
    total += sum(_node_size(node) for node in program.nodes)
    total += _uvarint_size(len(roots))

    for name, root in roots:
        name_bytes = name.encode("utf-8")
        if len(name_bytes) > MAX_NAME_BYTES:
            raise OneError("root name exceeds experimental wire limit")
        digest = bytes.fromhex(root.sha256)
        root_material.append((name_bytes, root))
        total += _blob_size(name_bytes) + _ref_size(root.ref) + _uvarint_size(root.length) + len(digest)

    out = bytearray(total)
    out[:len(MAGIC)] = MAGIC
    pos = len(MAGIC)
    for value in (
        program.limits.max_nodes,
        program.limits.max_output_bytes,
        program.limits.max_work_bytes,
        program.limits.max_depth,
        len(program.nodes),
    ):
        pos = _write_uvarint(out, pos, value)
    for node in program.nodes:
        pos = _write_node(out, pos, node)
    pos = _write_uvarint(out, pos, len(root_material))
    for name_bytes, root in root_material:
        pos = _write_blob(out, pos, name_bytes)
        pos = _write_ref(out, pos, root.ref)
        pos = _write_uvarint(out, pos, root.length)
        digest = bytes.fromhex(root.sha256)
        out[pos:pos + 32] = digest
        pos += 32
    if pos != total:
        raise AssertionError("bulk ONE emitter size/write disagreement")

    surprise_bytes = sum(len(node.surprise) for node in program.nodes)
    stats = WireStats(total_bytes=total, surprise_bytes=surprise_bytes, control_integrity_bytes=total - surprise_bytes)
    return bytes(out), stats


def encode_program_bulk(program: Program) -> tuple[bytes, WireStats]:
    """Validated research entrypoint; semantics and wire bytes match encode_program."""
    program.validate_shape()
    return _encode_program_bulk_prevalidated(program)
