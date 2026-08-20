from __future__ import annotations

"""Fresh-process worker used by the v0.30 runtime promotion gate.

Each invocation performs exactly one operation so Python allocator state, imports and previous decoder caches do
not leak across v0.29/v0.30 measurements. Linux ``ru_maxrss`` is recorded alongside wall time. The parent
harness owns balanced ordering and exact source-tree validation.

Timing covers the requested archive operation only. Source/destination identity hashing and result assembly are
mandatory correctness evidence but run outside the timed interval; otherwise different reader/hash surfaces can
silently contaminate a pack/extract comparison. Pack captures source identity before calling the writer so a
writer that changes module-global profile state cannot retroactively change the identity of the bytes it was
asked to encode.

Footnote: this worker prints one JSON object to stdout and no benchmark conclusion. Thresholds live only in
the parent harness, preventing a worker implementation change from silently redefining release policy.
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
        from experiments import entropygraph_v030_release as engine
    else:  # pragma: no cover - argparse constrains this.
        raise ValueError(name)
    return engine


def _rss_kib() -> int:
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)


def _timed(callable_):
    started = time.perf_counter()
    value = callable_()
    return value, time.perf_counter() - started


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", choices=("v029", "v030"), required=True)
    parser.add_argument("--op", choices=("pack", "verify", "extract"), required=True)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--destination", type=Path)
    args = parser.parse_args()

    engine = _engine(args.engine)
    if args.op == "pack":
        if args.source is None:
            raise SystemExit("--source required for pack")
        args.archive.parent.mkdir(parents=True, exist_ok=True)
        # Capture the source identity before writer execution. Some historical/research modules can alter private
        # profile dispatch while constructing an artifact; that must never redefine the source identity after the
        # fact. The parent already independently checks this identity against the frozen workload manifest.
        source_tree = engine.treehash(args.source)
        stats, wall_s = _timed(lambda: engine.build(args.source, args.archive))
        result = {
            "engine": args.engine,
            "op": args.op,
            "archive_bytes": args.archive.stat().st_size,
            "tree_sha256": source_tree,
            "build_stats": stats,
        }
    elif args.op == "verify":
        verified, wall_s = _timed(lambda: engine.strong_verify(args.archive))
        if not verified.get("ok"):
            raise RuntimeError(f"{args.engine} strong verification failed: {verified!r}")
        result = {
            "engine": args.engine,
            "op": args.op,
            "tree_sha256": verified.get("tree_sha256"),
            "verify": verified,
        }
    else:
        if args.destination is None:
            raise SystemExit("--destination required for extract")
        if args.destination.exists():
            shutil.rmtree(args.destination)
        _, wall_s = _timed(lambda: engine.extract(args.archive, args.destination))
        # Exact-tree validation remains mandatory, but it is evidence about the completed extraction rather than
        # part of extraction throughput. Keeping it outside the timer also makes v0.29/v0.30 comparisons symmetric
        # when their internal tree-verification implementations differ.
        result = {
            "engine": args.engine,
            "op": args.op,
            "tree_sha256": engine.treehash(args.destination),
        }

    result["wall_s"] = wall_s
    result["peak_rss_kib"] = _rss_kib()
    print(json.dumps(result, separators=(",", ":"), default=str), flush=True)


if __name__ == "__main__":
    main()
