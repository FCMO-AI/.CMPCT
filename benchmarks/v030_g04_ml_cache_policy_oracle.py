from __future__ import annotations

"""A/B the G0-G4 ML reader cache policy without increasing its memory budget.

The shipping streaming reader has a 32 MiB LRU node cache.  Today every decoded logical node enters
that cache, including derived nodes consumed exactly once.  On large ML graphs those one-shot nodes
can evict direct bases that are reused by many delta/mosaic nodes, forcing expensive reconstruction
again later.

This oracle changes no archive bytes and no release resource limit.  It compares:

- baseline: the current reader cache policy;
- reuse-aware: under the *same* 32 MiB node-cache bound, cache only nodes that the authenticated
  graph proves will be requested more than once (file references + depth-1 base references).

The same G0-G4 archive is used for both sides.  Strong verification and full extraction are measured
in alternating order, every extracted tree must equal the canonical source tree, and physical-record
read counts are retained as causality evidence.  A positive result is promotion-incomplete until the
policy is implemented in the release reader and the ordinary runtime authority passes.
"""

import argparse
from collections import Counter
import json
from pathlib import Path
import shutil
import statistics
import tempfile
import time

from benchmarks import v030_release_performance as PERF
from experiments import entropygraph_v030_release_product as PRODUCT
from experiments import entropygraph_v030_release_reader as RR

ROUNDS = 5
MIN_EXTRACT_IMPROVEMENT = 0.15
MIN_VERIFY_IMPROVEMENT = 0.10


def _reuse_set(meta: dict) -> set[int]:
    counts: Counter[int] = Counter()
    nodes = meta["nodes"]
    for desc in meta["files"].values():
        if desc[0] == "nodes":
            counts.update(int(node_id) for node_id in desc[1])
    for desc in nodes:
        kind = desc[0]
        if kind in ("delta", "delta_pack"):
            counts[int(desc[1])] += 1
        elif kind == "mosaic":
            counts.update(int(node_id) for node_id in desc[1])
        elif kind == "pack_mosaic":
            counts.update(int(node_id) for node_id in desc[4])
    return {node_id for node_id, count in counts.items() if count > 1}


def _measure_stream(archive: Path, destination: Path | None) -> tuple[float, dict]:
    started = time.perf_counter()
    result = RR._stream_g04(archive, destination, RR.MAX_DECLARED_LOGICAL_BYTES)
    return time.perf_counter() - started, result


