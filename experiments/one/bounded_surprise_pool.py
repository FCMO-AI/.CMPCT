"""Bounded output-local Surprise pooling for ONE-G0.2 research Programs.

This module changes only Program graph granularity.  It does not add a reader opcode:
explicit bytes remain ``surprise`` nodes, temporal reuse remains ranged ``Ref`` values,
and composition remains ``concat``.

The grouping span is derived from declared resource bounds.  In the worst case each
output-local group needs two nodes (one Surprise pool plus one concat), while the Program
also needs the previous/source node and a final current-root concat.  Choosing a fixed
span from ``max_output_bytes / max_groups`` therefore keeps every legal output inside the
existing hard node budget without workload-specific tuning.

A second bound matters on the wire: one concat cannot carry more references than the
reader's declared node cap.  Extremely fine fragmentation can satisfy the node-count
geometry while still overflowing that per-node reference envelope.  Such a group is
selectively Crystallized into explicit Surprise instead of manufacturing an unbounded
control vector.  This is the ONE Law/Surprise fallback, not a new reader mechanism.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Iterable, Sequence

from .ir import Limits, Node, OneError, Program, Ref, Root

PlanPiece = tuple[str, int, int, bytes]


@dataclass(frozen=True)
class SurprisePoolStats:
    groups: int
    max_groups: int
    group_span_bytes: int
    surprise_pool_nodes: int
    group_concat_nodes: int
    max_surprise_pool_bytes: int
    total_surprise_payload_bytes: int
    hierarchy_depth: int
    crystallized_groups: int
    crystallized_bytes: int
    max_group_refs: int


@dataclass(frozen=True)
class SurprisePoolGeometry:
    max_groups: int
    group_span_bytes: int
    groups_for_target: int
    worst_case_nodes_for_target: int


def _ceil_div(value: int, divisor: int) -> int:
    return (value + divisor - 1) // divisor


def pool_geometry(limits: Limits, target_length: int) -> SurprisePoolGeometry:
    """Return the resource-derived grouping geometry without examining corpus bytes."""
    limits.validate()
    if type(target_length) is not int or target_length <= 0:
        raise OneError("bounded Surprise pooling target length must be positive")
    if target_length > limits.max_output_bytes:
        raise OneError("target exceeds declared output limit")
    if limits.max_nodes < 4:
        raise OneError("node limit too small for bounded Surprise pooling")

    max_groups = (limits.max_nodes - 2) // 2
    if max_groups < 1:
        raise OneError("node limit leaves no bounded Surprise groups")
    group_span = max(1, _ceil_div(limits.max_output_bytes, max_groups))
    groups_for_target = _ceil_div(target_length, group_span)
    # Pessimistic graph: source + (Surprise pool + group concat) per group + final concat.
    # One-group outputs normally omit the final concat, so this intentionally overcharges.
    worst_case_nodes = 1 + 2 * groups_for_target + 1
    if groups_for_target > max_groups or worst_case_nodes > limits.max_nodes:
        raise OneError("declared resource bounds cannot contain pooled Program geometry")
    return SurprisePoolGeometry(
        max_groups=max_groups,
        group_span_bytes=group_span,
        groups_for_target=groups_for_target,
        worst_case_nodes_for_target=worst_case_nodes,
    )


def _validate_piece(piece: PlanPiece) -> None:
    kind, offset, length, payload = piece
    if kind not in {"ref", "surprise"}:
        raise OneError(f"unknown pooled plan piece {kind!r}")
    if type(offset) is not int or offset < 0 or type(length) is not int or length < 0:
        raise OneError("pooled plan offset/length must be non-negative integers")
    if not isinstance(payload, bytes):
        raise OneError("pooled plan payload must be bytes")
    if kind == "ref" and payload:
        raise OneError("ref plan piece must not carry Surprise")
    if kind == "surprise" and len(payload) != length:
        raise OneError("surprise plan payload length mismatch")


def _split_plan(plan: Sequence[PlanPiece], *, target_length: int, group_span: int) -> tuple[tuple[PlanPiece, ...], ...]:
    if target_length <= 0:
        raise OneError("bounded Surprise pooling currently requires a non-empty target")
    if group_span <= 0:
        raise OneError("bounded Surprise pooling group span must be positive")

    groups: list[tuple[PlanPiece, ...]] = []
    current: list[PlanPiece] = []
    current_bytes = 0
    total = 0

    def flush() -> None:
        nonlocal current, current_bytes
        if current:
            groups.append(tuple(current))
            current = []
            current_bytes = 0

    for original in plan:
        _validate_piece(original)
        kind, offset, length, payload = original
        if length == 0:
            continue
        remaining = length
        source_offset = offset
        payload_offset = 0
        while remaining:
            if current_bytes == group_span:
                flush()
            room = group_span - current_bytes
            take = min(remaining, room)
            if kind == "ref":
                piece: PlanPiece = ("ref", source_offset, take, b"")
                source_offset += take
            else:
                part = payload[payload_offset : payload_offset + take]
                piece = ("surprise", 0, take, part)
                payload_offset += take
            current.append(piece)
            current_bytes += take
            total += take
            remaining -= take
            if current_bytes == group_span:
                flush()
    flush()

    if total != target_length:
        raise OneError(f"pooled plan covers {total} bytes, expected {target_length}")
    return tuple(groups)


def program_from_plan_pooled(
    source: bytes,
    target: bytes,
    plan: Iterable[PlanPiece],
    previous_root: Root,
    current_digest: str | None = None,
    *,
    limits: Limits | None = None,
) -> tuple[Program, SurprisePoolStats]:
    """Compile an already-discovered plan into the generic ONE grammar under hard caps.

    Surprise pieces are pooled only inside contiguous output-local groups.  Ranged refs
    recover their original positions, so no reader discovery or temporal-specific opcode
    is introduced.  If a group's discovered fragmentation would exceed the canonical
    wire's per-node reference envelope, that group is selectively Crystallized instead.
    """
    if not isinstance(source, bytes) or not isinstance(target, bytes):
        raise OneError("pooled Program source/target must be bytes")
    limits = Limits() if limits is None else limits
    geometry = pool_geometry(limits, len(target))
    frozen_plan = tuple(plan)
    groups = _split_plan(
        frozen_plan,
        target_length=len(target),
        group_span=geometry.group_span_bytes,
    )
    if len(groups) > geometry.max_groups or len(groups) != geometry.groups_for_target:
        raise OneError("bounded Surprise grouping violated resource-derived geometry")

    nodes: list[Node] = [Node("surprise", surprise=source)]
    level: list[tuple[Ref, int]] = []
    pool_nodes = 0
    concat_nodes = 0
    max_pool_bytes = 0
    total_surprise = 0
    any_group_concat = False
    crystallized_groups = 0
    crystallized_bytes = 0
    max_group_refs = 0
    target_cursor = 0

    for group in groups:
        group_length = sum(length for _kind, _offset, length, _payload in group)
        if group_length <= 0:
            raise OneError("bounded Surprise group is empty")
        group_end = target_cursor + group_length
        if group_end > len(target):
            raise OneError("bounded Surprise group exceeds target root")
        max_group_refs = max(max_group_refs, len(group))

        # The experimental wire rejects concat/xor/add8 nodes whose reference count is
        # above the declared max_nodes cap.  Node-count pooling alone is therefore not a
        # complete resource proof.  When discovery fragments one output-local group more
        # finely than the reader can safely represent, crystallize that group instead of
        # emitting an oversized control vector.
        if len(group) > limits.max_nodes:
            crystallized = target[target_cursor:group_end]
            node_id = len(nodes)
            nodes.append(Node("surprise", surprise=crystallized))
            level.append((Ref(node_id), group_length))
            crystallized_groups += 1
            crystallized_bytes += group_length
            total_surprise += group_length
            target_cursor = group_end
            continue

        pool = b"".join(payload for kind, _offset, _length, payload in group if kind == "surprise")
        pool_id: int | None = None
        if pool:
            pool_id = len(nodes)
            nodes.append(Node("surprise", surprise=pool))
            pool_nodes += 1
            max_pool_bytes = max(max_pool_bytes, len(pool))
            total_surprise += len(pool)

        pool_offset = 0
        refs: list[Ref] = []
        for kind, offset, length, payload in group:
            if kind == "ref":
                if offset + length > len(source):
                    raise OneError("pooled plan ref exceeds source root")
                refs.append(Ref(0, offset, length))
            else:
                assert pool_id is not None
                refs.append(Ref(pool_id, pool_offset, length))
                pool_offset += length
        if pool_offset != len(pool):
            raise OneError("pooled Surprise cursor mismatch")
        if not refs:
            raise OneError("bounded Surprise group is empty")

        if len(refs) == 1:
            level.append((refs[0], group_length))
        else:
            node_id = len(nodes)
            nodes.append(Node("concat", refs=tuple(refs), declared_length=group_length))
            concat_nodes += 1
            any_group_concat = True
            level.append((Ref(node_id), group_length))
        target_cursor = group_end

    if target_cursor != len(target):
        raise OneError("bounded Surprise groups do not cover target root")
    if not level:
        raise OneError("bounded Surprise plan produced no current-root pieces")
    if len(level) == 1:
        current_ref = level[0][0]
        hierarchy_depth = 1 if not any_group_concat else 2
    else:
        current_node = len(nodes)
        nodes.append(Node("concat", refs=tuple(ref for ref, _length in level), declared_length=len(target)))
        concat_nodes += 1
        current_ref = Ref(current_node)
        hierarchy_depth = 2 if any_group_concat else 1

    if len(nodes) > limits.max_nodes:
        raise OneError("bounded Surprise Program exceeded declared node limit")

    digest = sha256(target).hexdigest() if current_digest is None else current_digest
    current_root = Root(current_ref, len(target), digest)
    program = Program(tuple(nodes), {"previous": previous_root, "current": current_root}, limits)
    stats = SurprisePoolStats(
        groups=len(groups),
        max_groups=geometry.max_groups,
        group_span_bytes=geometry.group_span_bytes,
        surprise_pool_nodes=pool_nodes,
        group_concat_nodes=concat_nodes,
        max_surprise_pool_bytes=max_pool_bytes,
        total_surprise_payload_bytes=total_surprise,
        hierarchy_depth=hierarchy_depth,
        crystallized_groups=crystallized_groups,
        crystallized_bytes=crystallized_bytes,
        max_group_refs=max_group_refs,
    )
    return program, stats