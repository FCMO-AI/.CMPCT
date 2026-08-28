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
    from experiments import entropygraph_v030_canonical_final as canonical
    from experiments import entropygraph_v030_geometry_overlay_g04 as g04
    from experiments import entropygraph_v030_prefixgraph_parallel as pg
    from experiments import entropygraph_v030_release_candidate as candidate
    from experiments import entropygraph_v030_release_product as product
    return canonical, g04, pg, candidate, product


def _strong_verify_for_mode(mode: str, pg, candidate, product, archive: Path) -> tuple[dict, str]:
    """Use the semantic owner that can actually read the bytes each measured builder emits.

    PrefixGraph remains research-only and has its own authenticated grammar. Sending those bytes through the
    canonical-r25 candidate reader silently asks a different parser to own them and can misclassify a valid
    PrefixGraph archive as an accepted-v0.29 fallback. Keep verification strict by dispatching directly to the
    grammar owner instead of weakening any parser or accepting a fallback classification.
    """
    if mode == "shipping":
        return dict(product.strong_verify(archive)), "release-product-dispatcher"
    if mode == "prefixgraph":
        return dict(pg.strong_verify(archive)), "prefixgraph-grammar-owner"
    return dict(candidate.READER.strong_verify(archive)), "canonical-r25-candidate-reader"


def _verification_identity_for_mode(mode: str, source: Path, candidate, canonical) -> tuple[str, str, str]:
    """Return research identity, verification identity, and the identity domain used by the selected reader.

    The research candidates intentionally hash only their historical content-tree domain. The promoted shipping
    product instead strong-verifies the canonical filesystem/user tree, which includes directory/symlink semantics.
    Both are exact identities, but comparing them directly is a category error. Keep both visible and require the
    reader result to match the identity of the grammar being measured rather than weakening verification.
    """
    research_tree = str(candidate.treehash(source))
    if mode == "shipping":
        return research_tree, str(canonical.treehash(source)), "canonical-filesystem-user-tree-v1"
    return research_tree, research_tree, "research-content-tree-v1"


def _require_verified_tree(mode: str, verified: dict, expected_tree: str) -> str:
    if not verified.get("ok"):
        raise RuntimeError(f"{mode} candidate failed strong verification: {verified!r}")
    observed = str(verified.get("tree_sha256") or "")
    if observed != expected_tree:
        raise RuntimeError(
            f"{mode} candidate verification identity mismatch: observed={observed!r} expected={expected_tree!r}"
        )
    return observed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("shipping", "g04", "prefixgraph"), required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    args = parser.parse_args()

    canonical, g04, pg, candidate, product = _imports()
    args.archive.parent.mkdir(parents=True, exist_ok=True)
    research_tree, expected_verification_tree, verification_identity_domain = _verification_identity_for_mode(
        args.mode, args.source, candidate, canonical
    )

    eligible = True
    reject_reason = None
    if args.mode == "prefixgraph":
        eligible, reject_reason = candidate._prefixgraph_eligibility(args.source, research_tree)
        if not eligible:
            print(json.dumps({
                "mode": args.mode,
                "eligible": False,
                "reject_reason": reject_reason,
                "research_tree_sha256": research_tree,
                "expected_verification_tree_sha256": expected_verification_tree,
                "verification_identity_domain": verification_identity_domain,
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
    # verification owner. G0-G4 is a canonical r25 candidate grammar. PrefixGraph is a distinct research
    # grammar and is verified by its own authenticated reader, never by fallback classification.
    verified, verification_owner = _strong_verify_for_mode(args.mode, pg, candidate, product, args.archive)
    verified_tree = _require_verified_tree(args.mode, verified, expected_verification_tree)

    print(json.dumps({
        "mode": args.mode,
        "eligible": True,
        "archive_bytes": args.archive.stat().st_size,
        "archive_sha256": _sha256_file(args.archive),
        "tree_sha256": verified_tree,
        "research_tree_sha256": research_tree,
        "expected_verification_tree_sha256": expected_verification_tree,
        "verified_tree_sha256": verified_tree,
        "verification_identity_domain": verification_identity_domain,
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
