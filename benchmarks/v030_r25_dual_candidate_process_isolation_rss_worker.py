from __future__ import annotations

"""Fresh-process worker for frozen dual-candidate process-lifetime RSS attribution."""

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
SELF = Path(__file__).resolve()


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
    out: list[int] = []
    for token in raw.split() if raw else ():
        try:
            out.append(int(token))
        except ValueError:
            pass
    return out


def _tree_rss_kib(root_pid: int) -> tuple[int, int]:
    total = count = 0
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
        self.samples = 0
        self.peak_kib = 0
        self.peak_processes = 0
        self.errors: list[str] = []
        self.thread: threading.Thread | None = None

    def start(self) -> None:
        root = os.getpid()
        def run() -> None:
            while not self.stop_event.is_set():
                try:
                    rss, processes = _tree_rss_kib(root)
                    self.samples += 1
                    if rss > self.peak_kib:
                        self.peak_kib, self.peak_processes = rss, processes
                except Exception as exc:
                    self.errors.append(f"{type(exc).__name__}:{exc}")
                self.stop_event.wait(self.interval_s)
            try:
                rss, processes = _tree_rss_kib(root)
                self.samples += 1
                if rss > self.peak_kib:
                    self.peak_kib, self.peak_processes = rss, processes
            except Exception as exc:
                self.errors.append(f"final:{type(exc).__name__}:{exc}")
        self.thread = threading.Thread(target=run, name="cmpct-dual-rss-tree-sampler", daemon=True)
        self.thread.start()

    def stop(self) -> None:
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=5.0)


class _ImmediateFuture:
    def __init__(self, value): self._value = value
    def result(self): return self._value


class _State:
    pg_submissions = 0
    pg_children = 0
    pg_returncodes: list[int] = []
    pg_child_wall_s: list[float] = []
    g04_children = 0
    g04_returncodes: list[int] = []
    g04_child_wall_s: list[float] = []
    g04_child_peak_kib: list[int] = []


def _child_env() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    return env


