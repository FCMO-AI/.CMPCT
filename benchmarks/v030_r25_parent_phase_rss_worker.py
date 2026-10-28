from __future__ import annotations

"""Fresh-process whole-tree RSS worker with exact parent-phase attribution."""

import argparse
from contextlib import contextmanager
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


class _PhaseState:
    lock = threading.Lock()
    active: dict[str, int] = {}

    @classmethod
    @contextmanager
    def enter(cls, name: str):
        with cls.lock:
            cls.active[name] = cls.active.get(name, 0) + 1
        try:
            yield
        finally:
            with cls.lock:
                left = cls.active.get(name, 0) - 1
                if left > 0:
                    cls.active[name] = left
                else:
                    cls.active.pop(name, None)

    @classmethod
    def signature(cls) -> tuple[str, ...]:
        with cls.lock:
            return tuple(sorted(k for k, v in cls.active.items() if v > 0))


class _TreeSampler:
    def __init__(self, interval_s: float = 0.01):
        self.interval_s = interval_s
        self.stop_event = threading.Event()
        self.samples = 0
        self.peak_kib = 0
        self.peak_processes = 0
        self.peak_signature: tuple[str, ...] = ()
        self.signature_peaks: dict[str, int] = {}
        self.errors: list[str] = []
        self.thread: threading.Thread | None = None

    def start(self) -> None:
        root = os.getpid()

        def run() -> None:
            while not self.stop_event.is_set():
                try:
                    rss, processes = _tree_rss_kib(root)
                    sig = _PhaseState.signature()
                    key = "+".join(sig) if sig else "(none)"
                    self.samples += 1
                    self.signature_peaks[key] = max(self.signature_peaks.get(key, 0), rss)
                    if rss > self.peak_kib:
                        self.peak_kib = rss
                        self.peak_processes = processes
                        self.peak_signature = sig
                except Exception as exc:
                    self.errors.append(f"{type(exc).__name__}:{exc}")
                self.stop_event.wait(self.interval_s)
            try:
                rss, processes = _tree_rss_kib(root)
                sig = _PhaseState.signature()
                key = "+".join(sig) if sig else "(none)"
                self.samples += 1
                self.signature_peaks[key] = max(self.signature_peaks.get(key, 0), rss)
                if rss > self.peak_kib:
                    self.peak_kib = rss
                    self.peak_processes = processes
                    self.peak_signature = sig
            except Exception as exc:
                self.errors.append(f"final:{type(exc).__name__}:{exc}")

        self.thread = threading.Thread(target=run, name="cmpct-parent-phase-rss-sampler", daemon=True)
        self.thread.start()

    def stop(self) -> None:
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=5.0)


class _ImmediateFuture:
    def __init__(self, value):
        self._value = value

    def result(self):
        return self._value


class _PGState:
    submissions = 0
    children = 0
    returncodes: list[int] = []
    child_wall_s: list[float] = []


def _child_env() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    return env


