from __future__ import annotations

"""Fresh-process Shifted RSS worker for r24 process-lifetime attribution."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import pickle
import resource
import subprocess
import sys
import time

from benchmarks import v030_r25_parent_phase_rss_worker as RSS

ROOT = Path(__file__).resolve().parents[1]
SELF = Path(__file__).resolve()


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class _ImmediateFuture:
    def __init__(self, value):
        self._value = value

    def result(self):
        return self._value


class _InlineOuterExecutor:
    def __init__(self, canonical):
        self.canonical = canonical
        self.submissions = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def submit(self, fn, *args, **kwargs):
        self.submissions += 1
        if kwargs or self.submissions > 2:
            raise RuntimeError("unexpected outer-product submission shape")
        if self.submissions == 1 and fn is not self.canonical._r24_build:
            raise RuntimeError("outer-product first submission is not exact canonical r24")
        if self.submissions == 2 and fn is not self.canonical._r25_build:
            raise RuntimeError("outer-product second submission is not exact canonical r25")
        return _ImmediateFuture(fn(*args))


class _ChildState:
    launches = 0
    returncodes: list[int] = []
    peaks_kib: list[int] = []
    walls_s: list[float] = []


def _child_env() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    return env


def _run_r24_child(root: Path, archive: Path) -> dict:
    stats_path = archive.with_suffix(archive.suffix + ".r24-stats.pickle")
    cmd = [
        sys.executable,
        str(SELF),
        "--child-r24",
        "--source", str(root),
        "--archive", str(archive),
        "--stats-pickle", str(stats_path),
    ]
    started = time.perf_counter()
    proc = subprocess.run(cmd, cwd=ROOT, env=_child_env(), capture_output=True, text=True)
    elapsed = time.perf_counter() - started
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    if proc.returncode or not lines or not stats_path.is_file():
        raise RuntimeError(
            f"isolated r24 child failed rc={proc.returncode} stdout={proc.stdout!r} stderr={proc.stderr!r}"
        )
    receipt = json.loads(lines[-1])
    if receipt.get("kind") != "canonical-r24" or receipt.get("archive_sha256") != _sha(archive):
        raise RuntimeError("isolated r24 child identity mismatch")
    with stats_path.open("rb") as stream:
        stats = pickle.load(stream)
    stats_path.unlink(missing_ok=True)
    _ChildState.launches += 1
    _ChildState.returncodes.append(int(proc.returncode))
    _ChildState.peaks_kib.append(int(receipt["peak_ru_maxrss_kib"]))
    _ChildState.walls_s.append(float(receipt["wall_s"]))
    if elapsed < float(receipt["wall_s"]):
        raise RuntimeError("isolated r24 parent wall clock shorter than child receipt")
    return stats


class _ChildR24ThenInlineExecutor(_InlineOuterExecutor):
    def submit(self, fn, *args, **kwargs):
        self.submissions += 1
        if kwargs or self.submissions > 2:
            raise RuntimeError("unexpected outer-product submission shape")
        if self.submissions == 1:
            if fn is not self.canonical._r24_build or len(args) != 2:
                raise RuntimeError("isolated outer first submission is not exact canonical r24")
            return _ImmediateFuture(_run_r24_child(Path(args[0]), Path(args[1])))
        if fn is not self.canonical._r25_build:
            raise RuntimeError("isolated outer second submission is not exact canonical r25")
        return _ImmediateFuture(fn(*args))


class _RoutingExecutor:
    original = None
    canonical = None
    mode = ""
    outer_intercepts = 0
    delegated = 0
    outer_instance = None

    def __new__(cls, *args, **kwargs):
        prefix = kwargs.get("thread_name_prefix")
        if prefix == "cmpct-v030-product":
            cls.outer_intercepts += 1
            if cls.outer_intercepts != 1:
                raise RuntimeError("outer-product executor intercepted more than once")
            if cls.mode == "same-parent-serialized":
                cls.outer_instance = _InlineOuterExecutor(cls.canonical)
            elif cls.mode == "r24-child-serialized":
                cls.outer_instance = _ChildR24ThenInlineExecutor(cls.canonical)
            else:
                raise RuntimeError(f"unexpected routed mode: {cls.mode}")
            return cls.outer_instance
        cls.delegated += 1
        return cls.original(*args, **kwargs)


def _child_r24(source: Path, archive: Path, stats_pickle: Path) -> None:
    from experiments import entropygraph_v030_canonical_final as canonical

    started = time.perf_counter()
    stats = canonical._r24_build(source, archive)
    wall = time.perf_counter() - started
    stats_pickle.parent.mkdir(parents=True, exist_ok=True)
    with stats_pickle.open("wb") as stream:
        pickle.dump(stats, stream, protocol=pickle.HIGHEST_PROTOCOL)
    print(json.dumps({
        "kind": "canonical-r24",
        "archive_bytes": archive.stat().st_size,
        "archive_sha256": _sha(archive),
        "wall_s": wall,
        "peak_ru_maxrss_kib": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
    }, separators=(",", ":")), flush=True)


def _run(mode: str, source: Path, archive: Path) -> None:
    from experiments import entropygraph_v030_canonical_final as canonical
    from experiments import entropygraph_v030_release_product as product

    iso = canonical.PROFILE_ISOLATION
    if canonical.RC.PG is not iso.PG or canonical.RC.G04 is not iso.SHARED or canonical.RC.READER is not iso.POLICY:
        raise RuntimeError("canonical semantic-owner identity mismatch")
    if mode not in {"inherited", "same-parent-serialized", "r24-child-serialized"}:
        raise ValueError(mode)

    source_tree = str(product.treehash(source))
    original_executor = canonical.ThreadPoolExecutor
    _RoutingExecutor.original = original_executor
    _RoutingExecutor.canonical = canonical
    _RoutingExecutor.mode = mode
    _RoutingExecutor.outer_intercepts = _RoutingExecutor.delegated = 0
    _RoutingExecutor.outer_instance = None
    _ChildState.launches = 0
    _ChildState.returncodes = []
    _ChildState.peaks_kib = []
    _ChildState.walls_s = []

    sampler = RSS._TreeSampler(0.01)
    sampler.start()
    try:
        if mode != "inherited":
            canonical.ThreadPoolExecutor = _RoutingExecutor
        started = time.perf_counter()
        stats = dict(product.build(source, archive))
        wall = time.perf_counter() - started
        parent_peak = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    finally:
        sampler.stop()
        canonical.ThreadPoolExecutor = original_executor

    verified = dict(product.strong_verify(archive))
    if not verified.get("ok") or str(verified.get("tree_sha256")) != source_tree:
        raise RuntimeError("final independent strong verification mismatch")
    if mode == "inherited":
        if _RoutingExecutor.outer_intercepts != 0 or _ChildState.launches != 0:
            raise RuntimeError("inherited arm unexpectedly altered product scheduling")
        outer_submissions = None
    else:
        if _RoutingExecutor.outer_intercepts != 1 or _RoutingExecutor.outer_instance is None:
            raise RuntimeError("diagnostic outer executor lifecycle mismatch")
        outer_submissions = int(_RoutingExecutor.outer_instance.submissions)
        if outer_submissions != 2:
            raise RuntimeError("diagnostic outer executor did not execute both exact candidates")
        expected_children = 1 if mode == "r24-child-serialized" else 0
        if _ChildState.launches != expected_children:
            raise RuntimeError("r24 child lifecycle mismatch")

    print(json.dumps({
        "mode": mode,
        "archive_bytes": archive.stat().st_size,
        "archive_sha256": _sha(archive),
        "selected": stats.get("selected"),
        "format_revision": stats.get("format_revision"),
        "r24_product_bytes": stats.get("r24_product_bytes"),
        "r25_product_bytes": stats.get("r25_product_bytes"),
        "tree_sha256": str(verified.get("tree_sha256")),
        "expected_verification_tree_sha256": source_tree,
        "wall_s": wall,
        "parent_peak_ru_maxrss_kib": parent_peak,
        "tree_peak_rss_kib": sampler.peak_kib,
        "tree_peak_processes": sampler.peak_processes,
        "tree_samples": sampler.samples,
        "tree_sampler_errors": sampler.errors,
        "tree_sampler_interval_s": sampler.interval_s,
        "outer_executor_intercepts": _RoutingExecutor.outer_intercepts,
        "outer_submissions": outer_submissions,
        "delegated_executors": _RoutingExecutor.delegated,
        "r24_child_launches": _ChildState.launches,
        "r24_child_returncodes": _ChildState.returncodes,
        "r24_child_peak_ru_maxrss_kib": _ChildState.peaks_kib,
        "r24_child_wall_s": _ChildState.walls_s,
        "all_wrappers_restored": canonical.ThreadPoolExecutor is original_executor,
        "semantic_owners": {
            "pg": canonical.RC.PG.__name__,
            "g04": canonical.RC.G04.__name__,
            "reader": canonical.RC.READER.__name__,
            "identity_exact": True,
        },
    }, separators=(",", ":"), default=str), flush=True)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=("inherited", "same-parent-serialized", "r24-child-serialized"))
    p.add_argument("--child-r24", action="store_true")
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--archive", type=Path, required=True)
    p.add_argument("--stats-pickle", type=Path)
    a = p.parse_args()
    if a.child_r24:
        if a.stats_pickle is None:
            raise SystemExit("--stats-pickle required for child-r24")
        _child_r24(a.source, a.archive, a.stats_pickle)
    else:
        if a.mode is None:
            raise SystemExit("--mode required")
        _run(a.mode, a.source, a.archive)


if __name__ == "__main__":
    main()
