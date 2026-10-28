from __future__ import annotations

"""A/B G0-G4 ML physical-record cache pollution without increasing memory.

This is intentionally orthogonal to the existing node-cache experiment.  The release reader owns a 64 MiB LRU
for decoded physical records.  Large records that are referenced once can evict records backing several direct
nodes / recipes that are revisited through the authenticated depth-1 graph.  This oracle compares the shipping
policy against a reference-count-aware policy under the exact same 64 MiB record-cache and 32 MiB node-cache
limits.  Archive bytes, reader grammar, integrity and locality remain unchanged.
"""

import argparse
from collections import Counter
import json
from pathlib import Path
import shutil
import statistics
import time

from benchmarks import v030_release_performance as PERF
from experiments import entropygraph_v030_release_product as PRODUCT
from experiments import entropygraph_v030_release_reader as RR

ROUNDS = 5
MIN_VERIFY_IMPROVEMENT = 0.05
MIN_EXTRACT_IMPROVEMENT = 0.10


def _record_reuse_set(meta: dict) -> set[int]:
    counts: Counter[int] = Counter()
    for desc in meta["nodes"]:
        kind = desc[0]
        if kind == "direct":
            counts[int(desc[1])] += 1
        elif kind in ("delta", "delta_pack", "mosaic"):
            counts[int(desc[2])] += 1
        elif kind == "pack_mosaic":
            counts[int(desc[1])] += 1
    for desc in meta["files"].values():
        if desc[0] == "preflate":
            counts[int(desc[1])] += 1
    return {record_id for record_id, count in counts.items() if count > 1}


def _measure(archive: Path, destination: Path | None) -> tuple[float, dict]:
    started = time.perf_counter()
    result = RR._stream_g04(archive, destination, RR.MAX_DECLARED_LOGICAL_BYTES)
    return time.perf_counter() - started, result


def _run_policy(archive: Path, source_tree: str, root: Path, *, reuse_aware: bool) -> dict:
    stream, meta, _record_start, _offsets, _merkle, _tail = RR._g04_open(archive)
    stream.close()
    retained = _record_reuse_set(meta)

    original_cache_put = RR._cache_put
    skipped = [0]

    def cache_put(cache, cache_bytes, key, value, limit):
        if reuse_aware and limit == RR.MAX_RECORD_CACHE_BYTES and int(key) not in retained:
            skipped[0] += 1
            return
        return original_cache_put(cache, cache_bytes, key, value, limit)

    verify_samples: list[float] = []
    extract_samples: list[float] = []
    verify_reads: list[int] = []
    extract_reads: list[int] = []
    RR._cache_put = cache_put
    try:
        for index in range(ROUNDS):
            verify_s, verified = _measure(archive, None)
            if not verified.get("ok") or verified.get("tree_sha256") != source_tree:
                raise RuntimeError("record-cache verification identity drift")
            verify_samples.append(verify_s)
            verify_reads.append(int(verified["physical_record_reads"]))

            destination = root / f"extract-{index}"
            shutil.rmtree(destination, ignore_errors=True)
            extract_s, extracted = _measure(archive, destination)
            if not extracted.get("ok") or extracted.get("tree_sha256") != source_tree:
                raise RuntimeError("record-cache extraction identity drift")
            if PRODUCT.treehash(destination) != source_tree:
                raise RuntimeError("record-cache extracted filesystem identity drift")
            extract_samples.append(extract_s)
            extract_reads.append(int(extracted["physical_record_reads"]))
            shutil.rmtree(destination, ignore_errors=True)
    finally:
        RR._cache_put = original_cache_put

    return {
        "reuse_aware": reuse_aware,
        "retained_reusable_records": len(retained),
        "total_records": len(meta["record_leaf_sha256"]),
        "skipped_one_shot_record_cache_insertions": int(skipped[0]),
        "median_verify_s": statistics.median(verify_samples),
        "median_extract_s": statistics.median(extract_samples),
        "raw_verify_s": verify_samples,
        "raw_extract_s": extract_samples,
        "median_verify_physical_record_reads": statistics.median(verify_reads),
        "median_extract_physical_record_reads": statistics.median(extract_reads),
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

    with PRODUCT.C._revision25_profile_context():
        built = PRODUCT.build(source, archive)
        if archive.read_bytes()[:8] != PRODUCT.G04_MAGIC:
            raise RuntimeError("ML runtime target did not select canonical G0-G4")
        verified = PRODUCT.strong_verify(archive)
        if not verified.get("ok") or verified.get("tree_sha256") != source_tree:
            raise RuntimeError("ML record-cache source archive failed shipping verification")
        baseline = _run_policy(archive, source_tree, work_root / "baseline", reuse_aware=False)
        optimized = _run_policy(archive, source_tree, work_root / "reuse-aware", reuse_aware=True)

    verify_improvement = 1.0 - optimized["median_verify_s"] / max(baseline["median_verify_s"], 1e-9)
    extract_improvement = 1.0 - optimized["median_extract_s"] / max(baseline["median_extract_s"], 1e-9)
    read_improvement = 1.0 - optimized["median_extract_physical_record_reads"] / max(
        baseline["median_extract_physical_record_reads"], 1e-9
    )
    gate = {
        "same_node_cache_limit": baseline["node_cache_limit_bytes"] == optimized["node_cache_limit_bytes"] == RR.MAX_NODE_CACHE_BYTES,
        "same_record_cache_limit": baseline["record_cache_limit_bytes"] == optimized["record_cache_limit_bytes"] == RR.MAX_RECORD_CACHE_BYTES,
        "one_shot_records_actually_skipped": optimized["skipped_one_shot_record_cache_insertions"] > 0,
        "verify_materially_faster": verify_improvement >= MIN_VERIFY_IMPROVEMENT,
        "extract_materially_faster": extract_improvement >= MIN_EXTRACT_IMPROVEMENT,
        "physical_record_reads_not_increased": optimized["median_extract_physical_record_reads"] <= baseline["median_extract_physical_record_reads"],
    }
    gate["passed"] = all(gate.values())
    return {
        "schema": "cmpct-v030-g04-ml-record-cache-policy-v1",
        "target": "neutral_hostile_v1/09_ml_artifacts",
        "shipping_build": built,
        "canonical_profile_binding": {"magic": PRODUCT.G04_MAGIC.hex(), "revision": 25, "operation_scoped": True},
        "cache_policy_inputs": ["authenticated_physical_record_reference_counts"],
        "memory_budget_change_bytes": 0,
        "baseline": baseline,
        "reuse_aware": optimized,
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
            "Research-only same-memory physical-record cache A/B on the exact promoted canonical ML G0-G4 archive. "
            "A green result cannot change release bytes or authorize a reader change; production reader/fuzz/native/"
            "runtime authority remain mandatory."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-g04-ml-record-cache-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-g04-ml-record-cache.json"))
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
        raise SystemExit("G0-G4 ML reuse-aware record cache policy did not earn promotion")


if __name__ == "__main__":
    main()
