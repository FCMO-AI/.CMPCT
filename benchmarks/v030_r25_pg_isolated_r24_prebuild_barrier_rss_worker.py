from __future__ import annotations

"""Fresh-process worker for the frozen PrefixGraph-isolated r24-prebuild barrier RSS A/B."""

import argparse
import json
from pathlib import Path
import resource
import time

from benchmarks import v030_r25_parent_phase_rss_worker as PHASE


class _BarrierState:
    waits = 0
    future_done_after_wait = False
    prebuilt_exists_after_wait = False


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=("overlap", "r24-barrier"), required=True)
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--archive", type=Path, required=True)
    a = p.parse_args()

    from experiments import entropygraph_v030_canonical_final as canonical
    from experiments import entropygraph_v030_release_product as product

    iso = canonical.PROFILE_ISOLATION
    if canonical.RC.PG is not iso.PG or canonical.RC.G04 is not iso.SHARED or canonical.RC.READER is not iso.POLICY:
        raise RuntimeError("canonical semantic-owner identity mismatch")

    source_tree = str(product.treehash(a.source))
    research_tree = str(canonical.RC.treehash(a.source))
    eligible, reason = canonical.RC._prefixgraph_eligibility(a.source, research_tree)
    if not eligible:
        raise RuntimeError(f"Shifted target unexpectedly PrefixGraph-ineligible: {reason}")

    PHASE._PGState.submissions = PHASE._PGState.children = 0
    PHASE._PGState.returncodes = []
    PHASE._PGState.child_wall_s = []
    PHASE._RoutingExecutor.intercepted = PHASE._RoutingExecutor.delegated = 0
    _BarrierState.waits = 0
    _BarrierState.future_done_after_wait = False
    _BarrierState.prebuilt_exists_after_wait = False

    original_executor = canonical.ThreadPoolExecutor
    original_prepare = canonical._prepare_profile_tree
    PHASE._RoutingExecutor.original = original_executor

    base = product._BASE_IMPL

    def prepare_with_barrier(root: Path, staging_root: Path):
        result = original_prepare(root, staging_root)
        key = base._prebuild_key(Path(staging_root))
        with base._R24_PREBUILD_LOCK:
            pending = base._R24_PREBUILDS.get(key)
        if pending is None:
            raise RuntimeError("r24 prebuild barrier could not find exact pending canonical prebuild")
        _executor, future, prebuilt = pending
        _BarrierState.waits += 1
        future.result()
        _BarrierState.future_done_after_wait = bool(future.done())
        _BarrierState.prebuilt_exists_after_wait = Path(prebuilt).is_file()
        if not _BarrierState.future_done_after_wait or not _BarrierState.prebuilt_exists_after_wait:
            raise RuntimeError("r24 prebuild barrier did not complete the exact pending artifact")
        return result

    canonical.ThreadPoolExecutor = PHASE._RoutingExecutor
    if a.mode == "r24-barrier":
        canonical._prepare_profile_tree = prepare_with_barrier

    sampler = PHASE._TreeSampler(0.01)
    sampler.start()
    try:
        started = time.perf_counter()
        stats = dict(product.build(a.source, a.archive))
        wall = time.perf_counter() - started
        parent_peak = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    finally:
        sampler.stop()
        canonical.ThreadPoolExecutor = original_executor
        canonical._prepare_profile_tree = original_prepare

    verify = dict(product.strong_verify(a.archive))
    verified_tree = str(verify.get("tree_sha256") or "")
    if not verify.get("ok") or verified_tree != source_tree:
        raise RuntimeError("final independent strong verification mismatch")

    r24 = dict(stats.get("r24") or {})
    if r24.get("r24_prebuild_reused") is not True:
        raise RuntimeError("canonical outer tournament did not reuse exact r24 prebuild")
    if PHASE._RoutingExecutor.intercepted != 1 or PHASE._PGState.submissions != 1 or PHASE._PGState.children != 1 or PHASE._PGState.returncodes != [0]:
        raise RuntimeError("PrefixGraph isolation lifecycle mismatch")
    if a.mode == "overlap" and _BarrierState.waits != 0:
        raise RuntimeError("overlap control unexpectedly waited on r24 prebuild")
    if a.mode == "r24-barrier" and _BarrierState.waits != 1:
        raise RuntimeError("barrier arm did not wait exactly once on r24 prebuild")

    print(json.dumps({
        "mode": a.mode,
        "archive_bytes": a.archive.stat().st_size,
        "archive_sha256": PHASE._sha(a.archive),
        "selected": stats.get("selected"),
        "format_revision": stats.get("format_revision"),
        "r24_product_bytes": stats.get("r24_product_bytes"),
        "r25_product_bytes": stats.get("r25_product_bytes"),
        "tree_sha256": verified_tree,
        "expected_verification_tree_sha256": source_tree,
        "research_tree_sha256": research_tree,
        "wall_s": wall,
        "parent_peak_ru_maxrss_kib": parent_peak,
        "tree_peak_rss_kib": sampler.peak_kib,
        "tree_peak_processes": sampler.peak_processes,
        "tree_peak_phase_signature": list(sampler.peak_signature),
        "tree_samples": sampler.samples,
        "tree_sampler_errors": sampler.errors,
        "tree_sampler_interval_s": sampler.interval_s,
        "prefixgraph_executor_intercepts": PHASE._RoutingExecutor.intercepted,
        "prefixgraph_submissions": PHASE._PGState.submissions,
        "prefixgraph_children": PHASE._PGState.children,
        "prefixgraph_returncodes": PHASE._PGState.returncodes,
        "prefixgraph_child_wall_s": PHASE._PGState.child_wall_s,
        "g04_children": 0,
        "r24_prebuild_barrier_waits": _BarrierState.waits,
        "r24_prebuild_future_done_after_wait": _BarrierState.future_done_after_wait,
        "r24_prebuilt_artifact_exists_after_wait": _BarrierState.prebuilt_exists_after_wait,
        "r24_prebuild_reused_by_canonical_consumer": r24.get("r24_prebuild_reused") is True,
        "bindings_restored": canonical.ThreadPoolExecutor is original_executor and canonical._prepare_profile_tree is original_prepare,
        "semantic_owners": {
            "pg": canonical.RC.PG.__name__,
            "g04": canonical.RC.G04.__name__,
            "reader": canonical.RC.READER.__name__,
            "identity_exact": True,
        },
        "build_stats": stats,
    }, separators=(",", ":"), default=str), flush=True)


if __name__ == "__main__":
    main()