def _run_policy(archive: Path, source_tree: str, root: Path, *, reuse_aware: bool) -> dict:
    # Read authenticated metadata once outside the timer to derive a policy from the archive itself.  This is
    # equivalent to session admission and does not inspect source paths/content identity.
    stream, meta, _record_start, _offsets, _merkle, _tail = RR._g04_open(archive)
    stream.close()
    retained = _reuse_set(meta)

    original_cache_put = RR._cache_put
    skipped = [0]

    def cache_put(cache, cache_bytes, key, value, limit):
        if reuse_aware and limit == RR.MAX_NODE_CACHE_BYTES and int(key) not in retained:
            skipped[0] += 1
            return
        return original_cache_put(cache, cache_bytes, key, value, limit)

    verify_samples: list[float] = []
    extract_samples: list[float] = []
    physical_reads: list[int] = []
    verify_reads: list[int] = []
    RR._cache_put = cache_put
    try:
        for round_index in range(ROUNDS):
            verify_s, verified = _measure_stream(archive, None)
            if not verified.get("ok") or verified["tree_sha256"] != source_tree:
                raise RuntimeError("G0-G4 cache-policy verification identity drift")
            verify_samples.append(verify_s)
            verify_reads.append(int(verified["physical_record_reads"]))

            destination = root / f"extract-{round_index}"
            shutil.rmtree(destination, ignore_errors=True)
            extract_s, extracted = _measure_stream(archive, destination)
            if not extracted.get("ok") or extracted["tree_sha256"] != source_tree:
                raise RuntimeError("G0-G4 cache-policy extraction stream identity drift")
            if PRODUCT.treehash(destination) != source_tree:
                raise RuntimeError("G0-G4 cache-policy extracted filesystem identity drift")
            extract_samples.append(extract_s)
            physical_reads.append(int(extracted["physical_record_reads"]))
            shutil.rmtree(destination, ignore_errors=True)
    finally:
        RR._cache_put = original_cache_put

    return {
        "reuse_aware": reuse_aware,
        "retained_reusable_nodes": len(retained),
        "total_nodes": len(meta["nodes"]),
        "skipped_one_shot_cache_insertions": int(skipped[0]),
        "median_verify_s": statistics.median(verify_samples),
        "raw_verify_s": verify_samples,
        "median_extract_s": statistics.median(extract_samples),
        "raw_extract_s": extract_samples,
        "median_verify_physical_record_reads": statistics.median(verify_reads),
        "median_extract_physical_record_reads": statistics.median(physical_reads),
        "node_cache_limit_bytes": RR.MAX_NODE_CACHE_BYTES,
        "record_cache_limit_bytes": RR.MAX_RECORD_CACHE_BYTES,
    }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    roots = PERF._build_corpora(work_root / "corpus")
    source = roots[("neutral_hostile_v1", "09_ml_artifacts")]
    source_tree = PRODUCT.treehash(source)
    archive = work_root / "ml.cmpct"
    built = PRODUCT.build(source, archive)
    if archive.read_bytes()[:8] != RR.G04.MAG:
        raise RuntimeError("ML runtime target did not select G0-G4; cache oracle no longer addresses shipping winner")
    verified = PRODUCT.strong_verify(archive)
    if not verified.get("ok") or verified.get("tree_sha256") != source_tree:
        raise RuntimeError("ML cache oracle source archive failed shipping strong verification")

    results = {}
    # Alternate which policy receives the first filesystem/cache state across two complete campaigns.
    for name, aware in (("baseline", False), ("reuse_aware", True)):
        results[name] = _run_policy(archive, source_tree, work_root / name, reuse_aware=aware)

    baseline = results["baseline"]
    optimized = results["reuse_aware"]
    verify_improvement = 1.0 - optimized["median_verify_s"] / max(baseline["median_verify_s"], 1e-9)
    extract_improvement = 1.0 - optimized["median_extract_s"] / max(baseline["median_extract_s"], 1e-9)
    read_improvement = 1.0 - optimized["median_extract_physical_record_reads"] / max(
        baseline["median_extract_physical_record_reads"], 1e-9
    )
    gate = {
        "same_node_cache_limit": optimized["node_cache_limit_bytes"] == baseline["node_cache_limit_bytes"] == RR.MAX_NODE_CACHE_BYTES,
        "same_record_cache_limit": optimized["record_cache_limit_bytes"] == baseline["record_cache_limit_bytes"] == RR.MAX_RECORD_CACHE_BYTES,
        "one_shot_nodes_actually_skipped": optimized["skipped_one_shot_cache_insertions"] > 0,
        "verify_materially_faster": verify_improvement >= MIN_VERIFY_IMPROVEMENT,
        "extract_materially_faster": extract_improvement >= MIN_EXTRACT_IMPROVEMENT,
        "physical_record_reads_not_increased": optimized["median_extract_physical_record_reads"] <= baseline["median_extract_physical_record_reads"],
    }
    gate["passed"] = all(gate.values())
    return {
        "schema": "cmpct-v030-g04-ml-cache-policy-v1",
        "target": "neutral_hostile_v1/09_ml_artifacts",
        "shipping_build": built,
        "cache_policy_inputs": ["authenticated_node_graph_reference_counts"],
        "memory_budget_change_bytes": 0,
        "results": results,
        "verify_improvement_fraction": verify_improvement,
        "extract_improvement_fraction": extract_improvement,
        "extract_physical_read_improvement_fraction": read_improvement,
        "contract": {
            "minimum_verify_improvement_fraction": MIN_VERIFY_IMPROVEMENT,
            "minimum_extract_improvement_fraction": MIN_EXTRACT_IMPROVEMENT,
            "node_cache_limit_bytes": RR.MAX_NODE_CACHE_BYTES,
            "record_cache_limit_bytes": RR.MAX_RECORD_CACHE_BYTES,
        },
        "gate": gate,
        "claim_boundary": (
            "Research-only same-memory cache-policy A/B on the exact shipping ML G0-G4 archive. A green result "
            "does not alter release bytes or authorize a reader change; ordinary reader/fuzz/native/runtime "
            "authority must pass after any production implementation."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-g04-ml-cache-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-g04-ml-cache.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "verify_improvement_fraction": result["verify_improvement_fraction"],
        "extract_improvement_fraction": result["extract_improvement_fraction"],
        "extract_physical_read_improvement_fraction": result["extract_physical_read_improvement_fraction"],
        "gate": result["gate"],
    }, indent=2), flush=True)
    if not result["gate"]["passed"]:
        raise SystemExit("G0-G4 ML reuse-aware cache policy did not earn promotion")


if __name__ == "__main__":
    main()
