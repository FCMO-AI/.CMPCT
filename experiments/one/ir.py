"""Minimal CMPCT ONE research IR for ONE-G0.1.

This is deliberately a small generic reconstruction algebra, not a registry of codecs.
The reader executes precompiled bounded operations; discovery belongs to the encoder.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Sequence


class OneError(ValueError):
    """Invalid ONE program or resource declaration."""


@dataclass(frozen=True)
class Ref:
    node: int
    start: int = 0
    length: int | None = None


@dataclass(frozen=True)
class Node:
    """One generic reconstruction node.

    Supported operations intentionally describe information relationships rather than
    historical mechanisms:
      surprise: emit explicit bytes
      concat: concatenate referenced ranges
      repeat: repeat one referenced range count times
      fill: emit one byte value count times
      xor: xor equally-sized referenced ranges and optional explicit Surprise bytes
      add8: modular-u8 sum of equally-sized referenced ranges and optional Surprise
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
            if not isinstance(value, int) or value < 0:
                raise OneError(f"invalid limit {name}={value!r}")


@dataclass(frozen=True)
class Program:
    nodes: tuple[Node, ...]
    roots: Mapping[str, Ref]
    limits: Limits = field(default_factory=Limits)

    def validate_shape(self) -> None:
        self.limits.validate()
        if len(self.nodes) > self.limits.max_nodes:
            raise OneError("node count exceeds declared limit")
        if not self.roots:
            raise OneError("program has no roots")
        for name, ref in self.roots.items():
            if not isinstance(name, str) or not name:
                raise OneError("root names must be non-empty strings")
            validate_ref(ref, len(self.nodes))
        for node in self.nodes:
            if node.op not in {"surprise", "concat", "repeat", "fill", "xor", "add8"}:
                raise OneError(f"unknown operation {node.op!r}")
            if node.declared_length is not None and node.declared_length < 0:
                raise OneError("negative declared length")
            if node.op == "surprise" and node.refs:
                raise OneError("surprise node cannot reference other nodes")
            if node.op in {"concat", "xor", "add8"} and not node.refs and not node.surprise:
                raise OneError(f"{node.op} requires input")
            if node.op == "repeat" and (len(node.refs) != 1 or node.count < 0):
                raise OneError("repeat requires one ref and non-negative count")
            if node.op == "fill" and (node.refs or not 0 <= node.value <= 255 or node.count < 0):
                raise OneError("fill requires byte value and non-negative count")
            for ref in node.refs:
                validate_ref(ref, len(self.nodes))


def validate_ref(ref: Ref, node_count: int) -> None:
    if not isinstance(ref.node, int) or not 0 <= ref.node < node_count:
        raise OneError(f"invalid node reference {ref.node!r}")
    if not isinstance(ref.start, int) or ref.start < 0:
        raise OneError("negative/non-integer range start")
    if ref.length is not None and (not isinstance(ref.length, int) or ref.length < 0):
        raise OneError("negative/non-integer range length")
