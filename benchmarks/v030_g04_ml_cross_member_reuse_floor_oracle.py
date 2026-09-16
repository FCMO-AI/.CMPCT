from __future__ import annotations

"""Exact structural floor for cross-member G0-G4 decode reuse on the canonical ML workload.

The portable Rust G0-G4 reader currently creates a fresh DecodeContext for each logical member. That makes its
64 MiB decoded-record cache and 32 MiB decoded-node cache member-local even during whole-archive verify/extract.
This oracle does not change the reader. It computes, from authenticated canonical archive metadata and physical
headers, how much decoded work is repeated *solely* because those contexts cannot survive across members.

Locality is deliberately kept member-scoped: every member is charged its complete unique physical-record closure
even if another member would have already decoded those records in an operation-scoped cache. Therefore the oracle
cannot manufacture a lower <=8x amplification number from cache hits. It only measures CPU/work reuse headroom.

The result is a decision oracle, not performance or release credit. A positive reuse floor authorizes an exact A/B
of operation-scoped native decoded-data ownership with unchanged per-member locality accounting and unchanged
64/32 MiB cache budgets.
"""

import argparse
import json
import os
from pathlib import Path
import shutil
from typing import Iterable

from benchmarks import v030_release_performance as PERF
from experiments import entropygraph_v030_release_product as PRODUCT
from experiments import entropygraph_v030_release_reader as RR


def _node_length(desc: list) -> int:
    kind = desc[0]
    if kind in ("direct", "delta", "mosaic"):
        return int(desc[3])
    if kind in ("delta_pack", "pack_mosaic"):
        return int(desc[5])
    raise RuntimeError(f"unknown G0-G4 node kind: {kind!r}")


def _node_dependencies(nodes: list, node_id: int, memo: dict[int, tuple[frozenset[int], frozenset[int]]]) -> tuple[frozenset[int], frozenset[int]]:
    cached = memo.get(node_id)
    if cached is not None:
        return cached
    desc = nodes[node_id]
    kind = desc[0]
    records: set[int] = set()
    logical_nodes: set[int] = {node_id}
    if kind == "direct":
        records.add(int(desc[1]))
    elif kind in ("delta", "delta_pack"):
        base_id = int(desc[1])
        recipe_record = int(desc[2])
        base_records, base_nodes = _node_dependencies(nodes, base_id, memo)
        records.update(base_records)
        records.add(recipe_record)
        logical_nodes.update(base_nodes)
    elif kind == "mosaic":
        for base_id in desc[1]:
            base_records, base_nodes = _node_dependencies(nodes, int(base_id), memo)
            records.update(base_records)
            logical_nodes.update(base_nodes)
        records.add(int(desc[2]))
    elif kind == "pack_mosaic":
        records.add(int(desc[1]))
        for base_id in desc[4]:
            base_records, base_nodes = _node_dependencies(nodes, int(base_id), memo)
            records.update(base_records)
            logical_nodes.update(base_nodes)
    else:
        raise RuntimeError(f"unknown G0-G4 node kind: {kind!r}")
    result = (frozenset(records), frozenset(logical_nodes))
    memo[node_id] = result
    return result


