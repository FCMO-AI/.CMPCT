"""Bounded exact compressed-length reuse for the v0.30 pack-plan product path.

The product call supplies its already-loaded semantic owner, so importing this helper adds no duplicate v0.28
module graph to the canonical parent or spawned child. A lazy historical owner exists only for standalone tests and
research diagnostics. Archive grammar, selector semantics and compression settings are unchanged.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Callable

HERE = Path(__file__).resolve().parent
V028_PATH = HERE / "entropygraph_v028.py"
_DEFAULT_V028 = None


def _default_owner():
    global _DEFAULT_V028
    if _DEFAULT_V028 is None:
        spec = importlib.util.spec_from_file_location("cmpct_v028_pack_cache", V028_PATH)
        if spec is None or spec.loader is None:
            raise RuntimeError("cannot load v0.28 engine")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _DEFAULT_V028 = module
    return _DEFAULT_V028


def __getattr__(name: str):
    # Backward-compatible research/test surface without paying the clone at product import time.
    if name == "V028":
        return _default_owner()
    raise AttributeError(name)


class CacheStats:
    __slots__ = ("hits", "misses")
    def __init__(self) -> None:
        self.hits = 0; self.misses = 0
    def __eq__(self, other: object) -> bool:
        return isinstance(other, CacheStats) and (self.hits, self.misses) == (other.hits, other.misses)


def choose_pack_plan_cached(nodes: list[bytes], sketches, root_ids: list[int], *, owner=None,
                            compress_record: Callable[[bytes], tuple[int, bytes]] | None = None):
    """Return the inherited pack choice while reusing only exact payload lengths.

    Cache identity is the ordered tuple of node IDs. It is sufficient inside one invocation because nodes and
    compression settings are immutable for the tournament. State dies with this call and retains no payload bytes.
    """
    base = owner if owner is not None else _default_owner()
    compress = compress_record or base._compress_record
    lengths: dict[tuple[int, ...], int] = {}
    stats = CacheStats(); trials = []
    for limit_kib in (64, 128, 256, 512, 1024, 2048):
        limit = limit_kib * 1024
        order_local = base.similarity_order([sketches[i] for i in root_ids])
        order = [root_ids[i] for i in order_local]
        groups: list[list[int]] = []; current: list[int] = []; current_len = 0
        for node_id in order:
            size = len(nodes[node_id])
            if size > limit:
                if current:
                    groups.append(current); current = []; current_len = 0
                groups.append([node_id]); continue
            if current and current_len + size > limit:
                groups.append(current); current = []; current_len = 0
            current.append(node_id); current_len += size
        if current: groups.append(current)
        bytes_cost = 0; decoded_weight = 0; logical_weight = 0
        for group in groups:
            key = tuple(group)
            if key in lengths:
                payload_len = lengths[key]; stats.hits += 1
            else:
                raw = b"".join(nodes[i] for i in group)
                _, payload = compress(raw); payload_len = len(payload)
                lengths[key] = payload_len; stats.misses += 1
            bytes_cost += base.PH.size + payload_len
            group_raw_len = sum(len(nodes[i]) for i in group)
            for i in group:
                decoded_weight += group_raw_len; logical_weight += max(1, len(nodes[i]))
        amp = decoded_weight / max(1, logical_weight)
        trials.append((bytes_cost, amp, limit, groups))
    feasible = [row for row in trials if row[1] <= 8.0]
    chosen = min(feasible or trials, key=lambda row: (row[0], row[1], row[2]))
    baseline = next(row for row in trials if row[2] == 512 * 1024)
    if chosen[2] > 512 * 1024 and baseline[0] - chosen[0] < max(1024, baseline[0] // 1000):
        chosen = baseline
    public_trials = [{"limit": limit, "bytes": cost, "read_amp": amp} for cost, amp, limit, _ in trials]
    return chosen, public_trials, stats


def assert_exact_equivalence(nodes: list[bytes], sketches, root_ids: list[int]) -> CacheStats:
    base = _default_owner()
    inherited, inherited_trials = base._choose_pack_plan(nodes, sketches, root_ids)
    cached, cached_trials, stats = choose_pack_plan_cached(nodes, sketches, root_ids, owner=base)
    if cached != inherited or cached_trials != inherited_trials:
        raise AssertionError("cached pack pricing changed inherited plan semantics")
    return stats
