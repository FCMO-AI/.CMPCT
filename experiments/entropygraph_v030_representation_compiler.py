"""CMPCT v0.30 production candidate — bounded per-node Representation Compiler.

This module is the consolidation boundary for byte-local transforms.  It does not define an archive magic;
it returns one exact, independently invertible physical representation for a logical node.  The current
portfolio is G0-G4 from Geometry IR plus G5 adaptive lane ordering.  Later production integration may add
only mechanisms that survive their independent frozen gates.

Selection deliberately prices both physical payload bytes and the representation descriptor.  Complete
archive tournamenting remains the final authority because shared/compressed metadata cannot be decomposed
perfectly per node, but a transform with a larger descriptor must not receive a free local audition.

Footnote: import the historical safety facade before resolving Geometry globals.  The parent research branch
keeps the caught ragged-delimiter CPU bug visible in history; this production consolidation consumes only the
bounded execution surface and never imports the unsafe reader path directly.
"""
from __future__ import annotations

import msgpack

from experiments import entropygraph_v030_geometry_safe as _GEOMETRY_SAFETY  # noqa: F401
from experiments import entropygraph_v030_geometry as G
from experiments import entropygraph_v030_hierarchical_geometry as HG
from experiments import entropygraph_v030_g5_entropy_lanes as G5

MIN_INCREMENTAL_STORED_SAVING = 64
G5_SCREEN_LEVEL = 6
G5_EXACT_FINALISTS = 3


def _descriptor(kind: str, param, logical_size: int, logical_hash: bytes) -> list:
    if kind == "direct":
        return ["direct", 0, logical_size, logical_hash]
    if kind == "lane":
        return ["lane", 0, int(param), logical_size, logical_hash]
    if kind == "delimiter":
        return ["delimiter", 0, logical_size, logical_hash]
    if kind == "hierarchical":
        return ["hierarchical", 0, logical_size, logical_hash]
    if kind == "lane_perm":
        width, permutation = param
        return ["lane_perm", 0, int(width), bytes(permutation), logical_size, logical_hash]
    raise ValueError(f"unknown representation kind: {kind}")


def _descriptor_bytes(kind: str, param, logical_size: int, logical_hash: bytes) -> int:
    return len(msgpack.packb(_descriptor(kind, param, logical_size, logical_hash), use_bin_type=True))


def _stored_cost(candidate: dict, logical_size: int, logical_hash: bytes) -> int:
    return int(candidate["payload_bytes"]) + _descriptor_bytes(
        str(candidate["kind"]), candidate.get("param", 0), logical_size, logical_hash
    )


def _g0_g4(raw: bytes) -> dict:
    incumbent = G._encode_node(raw)
    best = {
        "kind": str(incumbent["kind"]),
        "param": incumbent.get("param", 0),
        "physical": incumbent["physical"],
        "codec": int(incumbent["codec"]),
        "payload": incumbent["payload"],
        "payload_bytes": int(incumbent["payload_bytes"]),
        "hierarchical_screened_candidates": 0,
        "hierarchical_exact_finalists": 0,
        "g5_screened_candidates": 0,
        "g5_exact_finalists": 0,
        "g5_strategy": None,
    }
    hierarchical = HG.audition(raw)
    best["hierarchical_screened_candidates"] = int(hierarchical["screened_candidates"])
    best["hierarchical_exact_finalists"] = int(hierarchical["exact_finalists"])
    if hierarchical["kind"] == "hierarchical" and int(hierarchical["payload_bytes"]) < best["payload_bytes"]:
        best.update({
            "kind": "hierarchical",
            "param": 1 if hierarchical["prefix_planes"] else 0,
            "physical": hierarchical["physical"],
            "codec": int(hierarchical["codec"]),
            "payload": hierarchical["payload"],
            "payload_bytes": int(hierarchical["payload_bytes"]),
        })
    return best


