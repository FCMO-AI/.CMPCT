from __future__ import annotations

"""Fresh-process worker for exact canonical semantic-owner RSS attribution.

This supersedes the v1 candidate-phase worker for causal interpretation only.  V1 measured
``entropygraph_v030_prefixgraph_parallel`` as its isolated PrefixGraph arm, while the canonical shipping
candidate is explicitly rebound to the private canonical PrefixGraph clone.  This worker refuses that category
error: G0-G4 and PrefixGraph are obtained from ``canonical.RC`` and their object identity is asserted against the
private profile-isolation graph before any measurement.

Diagnostic only.  It changes no selector, admission, scheduling, grammar, recovery, locality or release state.
"""

import argparse
import hashlib
import json
from pathlib import Path
import resource
import time


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _imports():
    # Import the shipping facade and canonical graph before freezing the RSS baseline.
    from experiments import entropygraph_v030_canonical_final as canonical
    from experiments import entropygraph_v030_release_product as product
    return canonical, product


def _assert_semantic_owner_identity(canonical) -> dict:
    iso = canonical.PROFILE_ISOLATION
    if canonical.RC.PG is not iso.PG:
        raise RuntimeError("canonical RC.PG is not the private canonical PrefixGraph semantic owner")
    if canonical.RC.G04 is not iso.SHARED:
        raise RuntimeError("canonical RC.G04 is not the private canonical shared G0-G4 semantic owner")
    if canonical.RC.READER is not iso.POLICY:
        raise RuntimeError("canonical RC.READER is not the private canonical policy/reader owner")
    return {
        "rc_pg_module": canonical.RC.PG.__name__,
        "isolation_pg_module": iso.PG.__name__,
        "rc_g04_module": canonical.RC.G04.__name__,
        "isolation_g04_module": iso.SHARED.__name__,
        "rc_reader_module": canonical.RC.READER.__name__,
        "identity_exact": True,
    }


def _verification_identity(mode: str, source: Path, canonical) -> tuple[str, str, str]:
    research_tree = str(canonical.RC.treehash(source))
    if mode == "shipping":
        return research_tree, str(canonical.treehash(source)), "canonical-filesystem-user-tree-v1"
    return research_tree, research_tree, "research-content-tree-v1"


def _verify(mode: str, archive: Path, expected_tree: str, canonical, product) -> tuple[dict, str]:
    if mode == "shipping":
        result = dict(product.strong_verify(archive))
        owner = "release-product-dispatcher"
    else:
        # This is the exact private helper used by the canonical release-candidate tournament.
        result = dict(canonical.RC._verify_component(archive, expected_tree, f"isolated canonical {mode}"))
        owner = "canonical-private-release-candidate-reader"
    if not result.get("ok") or str(result.get("tree_sha256") or "") != expected_tree:
        raise RuntimeError(f"{mode} strong verification identity mismatch: {result!r}")
    return result, owner


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("shipping", "g04", "prefixgraph"), required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    args = parser.parse_args()

    canonical, product = _imports()
    semantic_owners = _assert_semantic_owner_identity(canonical)
    research_tree, expected_tree, identity_domain = _verification_identity(args.mode, args.source, canonical)

    if args.mode == "prefixgraph":
        eligible, reject_reason = canonical.RC._prefixgraph_eligibility(args.source, research_tree)
        if not eligible:
            print(json.dumps({
                "mode": args.mode,
                "eligible": False,
                "reject_reason": reject_reason,
                "research_tree_sha256": research_tree,
                "expected_verification_tree_sha256": expected_tree,
                "verification_identity_domain": identity_domain,
                "semantic_owners": semantic_owners,
            }, separators=(",", ":")), flush=True)
            return

    args.archive.parent.mkdir(parents=True, exist_ok=True)
    baseline_rss_kib = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    started = time.perf_counter()
    if args.mode == "shipping":
        stats = dict(product.build(args.source, args.archive))
    elif args.mode == "g04":
        stats = dict(canonical.RC.G04.build(args.source, args.archive))
    else:
        stats = dict(canonical.RC.PG.build(args.source, args.archive))
    wall_s = time.perf_counter() - started
    peak_rss_kib = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)

    verified, verification_owner = _verify(args.mode, args.archive, expected_tree, canonical, product)
    print(json.dumps({
        "mode": args.mode,
        "eligible": True,
        "archive_bytes": args.archive.stat().st_size,
        "archive_sha256": _sha256_file(args.archive),
        "tree_sha256": str(verified["tree_sha256"]),
        "research_tree_sha256": research_tree,
        "expected_verification_tree_sha256": expected_tree,
        "verified_tree_sha256": str(verified["tree_sha256"]),
        "verification_identity_domain": identity_domain,
        "wall_s": wall_s,
        "baseline_rss_kib": baseline_rss_kib,
        "peak_rss_kib": peak_rss_kib,
        "incremental_peak_rss_kib": max(0, peak_rss_kib - baseline_rss_kib),
        "selected": stats.get("selected"),
        "verification_owner": verification_owner,
        "semantic_owners": semantic_owners,
        "build_stats": stats,
    }, separators=(",", ":"), default=str), flush=True)


if __name__ == "__main__":
    main()
