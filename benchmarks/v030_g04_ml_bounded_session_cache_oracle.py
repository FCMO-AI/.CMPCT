from __future__ import annotations

"""Exact bounded-cache decision oracle for operation-scoped G0-G4 ML decode ownership.

The native G0-G4 reader currently creates one DecodeContext per logical member. A prior structural
oracle proves that records/nodes are reused across members, but its archive-unique floor is deliberately
optimistic because it does not model the shipping cache ceilings. This oracle models the native policy
itself: insertion-only decoded-record and decoded-node caches, capped at 64 MiB and 32 MiB respectively,
in exact logical-member traversal order.

The candidate simulation keeps locality accounting member-scoped and independent of cache hits. Cache
reuse may remove CPU/decode work, but every member is still charged its full unique physical-record
closure exactly as the shipping <=8x law requires. No archive bytes or semantic rules are changed.
"""

import argparse
import json
import os
from pathlib import Path
import shutil

from benchmarks import v030_release_performance as PERF
from benchmarks.v030_g04_ml_cross_member_reuse_floor_oracle import _node_dependencies, _node_length
from experiments import entropygraph_v030_release_product as PRODUCT
from experiments import entropygraph_v030_release_reader as RR


def _record_logical_size(usize: int, transform: object) -> int:
    if transform is None:
        return int(usize)
    if not isinstance(transform, list) or not transform:
        raise RuntimeError(f"malformed physical geometry descriptor: {transform!r}")
    kind = transform[0]
    if kind == "lane" and len(transform) == 3:
        return int(transform[2])
    if kind == "delimiter" and len(transform) == 3:
        return int(transform[2])
    if kind == "hierarchical" and len(transform) == 5:
        return int(transform[4])
    raise RuntimeError(f"unknown physical geometry descriptor: {transform!r}")