def _union_sets(parts: Iterable[frozenset[int]]) -> set[int]:
    out: set[int] = set()
    for part in parts:
        out.update(part)
    return out


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
            record_sizes: list[int] = []
            for rel in offsets:
                stream.seek(int(record_start) + int(rel))
                header = stream.read(RR.PH.size)
                if len(header) != RR.PH.size:
                    raise RuntimeError("short G0-G4 physical header")
                _codec, usize, _csize, _crc, _sha = RR.PH.unpack(header)
                record_sizes.append(int(usize))
        finally:
            stream.close()

    nodes = meta["nodes"]
    memo: dict[int, tuple[frozenset[int], frozenset[int]]] = {}
    node_sizes = [_node_length(desc) for desc in nodes]
    member_rows = []
    archive_records: set[int] = set()
    archive_nodes: set[int] = set()
    fresh_record_bytes = 0
    fresh_node_bytes = 0
    max_amp = 0.0

    for rel in sorted(meta["files"]):
        desc = meta["files"][rel]
        size = int(desc[2])
        if desc[0] == "preflate":
            records = {int(desc[1])}
            member_nodes: set[int] = set()
        elif desc[0] == "nodes":
            closures = [_node_dependencies(nodes, int(node_id), memo) for node_id in desc[1]]
            records = _union_sets(part[0] for part in closures)
            member_nodes = _union_sets(part[1] for part in closures)
        else:
            raise RuntimeError("unknown G0-G4 file descriptor")
        record_bytes = sum(record_sizes[r] for r in records)
        node_bytes = sum(node_sizes[n] for n in member_nodes)
        amp = record_bytes / max(1, size)
        if amp > 8.0 + 1e-12:
            raise RuntimeError(f"member dependency closure exceeds 8x locality: {rel}={amp:.6f}x")
        max_amp = max(max_amp, amp)
        fresh_record_bytes += record_bytes
        fresh_node_bytes += node_bytes
        archive_records.update(records)
        archive_nodes.update(member_nodes)
        member_rows.append({
            "path": rel,
            "logical_bytes": size,
            "required_unique_records": len(records),
            "required_decoded_record_bytes": record_bytes,
            "required_unique_nodes": len(member_nodes),
            "required_logical_node_bytes": node_bytes,
            "member_read_amplification": amp,
        })

    session_record_floor = sum(record_sizes[r] for r in archive_records)
    session_node_floor = sum(node_sizes[n] for n in archive_nodes)
    repeated_record_bytes = fresh_record_bytes - session_record_floor
    repeated_node_bytes = fresh_node_bytes - session_node_floor
    record_reuse_fraction = repeated_record_bytes / max(1, fresh_record_bytes)
    node_reuse_fraction = repeated_node_bytes / max(1, fresh_node_bytes)
    candidate_head = os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA")

    return {
        "schema": "cmpct-v030-g04-ml-cross-member-reuse-floor-v1",
        "candidate_head": candidate_head,
        "target": "neutral_hostile_v1/09_ml_artifacts",
        "tree_sha256": source_tree,
        "shipping_build": built,
        "member_count": len(member_rows),
        "record_count": len(record_sizes),
        "node_count": len(nodes),
        "current_native_context_scope": "one DecodeContext per logical member",
        "fresh_context_work": {
            "sum_member_unique_decoded_record_bytes": fresh_record_bytes,
            "sum_member_unique_logical_node_bytes": fresh_node_bytes,
        },
        "ideal_operation_scope_floor": {
            "archive_unique_decoded_record_bytes": session_record_floor,
            "archive_unique_logical_node_bytes": session_node_floor,
        },
        "provable_cross_member_repetition": {
            "decoded_record_bytes": repeated_record_bytes,
            "decoded_record_fraction": record_reuse_fraction,
            "logical_node_bytes": repeated_node_bytes,
            "logical_node_fraction": node_reuse_fraction,
        },
        "locality": {
            "accounting_scope": "per-member dependency closure independent of cache hits",
            "max_member_read_amplification": max_amp,
            "limit": 8.0,
        },
        "cache_contract": {
            "record_cache_limit_bytes": RR.MAX_RECORD_CACHE_BYTES,
            "node_cache_limit_bytes": RR.MAX_NODE_CACHE_BYTES,
            "budget_change_bytes": 0,
            "note": "The ideal floor is structural headroom, not a claim that finite caches retain every object simultaneously.",
        },
        "members": member_rows,
        "gate": {
            "canonical_archive_verified": True,
            "tree_identity_preserved": True,
            "archive_bytes_changed": False,
            "memory_budget_changed": False,
            "locality_accounting_not_reduced_by_cache_hits": True,
            "max_member_locality_within_8x": max_amp <= 8.0,
            "cross_member_record_repetition_exists": repeated_record_bytes > 0,
            "experiment_valid": True,
            "release_credit": False,
        },
        "claim_boundary": (
            "Exact structural decoded-work floor only. It proves repeated record/node dependency work caused by "
            "member-local native contexts while retaining full per-member locality charges. It does not predict "
            "wall-clock speedup or assume an infinite shipping cache. Any operation-scoped native implementation "
            "must preserve the 64/32 MiB budgets, hostile-input checks, exact outputs and per-member locality stats."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-g04-ml-cross-member-reuse-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-g04-ml-cross-member-reuse-floor.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "candidate_head": result["candidate_head"],
        "member_count": result["member_count"],
        "provable_cross_member_repetition": result["provable_cross_member_repetition"],
        "locality": result["locality"],
        "gate": result["gate"],
    }, indent=2), flush=True)
    if not result["gate"]["experiment_valid"]:
        raise SystemExit("ML cross-member reuse floor oracle invalid")


if __name__ == "__main__":
    main()