def _run_child(kind: str, source: Path, archive: Path) -> tuple[dict, float]:
    cmd = [sys.executable, str(SELF), f"--child-{kind}", "--source", str(source), "--archive", str(archive)]
    started = time.perf_counter()
    proc = subprocess.Popen(cmd, cwd=ROOT, env=_child_env(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout, stderr = proc.communicate()
    elapsed = time.perf_counter() - started
    lines = [line for line in stdout.splitlines() if line.strip()]
    if proc.returncode or not lines:
        raise RuntimeError(f"isolated {kind} child failed rc={proc.returncode} stdout={stdout!r} stderr={stderr!r}")
    payload = json.loads(lines[-1])
    if payload.get("semantic_owner_exact") is not True or payload.get("kind") != kind:
        raise RuntimeError(f"isolated {kind} semantic-owner mismatch: {payload!r}")
    if not archive.is_file() or payload.get("archive_bytes") != archive.stat().st_size or payload.get("archive_sha256") != _sha(archive):
        raise RuntimeError(f"isolated {kind} archive identity mismatch")
    payload["returncode"] = int(proc.returncode)
    return payload, elapsed


class _IsolatedPrefixGraphExecutor:
    def __enter__(self): return self
    def __exit__(self, exc_type, exc, tb): return False
    def submit(self, fn, *args, **kwargs):
        _State.pg_submissions += 1
        if _State.pg_submissions != 1 or len(args) < 2 or kwargs:
            raise RuntimeError("unexpected frozen PrefixGraph submission shape")
        payload, elapsed = _run_child("prefixgraph", Path(args[0]), Path(args[1]))
        _State.pg_children += 1
        _State.pg_returncodes.append(payload["returncode"])
        _State.pg_child_wall_s.append(elapsed)
        return _ImmediateFuture(payload["stats"])


class _RoutingExecutor:
    original = None
    intercepted = 0
    delegated = 0
    def __new__(cls, *args, **kwargs):
        if kwargs.get("thread_name_prefix") == "cmpct-v030-prefixgraph":
            cls.intercepted += 1
            return _IsolatedPrefixGraphExecutor()
        cls.delegated += 1
        return cls.original(*args, **kwargs)


def _isolated_g04_build(source: Path, archive: Path):
    payload, elapsed = _run_child("g04", Path(source), Path(archive))
    _State.g04_children += 1
    _State.g04_returncodes.append(payload["returncode"])
    _State.g04_child_wall_s.append(elapsed)
    _State.g04_child_peak_kib.append(int(payload["peak_ru_maxrss_kib"]))
    return payload["stats"]


def _child(kind: str, source: Path, archive: Path) -> None:
    from experiments import entropygraph_v030_canonical_final as canonical
    iso = canonical.PROFILE_ISOLATION
    owner = canonical.RC.PG if kind == "prefixgraph" else canonical.RC.G04
    expected = iso.PG if kind == "prefixgraph" else iso.SHARED
    if owner is not expected:
        raise RuntimeError(f"child {kind} semantic-owner identity mismatch")
    started = time.perf_counter()
    stats = dict(owner.build(source, archive))
    print(json.dumps({
        "kind": kind,
        "semantic_owner_exact": True,
        "semantic_owner": owner.__name__,
        "archive_bytes": archive.stat().st_size,
        "archive_sha256": _sha(archive),
        "wall_s": time.perf_counter() - started,
        "peak_ru_maxrss_kib": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
        "stats": stats,
    }, separators=(",", ":"), default=str), flush=True)


def _reset() -> None:
    _State.pg_submissions = _State.pg_children = _State.g04_children = 0
    _State.pg_returncodes = []
    _State.pg_child_wall_s = []
    _State.g04_returncodes = []
    _State.g04_child_wall_s = []
    _State.g04_child_peak_kib = []
    _RoutingExecutor.intercepted = _RoutingExecutor.delegated = 0


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
        raise RuntimeError(f"Shifted target unexpectedly PrefixGraph-ineligible: {reason}")

    _reset()
    original_executor = canonical.ThreadPoolExecutor
    original_g04_build = canonical.RC.G04.build
    _RoutingExecutor.original = original_executor
    canonical.ThreadPoolExecutor = _RoutingExecutor
    if mode == "dual-isolated":
        canonical.RC.G04.build = _isolated_g04_build

    sampler = _TreeSampler(0.01)
    sampler.start()
    try:
        started = time.perf_counter()
        stats = dict(product.build(source, archive))
        wall = time.perf_counter() - started
        parent_peak = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    finally:
        sampler.stop()
        canonical.ThreadPoolExecutor = original_executor
        canonical.RC.G04.build = original_g04_build

    verify = dict(product.strong_verify(archive))
    verified_tree = str(verify.get("tree_sha256") or "")
    if not verify.get("ok") or verified_tree != source_tree:
        raise RuntimeError("final strong verification mismatch")
    if _RoutingExecutor.intercepted != 1 or _State.pg_submissions != 1 or _State.pg_children != 1 or _State.pg_returncodes != [0]:
        raise RuntimeError("PrefixGraph isolation lifecycle mismatch")
    if mode == "dual-isolated":
        if _State.g04_children != 1 or _State.g04_returncodes != [0]:
            raise RuntimeError("G0-G4 isolation lifecycle mismatch")
    elif _State.g04_children or _State.g04_returncodes:
        raise RuntimeError("pg-only control unexpectedly isolated G0-G4")

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
        "wall_s": wall,
        "parent_peak_ru_maxrss_kib": parent_peak,
        "tree_peak_rss_kib": sampler.peak_kib,
        "tree_peak_processes": sampler.peak_processes,
        "tree_samples": sampler.samples,
        "tree_sampler_errors": sampler.errors,
        "tree_sampler_interval_s": sampler.interval_s,
        "prefixgraph_executor_intercepts": _RoutingExecutor.intercepted,
        "prefixgraph_submissions": _State.pg_submissions,
        "prefixgraph_children": _State.pg_children,
        "prefixgraph_returncodes": _State.pg_returncodes,
        "prefixgraph_child_wall_s": _State.pg_child_wall_s,
        "g04_children": _State.g04_children,
        "g04_returncodes": _State.g04_returncodes,
        "g04_child_wall_s": _State.g04_child_wall_s,
        "g04_child_peak_ru_maxrss_kib": _State.g04_child_peak_kib,
        "executor_restored": canonical.ThreadPoolExecutor is original_executor,
        "g04_build_restored": canonical.RC.G04.build is original_g04_build,
        "semantic_owners": {"pg": canonical.RC.PG.__name__, "g04": canonical.RC.G04.__name__, "reader": canonical.RC.READER.__name__, "identity_exact": True},
        "build_stats": stats,
    }, separators=(",", ":"), default=str), flush=True)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=("pg-isolated-control", "dual-isolated"))
    p.add_argument("--child-prefixgraph", action="store_true")
    p.add_argument("--child-g04", action="store_true")
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--archive", type=Path, required=True)
    a = p.parse_args()
    if a.child_prefixgraph:
        _child("prefixgraph", a.source, a.archive)
    elif a.child_g04:
        _child("g04", a.source, a.archive)
    elif a.mode:
        _parent(a.mode, a.source, a.archive)
    else:
        p.error("--mode or child mode required")


if __name__ == "__main__":
    main()