def _run_pg_child(source: Path, archive: Path) -> tuple[dict, float]:
    cmd = [sys.executable, str(SELF), "--child-prefixgraph", "--source", str(source), "--archive", str(archive)]
    started = time.perf_counter()
    proc = subprocess.Popen(cmd, cwd=ROOT, env=_child_env(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout, stderr = proc.communicate()
    elapsed = time.perf_counter() - started
    lines = [line for line in stdout.splitlines() if line.strip()]
    if proc.returncode or not lines:
        raise RuntimeError(f"isolated PrefixGraph child failed rc={proc.returncode} stdout={stdout!r} stderr={stderr!r}")
    payload = json.loads(lines[-1])
    if payload.get("semantic_owner_exact") is not True or payload.get("kind") != "prefixgraph":
        raise RuntimeError(f"isolated PrefixGraph semantic-owner mismatch: {payload!r}")
    if not archive.is_file() or payload.get("archive_bytes") != archive.stat().st_size or payload.get("archive_sha256") != _sha(archive):
        raise RuntimeError("isolated PrefixGraph archive identity mismatch")
    payload["returncode"] = int(proc.returncode)
    return payload, elapsed


class _IsolatedPrefixGraphExecutor:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def submit(self, fn, *args, **kwargs):
        _PGState.submissions += 1
        if _PGState.submissions != 1 or len(args) < 2 or kwargs:
            raise RuntimeError("unexpected frozen PrefixGraph submission shape")
        payload, elapsed = _run_pg_child(Path(args[0]), Path(args[1]))
        _PGState.children += 1
        _PGState.returncodes.append(payload["returncode"])
        _PGState.child_wall_s.append(elapsed)
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


def _wrap_phase(name: str, fn):
    def wrapped(*args, **kwargs):
        with _PhaseState.enter(name):
            return fn(*args, **kwargs)
    return wrapped


def _child_prefixgraph(source: Path, archive: Path) -> None:
    from experiments import entropygraph_v030_canonical_final as canonical

    iso = canonical.PROFILE_ISOLATION
    if canonical.RC.PG is not iso.PG:
        raise RuntimeError("child PrefixGraph semantic-owner identity mismatch")
    started = time.perf_counter()
    stats = dict(canonical.RC.PG.build(source, archive))
    print(json.dumps({
        "kind": "prefixgraph",
        "semantic_owner_exact": True,
        "semantic_owner": canonical.RC.PG.__name__,
        "archive_bytes": archive.stat().st_size,
        "archive_sha256": _sha(archive),
        "wall_s": time.perf_counter() - started,
        "peak_ru_maxrss_kib": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
        "stats": stats,
    }, separators=(",", ":"), default=str), flush=True)


def _parent(source: Path, archive: Path) -> None:
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

    _PGState.submissions = _PGState.children = 0
    _PGState.returncodes = []
    _PGState.child_wall_s = []
    _RoutingExecutor.intercepted = _RoutingExecutor.delegated = 0
    _PhaseState.active = {}

    originals = {
        "executor": canonical.ThreadPoolExecutor,
        "profile_prepare": canonical._prepare_profile_tree,
        "r24_build": canonical._r24_build,
        "r25_build": canonical._r25_build,
        "g04_build": canonical.RC.G04.build,
        "publish": canonical._publish_atomic,
        "verify": canonical.strong_verify,
    }
    _RoutingExecutor.original = originals["executor"]

    canonical.ThreadPoolExecutor = _RoutingExecutor
    canonical._prepare_profile_tree = _wrap_phase("profile-prepare", originals["profile_prepare"])
    canonical._r24_build = _wrap_phase("r24-build", originals["r24_build"])
    canonical._r25_build = _wrap_phase("r25-build", originals["r25_build"])
    canonical.RC.G04.build = _wrap_phase("g04-build", originals["g04_build"])
    canonical._publish_atomic = _wrap_phase("publication", originals["publish"])
    canonical.strong_verify = _wrap_phase("final-verify", originals["verify"])

    sampler = _TreeSampler(0.01)
    sampler.start()
    try:
        started = time.perf_counter()
        stats = dict(product.build(source, archive))
        wall = time.perf_counter() - started
        parent_peak = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    finally:
        sampler.stop()
        canonical.ThreadPoolExecutor = originals["executor"]
        canonical._prepare_profile_tree = originals["profile_prepare"]
        canonical._r24_build = originals["r24_build"]
        canonical._r25_build = originals["r25_build"]
        canonical.RC.G04.build = originals["g04_build"]
        canonical._publish_atomic = originals["publish"]
        canonical.strong_verify = originals["verify"]

    verify = dict(product.strong_verify(archive))
    verified_tree = str(verify.get("tree_sha256") or "")
    if not verify.get("ok") or verified_tree != source_tree:
        raise RuntimeError("final independent strong verification mismatch")
    if _RoutingExecutor.intercepted != 1 or _PGState.submissions != 1 or _PGState.children != 1 or _PGState.returncodes != [0]:
        raise RuntimeError("PrefixGraph isolation lifecycle mismatch")

    restored = (
        canonical.ThreadPoolExecutor is originals["executor"]
        and canonical._prepare_profile_tree is originals["profile_prepare"]
        and canonical._r24_build is originals["r24_build"]
        and canonical._r25_build is originals["r25_build"]
        and canonical.RC.G04.build is originals["g04_build"]
        and canonical._publish_atomic is originals["publish"]
        and canonical.strong_verify is originals["verify"]
    )

    print(json.dumps({
        "mode": "pg-isolated-parent-phase",
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
        "tree_peak_phase_signature": list(sampler.peak_signature),
        "tree_phase_signature_peaks_kib": sampler.signature_peaks,
        "tree_samples": sampler.samples,
        "tree_sampler_errors": sampler.errors,
        "tree_sampler_interval_s": sampler.interval_s,
        "prefixgraph_executor_intercepts": _RoutingExecutor.intercepted,
        "prefixgraph_submissions": _PGState.submissions,
        "prefixgraph_children": _PGState.children,
        "prefixgraph_returncodes": _PGState.returncodes,
        "prefixgraph_child_wall_s": _PGState.child_wall_s,
        "g04_children": 0,
        "all_wrappers_restored": restored,
        "semantic_owners": {
            "pg": canonical.RC.PG.__name__,
            "g04": canonical.RC.G04.__name__,
            "reader": canonical.RC.READER.__name__,
            "identity_exact": True,
        },
        "build_stats": stats,
    }, separators=(",", ":"), default=str), flush=True)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--child-prefixgraph", action="store_true")
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--archive", type=Path, required=True)
    a = p.parse_args()
    if a.child_prefixgraph:
        _child_prefixgraph(a.source, a.archive)
    else:
        _parent(a.source, a.archive)


if __name__ == "__main__":
    main()
