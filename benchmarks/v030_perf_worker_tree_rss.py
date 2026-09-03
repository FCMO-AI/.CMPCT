from __future__ import annotations

"""Whole-process-tree RSS worker for the v0.30 paired runtime custody companion.

Operation semantics and timing match ``v030_perf_worker_v2.py``.  The sole stronger evidence boundary is memory:
a 10 ms sampler charges the worker plus every live descendant while the requested pack/verify/extract operation is
active, then stops before post-operation source/destination tree hashing.  Parent RUSAGE_SELF ru_maxrss remains a
floor, so this companion can never report less memory than the inherited worker merely because sampling missed a
short parent allocation.
"""

import argparse
import json
import os
from pathlib import Path
import resource
import shutil
import threading
import time

SAMPLE_INTERVAL_S = 0.01
RSS_ACCOUNTING = "whole-process-tree-vmrss-10ms-with-parent-rumaxrss-floor"


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


def _pid_vmrss_kib(pid: int) -> int:
    try:
        text = Path(f"/proc/{pid}/status").read_text()
    except (FileNotFoundError, ProcessLookupError, PermissionError):
        return 0
    for line in text.splitlines():
        if line.startswith("VmRSS:"):
            try:
                return int(line.split()[1])
            except (IndexError, ValueError):
                return 0
    return 0


def _children(pid: int) -> list[int]:
    try:
        raw = Path(f"/proc/{pid}/task/{pid}/children").read_text().strip()
    except (FileNotFoundError, ProcessLookupError, PermissionError):
        return []
    out: list[int] = []
    for token in raw.split():
        try:
            out.append(int(token))
        except ValueError:
            pass
    return out


def _tree_rss_kib(root_pid: int) -> tuple[int, int]:
    total = 0
    count = 0
    queue = [root_pid]
    seen: set[int] = set()
    while queue:
        pid = queue.pop()
        if pid in seen:
            continue
        seen.add(pid)
        rss = _pid_vmrss_kib(pid)
        if rss:
            total += rss
            count += 1
        queue.extend(_children(pid))
    return total, count


class _TreeSampler:
    def __init__(self) -> None:
        self.stop_event = threading.Event()
        self.thread: threading.Thread | None = None
        self.samples = 0
        self.peak_kib = 0
        self.peak_processes = 0
        self.errors: list[str] = []

    def start(self) -> None:
        root = os.getpid()

        def run() -> None:
            while not self.stop_event.is_set():
                try:
                    rss, processes = _tree_rss_kib(root)
                    self.samples += 1
                    if rss > self.peak_kib:
                        self.peak_kib = rss
                        self.peak_processes = processes
                except Exception as exc:  # evidence sampling must not perturb product semantics
                    self.errors.append(f"{type(exc).__name__}:{exc}")
                self.stop_event.wait(SAMPLE_INTERVAL_S)
            try:
                rss, processes = _tree_rss_kib(root)
                self.samples += 1
                if rss > self.peak_kib:
                    self.peak_kib = rss
                    self.peak_processes = processes
            except Exception as exc:
                self.errors.append(f"final:{type(exc).__name__}:{exc}")

        self.thread = threading.Thread(target=run, name="cmpct-release-tree-rss-sampler", daemon=True)
        self.thread.start()

    def stop(self) -> None:
        self.stop_event.set()
        if self.thread is not None:
            self.thread.join(timeout=5.0)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", choices=("v029", "v030"), required=True)
    parser.add_argument("--op", choices=("pack", "verify", "extract"), required=True)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--destination", type=Path)
    args = parser.parse_args()

    engine = _engine(args.engine)
    sampler = _TreeSampler()
    sampler.start()
    started = time.perf_counter()
    try:
        if args.op == "pack":
            if args.source is None:
                raise SystemExit("--source required for pack")
            args.archive.parent.mkdir(parents=True, exist_ok=True)
            stats = engine.build(args.source, args.archive)
            result = {
                "engine": args.engine,
                "op": args.op,
                "archive_bytes": args.archive.stat().st_size,
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
            result = {"engine": args.engine, "op": args.op}
        operation_wall_s = time.perf_counter() - started
        parent_peak_rss_kib = _rss_kib()
    finally:
        sampler.stop()

    decisive_peak = max(parent_peak_rss_kib, sampler.peak_kib)

    # Correctness hashing remains outside the frozen operation clock and outside the decisive sampled operation
    # interval, exactly matching the canonical v2 worker's evidence/timing split.
    if args.op == "pack":
        source_tree = engine.treehash(args.source)
        result["tree_sha256"] = source_tree
    elif args.op == "extract":
        result["tree_sha256"] = engine.treehash(args.destination)

    result["wall_s"] = operation_wall_s
    result["peak_rss_kib"] = decisive_peak
    result["parent_peak_rss_kib"] = parent_peak_rss_kib
    result["sampled_tree_peak_rss_kib"] = sampler.peak_kib
    result["tree_rss_samples"] = sampler.samples
    result["tree_peak_processes"] = sampler.peak_processes
    result["tree_sampler_errors"] = sampler.errors
    result["sample_interval_s"] = SAMPLE_INTERVAL_S
    result["rss_accounting"] = RSS_ACCOUNTING
    print(json.dumps(result, separators=(",", ":"), default=str), flush=True)


if __name__ == "__main__":
    main()
