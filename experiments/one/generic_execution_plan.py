"""ONE-G0.2 generic prepared execution-plan experiment.

This module lowers the existing six-op ONE IR into a deterministic topological replay
plan. It does not add reader-visible operations or discovery. The purpose is to separate
one-time graph validation/range resolution from repeated execution across *multiple* Law
shapes, so terminal-only fast paths cannot masquerade as a general reader architecture.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256

from experiments.one.ir import OneError, Program
from experiments.one.vm import _preflight


@dataclass(frozen=True)
class PlanRef:
    node: int
    start: int
    length: int


@dataclass(frozen=True)
class PlanOp:
    node: int
    op: str
    length: int
    refs: tuple[PlanRef, ...]
    surprise: bytes
    count: int
    value: int


@dataclass(frozen=True)
class PlanRoot:
    name: str
    node: int
    start: int
    length: int
    sha256_hex: str


@dataclass(frozen=True)
class GenericExecutionPlan:
    ops: tuple[PlanOp, ...]
    roots: tuple[PlanRoot, ...]
    max_work_bytes: int
    preflight_worst_work_bytes: int


@dataclass(frozen=True)
class PlanStats:
    materialized_bytes: int
    work_bytes: int
    nodes_executed: int
    roots_verified: int


def compile_execution_plan(program: Program) -> GenericExecutionPlan:
    """Validate once and lower the generic ONE graph to dependency order.

    `_preflight` validates *all* stored nodes, including unreachable ones, preserving the
    reference validity contract. The executable plan itself contains only nodes reachable
    from current roots, matching the reference evaluator's execution/work semantics.
    """
    program.validate_shape()
    pf = _preflight(program)

    order: list[int] = []
    seen: set[int] = set()

    def visit(node_id: int) -> None:
        if node_id in seen:
            return
        for ref in program.nodes[node_id].refs:
            visit(ref.node)
        seen.add(node_id)
        order.append(node_id)

    for root in program.roots.values():
        visit(root.ref.node)

    ops: list[PlanOp] = []
    for node_id in order:
        node = program.nodes[node_id]
        refs: list[PlanRef] = []
        for ref in node.refs:
            source_len = pf.lengths[ref.node]
            end = source_len if ref.length is None else ref.start + ref.length
            if ref.start > source_len or end < ref.start or end > source_len:
                raise OneError("execution-plan range disagrees with preflight")
            refs.append(PlanRef(ref.node, ref.start, end - ref.start))
        ops.append(PlanOp(node_id, node.op, pf.lengths[node_id], tuple(refs), node.surprise, node.count, node.value))

    roots: list[PlanRoot] = []
    for name, root in program.roots.items():
        source_len = pf.lengths[root.ref.node]
        end = source_len if root.ref.length is None else root.ref.start + root.ref.length
        roots.append(PlanRoot(name, root.ref.node, root.ref.start, end - root.ref.start, root.sha256))

    return GenericExecutionPlan(tuple(ops), tuple(roots), program.limits.max_work_bytes, pf.worst_work_bytes)


def execute_plan(plan: GenericExecutionPlan) -> tuple[dict[str, bytes], PlanStats]:
    """Replay a compiled generic plan with semantics equivalent to the reference VM."""
    values: dict[int, bytes] = {}
    work = 0

    def charge(amount: int) -> None:
        nonlocal work
        if amount < 0:
            raise OneError("negative execution-plan work charge")
        work += amount
        if work > plan.max_work_bytes:
            raise OneError("execution-plan work exceeds declared limit")

    def part(ref: PlanRef) -> bytes:
        source = values[ref.node]
        out = source[ref.start : ref.start + ref.length]
        if len(out) != ref.length:
            raise OneError("execution-plan range mismatch")
        charge(len(out))
        return out

    for item in plan.ops:
        if item.op == "surprise":
            result = bytes(item.surprise)
            charge(len(result))
        elif item.op == "fill":
            result = bytes([item.value]) * item.count
            charge(item.count)
        elif item.op == "concat":
            pieces = [part(ref) for ref in item.refs]
            if item.surprise:
                pieces.append(item.surprise)
                charge(len(item.surprise))
            result = b"".join(pieces)
            charge(len(result))
        elif item.op == "repeat":
            source = part(item.refs[0])
            result = source * item.count
            charge(len(result))
        elif item.op in {"xor", "add8"}:
            pieces = [part(ref) for ref in item.refs]
            if item.surprise:
                pieces.append(item.surprise)
                charge(len(item.surprise))
            if not pieces:
                raise OneError(f"{item.op} has no operands")
            width = len(pieces[0])
            if any(len(piece) != width for piece in pieces[1:]):
                raise OneError(f"{item.op} operands differ in length")
            if item.op == "xor":
                acc = bytearray(width)
                for piece in pieces:
                    for i, value in enumerate(piece):
                        acc[i] ^= value
                result = bytes(acc)
            else:
                result = bytes(sum(piece[i] for piece in pieces) & 0xFF for i in range(width))
            charge(width * len(pieces))
        else:
            raise OneError(f"unknown planned operation {item.op!r}")

        if len(result) != item.length:
            raise OneError("execution-plan output length disagrees with preflight")
        values[item.node] = result

    outputs: dict[str, bytes] = {}
    for root in plan.roots:
        source = values[root.node]
        value = source[root.start : root.start + root.length]
        if len(value) != root.length:
            raise OneError(f"root {root.name!r} length mismatch")
        charge(len(value))
        charge(len(value))
        if sha256(value).hexdigest() != root.sha256_hex:
            raise OneError(f"root {root.name!r} sha256 mismatch")
        outputs[root.name] = value

    if work > plan.preflight_worst_work_bytes:
        raise OneError("execution-plan runtime work exceeded preflight upper bound")
    return outputs, PlanStats(sum(len(value) for value in values.values()), work, len(values), len(outputs))
