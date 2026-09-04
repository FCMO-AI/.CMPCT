"""Reference evaluator for the ONE-G0.1 reconstruction algebra.

The implementation favors semantic clarity and fail-closed bounds over speed. Optimized
execution may later fuse these operations, but must remain equivalent to this evaluator.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256

from .ir import Node, OneError, Program, Ref


@dataclass(frozen=True)
class EvaluationStats:
    materialized_bytes: int
    work_bytes: int
    max_depth: int
    nodes_evaluated: int


class Evaluator:
    def __init__(self, program: Program):
        program.validate_shape()
        self.program = program
        self._cache: dict[int, bytes] = {}
        self._active: set[int] = set()
        self._work = 0
        self._max_depth = 0

    def _charge(self, amount: int) -> None:
        if amount < 0:
            raise OneError("negative work charge")
        self._work += amount
        if self._work > self.program.limits.max_work_bytes:
            raise OneError("reconstruction work exceeds declared limit")

    def _slice(self, ref: Ref, depth: int) -> bytes:
        value = self._eval_node(ref.node, depth)
        if ref.start > len(value):
            raise OneError("range starts past referenced output")
        end = len(value) if ref.length is None else ref.start + ref.length
        if end < ref.start or end > len(value):
            raise OneError("range exceeds referenced output")
        out = value[ref.start:end]
        self._charge(len(out))
        return out

    def _check_result(self, node: Node, result: bytes) -> bytes:
        if node.declared_length is not None and len(result) != node.declared_length:
            raise OneError("node declared length mismatch")
        if len(result) > self.program.limits.max_output_bytes:
            raise OneError("node output exceeds declared limit")
        return result

    def _equal_parts(self, node: Node, depth: int) -> list[bytes]:
        parts = [self._slice(ref, depth + 1) for ref in node.refs]
        if node.surprise:
            parts.append(node.surprise)
        if not parts:
            raise OneError(f"{node.op} has no operands")
        width = len(parts[0])
        if any(len(part) != width for part in parts[1:]):
            raise OneError(f"{node.op} operands differ in length")
        return parts

    def _eval_node(self, node_id: int, depth: int) -> bytes:
        if node_id in self._cache:
            return self._cache[node_id]
        if depth > self.program.limits.max_depth:
            raise OneError("dependency depth exceeds declared limit")
        self._max_depth = max(self._max_depth, depth)
        if node_id in self._active:
            raise OneError("cycle in reconstruction graph")
        self._active.add(node_id)
        try:
            node = self.program.nodes[node_id]
            if node.op == "surprise":
                result = bytes(node.surprise)
                self._charge(len(result))
            elif node.op == "concat":
                parts = [self._slice(ref, depth + 1) for ref in node.refs]
                if node.surprise:
                    parts.append(node.surprise)
                    self._charge(len(node.surprise))
                total = sum(len(part) for part in parts)
                if total > self.program.limits.max_output_bytes:
                    raise OneError("concat output exceeds declared limit")
                result = b"".join(parts)
                self._charge(total)
            elif node.op == "repeat":
                part = self._slice(node.refs[0], depth + 1)
                total = len(part) * node.count
                if total > self.program.limits.max_output_bytes:
                    raise OneError("repeat output exceeds declared limit")
                result = part * node.count
                self._charge(total)
            elif node.op == "fill":
                if node.count > self.program.limits.max_output_bytes:
                    raise OneError("fill output exceeds declared limit")
                result = bytes([node.value]) * node.count
                self._charge(node.count)
            elif node.op == "xor":
                parts = self._equal_parts(node, depth)
                width = len(parts[0])
                acc = bytearray(width)
                for part in parts:
                    for i, value in enumerate(part):
                        acc[i] ^= value
                result = bytes(acc)
                self._charge(width * len(parts))
            elif node.op == "add8":
                parts = self._equal_parts(node, depth)
                width = len(parts[0])
                # Arithmetic is explicitly modulo 256; there is no platform-dependent overflow.
                result = bytes(sum(part[i] for part in parts) & 0xFF for i in range(width))
                self._charge(width * len(parts))
            else:  # validate_shape should make this unreachable.
                raise OneError(f"unknown operation {node.op!r}")
            result = self._check_result(node, result)
            self._cache[node_id] = result
            return result
        finally:
            self._active.remove(node_id)

    def evaluate(self) -> tuple[dict[str, bytes], EvaluationStats]:
        outputs: dict[str, bytes] = {}
        total_output = 0
        for name, root in self.program.roots.items():
            value = self._slice(root.ref, 1)
            if len(value) != root.length:
                raise OneError(f"root {name!r} length mismatch")
            if sha256(value).hexdigest() != root.sha256:
                raise OneError(f"root {name!r} sha256 mismatch")
            total_output += len(value)
            if total_output > self.program.limits.max_output_bytes:
                raise OneError("root outputs exceed declared limit")
            outputs[name] = value
        return outputs, EvaluationStats(
            materialized_bytes=sum(len(v) for v in self._cache.values()),
            work_bytes=self._work,
            max_depth=self._max_depth,
            nodes_evaluated=len(self._cache),
        )


def evaluate(program: Program) -> tuple[dict[str, bytes], EvaluationStats]:
    return Evaluator(program).evaluate()
