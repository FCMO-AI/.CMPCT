from __future__ import annotations

"""Fresh-process worker for the r25 complete-candidate overlap RSS oracle.

``shipping`` leaves the promoted release-product scheduler untouched. ``serial-r25`` replaces only the
release-candidate module's two-way executor with an in-process sequential executor before the first build.
G0-G4 and PrefixGraph therefore keep their exact builders, bytes, integrity checks, locality rules and selector;
only their *inter-candidate* overlap changes. Internal bounded parallelism inside either candidate is unchanged.
"""

import argparse
from concurrent.futures import Future
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


class _SequentialExecutor:
    """Minimal ThreadPoolExecutor-compatible context used only by this research A/B."""

    def __init__(self, *args, **kwargs):
        self._shutdown = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.shutdown()
        return False

    def submit(self, fn, /, *args, **kwargs):
        if self._shutdown:
            raise RuntimeError("sequential oracle executor already shut down")
        future: Future = Future()
        try:
            future.set_result(fn(*args, **kwargs))
        except BaseException as exc:  # preserve Future.result() exception semantics
            future.set_exception(exc)
        return future

    def shutdown(self, wait=True, *, cancel_futures=False):
        self._shutdown = True


def _engine(mode: str):
    from experiments import entropygraph_v030_release_candidate as candidate
    from experiments import entropygraph_v030_release_product as product

    if mode == "serial-r25":
        candidate.ThreadPoolExecutor = _SequentialExecutor
    elif mode != "shipping":  # pragma: no cover
        raise ValueError(mode)
    return product


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("shipping", "serial-r25"), required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    args = parser.parse_args()

    engine = _engine(args.mode)
    args.archive.parent.mkdir(parents=True, exist_ok=True)
    baseline_rss_kib = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    started = time.perf_counter()
    stats = dict(engine.build(args.source, args.archive))
    wall_s = time.perf_counter() - started
    peak_rss_kib = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)

    # Correctness evidence is mandatory but intentionally outside the operation timer.
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
        "baseline_rss_kib": baseline_rss_kib,
        "peak_rss_kib": peak_rss_kib,
        "incremental_peak_rss_kib": max(0, peak_rss_kib - baseline_rss_kib),
        "selected": stats.get("selected"),
        "r25_selected": (stats.get("r25") or {}).get("selected"),
        "r25_candidate_scheduler": (stats.get("r25") or {}).get("candidate_build_scheduler"),
        "build_stats": stats,
    }, separators=(",", ":"), default=str), flush=True)


if __name__ == "__main__":
    main()
