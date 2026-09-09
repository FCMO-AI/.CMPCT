"""ONE-G0.2 budget-aware exact relation-span growth.

Cheap writer observers may nominate a bounded add8/xor seed.  This module performs the
expensive proof: verify the seed and extend it in adjacent windows without rereading bytes
inside an accepted span.  The output is only verified `(start, length)` intervals; callers
compile them through the existing ONE grammar.  No reader behavior or stored opcode lives
here.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RelationGrowthResult:
    runs: tuple[tuple[int, int], ...]
    compared_bytes: int
    accepted_bytes: int
    rejected_seeds: int


def _equal_at(parent: bytes, child: bytes, start: int, length: int, op: str, value: int) -> tuple[bool, int]:
    end = min(len(parent), len(child), start + length)
    checked = 0
    for i in range(start, end):
        checked += 1
        expected = ((parent[i] + value) & 0xFF) if op == "add8" else (parent[i] ^ value)
        if child[i] != expected:
            return False, checked
    return end - start == length, checked


def grow_relation_spans(
    parent: bytes,
    child: bytes,
    *,
    op: str,
    value: int,
    nominations: tuple[int, ...],
    seed_bytes: int = 64,
    extension_bytes: int = 4096,
) -> RelationGrowthResult:
    if op not in {"add8", "xor"}:
        raise ValueError(op)
    if len(parent) != len(child) or seed_bytes <= 0 or extension_bytes <= 0:
        raise ValueError("invalid relation geometry")
    limit = len(parent)
    compared = 0
    rejected = 0
    accepted: list[tuple[int, int]] = []
    covered_until = 0

    for seed in sorted(set(nominations)):
        if seed < 0 or seed + seed_bytes > limit:
            continue
        if seed < covered_until:
            continue
        ok, cost = _equal_at(parent, child, seed, seed_bytes, op, value)
        compared += cost
        if not ok:
            rejected += 1
            continue

        start = seed
        end = seed + seed_bytes
        # Extend right in large bounded chunks. An accepted chunk is never reread. A failed
        # chunk is refined only until the first mismatch so the exact frontier is known.
        while end < limit:
            width = min(extension_bytes, limit - end)
            ok, cost = _equal_at(parent, child, end, width, op, value)
            compared += cost
            if ok:
                end += width
                continue
            # `cost` includes the mismatching byte; bytes before it are valid relation.
            end += max(0, cost - 1)
            break
        accepted.append((start, end - start))
        covered_until = end

    # Coalesce adjacent independently nominated runs. Cracks remain gaps for Surprise.
    merged: list[tuple[int, int]] = []
    for start, length in accepted:
        if length <= 0:
            continue
        if merged and merged[-1][0] + merged[-1][1] == start:
            prev_start, prev_len = merged[-1]
            merged[-1] = (prev_start, prev_len + length)
        else:
            merged.append((start, length))
    return RelationGrowthResult(tuple(merged), compared, sum(length for _, length in merged), rejected)
