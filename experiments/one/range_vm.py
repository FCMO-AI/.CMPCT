"""Generic cone-only range reconstruction for experimental ONE programs.

This module intentionally does *not* claim authenticated selective reads.  The canonical
research IR currently authenticates each root with one whole-root SHA-256, so reconstructing
only a range cannot verify that root digest without reading the rest of the root.  Keeping
that limitation explicit prevents an optimization experiment from quietly borrowing
integrity debt.

The evaluator is nevertheless useful to isolate reconstruction-cone cost from wire/index
and authentication cost.  It supports the same six generic Law operations as the reference
VM and performs no discovery.
"""
from __future__ import annotations

from dataclasses import dataclass

from .ir import Node, OneError, Program, Ref
from .vm import _preflight


@dataclass(frozen=True)
class RangeEvaluationStats:
    requested_bytes: int
    materialized_bytes: int
    work_bytes: int
    nodes_touched: int
    max_depth: int
    authenticated: bool = False


class RangeEvaluator:
    """Reconstruct only a requested interval of one root.

    Shape, graph, range and declared resource limits are proven by the same static
    preflight used by the full reference evaluator. Runtime work is additionally bounded
    by ``max_work_bytes``. Root authentication is deliberately not asserted: with the
    current single SHA-256 root digest, doing so would require a whole-root scan.

    Nested ``concat`` nodes are executed as one associative reconstruction cone. Their
    stored hierarchy still counts for validation and depth, but a concat whose output is
    consumed directly by another concat is not separately materialized. This preserves
    hard fanout bounds without charging a synthetic intermediate-copy tax.
    """

    def __init__(self, program: Program):
        program.validate_shape()
        self.program = program
        self._preflight = _preflight(program)
        self._work = 0
        self._materialized = 0
        self._touched: set[int] = set()
        self._active: set[tuple[int, int, int]] = set()
        self._max_depth_seen = 0

    def _charge(self, work: int = 0, materialized: int = 0) -> None:
        if work < 0 or materialized < 0:
            raise OneError("negative range-evaluation accounting")
        self._work += work
        self._materialized += materialized
        if self._work > self.program.limits.max_work_bytes:
            raise OneError("range reconstruction work exceeds declared limit")

    def _ref_length(self, ref: Ref) -> int:
        source_len = self._preflight.lengths[ref.node]
        end = source_len if ref.length is None else ref.start + ref.length
        if ref.start > source_len or end < ref.start or end > source_len:
            raise OneError("range exceeds referenced output")
        return end - ref.start

    def _slice_ref(self, ref: Ref, start: int, length: int, depth: int, *, materialize_concat: bool = True) -> bytes:
        width = self._ref_length(ref)
        if start < 0 or length < 0 or start + length > width:
            raise OneError("requested subrange exceeds reference")
        return self._eval_node(
            ref.node,
            ref.start + start,
            length,
            depth,
            materialize_concat=materialize_concat,
        )

    @staticmethod
    def _overlap(start: int, length: int, part_start: int, part_len: int) -> tuple[int, int] | None:
        end = start + length
        part_end = part_start + part_len
        lo = max(start, part_start)
        hi = min(end, part_end)
        if hi <= lo:
            return None
        return lo - part_start, hi - lo

    def _eval_concat(self, node: Node, start: int, length: int, depth: int, *, materialize_output: bool) -> bytes:
        pieces: list[bytes] = []
        cursor = 0
        for ref in node.refs:
            part_len = self._ref_length(ref)
            overlap = self._overlap(start, length, cursor, part_len)
            if overlap is not None:
                rel, take = overlap
                # Concat is associative. If the referenced node is another concat, traverse
                # through it without materializing the intermediate output. Non-concat Laws
                # retain their ordinary accounting because their operation is real work.
                child_is_concat = self.program.nodes[ref.node].op == "concat"
                pieces.append(
                    self._slice_ref(
                        ref,
                        rel,
                        take,
                        depth + 1,
                        materialize_concat=not child_is_concat,
                    )
                )
            cursor += part_len
        if node.surprise:
            overlap = self._overlap(start, length, cursor, len(node.surprise))
            if overlap is not None:
                rel, take = overlap
                part = node.surprise[rel : rel + take]
                self._charge(work=take, materialized=take)
                pieces.append(part)
        result = b"".join(pieces)
        if len(result) != length:
            raise OneError("range concat coverage mismatch")
        if materialize_output:
            self._charge(work=length, materialized=length)
        return result

    def _eval_repeat(self, node: Node, start: int, length: int, depth: int) -> bytes:
        source_len = self._ref_length(node.refs[0])
        if length == 0:
            return b""
        if source_len == 0:
            raise OneError("non-empty range requested from empty repeat source")
        pieces: list[bytes] = []
        pos = start
        remaining = length
        while remaining:
            rel = pos % source_len
            take = min(remaining, source_len - rel)
            pieces.append(self._slice_ref(node.refs[0], rel, take, depth + 1))
            pos += take
            remaining -= take
        result = b"".join(pieces)
        self._charge(work=length, materialized=length)
        return result

    def _eval_equal(self, node: Node, start: int, length: int, depth: int) -> bytes:
        parts = [self._slice_ref(ref, start, length, depth + 1) for ref in node.refs]
        if node.surprise:
            part = node.surprise[start : start + length]
            if len(part) != length:
                raise OneError(f"{node.op} Surprise range mismatch")
            self._charge(work=length, materialized=length)
            parts.append(part)
        if not parts:
            raise OneError(f"{node.op} has no operands")
        if any(len(part) != length for part in parts):
            raise OneError(f"{node.op} range operand mismatch")
        if node.op == "xor":
            acc = bytearray(length)
            for part in parts:
                for i, value in enumerate(part):
                    acc[i] ^= value
            result = bytes(acc)
        else:
            result = bytes(sum(part[i] for part in parts) & 0xFF for i in range(length))
        self._charge(work=length * len(parts), materialized=length)
        return result

    def _eval_node(
        self,
        node_id: int,
        start: int,
        length: int,
        depth: int,
        *,
        materialize_concat: bool = True,
    ) -> bytes:
        if depth > self.program.limits.max_depth:
            raise OneError("dependency depth exceeds declared limit")
        node_len = self._preflight.lengths[node_id]
        if start < 0 or length < 0 or start + length > node_len:
            raise OneError("requested range exceeds node output")
        if length == 0:
            return b""
        key = (node_id, start, length)
        if key in self._active:
            raise OneError("cycle in range reconstruction graph")
        self._active.add(key)
        self._touched.add(node_id)
        self._max_depth_seen = max(self._max_depth_seen, depth)
        try:
            node = self.program.nodes[node_id]
            if node.op == "surprise":
                result = node.surprise[start : start + length]
                self._charge(work=length, materialized=length)
            elif node.op == "fill":
                result = bytes([node.value]) * length
                self._charge(work=length, materialized=length)
            elif node.op == "concat":
                result = self._eval_concat(
                    node,
                    start,
                    length,
                    depth,
                    materialize_output=materialize_concat,
                )
            elif node.op == "repeat":
                result = self._eval_repeat(node, start, length, depth)
            elif node.op in {"xor", "add8"}:
                result = self._eval_equal(node, start, length, depth)
            else:
                raise OneError(f"unknown operation {node.op!r}")
            if len(result) != length:
                raise OneError("range evaluator produced wrong length")
            return result
        finally:
            self._active.remove(key)

    def reconstruct(self, root_name: str, start: int, length: int) -> tuple[bytes, RangeEvaluationStats]:
        if root_name not in self.program.roots:
            raise OneError(f"unknown root {root_name!r}")
        root = self.program.roots[root_name]
        if type(start) is not int or type(length) is not int or start < 0 or length < 0:
            raise OneError("range start/length must be non-negative integers")
        if start + length > root.length:
            raise OneError("requested range exceeds root")
        value = self._slice_ref(root.ref, start, length, 1)
        if len(value) != length:
            raise OneError("root range length mismatch")
        return value, RangeEvaluationStats(
            requested_bytes=length,
            materialized_bytes=self._materialized,
            work_bytes=self._work,
            nodes_touched=len(self._touched),
            max_depth=self._max_depth_seen,
            authenticated=False,
        )


def reconstruct_range_unverified(program: Program, root_name: str, start: int, length: int) -> tuple[bytes, RangeEvaluationStats]:
    """Return an exact but *unauthenticated* root slice and measured cone cost."""
    return RangeEvaluator(program).reconstruct(root_name, start, length)
