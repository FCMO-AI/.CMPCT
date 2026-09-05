"""Deterministic experimental ONE-G0.1 wire format.

This is research evidence, not a canonical CMPCT format revision. Its purpose is to make
ONE-01 control/Surprise overhead measurable and to force the Python-object semantics
through a bounded, independently parseable byte representation early.
"""
from __future__ import annotations

from dataclasses import dataclass

from .ir import Limits, Node, OneError, Program, Ref, Root

MAGIC = b"ONE0"
TAGS = {"surprise": 0, "concat": 1, "repeat": 2, "fill": 3, "xor": 4, "add8": 5}
OPS = {value: key for key, value in TAGS.items()}
DEFAULT_DECODE_CAPS = Limits(
    max_nodes=4096,
    max_output_bytes=64 * 1024 * 1024,
    max_work_bytes=256 * 1024 * 1024,
    max_depth=64,
)
MAX_WIRE_BYTES = 128 * 1024 * 1024
MAX_ROOTS = 65536
MAX_NAME_BYTES = 4096
MAX_U64 = (1 << 64) - 1


@dataclass(frozen=True)
class WireStats:
    total_bytes: int
    surprise_bytes: int
    control_integrity_bytes: int


def _uvarint(value: int) -> bytes:
    if not isinstance(value, int) or value < 0 or value > MAX_U64:
        raise OneError("uvarint requires unsigned 64-bit integer")
    out = bytearray()
    while True:
        byte = value & 0x7F
        value >>= 7
        if value:
            out.append(byte | 0x80)
        else:
            out.append(byte)
            return bytes(out)


def _blob(value: bytes) -> bytes:
    return _uvarint(len(value)) + value


def _ref(ref: Ref) -> bytes:
    length_code = 0 if ref.length is None else ref.length + 1
    return _uvarint(ref.node) + _uvarint(ref.start) + _uvarint(length_code)


def _node(node: Node) -> bytes:
    out = bytearray([TAGS[node.op]])
    out += _uvarint(0 if node.declared_length is None else node.declared_length + 1)
    if node.op == "surprise":
        out += _blob(node.surprise)
    elif node.op == "concat":
        out += _uvarint(len(node.refs))
        for ref in node.refs:
            out += _ref(ref)
        out += _blob(node.surprise)
    elif node.op == "repeat":
        out += _ref(node.refs[0])
        out += _uvarint(node.count)
    elif node.op == "fill":
        out.append(node.value)
        out += _uvarint(node.count)
    elif node.op in {"xor", "add8"}:
        out += _uvarint(len(node.refs))
        for ref in node.refs:
            out += _ref(ref)
        out += _blob(node.surprise)
    else:
        raise OneError(f"unknown operation {node.op!r}")
    return bytes(out)


def encode_program(program: Program) -> tuple[bytes, WireStats]:
    program.validate_shape()
    out = bytearray(MAGIC)
    for value in (
        program.limits.max_nodes,
        program.limits.max_output_bytes,
        program.limits.max_work_bytes,
        program.limits.max_depth,
        len(program.nodes),
    ):
        out += _uvarint(value)
    for node in program.nodes:
        out += _node(node)
    roots = sorted(program.roots.items())
    if len(roots) > MAX_ROOTS:
        raise OneError("root count exceeds experimental wire limit")
    out += _uvarint(len(roots))
    for name, root in roots:
        name_bytes = name.encode("utf-8")
        if len(name_bytes) > MAX_NAME_BYTES:
            raise OneError("root name exceeds experimental wire limit")
        out += _blob(name_bytes)
        out += _ref(root.ref)
        out += _uvarint(root.length)
        out += bytes.fromhex(root.sha256)
    surprise_bytes = sum(len(node.surprise) for node in program.nodes)
    stats = WireStats(
        total_bytes=len(out),
        surprise_bytes=surprise_bytes,
        control_integrity_bytes=len(out) - surprise_bytes,
    )
    return bytes(out), stats


