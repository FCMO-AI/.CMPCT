from __future__ import annotations

"""Final-authority fresh-process worker for the v0.30 paired runtime gate.

The v0.29 side remains the accepted historical release baseline.  The v0.30 side must exercise the one promoted
product front door, ``entropygraph_v030_release_product``: that surface owns canonical r24/r25 selection, the
current bounded/ordered Geometry scheduler, revision-25 filesystem semantics, and exact r24 fallback.  Benchmarking
the demoted ``entropygraph_v030_authoritative`` research facade would measure a historical convergence adapter
that the release itself does not ship and would therefore make runtime evidence non-authoritative.
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
    args = parser.parse_args()

    engine = _engine(args.engine)
    started = time.perf_counter()
    if args.op == "pack":
        if args.source is None:
            raise SystemExit("--source required for pack")
        args.archive.parent.mkdir(parents=True, exist_ok=True)
        stats = engine.build(args.source, args.archive)
        result = {
            "engine": args.engine,
            "op": args.op,
            "archive_bytes": args.archive.stat().st_size,
            "tree_sha256": engine.treehash(args.source),
            "build_stats": stats,
        }
    elif args.op == "verify":
        verified = engine.strong_verify(args.archive)
        if not verified.get("ok"):
            raise RuntimeError(f"{args.engine} strong verification failed: {verified!r}")
        result = {"engine": args.engine, "op": args.op, "tree_sha256": verified.get("tree_sha256"), "verify": verified}
    else:
        if args.destination is None:
            raise SystemExit("--destination required for extract")
        if args.destination.exists():
            shutil.rmtree(args.destination)
        engine.extract(args.archive, args.destination)
        result = {"engine": args.engine, "op": args.op, "tree_sha256": engine.treehash(args.destination)}

    result["wall_s"] = time.perf_counter() - started
    result["peak_rss_kib"] = _rss_kib()
    print(json.dumps(result, separators=(",", ":"), default=str), flush=True)


if __name__ == "__main__":
    main()