class CacheSim:
    def __init__(self, nodes: list, record_sizes: list[int], node_sizes: list[int]) -> None:
        self.nodes = nodes
        self.record_sizes = record_sizes
        self.node_sizes = node_sizes
        self.record_cache: set[int] = set()
        self.node_cache: set[int] = set()
        self.record_cache_bytes = 0
        self.node_cache_bytes = 0
        self.record_accesses = 0
        self.node_accesses = 0
        self.record_hits = 0
        self.node_hits = 0
        self.decoded_record_bytes = 0
        self.reconstructed_node_bytes = 0

    def record(self, record_id: int) -> None:
        self.record_accesses += 1
        if record_id in self.record_cache:
            self.record_hits += 1
            return
        size = self.record_sizes[record_id]
        self.decoded_record_bytes += size
        if self.record_cache_bytes + size <= RR.MAX_RECORD_CACHE_BYTES:
            self.record_cache.add(record_id)
            self.record_cache_bytes += size

    def node(self, node_id: int) -> None:
        self.node_accesses += 1
        if node_id in self.node_cache:
            self.node_hits += 1
            return
        desc = self.nodes[node_id]
        kind = desc[0]
        if kind == "direct":
            self.record(int(desc[1]))
        elif kind in ("delta", "delta_pack"):
            self.node(int(desc[1]))
            self.record(int(desc[2]))
        elif kind == "mosaic":
            for base in desc[1]:
                self.node(int(base))
            self.record(int(desc[2]))
        elif kind == "pack_mosaic":
            for base in desc[4]:
                self.node(int(base))
            self.record(int(desc[1]))
        else:
            raise RuntimeError(f"unknown node kind: {kind!r}")
        size = self.node_sizes[node_id]
        self.reconstructed_node_bytes += size
        if self.node_cache_bytes + size <= RR.MAX_NODE_CACHE_BYTES:
            self.node_cache.add(node_id)
            self.node_cache_bytes += size

    def member(self, desc: list) -> None:
        if desc[0] == "preflate":
            self.record(int(desc[1]))
            return
        if desc[0] != "nodes":
            raise RuntimeError(f"unknown file descriptor: {desc[0]!r}")
        for node_id in desc[1]:
            self.node(int(node_id))

    def snapshot(self) -> dict:
        return {
            "record_accesses": self.record_accesses,
            "record_cache_hits": self.record_hits,
            "record_hit_fraction": self.record_hits / max(1, self.record_accesses),
            "node_accesses": self.node_accesses,
            "node_cache_hits": self.node_hits,
            "node_hit_fraction": self.node_hits / max(1, self.node_accesses),
            "decoded_record_bytes": self.decoded_record_bytes,
            "reconstructed_node_bytes": self.reconstructed_node_bytes,
            "record_cache_bytes_final": self.record_cache_bytes,
            "node_cache_bytes_final": self.node_cache_bytes,
            "record_cache_objects_final": len(self.record_cache),
            "node_cache_objects_final": len(self.node_cache),
        }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    roots = PERF._build_corpora(work_root / "corpus")
    source = roots[("neutral_hostile_v1", "09_ml_artifacts")]
    source_tree = PRODUCT.treehash(source)
    archive = work_root / "ml.cmpct"

    with PRODUCT.C._revision25_profile_context():
        built = PRODUCT.build(source, archive)
        if archive.read_bytes()[:8] != PRODUCT.G04_MAGIC:
            raise RuntimeError("ML target did not select canonical G0-G4")
        verified = PRODUCT.strong_verify(archive)
        if not verified.get("ok") or verified.get("tree_sha256") != source_tree:
            raise RuntimeError("canonical ML archive failed shipping verification")
        stream, meta, record_start, offsets, _merkle, _tail = RR._g04_open(archive)
        try:
            physical_usizes: list[int] = []
            for rel in offsets:
                stream.seek(int(record_start) + int(rel))
                header = stream.read(RR.PH.size)
                if len(header) != RR.PH.size:
                    raise RuntimeError("short G0-G4 physical header")
                _codec, usize, _csize, _crc, _sha = RR.PH.unpack(header)
                physical_usizes.append(int(usize))
        finally:
            stream.close()

    geometries = meta["physical_geometry"]
    if len(geometries) != len(physical_usizes):
        raise RuntimeError("physical geometry/record count drift")
    record_sizes = [
        _record_logical_size(usize, transform)
        for usize, transform in zip(physical_usizes, geometries)
    ]
    nodes = meta["nodes"]
    node_sizes = [_node_length(desc) for desc in nodes]
    ordered_files = [(rel, meta["files"][rel]) for rel in sorted(meta["files"])]

    # Current native behavior: new bounded cache for every member.
    fresh_total = {
        "record_accesses": 0,
        "record_cache_hits": 0,
        "node_accesses": 0,
        "node_cache_hits": 0,
        "decoded_record_bytes": 0,
        "reconstructed_node_bytes": 0,
    }
    for _rel, desc in ordered_files:
        sim = CacheSim(nodes, record_sizes, node_sizes)
        sim.member(desc)
        snap = sim.snapshot()
        for key in fresh_total:
            fresh_total[key] += int(snap[key])
    fresh_total["record_hit_fraction"] = fresh_total["record_cache_hits"] / max(1, fresh_total["record_accesses"])
    fresh_total["node_hit_fraction"] = fresh_total["node_cache_hits"] / max(1, fresh_total["node_accesses"])

    # Proposed operation ownership: exact same cache limits/policy, persisted across members.
    session = CacheSim(nodes, record_sizes, node_sizes)
    for _rel, desc in ordered_files:
        session.member(desc)
    bounded = session.snapshot()

    # Locality is computed structurally and remains independent of both simulations.
    memo: dict[int, tuple[frozenset[int], frozenset[int]]] = {}
    max_amp = 0.0
    for rel, desc in ordered_files:
        logical_size = int(desc[2])
        if desc[0] == "preflate":
            required_records = {int(desc[1])}
        else:
            required_records: set[int] = set()
            for node_id in desc[1]:
                records, _nodes = _node_dependencies(nodes, int(node_id), memo)
                required_records.update(records)
        charged = sum(record_sizes[r] for r in required_records)
        amp = charged / max(1, logical_size)
        if amp > 8.0 + 1e-12:
            raise RuntimeError(f"member dependency closure exceeds 8x locality: {rel}={amp:.6f}x")
        max_amp = max(max_amp, amp)

    record_saved = fresh_total["decoded_record_bytes"] - bounded["decoded_record_bytes"]
    node_saved = fresh_total["reconstructed_node_bytes"] - bounded["reconstructed_node_bytes"]
    total_fresh = fresh_total["decoded_record_bytes"] + fresh_total["reconstructed_node_bytes"]
    total_bounded = bounded["decoded_record_bytes"] + bounded["reconstructed_node_bytes"]
    total_saved = total_fresh - total_bounded

    return {
        "schema": "cmpct-v030-g04-ml-bounded-session-cache-v1",
        "candidate_head": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA"),
        "target": "neutral_hostile_v1/09_ml_artifacts",
        "tree_sha256": source_tree,
        "shipping_build": built,
        "member_count": len(ordered_files),
        "record_count": len(record_sizes),
        "node_count": len(nodes),
        "cache_policy": {
            "kind": "insertion_only_no_eviction",
            "record_limit_bytes": RR.MAX_RECORD_CACHE_BYTES,
            "node_limit_bytes": RR.MAX_NODE_CACHE_BYTES,
            "budget_change_bytes": 0,
            "member_order": "sorted logical path, matching native verify traversal",
        },
        "current_member_scoped": fresh_total,
        "bounded_operation_scoped": bounded,
        "realisable_work_removed": {
            "decoded_record_bytes": record_saved,
            "decoded_record_fraction": record_saved / max(1, fresh_total["decoded_record_bytes"]),
            "reconstructed_node_bytes": node_saved,
            "reconstructed_node_fraction": node_saved / max(1, fresh_total["reconstructed_node_bytes"]),
            "combined_bytes": total_saved,
            "combined_fraction": total_saved / max(1, total_fresh),
        },
        "locality": {
            "accounting_scope": "per-member dependency closure independent of cache hits",
            "max_member_read_amplification": max_amp,
            "limit": 8.0,
        },
        "gate": {
            "canonical_archive_verified": True,
            "tree_identity_preserved": True,
            "archive_bytes_changed": False,
            "memory_budget_changed": False,
            "exact_shipping_cache_limits_modeled": True,
            "locality_accounting_not_reduced_by_cache_hits": True,
            "max_member_locality_within_8x": max_amp <= 8.0,
            "bounded_cross_member_reuse_exists": total_saved > 0,
            "promotion_signal": (total_saved / max(1, total_fresh)) >= 0.10,
            "experiment_valid": True,
            "release_credit": False,
        },
        "claim_boundary": (
            "Research-only exact policy simulation. It measures decoded/reconstructed byte-work removable under the "
            "shipping insertion-only 64/32 MiB cache ceilings and traversal order. It is not wall-clock evidence. "
            "A promotion signal only authorizes a native A/B that must preserve archive/output identity, hostile-input "
            "checks, the same memory ceilings, and per-member physical dependency accounting on cache hits."
        ),
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-g04-ml-bounded-session-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-g04-ml-bounded-session-cache.json"))
    args = p.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "candidate_head": result["candidate_head"],
        "realisable_work_removed": result["realisable_work_removed"],
        "locality": result["locality"],
        "gate": result["gate"],
    }, indent=2), flush=True)
    if not result["gate"]["experiment_valid"]:
        raise SystemExit("bounded ML session-cache oracle invalid")


if __name__ == "__main__":
    main()
