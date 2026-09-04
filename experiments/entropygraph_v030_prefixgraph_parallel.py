"""Release-facing PrefixGraph builder with exact-byte bounded anchor parallelism.

The research oracle proved that PrefixGraph anchor auditions are independent once the
shared direct Zstd payload floor has been constructed.  This module changes only that
schedule: every nominated anchor still calls the historical serializer, the complete
serialized-byte tournament and tie law are unchanged, and all reader/recovery/locality
semantics remain owned by ``entropygraph_v030_prefixgraph``.

Anchor results are consumed through a bounded submission window instead of retaining
the complete set of serialized candidate archives.  At most the current winner plus the
configured in-flight auditions remain reachable.  This removes an O(anchor_count *
archive_size) memory retention term without changing a candidate byte, nomination rule,
comparison key, or completion-order-independent winner.

A fresh-process 1/2/4-worker diagnostic initially showed a large isolated RSS reduction
at two workers.  Exact shipping evidence then falsified that as a product-level fix:
Shifted remained near the same full-product RSS peak and far above the frozen release
limit, while the two-worker arm was about 4.6% slower than four workers in the exact-byte
candidate A/B.  The release wrapper therefore restores four workers globally while
retaining bounded result ownership.  This is a content-agnostic throughput policy: it
does not inspect workload names, paths, hashes, or candidate bytes.

Keep this wrapper deliberately thin so canonical operation-scoped profile bindings on
the historical PrefixGraph module remain authoritative.  Unknown attributes are
forwarded dynamically rather than copied at import time.
"""
from __future__ import annotations

from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
import os
from pathlib import Path
import time

from experiments import entropygraph_v030_prefixgraph as BASE

# The isolated frontier measured 63,550 / 145,070 / 297,572 KiB incremental RSS for
# 1 / 2 / 4 workers, but the exact product-phase run after the two-worker promotion
# still measured 273,618 KiB incremental / 396,754 KiB operation peak on Shifted and
# the authoritative runtime RSS ratio remained 3.38485x.  The isolated memory win did
# not retire or materially move the shipping blocker.  Recover the measured ~4.6%
# audition throughput loss while preserving the bounded winner/in-flight ownership that
# removed complete-candidate-list retention.
MAX_ANCHOR_WORKERS = 4
WORKER_POLICY = "global-four-worker-throughput-bounded-retention-v2"


def __getattr__(name: str):
    return getattr(BASE, name)


def _candidate_key(item: tuple[bytes, dict]) -> tuple[int, int]:
    return (
        len(item[0]),
        -1 if item[1]["anchor"] is None else int(item[1]["anchor"]),
    )


def build(root: Path, out: Path) -> dict:
    started = time.perf_counter()
    files = sorted(path for path in root.rglob("*") if path.is_file())
    if not files or len(files) > BASE.MAX_FILES:
        raise ValueError("PrefixGraph requires 1..MAX_FILES regular files")
    rels = [path.relative_to(root).as_posix() for path in files]
    raws = [path.read_bytes() for path in files]
    if any(len(raw) > BASE.MAX_FILE_BYTES for raw in raws):
        raise ValueError("PrefixGraph research seed file ceiling exceeded")
    expected_tree = BASE._treehash_parts(rels, raws)

    # The direct payload floor is common to every anchor and remains computed once.
    direct_payloads = [BASE._compress(raw) for raw in raws]
    all_direct, direct_stats = BASE._serialize_candidate(
        rels, raws, direct_payloads, expected_tree, None
    )
    all_direct_bytes = len(all_direct)
    anchors = BASE._anchor_indices(len(raws))
    workers = max(
        1,
        min(MAX_ANCHOR_WORKERS, os.cpu_count() or 1, len(anchors) or 1),
    )

    def audition(anchor: int):
        return BASE._serialize_candidate(
            rels, raws, direct_payloads, expected_tree, anchor
        )

    # Keep only the deterministic current winner plus a bounded number of in-flight
    # auditions.  The previous ``list(pool.map(...))`` retained every complete archive
    # until all anchors finished, which made RSS scale with the audition count even
    # though the tournament only needs one winner.
    best: tuple[bytes, dict] = (all_direct, direct_stats)
    # ``best`` is now the sole owner of the direct full-archive candidate.  If an
    # anchor displaces it, that byte buffer can be reclaimed immediately instead of
    # surviving just because the reporting path still names ``all_direct``.
    all_direct = None
    max_inflight = 0
    audition_started = time.perf_counter()
    if workers == 1:
        for anchor in anchors:
            candidate = audition(anchor)
            if _candidate_key(candidate) < _candidate_key(best):
                best = candidate
            candidate = None
        scheduler = "serial-streaming-winner-v2"
        max_inflight = 1 if anchors else 0
    else:
        with ThreadPoolExecutor(
            max_workers=workers,
            thread_name_prefix="cmpct-prefixgraph",
        ) as pool:
            anchor_iter = iter(anchors)
            pending = {}

            def submit_one() -> bool:
                try:
                    anchor = next(anchor_iter)
                except StopIteration:
                    return False
                future = pool.submit(audition, anchor)
                pending[future] = anchor
                return True

            for _ in range(workers):
                if not submit_one():
                    break
            max_inflight = max(max_inflight, len(pending))

            while pending:
                done, _ = wait(tuple(pending), return_when=FIRST_COMPLETED)
                # ``done`` is intentionally unordered.  The winner key contains the
                # historical anchor tie-break, so completion order cannot affect bytes.
                for future in done:
                    pending.pop(future)
                    candidate = future.result()
                    if _candidate_key(candidate) < _candidate_key(best):
                        best = candidate
                    # Drop the losing result before admitting another full candidate.
                    candidate = None
                    submit_one()
                max_inflight = max(max_inflight, len(pending))
        scheduler = "parallel-bounded-streaming-winner-v2"
    audition_s = time.perf_counter() - audition_started

    blob, stats = best
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(blob)
    stats = dict(stats)
    stats.update(
        {
            "archive_bytes": len(blob),
            "all_direct_bytes": all_direct_bytes,
            "saving_vs_all_direct_bytes": all_direct_bytes - len(blob),
            "anchor_auditions": len(anchors),
            "files": len(files),
            "logical_bytes": sum(map(len, raws)),
            "tree_sha256": expected_tree,
            "create_s": time.perf_counter() - started,
            "anchor_audition_s": audition_s,
            "anchor_audition_workers": workers,
            "anchor_audition_worker_policy": WORKER_POLICY,
            "anchor_audition_scheduler": scheduler,
            "max_anchor_results_inflight": max_inflight,
            "full_candidate_list_retained": False,
            "displaced_direct_archive_retained": False,
            "candidate_retention_policy": "winner-plus-bounded-inflight-v1",
            "candidate_set_unchanged": True,
            "complete_byte_tournament_unchanged": True,
            "direct_payload_floor_unchanged": True,
            "max_dependency_depth": 1 if stats["prefix_records"] else 0,
        }
    )
    return stats