class _Reader:
    def __init__(self, data: bytes):
        if len(data) > MAX_WIRE_BYTES:
            raise OneError("ONE wire exceeds hard input cap")
        self.data = memoryview(data)
        self.pos = 0

    def take(self, count: int) -> bytes:
        if count < 0 or self.pos + count > len(self.data):
            raise OneError("truncated ONE wire")
        out = bytes(self.data[self.pos : self.pos + count])
        self.pos += count
        return out

    def byte(self) -> int:
        return self.take(1)[0]

    def uvarint(self) -> int:
        start = self.pos
        value = 0
        shift = 0
        for index in range(10):
            byte = self.byte()
            # A canonical unsigned-64 LEB128 value has at most one payload bit in
            # byte ten. Rejecting larger payloads prevents Python's unbounded ints
            # from becoming an accidental wire capability.
            if index == 9 and (byte & 0x7E):
                raise OneError("uvarint exceeds 64-bit envelope")
            value |= (byte & 0x7F) << shift
            if not byte & 0x80:
                encoded = bytes(self.data[start : self.pos])
                if encoded != _uvarint(value):
                    raise OneError("non-canonical uvarint")
                return value
            shift += 7
        raise OneError("uvarint exceeds 64-bit envelope")

    def blob(self, hard_cap: int) -> bytes:
        size = self.uvarint()
        if size > hard_cap:
            raise OneError("blob exceeds hard cap")
        return self.take(size)

    def ref(self, node_count: int) -> Ref:
        node = self.uvarint()
        start = self.uvarint()
        length_code = self.uvarint()
        ref = Ref(node=node, start=start, length=None if length_code == 0 else length_code - 1)
        if node >= node_count:
            raise OneError("wire reference exceeds node table")
        return ref


def _decode_node(reader: _Reader, node_count: int, caps: Limits) -> Node:
    tag = reader.byte()
    if tag not in OPS:
        raise OneError("unknown ONE wire opcode")
    op = OPS[tag]
    length_code = reader.uvarint()
    declared_length = None if length_code == 0 else length_code - 1
    if declared_length is not None and declared_length > caps.max_output_bytes:
        raise OneError("declared node output exceeds hard cap")
    if op == "surprise":
        return Node(op, surprise=reader.blob(caps.max_output_bytes), declared_length=declared_length)
    if op == "concat":
        count = reader.uvarint()
        if count > caps.max_nodes:
            raise OneError("concat reference count exceeds hard cap")
        refs = tuple(reader.ref(node_count) for _ in range(count))
        surprise = reader.blob(caps.max_output_bytes)
        return Node(op, refs=refs, surprise=surprise, declared_length=declared_length)
    if op == "repeat":
        return Node(op, refs=(reader.ref(node_count),), count=reader.uvarint(), declared_length=declared_length)
    if op == "fill":
        return Node(op, value=reader.byte(), count=reader.uvarint(), declared_length=declared_length)
    count = reader.uvarint()
    if count > caps.max_nodes:
        raise OneError(f"{op} reference count exceeds hard cap")
    refs = tuple(reader.ref(node_count) for _ in range(count))
    surprise = reader.blob(caps.max_output_bytes)
    return Node(op, refs=refs, surprise=surprise, declared_length=declared_length)


def decode_program(data: bytes, *, caps: Limits = DEFAULT_DECODE_CAPS) -> Program:
    caps.validate()
    reader = _Reader(data)
    if reader.take(len(MAGIC)) != MAGIC:
        raise OneError("wrong ONE wire magic")
    encoded_limits = Limits(
        max_nodes=reader.uvarint(),
        max_output_bytes=reader.uvarint(),
        max_work_bytes=reader.uvarint(),
        max_depth=reader.uvarint(),
    )
    encoded_limits.validate()
    for field in ("max_nodes", "max_output_bytes", "max_work_bytes", "max_depth"):
        if getattr(encoded_limits, field) > getattr(caps, field):
            raise OneError(f"encoded {field} exceeds reader cap")
    node_count = reader.uvarint()
    if node_count > encoded_limits.max_nodes:
        raise OneError("node table exceeds declared limit")
    nodes = tuple(_decode_node(reader, node_count, encoded_limits) for _ in range(node_count))
    root_count = reader.uvarint()
    if root_count == 0 or root_count > MAX_ROOTS:
        raise OneError("invalid root count")
    roots: dict[str, Root] = {}
    previous_name: str | None = None
    for _ in range(root_count):
        raw_name = reader.blob(MAX_NAME_BYTES)
        try:
            name = raw_name.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise OneError("root name is not valid UTF-8") from exc
        if not name or name in roots:
            raise OneError("empty/duplicate root name")
        if previous_name is not None and name <= previous_name:
            raise OneError("roots are not in canonical order")
        previous_name = name
        ref = reader.ref(node_count)
        length = reader.uvarint()
        if length > encoded_limits.max_output_bytes:
            raise OneError("root length exceeds declared limit")
        roots[name] = Root(ref=ref, length=length, sha256=reader.take(32).hex())
    if reader.pos != len(reader.data):
        raise OneError("trailing bytes after ONE program")
    program = Program(nodes=nodes, roots=roots, limits=encoded_limits)
    program.validate_shape()
    # Canonicalization is part of the experimental wire contract: exactly one byte
    # encoding exists for one in-memory semantic program.
    encoded, _ = encode_program(program)
    if encoded != data:
        raise OneError("non-canonical ONE wire")
    return program
