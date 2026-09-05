"""Minimal CMPCT ONE research IR for ONE-G0.1.

This is deliberately a small generic reconstruction algebra, not a registry of codecs.
The reader executes precompiled bounded operations; discovery belongs to the encoder.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping


class OneError(ValueError):
    """Invalid ONE program or resource declaration."""


def _is_uint(value: object) -> bool:
    # bool is intentionally not an integer in the ONE grammar even though Python makes
    # it an int subclass; semantic inputs should have one unambiguous type.
    return type(value) is int and value >= 0


@dataclass(frozen=True)
class Ref:
    node: int
    start: int = 0
    length: int | None = None


@dataclass(frozen=True)
class Root:
    ref: Ref
    length: int
    sha256: str


@dataclass(frozen=True)
class Node:
    """One generic reconstruction node.

    Operations describe information relationships rather than historical codecs:
      surprise: emit explicit bytes
      concat: concatenate referenced ranges and optional explicit Surprise
      repeat: repeat one referenced range count times
      fill: emit one byte value count times
      xor: xor equal-size referenced ranges and optional explicit Surprise bytes
      add8: modular-u8 sum of equal-size referenced ranges and optional Surprise
    """

    op: str
    refs: tuple[Ref, ...] = ()
    surprise: bytes = b""
    count: int = 0
    value: int = 0
    declared_length: int | None = None


@dataclass(frozen=True)
class Limits:
    max_nodes: int = 4096
    max_output_bytes: int = 64 * 1024 * 1024
    max_work_bytes: int = 256 * 1024 * 1024
    max_depth: int = 64

    def validate(self) -> None:
        for name, value in vars(self).items():
            if not _is_uint(value):
                raise OneError(f"invalid limit {name}={value!r}")


@dataclass(frozen=True)
class Program:
    nodes: tuple[Node, ...]
    roots: Mapping[str, Root]
    limits: Limits = field(default_factory=Limits)

    def validate_shape(self) -> None:
        if not isinstance(self.limits, Limits):
            raise OneError("program limits must be Limits")
        self.limits.validate()
        if not isinstance(self.nodes, tuple):
            raise OneError("program nodes must be a tuple")
        if len(self.nodes) > self.limits.max_nodes:
            raise OneError("node count exceeds declared limit")
        if not isinstance(self.roots, Mapping) or not self.roots:
            raise OneError("program roots must be a non-empty mapping")
        for name, root in self.roots.items():
            if not isinstance(name, str) or not name:
                raise OneError("root names must be non-empty strings")
            if not isinstance(root, Root):
                raise OneError("root entries must be Root values")
            validate_ref(root.ref, len(self.nodes))
            if not _is_uint(root.length):
                raise OneError("root length must be non-negative integer")
            if not isinstance(root.sha256, str) or len(root.sha256) != 64:
                raise OneError("root sha256 must be exactly 64 hex characters")
            try:
                digest = bytes.fromhex(root.sha256)
            except ValueError as exc:
                raise OneError("root sha256 is not hexadecimal") from exc
            if len(digest) != 32:
                # bytes.fromhex ignores ASCII whitespace, so length-of-text alone is
                # not a sufficient digest-shape check.
                raise OneError("root sha256 must decode to exactly 32 bytes")
        for node in self.nodes:
            if not isinstance(node, Node):
                raise OneError("node table contains non-Node value")
            if not isinstance(node.op, str) or node.op not in {"surprise", "concat", "repeat", "fill", "xor", "add8"}:
                raise OneError(f"unknown operation {node.op!r}")
            if not isinstance(node.refs, tuple) or any(not isinstance(ref, Ref) for ref in node.refs):
                raise OneError("node refs must be a tuple of Ref values")
            if not isinstance(node.surprise, bytes):
                raise OneError("node Surprise must be bytes")
            if not _is_uint(node.count) or not _is_uint(node.value):
                raise OneError("node count/value must be non-negative integers")
            if node.declared_length is not None and not _is_uint(node.declared_length):
                raise OneError("declared length must be non-negative integer or None")
            if node.op == "surprise":
                if node.refs or node.count or node.value:
                    raise OneError("surprise node has semantically dead fields")
            elif node.op == "concat":
                if node.count or node.value:
                    raise OneError("concat node has semantically dead fields")
                if not node.refs and not node.surprise:
                    raise OneError("concat requires input")
            elif node.op in {"xor", "add8"}:
                if node.count or node.value:
                    raise OneError(f"{node.op} node has semantically dead fields")
                if not node.refs and not node.surprise:
                    raise OneError(f"{node.op} requires input")
            elif node.op == "repeat":
                if len(node.refs) != 1:
                    raise OneError("repeat requires exactly one ref")
                if node.surprise or node.value:
                    raise OneError("repeat node has semantically dead fields")
            elif node.op == "fill":
                if node.refs or node.surprise or node.value > 255:
                    raise OneError("fill requires only a byte value and non-negative count")
            for ref in node.refs:
                validate_ref(ref, len(self.nodes))


def validate_ref(ref: Ref, node_count: int) -> None:
    if not isinstance(ref, Ref):
        raise OneError("reference must be Ref")
    if not _is_uint(ref.node) or ref.node >= node_count:
        raise OneError(f"invalid node reference {ref.node!r}")
    if not _is_uint(ref.start):
        raise OneError("range start must be non-negative integer")
    if ref.length is not None and not _is_uint(ref.length):
        raise OneError("range length must be non-negative integer or None")
