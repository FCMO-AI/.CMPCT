from __future__ import annotations

"""Fresh-process worker used by the v0.30 runtime promotion gate.

Each invocation performs exactly one operation so Python allocator state, imports and previous decoder caches do
not leak across v0.29/v0.30 measurements.  Linux ``ru_maxrss`` is recorded alongside wall time.  The parent
harness owns balanced ordering and exact source-tree validation.

Footnote: this worker prints one JSON object to stdout and no benchmark conclusion.  Thresholds live only in
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
        # Preserve the frozen timing envelope: this post-build treehash remains inside the measured operation
        # exactly as before. It is diagnostic, however, not allowed to retroactively redefine the source identity
        # that the writer captured before construction and then authenticated through its selected archive.
        post_build_tree = engine.treehash(args.source)
        writer_tree = stats.get("tree_sha256") if isinstance(stats, dict) else None
        if not isinstance(writer_tree, str) or len(writer_tree) != 64:
            writer_tree = post_build_tree
        result = {
            "engine": args.engine,
            "op": args.op,
            "archive_bytes": args.archive.stat().st_size,
            "tree_sha256": writer_tree,
            "post_build_source_tree_sha256": post_build_tree,
            "build_stats": stats,
        }
    elif args.op == "verify":
        verified = engine.strong_verify(args.archive)
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
        engine.extract(args.archive, args.destination)
        result = {
            "engine": args.engine,
            "op": args.op,
            "tree_sha256": engine.treehash(args.destination),
        }

    result["wall_s"] = time.perf_counter() - started
    result["peak_rss_kib"] = _rss_kib()
    print(json.dumps(result, separators=(",", ":"), default=str), flush=True)


if __name__ == "__main__":
    main()
