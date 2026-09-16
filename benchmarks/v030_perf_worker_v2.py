from __future__ import annotations

"""Final-authority fresh-process worker for the v0.30 paired runtime gate.

The ordinary path is frozen release evidence. ``--diagnostic-sequential-r24`` is an explicitly non-credit
counterfactual used only by the authority adapter after the frozen run: it removes the r24/manifest overlap while
preserving candidate bytes and selection law, so we can test whether overlapping independent builders owns the
measured pack-RSS debt. The default operation/timing boundary is unchanged.
"""

import argparse
import json
from pathlib import Path
import resource
import shutil
import time


def _engine(name: str):
    if name == "v029":
        from experiments import entropygraph_v029_release as engine
    elif name == "v030":
        from experiments import entropygraph_v030_release_product as engine
    else:  # pragma: no cover
        raise ValueError(name)
    return engine


def _rss_kib() -> int:
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", choices=("v029", "v030"), required=True)
    parser.add_argument("--op", choices=("pack", "verify", "extract"), required=True)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--destination", type=Path)
    parser.add_argument("--diagnostic-sequential-r24", action="store_true")
    args = parser.parse_args()

    engine = _engine(args.engine)
    if args.diagnostic_sequential_r24:
        if args.engine != "v030" or args.op != "pack":
            raise SystemExit("--diagnostic-sequential-r24 is valid only for v030 pack")
        from experiments import entropygraph_v030_release_product_base as base
        # Research-only counterfactual: same builders/bytes/selection, but no r24 build overlaps manifest/r25 prep.
        base.C._prepare_profile_tree = base._ORIGINAL_PREPARE_PROFILE_TREE
        base.C._r24_build = engine._locality_bounded_r24_build

    started = time.perf_counter()
    if args.op == "pack":
        if args.source is None:
            raise SystemExit("--source required for pack")
        args.archive.parent.mkdir(parents=True, exist_ok=True)
        stats = engine.build(args.source, args.archive)
        operation_wall_s = time.perf_counter() - started
        operation_peak_rss_kib = _rss_kib()
        source_tree = engine.treehash(args.source)
        result = {"engine": args.engine,"op": args.op,"archive_bytes": args.archive.stat().st_size,"tree_sha256": source_tree,"build_stats": stats}
    elif args.op == "verify":
        verified = engine.strong_verify(args.archive)
        operation_wall_s = time.perf_counter() - started
        operation_peak_rss_kib = _rss_kib()
        if not verified.get("ok"):
            raise RuntimeError(f"{args.engine} strong verification failed: {verified!r}")
        result = {"engine": args.engine, "op": args.op, "tree_sha256": verified.get("tree_sha256"), "verify": verified}
    else:
        if args.destination is None:
            raise SystemExit("--destination required for extract")
        if args.destination.exists():
            shutil.rmtree(args.destination)
        engine.extract(args.archive, args.destination)
        operation_wall_s = time.perf_counter() - started
        operation_peak_rss_kib = _rss_kib()
        destination_tree = engine.treehash(args.destination)
        result = {"engine": args.engine, "op": args.op, "tree_sha256": destination_tree}

    result["wall_s"] = operation_wall_s
    result["peak_rss_kib"] = operation_peak_rss_kib
    result["diagnostic_sequential_r24"] = bool(args.diagnostic_sequential_r24)
    print(json.dumps(result, separators=(",", ":"), default=str), flush=True)


if __name__ == "__main__":
    main()
