from __future__ import annotations

"""Fresh-process worker for the superseding r25 candidate-scheduling RSS v2 A/B.

V1 compared the shipping verifier's canonical filesystem/user-tree identity against the private
release-candidate research-content identity.  V2 reports and checks both identity domains explicitly.
Only candidate scheduling changes between arms; production source remains untouched.
"""

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

    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def submit(self, fn, *args, **kwargs):
        type(self).submissions += 1
        return _ImmediateFuture(fn, args, kwargs)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("concurrent", "serialized"), required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    args = parser.parse_args()

    from experiments import entropygraph_v030_canonical_final as canonical
    from experiments import entropygraph_v030_release_product as product

    iso = canonical.PROFILE_ISOLATION
    if canonical.RC.PG is not iso.PG or canonical.RC.G04 is not iso.SHARED or canonical.RC.READER is not iso.POLICY:
        raise RuntimeError("canonical semantic-owner identity mismatch")

    research_tree = str(canonical.RC.treehash(args.source))
    expected_product_tree = str(canonical.treehash(args.source))
    eligible, reason = canonical.RC._prefixgraph_eligibility(args.source, research_tree)
    if not eligible:
        raise RuntimeError(f"preregistered shifted workload unexpectedly PrefixGraph-ineligible: {reason}")

    original_executor = canonical.RC.ThreadPoolExecutor
    if args.mode == "serialized":
        canonical.RC.ThreadPoolExecutor = _InlineExecutor

    try:
        baseline = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        started = time.perf_counter()
        stats = dict(product.build(args.source, args.archive))
        wall = time.perf_counter() - started
        peak = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    finally:
        canonical.RC.ThreadPoolExecutor = original_executor

    verify = dict(product.strong_verify(args.archive))
    verified_tree = str(verify.get("tree_sha256") or "")
    if not verify.get("ok") or verified_tree != expected_product_tree:
        raise RuntimeError(
            "shipping strong verification identity mismatch: "
            f"expected={expected_product_tree} actual={verified_tree} result={verify!r}"
        )

    print(
        json.dumps(
            {
                "mode": args.mode,
                "archive_bytes": args.archive.stat().st_size,
                "archive_sha256": _sha(args.archive),
                "tree_sha256": verified_tree,
                "research_tree_sha256": research_tree,
                "expected_verification_tree_sha256": expected_product_tree,
                "verified_tree_sha256": verified_tree,
                "verification_identity_domain": "canonical-filesystem-user-tree-v1",
                "research_identity_domain": "research-content-tree-v1",
                "selected": stats.get("selected"),
                "wall_s": wall,
                "baseline_rss_kib": baseline,
                "peak_rss_kib": peak,
                "incremental_peak_rss_kib": max(0, peak - baseline),
                "inline_executor_submissions": _InlineExecutor.submissions if args.mode == "serialized" else 0,
                "semantic_owners": {
                    "pg": canonical.RC.PG.__name__,
                    "g04": canonical.RC.G04.__name__,
                    "reader": canonical.RC.READER.__name__,
                    "identity_exact": True,
                },
                "build_stats": stats,
            },
            separators=(",", ":"),
            default=str,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
