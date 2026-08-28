from __future__ import annotations

"""Fresh-process PrefixGraph worker-count measurement.

This worker changes only ``MAX_ANCHOR_WORKERS`` on the release-facing bounded
PrefixGraph wrapper. Candidate bytes, anchor nomination, serializer, tie law,
strong verification and source identity remain unchanged.
"""

import argparse
import json
from pathlib import Path
import resource
import time

from experiments import entropygraph_v030_prefixgraph as BASE
from experiments import entropygraph_v030_prefixgraph_parallel as PG


def _rss_kib() -> int:
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--workers", type=int, choices=(1, 2, 4), required=True)
    args = parser.parse_args()

    expected_tree = BASE.treehash(args.source)
    PG.MAX_ANCHOR_WORKERS = int(args.workers)
    baseline = _rss_kib()
    started = time.perf_counter()
    stats = PG.build(args.source, args.archive)
    wall_s = time.perf_counter() - started
    peak = _rss_kib()
    verified = BASE.strong_verify(args.archive)
    if verified.get("ok") is not True or verified.get("tree_sha256") != expected_tree:
        raise SystemExit("PrefixGraph strong verification identity mismatch")

    print(json.dumps({
        "workers": int(args.workers),
        "archive_bytes": args.archive.stat().st_size,
        "archive_sha256": __import__("hashlib").sha256(args.archive.read_bytes()).hexdigest(),
        "tree_sha256": expected_tree,
        "wall_s": wall_s,
        "baseline_rss_kib": baseline,
        "peak_rss_kib": peak,
        "incremental_peak_rss_kib": peak - baseline,
        "anchor_auditions": stats.get("anchor_auditions"),
        "reported_anchor_workers": stats.get("anchor_audition_workers"),
        "max_anchor_results_inflight": stats.get("max_anchor_results_inflight"),
        "full_candidate_list_retained": stats.get("full_candidate_list_retained"),
        "candidate_set_unchanged": stats.get("candidate_set_unchanged"),
        "complete_byte_tournament_unchanged": stats.get("complete_byte_tournament_unchanged"),
        "verification": verified,
    }, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
