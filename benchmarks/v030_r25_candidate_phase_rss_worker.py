from __future__ import annotations

"""Fresh-process worker for per-candidate r25 RSS ownership.

This worker is diagnostic only. It measures the promoted full product, the exact G0-G4 complete candidate,
or the exact PrefixGraph complete candidate in isolation. Candidate bytes are never compared with one another here;
only semantic-tree identity, strong verification, wall time and process-local peak RSS are observed.
"""

import argparse
import hashlib
import json
from pathlib import Path
import resource
import time


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _imports():
    # Import every candidate surface before freezing the baseline so mode-to-mode RSS deltas do not merely
    # measure different module import sets.
    from experiments import entropygraph_v030_geometry_overlay_g04 as g04
    from experiments import entropygraph_v030_prefixgraph_parallel as pg
    from experiments import entropygraph_v030_release_candidate as candidate
    from experiments import entropygraph_v030_release_product as product
    return g04, pg, candidate, product


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("shipping", "g04", "prefixgraph"), required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    args = parser.parse_args()

    g04, pg, candidate, product = _imports()
    args.archive.parent.mkdir(parents=True, exist_ok=True)
    expected_tree = candidate.treehash(args.source)

    eligible = True
    reject_reason = None
    if args.mode == "prefixgraph":
        eligible, reject_reason = candidate._prefixgraph_eligibility(args.source, expected_tree)
        if not eligible:
            print(json.dumps({
                "mode": args.mode,
                "eligible": False,
                "reject_reason": reject_reason,
                "tree_sha256": expected_tree,
            }, separators=(",", ":")), flush=True)
            return

    baseline_rss_kib = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    started = time.perf_counter()
    if args.mode == "shipping":
        stats = dict(product.build(args.source, args.archive))
    elif args.mode == "g04":
        stats = dict(g04.build(args.source, args.archive))
    else:
        stats = dict(pg.build(args.source, args.archive))
    wall_s = time.perf_counter() - started
    peak_rss_kib = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)

    # Correctness stays mandatory but outside the pack timer, matching the other RSS ownership oracles.
    # The promoted product is a portfolio and may legally publish r24, canonical r25 profiles, logs/CC
    # terminals, or the accepted-v0.29 research fallback. Its own dispatcher is therefore the semantic
    # verification owner. Isolated G0-G4/PrefixGraph candidates are fixed r25 candidate grammars and remain
    # verified by the independent canonical candidate reader.
    if args.mode == "shipping":
        verified = dict(product.strong_verify(args.archive))
        verification_owner = "release-product-dispatcher"
    else:
        verified = dict(candidate.READER.strong_verify(args.archive))
        verification_owner = "canonical-r25-candidate-reader"
    if not verified.get("ok") or verified.get("tree_sha256") != expected_tree:
        raise RuntimeError(f"{args.mode} candidate failed strong verification: {verified!r}")

    print(json.dumps({
        "mode": args.mode,
        "eligible": True,
        "archive_bytes": args.archive.stat().st_size,
        "archive_sha256": _sha256_file(args.archive),
        "tree_sha256": expected_tree,
        "wall_s": wall_s,
        "baseline_rss_kib": baseline_rss_kib,
        "peak_rss_kib": peak_rss_kib,
        "incremental_peak_rss_kib": max(0, peak_rss_kib - baseline_rss_kib),
        "selected": stats.get("selected"),
        "verification_owner": verification_owner,
        "build_stats": stats,
    }, separators=(",", ":"), default=str), flush=True)


if __name__ == "__main__":
    main()
