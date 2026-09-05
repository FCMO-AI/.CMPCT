"""One-pass growable ONE canonical emitter experiment.

Research-only ONE-G0.2 implementation. It preserves the ordinary validation
boundary and canonical ONE0 bytes while avoiding temporary per-varint/ref/node
byte strings. Unlike the retired bulk emitter, it performs no sizing pass.
"""
from __future__ import annotations

from .ir import Node, OneError, Program, Ref
from .wire import MAGIC, MAX_NAME_BYTES, MAX_ROOTS, MAX_U64, TAGS, WireStats


def _append_uvarint(out: bytearray, value: int) -> None:
    if not isinstance(value, int) or value < 0 or value > MAX_U64:
        raise OneError("uvarint requires unsigned 64-bit integer")
    while value >= 0x80:
        out.append((value & 0x7F) | 0x80)
        value >>= 7
    out.append(value)


def _append_blob(out: bytearray, value: bytes) -> None:
    _append_uvarint(out, len(value))
    out.extend(value)


def _append_ref(out: bytearray, ref: Ref) -> None:
    _append_uvarint(out, ref.node)
    _append_uvarint(out, ref.start)
    _append_uvarint(out, 0 if ref.length is None else ref.length + 1)


def _append_node(out: bytearray, node: Node) -> None:
    out.append(TAGS[node.op])
    _append_uvarint(out, 0 if node.declared_length is None else node.declared_length + 1)
    if node.op == "surprise":
        _append_blob(out, node.surprise)
    elif node.op == "concat":
        _append_uvarint(out, len(node.refs))
        for ref in node.refs:
            _append_ref(out, ref)
        _append_blob(out, node.surprise)
    elif node.op == "repeat":
        _append_ref(out, node.refs[0])
        _append_uvarint(out, node.count)
    elif node.op == "fill":
        out.append(node.value)
        _append_uvarint(out, node.count)
    elif node.op in {"xor", "add8"}:
        _append_uvarint(out, len(node.refs))
        for ref in node.refs:
            _append_ref(out, ref)
        _append_blob(out, node.surprise)
    else:
        raise OneError(f"unknown operation {node.op!r}")


def _encode_program_growable_prevalidated(program: Program) -> tuple[bytes, WireStats]:
    out = bytearray(MAGIC)
    for value in (
        program.limits.max_nodes,
        program.limits.max_output_bytes,
        program.limits.max_work_bytes,
        program.limits.max_depth,
        len(program.nodes),
    ):
        _append_uvarint(out, value)
    for node in program.nodes:
        _append_node(out, node)

    roots = sorted(program.roots.items())
    if len(roots) > MAX_ROOTS:
        raise OneError("root count exceeds experimental wire limit")
    _append_uvarint(out, len(roots))
    for name, root in roots:
        name_bytes = name.encode("utf-8")
        if len(name_bytes) > MAX_NAME_BYTES:
            raise OneError("root name exceeds experimental wire limit")
        _append_blob(out, name_bytes)
        _append_ref(out, root.ref)
        _append_uvarint(out, root.length)
        out.extend(bytes.fromhex(root.sha256))

    surprise_bytes = sum(len(node.surprise) for node in program.nodes)
    stats = WireStats(
        total_bytes=len(out),
        surprise_bytes=surprise_bytes,
        control_integrity_bytes=len(out) - surprise_bytes,
    )
    return bytes(out), stats


def encode_program_growable(program: Program) -> tuple[bytes, WireStats]:
    program.validate_shape()
    return _encode_program_growable_prevalidated(program)
