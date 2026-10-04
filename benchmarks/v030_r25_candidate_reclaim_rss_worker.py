from __future__ import annotations

"""Fresh-process worker for frozen post-PrefixGraph reclaim attribution."""

import argparse
import ctypes
import gc
import hashlib
import json
import resource
import sys
import time
from pathlib import Path


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _vmrss_kib() -> int:
    for line in Path("/proc/self/status").read_text().splitlines():
        if line.startswith("VmRSS:"):
            return int(line.split()[1])
    raise RuntimeError("VmRSS unavailable from /proc/self/status")


def _deep_size(value) -> int:
    """Conservative Python-owned object census; native allocator state is intentionally excluded."""
    seen: set[int] = set()

    def walk(obj) -> int:
        ident = id(obj)
        if ident in seen:
            return 0
        seen.add(ident)
        total = sys.getsizeof(obj, 0)
        if isinstance(obj, dict):
            for key, child in obj.items():
                total += walk(key) + walk(child)
        elif isinstance(obj, (list, tuple, set, frozenset)):
            for child in obj:
                total += walk(child)
        return total

    return walk(value)


def _malloc_trim() -> int:
    libc = ctypes.CDLL(None)
    fn = getattr(libc, "malloc_trim", None)
    if fn is None:
        raise RuntimeError("glibc malloc_trim unavailable for frozen trim diagnostic")
    fn.argtypes = [ctypes.c_size_t]
    fn.restype = ctypes.c_int
    return int(fn(0))


class _ImmediateFuture:
    def __init__(self, value):
        self._value = value

    def result(self):
        return self._value


class _InlineExecutor:
    arm = "control"
    submissions = 0
    observations: list[dict] = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def submit(self, fn, *args, **kwargs):
        type(self).submissions += 1
        started = time.perf_counter()
        value = fn(*args, **kwargs)
        pre = _vmrss_kib()
        deep = _deep_size(value)
        collected = None
        trim_return = None
        if type(self).arm in {"gc", "trim"}:
            collected = int(gc.collect())
        if type(self).arm == "trim":
            trim_return = _malloc_trim()
        post = _vmrss_kib()
        type(self).observations.append({
            "pre_action_vmrss_kib": pre,
            "post_action_vmrss_kib": post,
            "vmrss_drop_kib": max(0, pre - post),
            "retained_result_deep_bytes": deep,
            "gc_collected": collected,
            "malloc_trim_return": trim_return,
            "first_candidate_wall_s": time.perf_counter() - started,
        })
        return _ImmediateFuture(value)


class _RoutingExecutor:
    original = None
    intercepted_constructions = 0
    delegated_constructions = 0

    def __new__(cls, *args, **kwargs):
        prefix = kwargs.get("thread_name_prefix")
        if prefix == "cmpct-v030-prefixgraph":
            cls.intercepted_constructions += 1
            return _InlineExecutor()
        cls.delegated_constructions += 1
        return cls.original(*args, **kwargs)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--arm", choices=("control", "gc", "trim"), required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    args = parser.parse_args()

    from experiments import entropygraph_v030_canonical_final as canonical
    from experiments import entropygraph_v030_release_product as product

    iso = canonical.PROFILE_ISOLATION
    if canonical.RC.PG is not iso.PG or canonical.RC.G04 is not iso.SHARED or canonical.RC.READER is not iso.POLICY:
        raise RuntimeError("canonical semantic-owner identity mismatch")

    research_tree = str(canonical.RC.treehash(args.source))
    expected_product_tree = str(product.treehash(args.source))
    eligible, reason = canonical.RC._prefixgraph_eligibility(args.source, research_tree)
    if not eligible:
        raise RuntimeError(f"preregistered Shifted target unexpectedly PrefixGraph-ineligible: {reason}")

    _InlineExecutor.arm = args.arm
    original_executor = canonical.ThreadPoolExecutor
    _RoutingExecutor.original = original_executor
    canonical.ThreadPoolExecutor = _RoutingExecutor
    try:
        baseline_ru = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        baseline_vm = _vmrss_kib()
        started = time.perf_counter()
        stats = dict(product.build(args.source, args.archive))
        wall = time.perf_counter() - started
        peak_ru = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    finally:
        canonical.ThreadPoolExecutor = original_executor

    verify = dict(product.strong_verify(args.archive))
    verified_tree = str(verify.get("tree_sha256") or "")
    if not verify.get("ok") or verified_tree != expected_product_tree:
        raise RuntimeError(f"shipping strong verification mismatch: expected={expected_product_tree} actual={verified_tree}")
    if _RoutingExecutor.intercepted_constructions != 1 or _InlineExecutor.submissions != 1:
        raise RuntimeError("frozen PrefixGraph serialization seam was not exercised exactly once")
    if len(_InlineExecutor.observations) != 1:
        raise RuntimeError("missing frozen post-PrefixGraph reclaim observation")

    print(json.dumps({
        "arm": args.arm,
        "archive_bytes": args.archive.stat().st_size,
        "archive_sha256": _sha(args.archive),
        "selected": stats.get("selected"),
        "format_revision": stats.get("format_revision"),
        "r24_product_bytes": stats.get("r24_product_bytes"),
        "r25_product_bytes": stats.get("r25_product_bytes"),
        "tree_sha256": verified_tree,
        "research_tree_sha256": research_tree,
        "expected_verification_tree_sha256": expected_product_tree,
        "verification_identity_domain": "canonical-filesystem-user-tree-v1",
        "research_identity_domain": "research-content-tree-v1",
        "wall_s": wall,
        "baseline_ru_maxrss_kib": baseline_ru,
        "baseline_vmrss_kib": baseline_vm,
        "peak_ru_maxrss_kib": peak_ru,
        "incremental_ru_maxrss_kib": max(0, peak_ru - baseline_ru),
        "reclaim_observation": _InlineExecutor.observations[0],
        "intercepted_prefixgraph_executor_constructions": _RoutingExecutor.intercepted_constructions,
        "intercepted_prefixgraph_submissions": _InlineExecutor.submissions,
        "delegated_executor_constructions": _RoutingExecutor.delegated_constructions,
        "executor_restored": canonical.ThreadPoolExecutor is original_executor,
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
