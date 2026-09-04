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
    preflight_worst_work_bytes: int


@dataclass(frozen=True)
class _Preflight:
    lengths: tuple[int, ...]
    max_depth: int
    worst_work_bytes: int


def _preflight(program: Program) -> _Preflight:
    """Prove graph/range/output/work bounds before materializing any reconstructed byte.

    ONE-G0.1's six operations all have statically inferable output lengths. That lets the
    reader reject cycles, deep graphs, range bombs, unequal vector operands, impossible
    declared lengths and over-budget worst-case work before execution. Every stored node
    is included even if no current root reaches it, so validity cannot depend on cache or
    root order.
    """
    lengths: dict[int, int] = {}
    depths: dict[int, int] = {}
    local_work: dict[int, int] = {}
    active: set[int] = set()

    def visit(node_id: int) -> tuple[int, int]:
        if node_id in lengths:
            return lengths[node_id], depths[node_id]
        if node_id in active:
            raise OneError("cycle in reconstruction graph")
        active.add(node_id)
        try:
            node = program.nodes[node_id]
            for ref in node.refs:
                visit(ref.node)
            depth = 1 if not node.refs else 1 + max(depths[ref.node] for ref in node.refs)
            if depth > program.limits.max_depth:
                raise OneError("dependency depth exceeds declared limit")

            def slice_len(ref: Ref) -> int:
                source_len = lengths[ref.node]
                if ref.start > source_len:
                    raise OneError("range starts past referenced output")
                end = source_len if ref.length is None else ref.start + ref.length
                if end < ref.start or end > source_len:
                    raise OneError("range exceeds referenced output")
                return end - ref.start

            if node.op == "surprise":
                length = len(node.surprise)
                work = length
            elif node.op == "fill":
                length = node.count
                work = length
            elif node.op == "repeat":
                source = slice_len(node.refs[0])
                length = source * node.count
                work = source + length
            elif node.op == "concat":
                ref_bytes = sum(slice_len(ref) for ref in node.refs)
                length = ref_bytes + len(node.surprise)
                # Read every input byte once and write every output byte once.
                work = ref_bytes + len(node.surprise) + length
            elif node.op in {"xor", "add8"}:
                part_lengths = [slice_len(ref) for ref in node.refs]
                if node.surprise:
                    part_lengths.append(len(node.surprise))
                if not part_lengths or any(size != part_lengths[0] for size in part_lengths[1:]):
                    raise OneError(f"{node.op} operands differ in length")
                length = part_lengths[0]
                # One read pass over each operand plus one byte-operation pass per
                # operand. This is conservative for later fused native kernels.
                work = sum(part_lengths) + length * len(part_lengths)
            else:
                raise OneError(f"unknown operation {node.op!r}")

            if node.declared_length is not None and length != node.declared_length:
                raise OneError("node declared length mismatch")
            if length > program.limits.max_output_bytes:
                raise OneError(f"{node.op} output exceeds declared limit")
            lengths[node_id] = length
            depths[node_id] = depth
            local_work[node_id] = work
            return length, depth
        finally:
            active.remove(node_id)

    for node_id in range(len(program.nodes)):
        visit(node_id)

    root_bytes = 0
    for root in program.roots.values():
        source_len = lengths[root.ref.node]
        if root.ref.start > source_len:
            raise OneError("range starts past referenced output")
        end = source_len if root.ref.length is None else root.ref.start + root.ref.length
        if end < root.ref.start or end > source_len:
            raise OneError("range exceeds referenced output")
        length = end - root.ref.start
        if length != root.length:
            raise OneError("root declared length mismatch")
        root_bytes += length
    if root_bytes > program.limits.max_output_bytes:
        raise OneError("root outputs exceed declared limit")

    # Worst case includes every stored node, every root-range read, and one complete
    # SHA-256 scan per root. Runtime caching may do less work but may never exceed this.
    worst_work = sum(local_work.values()) + 2 * root_bytes
    if worst_work > program.limits.max_work_bytes:
        raise OneError("preflight reconstruction work exceeds declared limit")
    return _Preflight(
        lengths=tuple(lengths[node_id] for node_id in range(len(program.nodes))),
        max_depth=max(depths.values(), default=0),
        worst_work_bytes=worst_work,
    )


class Evaluator:
    def __init__(self, program: Program):
        program.validate_shape()
        self.program = program
        self._preflight = _preflight(program)
        self._cache: dict[int, bytes] = {}
        self._active: set[int] = set()
        self._work = 0

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

    def _check_result(self, node_id: int, result: bytes) -> bytes:
        if len(result) != self._preflight.lengths[node_id]:
            raise OneError("runtime output disagrees with preflight length")
        return result

    def _equal_parts(self, node: Node, depth: int) -> list[bytes]:
        parts = [self._slice(ref, depth + 1) for ref in node.refs]
        if node.surprise:
            parts.append(node.surprise)
            self._charge(len(node.surprise))
        if not parts:
            raise OneError(f"{node.op} has no operands")
        width = len(parts[0])
        if any(len(part) != width for part in parts[1:]):
            raise OneError(f"{node.op} operands differ in length")
        return parts

    def _eval_node(self, node_id: int, depth: int) -> bytes:
        # Static preflight makes this check independent of cache order; retaining the
        # runtime check is defense-in-depth for future evaluator changes.
        if depth > self.program.limits.max_depth:
            raise OneError("dependency depth exceeds declared limit")
        if node_id in self._cache:
            return self._cache[node_id]
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
                result = b"".join(parts)
                self._charge(len(result))
            elif node.op == "repeat":
                part = self._slice(node.refs[0], depth + 1)
                result = part * node.count
                self._charge(len(result))
            elif node.op == "fill":
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
            result = self._check_result(node_id, result)
            self._cache[node_id] = result
            return result
        finally:
            self._active.remove(node_id)

    def evaluate(self) -> tuple[dict[str, bytes], EvaluationStats]:
        outputs: dict[str, bytes] = {}
        for name, root in self.program.roots.items():
            value = self._slice(root.ref, 1)
            # Root length/range shape was proven before execution; retain a runtime
            # assertion so future fused evaluators cannot silently diverge.
            if len(value) != root.length:
                raise OneError(f"root {name!r} length mismatch")
            self._charge(len(value))  # SHA-256 must scan the complete authenticated root.
            if sha256(value).hexdigest() != root.sha256:
                raise OneError(f"root {name!r} sha256 mismatch")
            outputs[name] = value
        if self._work > self._preflight.worst_work_bytes:
            raise OneError("runtime work exceeded preflight upper bound")
        return outputs, EvaluationStats(
            materialized_bytes=sum(len(v) for v in self._cache.values()),
            work_bytes=self._work,
            max_depth=self._preflight.max_depth,
            nodes_evaluated=len(self._cache),
            preflight_worst_work_bytes=self._preflight.worst_work_bytes,
        )


def evaluate(program: Program) -> tuple[dict[str, bytes], EvaluationStats]:
    return Evaluator(program).evaluate()
