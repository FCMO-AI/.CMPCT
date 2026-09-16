from __future__ import annotations

"""Fresh-process worker for frozen PrefixGraph process-isolation RSS attribution."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[1]


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


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
    if not raw:
        return []
    out: list[int] = []
    for token in raw.split():
        try:
            out.append(int(token))
        except ValueError:
            continue
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
    def __init__(self, interval_s: float = 0.01):
        self.interval_s = interval_s
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
                except Exception as exc:  # diagnostic sampler must never perturb product execution
                    self.errors.append(f"{type(exc).__name__}:{exc}")
                self.stop_event.wait(self.interval_s)
            try:
                rss, processes = _tree_rss_kib(root)
                self.samples += 1
                if rss > self.peak_kib:
                    self.peak_kib = rss
                    self.peak_processes = processes
            except Exception as exc:
                self.errors.append(f"final:{type(exc).__name__}:{exc}")

        self.thread = threading.Thread(target=run, name="cmpct-rss-tree-sampler", daemon=True)
        self.thread.start()

    def stop(self) -> None:
        self.stop_event.set()
        if self.thread is not None:
            self.thread.join(timeout=5.0)


class _ImmediateFuture:
    def __init__(self, value):
        self._value = value

    def result(self):
        return self._value


class _IsolatedPrefixGraphExecutor:
    submissions = 0
    children_launched = 0
    child_returncodes: list[int] = []
    child_wall_s: list[float] = []
    child_archive_bytes: list[int] = []
    child_archive_sha256: list[str] = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def submit(self, fn, *args, **kwargs):
        type(self).submissions += 1
        if type(self).submissions != 1:
            raise RuntimeError("frozen isolated PrefixGraph executor received more than one submission")
        if len(args) < 2 or kwargs:
            raise RuntimeError("unexpected PrefixGraph build call shape at frozen isolation seam")
        source = Path(args[0])
        archive = Path(args[1])
        env = os.environ.copy()
        env["PYTHONPATH"] = str(ROOT) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
        cmd = [
            sys.executable,
            str(Path(__file__).resolve()),
            "--child-prefixgraph",
            "--source", str(source),
            "--archive", str(archive),
        ]
        started = time.perf_counter()
        proc = subprocess.Popen(cmd, cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        type(self).children_launched += 1
        stdout, stderr = proc.communicate()
        elapsed = time.perf_counter() - started
        type(self).child_returncodes.append(int(proc.returncode))
        type(self).child_wall_s.append(elapsed)
        lines = [line for line in stdout.splitlines() if line.strip()]
        if proc.returncode or not lines:
            raise RuntimeError(
                f"isolated PrefixGraph child failed rc={proc.returncode} stdout={stdout!r} stderr={stderr!r}"
            )
        try:
            payload = json.loads(lines[-1])
        except Exception as exc:
            raise RuntimeError(f"isolated PrefixGraph child emitted invalid JSON: {exc}: {stdout!r}") from exc
        if payload.get("semantic_owner_exact") is not True:
            raise RuntimeError(f"isolated child semantic-owner mismatch: {payload!r}")
        if not archive.is_file() or int(payload.get("archive_bytes", -1)) != archive.stat().st_size:
            raise RuntimeError("isolated child archive accounting mismatch")
        if payload.get("archive_sha256") != _sha(archive):
            raise RuntimeError("isolated child archive SHA mismatch")
        type(self).child_archive_bytes.append(archive.stat().st_size)
        type(self).child_archive_sha256.append(payload["archive_sha256"])
        return _ImmediateFuture(payload["stats"])


class _RoutingExecutor:
    original = None
    intercepted_constructions = 0
    delegated_constructions = 0

    def __new__(cls, *args, **kwargs):
        prefix = kwargs.get("thread_name_prefix")
        if prefix == "cmpct-v030-prefixgraph":
            cls.intercepted_constructions += 1
            return _IsolatedPrefixGraphExecutor()
        cls.delegated_constructions += 1
        return cls.original(*args, **kwargs)


def _child_prefixgraph(source: Path, archive: Path) -> None:
    from experiments import entropygraph_v030_canonical_final as canonical

    iso = canonical.PROFILE_ISOLATION
    if canonical.RC.PG is not iso.PG:
        raise RuntimeError("child PrefixGraph semantic-owner identity mismatch")
    started = time.perf_counter()
    stats = dict(canonical.RC.PG.build(source, archive))
    print(json.dumps({
        "semantic_owner_exact": True,
        "semantic_owner": canonical.RC.PG.__name__,
        "archive_bytes": archive.stat().st_size,
        "archive_sha256": _sha(archive),
        "wall_s": time.perf_counter() - started,
        "peak_ru_maxrss_kib": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
        "stats": stats,
    }, separators=(",", ":"), default=str), flush=True)


def _reset_intervention_state() -> None:
    _IsolatedPrefixGraphExecutor.submissions = 0
    _IsolatedPrefixGraphExecutor.children_launched = 0
    _IsolatedPrefixGraphExecutor.child_returncodes = []
    _IsolatedPrefixGraphExecutor.child_wall_s = []
    _IsolatedPrefixGraphExecutor.child_archive_bytes = []
    _IsolatedPrefixGraphExecutor.child_archive_sha256 = []
    _RoutingExecutor.intercepted_constructions = 0
    _RoutingExecutor.delegated_constructions = 0


def _parent(mode: str, source: Path, archive: Path) -> None:
    from experiments import entropygraph_v030_canonical_final as canonical
    from experiments import entropygraph_v030_release_product as product

    iso = canonical.PROFILE_ISOLATION
    if canonical.RC.PG is not iso.PG or canonical.RC.G04 is not iso.SHARED or canonical.RC.READER is not iso.POLICY:
        raise RuntimeError("canonical semantic-owner identity mismatch")

    source_tree = str(product.treehash(source))
    research_tree = str(canonical.RC.treehash(source))
    eligible, reason = canonical.RC._prefixgraph_eligibility(source, research_tree)
    if not eligible:
        raise RuntimeError(f"preregistered Shifted target unexpectedly PrefixGraph-ineligible: {reason}")

    _reset_intervention_state()
    original_executor = canonical.ThreadPoolExecutor
    _RoutingExecutor.original = original_executor
    if mode == "isolated-serialized-pg":
        canonical.ThreadPoolExecutor = _RoutingExecutor

    sampler = _TreeSampler(interval_s=0.01)
    baseline_ru = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    sampler.start()
    try:
        started = time.perf_counter()
        stats = dict(product.build(source, archive))
        wall = time.perf_counter() - started
        peak_ru = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    finally:
        sampler.stop()
        canonical.ThreadPoolExecutor = original_executor

    verify = dict(product.strong_verify(archive))
    verified_tree = str(verify.get("tree_sha256") or "")
    if not verify.get("ok") or verified_tree != source_tree:
        raise RuntimeError(f"shipping strong verification mismatch: expected={source_tree} actual={verified_tree}")
    if stats.get("r24_product_bytes") is None or stats.get("r25_product_bytes") is None:
        raise RuntimeError("outer tournament did not price both complete products")

    if mode == "isolated-serialized-pg":
        if _RoutingExecutor.intercepted_constructions != 1 or _IsolatedPrefixGraphExecutor.submissions != 1:
            raise RuntimeError("frozen process-isolation seam was not exercised exactly once")
        if _IsolatedPrefixGraphExecutor.children_launched != 1 or _IsolatedPrefixGraphExecutor.child_returncodes != [0]:
            raise RuntimeError("isolated PrefixGraph child lifecycle mismatch")
    else:
        if _RoutingExecutor.intercepted_constructions or _IsolatedPrefixGraphExecutor.submissions:
            raise RuntimeError("shipping control unexpectedly exercised process-isolation route")

    print(json.dumps({
        "mode": mode,
        "archive_bytes": archive.stat().st_size,
        "archive_sha256": _sha(archive),
        "selected": stats.get("selected"),
        "format_revision": stats.get("format_revision"),
        "r24_product_bytes": stats.get("r24_product_bytes"),
        "r25_product_bytes": stats.get("r25_product_bytes"),
        "tree_sha256": verified_tree,
        "expected_verification_tree_sha256": source_tree,
        "research_tree_sha256": research_tree,
        "verification_identity_domain": "canonical-filesystem-user-tree-v1",
        "research_identity_domain": "research-content-tree-v1",
        "wall_s": wall,
        "baseline_parent_ru_maxrss_kib": baseline_ru,
        "parent_peak_ru_maxrss_kib": peak_ru,
        "tree_peak_rss_kib": sampler.peak_kib,
        "tree_peak_processes": sampler.peak_processes,
        "tree_samples": sampler.samples,
        "tree_sampler_errors": sampler.errors,
        "tree_sampler_interval_s": sampler.interval_s,
        "intercepted_prefixgraph_executor_constructions": _RoutingExecutor.intercepted_constructions,
        "intercepted_prefixgraph_submissions": _IsolatedPrefixGraphExecutor.submissions,
        "isolated_children_launched": _IsolatedPrefixGraphExecutor.children_launched,
        "isolated_child_returncodes": _IsolatedPrefixGraphExecutor.child_returncodes,
        "isolated_child_wall_s": _IsolatedPrefixGraphExecutor.child_wall_s,
        "isolated_child_archive_bytes": _IsolatedPrefixGraphExecutor.child_archive_bytes,
        "isolated_child_archive_sha256": _IsolatedPrefixGraphExecutor.child_archive_sha256,
        "delegated_executor_constructions": _RoutingExecutor.delegated_constructions,
        "executor_restored": canonical.ThreadPoolExecutor is original_executor,
        "semantic_owners": {
            "pg": canonical.RC.PG.__name__,
            "g04": canonical.RC.G04.__name__,
            "reader": canonical.RC.READER.__name__,
            "identity_exact": True,
        },
        "build_stats": stats,
    }, separators=(",", ":"), default=str), flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("shipping-control", "isolated-serialized-pg"))
    parser.add_argument("--child-prefixgraph", action="store_true")
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    args = parser.parse_args()
    if args.child_prefixgraph:
        _child_prefixgraph(args.source, args.archive)
        return
    if not args.mode:
        parser.error("--mode is required outside --child-prefixgraph")
    _parent(args.mode, args.source, args.archive)


if __name__ == "__main__":
    main()
