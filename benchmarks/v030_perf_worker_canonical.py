from __future__ import annotations

"""Fresh-process runtime worker for the canonical v0.30/r25 release bytes."""

import argparse
import hashlib
import json
from pathlib import Path
import resource
import shutil
import time


def _engine(name: str):
    if name == "v029":
        from experiments import entropygraph_v029_release as engine
    elif name == "v030":
        from experiments import entropygraph_v030_canonical as engine
    else:  # pragma: no cover
        raise ValueError(name)
    return engine


def _rss_kib() -> int:
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", choices=("v029", "v030"), required=True)
    parser.add_argument("--op", choices=("pack", "verify", "extract", "member"), required=True)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--destination", type=Path)
    parser.add_argument("--member")
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
    elif args.op == "extract":
        if args.destination is None:
            raise SystemExit("--destination required for extract")
        if args.destination.exists():
            shutil.rmtree(args.destination)
        engine.extract(args.archive, args.destination)
        result = {"engine": args.engine, "op": args.op, "tree_sha256": engine.treehash(args.destination)}
    else:
        if args.engine != "v030":
            raise SystemExit("selective member operation is defined only for the promoted v0.30 member-reader surface")
        if not args.member:
            raise SystemExit("--member required for member operation")
        from experiments import entropygraph_v030_member_reader as member_reader

        raw, stats = member_reader.read_member(args.archive, args.member, with_stats=True)
        result = {
            "engine": args.engine,
            "op": args.op,
            "member": args.member,
            "member_bytes": len(raw),
            "member_sha256": hashlib.sha256(raw).hexdigest(),
            "member_stats": stats,
        }
        # Footnote: the member reader is intentionally invoked only after importing the canonical engine above.
        # That import installs the revision-25 profile magics before the bounded reader probes the archive, so
        # this timing measures the actual promoted read path rather than a research-magic compatibility shim.

    result["wall_s"] = time.perf_counter() - started
    result["peak_rss_kib"] = _rss_kib()
    print(json.dumps(result, separators=(",", ":"), default=str), flush=True)


if __name__ == "__main__":
    main()
