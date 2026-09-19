"""Bounded exact compressed-length reuse for the v0.30 pack-plan product experiment.

This module deliberately changes no archive grammar or selector semantics.  It caches only the
exact stored payload length for structurally identical groups during one six-limit pack-plan
tournament.  Raw/compressed bytes are never retained across trials.
"""
from __future__ import annotations

from dataclasses import dataclass
import importlib.util
from pathlib import Path
from typing import Callable

HERE = Path(__file__).resolve().parent
V028_PATH = HERE / "entropygraph_v028.py"


def _load_v028():
    spec = importlib.util.spec_from_file_location("cmpct_v028_pack_cache", V028_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load v0.28 engine")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


V028 = _load_v028()


@dataclass
class CacheStats:
    hits: int = 0
    misses: int = 0


def choose_pack_plan_cached(nodes: list[bytes], sketches, root_ids: list[int], *,
                            compress_record: Callable[[bytes], tuple[int, bytes]] | None = None):
    """Return the inherited pack choice while reusing only exact payload lengths.

    Cache identity is the ordered tuple of node IDs.  That identity is sufficient inside one
    invocation because `nodes` and compression level are immutable for the tournament.  The cache
    dies with this call, bounding retained state to O(number of distinct trial groups) integers.
    """
    compress = compress_record or V028._compress_record
    lengths: dict[tuple[int, ...], int] = {}
    stats = CacheStats()
    trials = []

    for limit_kib in (64, 128, 256, 512, 1024, 2048):
        limit = limit_kib * 1024
        order_local = V028.similarity_order([sketches[i] for i in root_ids])
        order = [root_ids[i] for i in order_local]
        groups: list[list[int]] = []
        current: list[int] = []
        current_len = 0
        for node_id in order:
            size = len(nodes[node_id])
            if size > limit:
                if current:
                    groups.append(current)
                    current = []
                    current_len = 0
                groups.append([node_id])
                continue
            if current and current_len + size > limit:
                groups.append(current)
                current = []
                current_len = 0
            current.append(node_id)
            current_len += size
        if current:
            groups.append(current)

        bytes_cost = 0
        decoded_weight = 0
        logical_weight = 0
        for group in groups:
            key = tuple(group)
            payload_len = lengths.get(key)
            if payload_len is None:
                raw = b"".join(nodes[i] for i in group)
                _, payload = compress(raw)
                payload_len = len(payload)
                lengths[key] = payload_len
                stats.misses += 1
            else:
                raw = None
                stats.hits += 1
            bytes_cost += V028.PH.size + payload_len
            group_raw_len = sum(len(nodes[i]) for i in group)
            for i in group:
                decoded_weight += group_raw_len
                logical_weight += max(1, len(nodes[i]))
        amp = decoded_weight / max(1, logical_weight)
        trials.append((bytes_cost, amp, limit, groups))

    feasible = [row for row in trials if row[1] <= 8.0]
    chosen = min(feasible or trials, key=lambda row: (row[0], row[1], row[2]))
    baseline = next(row for row in trials if row[2] == 512 * 1024)
    if chosen[2] > 512 * 1024 and baseline[0] - chosen[0] < max(1024, baseline[0] // 1000):
        chosen = baseline
    public_trials = [{"limit": limit, "bytes": cost, "read_amp": amp}
                     for cost, amp, limit, _ in trials]
    return chosen, public_trials, stats


def assert_exact_equivalence(nodes: list[bytes], sketches, root_ids: list[int]) -> CacheStats:
    """Differently rooted control: exact inherited selector must agree field-for-field."""
    inherited, inherited_trials = V028._choose_pack_plan(nodes, sketches, root_ids)
    cached, cached_trials, stats = choose_pack_plan_cached(nodes, sketches, root_ids)
    if cached != inherited or cached_trials != inherited_trials:
        raise AssertionError("cached pack pricing changed inherited plan semantics")
    return stats