def encode_node(raw: bytes) -> dict:
    """Return the cheapest legal G0-G5 representation under bounded exact pricing."""
    logical_hash = G.H(raw)
    best = _g0_g4(raw)
    base_kind = str(best["kind"])
    base_payload_bytes = int(best["payload_bytes"])
    base_cost = _stored_cost(best, len(raw), logical_hash)
    best_cost = base_cost

    screened: list[tuple[int, int, tuple[int, ...], str, bytes]] = []
    if len(raw) >= G.MIN_NODE_BYTES:
        for width in G5.LANE_WIDTHS:
            entropy = G5.entropy_order(raw, width)
            similarity = G5.histogram_chain_order(raw, width)
            strategy_by_order = {entropy: "entropy", similarity: "histogram-chain"}
            for order in G5.nominated_orders(raw, width):
                transformed = G5.forward(raw, width, order)
                if G5.inverse(transformed, width, order, len(raw)) != raw:
                    raise RuntimeError("G5 candidate failed exact inverse")
                compressed = G.zc(transformed, G5_SCREEN_LEVEL)
                screen_bytes = min(len(transformed), len(compressed))
                screened.append((screen_bytes, width, order, strategy_by_order.get(order, "deterministic"), transformed))

    screened.sort(key=lambda row: (row[0], row[1], row[2], row[3]))
    finalists = screened[:G5_EXACT_FINALISTS]
    for _, width, order, strategy, transformed in finalists:
        codec, payload = G._compress_physical(transformed)
        candidate = {
            "kind": "lane_perm",
            "param": (width, order),
            "physical": transformed,
            "codec": int(codec),
            "payload": payload,
            "payload_bytes": len(payload),
        }
        candidate_cost = _stored_cost(candidate, len(raw), logical_hash)
        # Footnote: the 64-byte admission floor is measured against the original G0-G4 incumbent, not the
        # currently winning G5 candidate.  This keeps finalist order from suppressing a slightly better legal
        # view after an earlier G5 candidate has already crossed the threshold.
        if base_cost - candidate_cost < MIN_INCREMENTAL_STORED_SAVING:
            continue
        rank = (candidate_cost, len(payload), width, order, strategy)
        current = (
            best_cost,
            int(best["payload_bytes"]),
            int(best["param"][0]) if best["kind"] == "lane_perm" else 1 << 30,
            tuple(best["param"][1]) if best["kind"] == "lane_perm" else tuple(range(256)),
            best.get("g5_strategy") or "~",
        )
        if rank < current:
            best.update(candidate)
            best["g5_strategy"] = strategy
            best_cost = candidate_cost

    best.update({
        "incumbent_g0_g4_kind": base_kind,
        "incumbent_g0_g4_payload_bytes": base_payload_bytes,
        "incumbent_g0_g4_stored_cost": base_cost,
        "selected_stored_cost": best_cost,
        "incremental_stored_saving_vs_g0_g4": base_cost - best_cost,
        "g5_screened_candidates": len(screened),
        "g5_exact_finalists": len(finalists),
    })
    return best


def inverse_physical(kind: str, param, physical: bytes, logical_size: int) -> bytes:
    """Invert the local representation without archive/container knowledge."""
    if kind == "direct":
        raw = physical
    elif kind == "lane":
        raw = G.L.lane_inverse(physical, int(param), logical_size)
    elif kind == "delimiter":
        raw = G.delimiter_inverse(physical, logical_size)
    elif kind == "hierarchical":
        raw = HG.hierarchy_inverse(physical, logical_size)
    elif kind == "lane_perm":
        width, permutation = param
        raw = G5.inverse(physical, int(width), tuple(permutation), logical_size)
    else:
        raise RuntimeError(f"unknown representation kind: {kind}")
    if len(raw) != logical_size:
        raise RuntimeError("representation inverse logical-size mismatch")
    return raw


RESOURCE_LIMITS = {
    "min_incremental_stored_saving": MIN_INCREMENTAL_STORED_SAVING,
    "g5_screen_level": G5_SCREEN_LEVEL,
    "g5_exact_finalists": G5_EXACT_FINALISTS,
    "g5_max_orders_per_width": G5.MAX_NOMINATED_ORDERS_PER_WIDTH,
    "max_logical_node_bytes": G.MAX_CHUNK,
    "max_decode_unit": G.MAX_DECODE_UNIT,
}
