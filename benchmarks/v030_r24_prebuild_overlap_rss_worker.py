from __future__ import annotations

"""Fresh-process pack worker for the r24-prebuild overlap RSS oracle.

This worker exists only to separate scheduling from format semantics. ``shipping`` uses the promoted v0.30 product
unchanged. ``serial-r24`` imports that same product and then restores the canonical profile-tree preparation and
r24 builder to serial ordering before the first build. The two modes therefore exercise identical archive grammar,
selection, integrity and publication logic while differing only in whether r24 compression overlaps profile-tree
manifest capture.
"""

import argparse
import hashlib
import json
from pathlib import Path
import resource
import time


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _engine(mode: str):
    from experiments import entropygraph_v030_release_product as product

    if mode == "serial-r24":
        from experiments import entropygraph_v030_release_product_base as base

        if base._R24_PREBUILDS:
            raise RuntimeError("serial-r24 oracle imported with an unexpected in-flight r24 prebuild")
        base.C._prepare_profile_tree = base._ORIGINAL_PREPARE_PROFILE_TREE
        base.C._r24_build = base._locality_bounded_r24_build
    elif mode != "shipping":  # pragma: no cover
        raise ValueError(mode)
    return product


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("shipping", "serial-r24"), required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    args = parser.parse_args()

    engine = _engine(args.mode)
    args.archive.parent.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    stats = dict(engine.build(args.source, args.archive))
    wall_s = time.perf_counter() - started
    peak_rss_kib = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)

    # Correctness evidence is deliberately outside the operation timer but mandatory.
    tree = engine.treehash(args.source)
    verified = dict(engine.strong_verify(args.archive))
    if not verified.get("ok") or verified.get("tree_sha256") != tree:
        raise RuntimeError(f"{args.mode} archive failed strong verification: {verified!r}")

    print(json.dumps({
        "mode": args.mode,
        "archive_bytes": args.archive.stat().st_size,
        "archive_sha256": _sha256_file(args.archive),
        "tree_sha256": tree,
        "wall_s": wall_s,
        "peak_rss_kib": peak_rss_kib,
        "build_stats": stats,
    }, separators=(",", ":"), default=str), flush=True)


if __name__ == "__main__":
    main()
