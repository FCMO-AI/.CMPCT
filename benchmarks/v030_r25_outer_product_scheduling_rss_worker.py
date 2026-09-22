from __future__ import annotations

"""Fresh-process worker for the frozen outer r24-vs-r25 product scheduling RSS A/B."""

import argparse
import hashlib
import json
import resource
import time
from pathlib import Path


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class _ImmediateFuture:
    def __init__(self, fn, args, kwargs):
        self._value = fn(*args, **kwargs)

    def result(self):
        return self._value


class _InlineExecutor:
    submissions = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def submit(self, fn, *args, **kwargs):
        type(self).submissions += 1
        return _ImmediateFuture(fn, args, kwargs)


class _RoutingExecutor:
    original = None
    intercepted_constructions = 0
    delegated_constructions = 0

    def __new__(cls, *args, **kwargs):
        prefix = kwargs.get("thread_name_prefix")
        if prefix == "cmpct-v030-product":
            cls.intercepted_constructions += 1
            return _InlineExecutor()
        cls.delegated_constructions += 1
        return cls.original(*args, **kwargs)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("concurrent", "serialized"), required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    args = parser.parse_args()

    from experiments import entropygraph_v030_canonical_final as canonical
    from experiments import entropygraph_v030_release_product as product

    # Canonical-final executes the preserved implementation in this public module dictionary. The shipping
    # outer tournament therefore resolves ThreadPoolExecutor here. Patch only this global and route every
    # non-product executor to the exact inherited implementation; the release-product r24 prebuild executor lives
    # in its own module and remains untouched.
    original_executor = canonical.ThreadPoolExecutor
    _RoutingExecutor.original = original_executor

    source_tree = str(product.treehash(args.source))
    research_tree = str(canonical.RC.treehash(args.source))
    if canonical.RC.PG is not canonical.PROFILE_ISOLATION.PG:
        raise RuntimeError("canonical PrefixGraph semantic-owner identity mismatch")
    if canonical.RC.G04 is not canonical.PROFILE_ISOLATION.SHARED:
        raise RuntimeError("canonical G0-G4 semantic-owner identity mismatch")
    if canonical.RC.READER is not canonical.PROFILE_ISOLATION.POLICY:
        raise RuntimeError("canonical reader semantic-owner identity mismatch")

    if args.mode == "serialized":
        canonical.ThreadPoolExecutor = _RoutingExecutor

    try:
        baseline = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        started = time.perf_counter()
        stats = dict(product.build(args.source, args.archive))
        wall = time.perf_counter() - started
        peak = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    finally:
        canonical.ThreadPoolExecutor = original_executor

    verify = dict(product.strong_verify(args.archive))
    verified_tree = str(verify.get("tree_sha256") or "")
    if not verify.get("ok") or verified_tree != source_tree:
        raise RuntimeError(f"shipping strong verification mismatch: expected={source_tree} actual={verified_tree}")

    # The selected complete product must expose both priced branches on this non-terminal Shifted workload.
    if stats.get("r24_product_bytes") is None or stats.get("r25_product_bytes") is None:
        raise RuntimeError(f"outer tournament did not price both complete products: {stats!r}")
    if stats.get("r25_attempted") is False:
        raise RuntimeError("outer tournament unexpectedly skipped r25")

    print(json.dumps({
        "mode": args.mode,
        "archive_bytes": args.archive.stat().st_size,
        "archive_sha256": _sha(args.archive),
        "selected": stats.get("selected"),
        "format_revision": stats.get("format_revision"),
        "r24_product_bytes": stats.get("r24_product_bytes"),
        "r25_product_bytes": stats.get("r25_product_bytes"),
        "r25_attempted": stats.get("r25_attempted"),
        "tree_sha256": verified_tree,
        "expected_verification_tree_sha256": source_tree,
        "research_tree_sha256": research_tree,
        "verification_identity_domain": "canonical-filesystem-user-tree-v1",
        "research_identity_domain": "research-content-tree-v1",
        "wall_s": wall,
        "baseline_rss_kib": baseline,
        "peak_rss_kib": peak,
        "incremental_peak_rss_kib": max(0, peak - baseline),
        "intercepted_product_executor_constructions": _RoutingExecutor.intercepted_constructions if args.mode == "serialized" else 0,
        "intercepted_product_submissions": _InlineExecutor.submissions if args.mode == "serialized" else 0,
        "delegated_canonical_executor_constructions": _RoutingExecutor.delegated_constructions if args.mode == "serialized" else 0,
        "r24_prebuild_executor_patched": False,
        "inner_r25_executor_patched": False,
        "canonical_executor_restored": canonical.ThreadPoolExecutor is original_executor,
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
