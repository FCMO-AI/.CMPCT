from __future__ import annotations

"""Fresh-process worker for the frozen PrefixGraph Builder-isolation S6 transfer review.

This is evidence code only. Candidate uses the promoted release-product front door and therefore inherits the
same operation-scoped r24 policy, terminal preflight and canonical Builder seam as the shipping runtime gate.
Control swaps only the private canonical ``_r25_build`` callable to the preserved threaded control after importing
that front door. Whole-process-tree RSS charges the parent and every live descendant, so the PrefixGraph child is
never gifted away.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import threading
import time


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
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
                except Exception as exc:  # measurement must not perturb the product
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

        self.thread = threading.Thread(target=run, name="cmpct-s6-rss-tree-sampler", daemon=True)
        self.thread.start()

    def stop(self) -> None:
        self.stop_event.set()
        if self.thread is not None:
            self.thread.join(timeout=5.0)


class _AuditedExecutor:
    """Delegate the real shipping executor while counting the exact one-shot lifecycle."""

    delegate_cls = None
    constructions = 0
    submissions = 0
    receipts: list[dict] = []
    child_dead_on_submit_return: list[bool] = []

    def __init__(self, *args, **kwargs):
        type(self).constructions += 1
        self.delegate = type(self).delegate_cls(*args, **kwargs)
        self.last_receipt = None

    def __enter__(self):
        self.delegate.__enter__()
        return self

    def __exit__(self, exc_type, exc, tb):
        return self.delegate.__exit__(exc_type, exc, tb)

    def submit(self, fn, *args, **kwargs):
        type(self).submissions += 1
        future = self.delegate.submit(fn, *args, **kwargs)
        self.last_receipt = dict(self.delegate.last_receipt or {})
        type(self).receipts.append(dict(self.last_receipt))
        # The real executor is synchronous. At this exact seam, submit returns only after the helper has been
        # reaped. No direct child here therefore proves G0-G4 cannot overlap that PrefixGraph child lifetime.
        type(self).child_dead_on_submit_return.append(len(_children(os.getpid())) == 0)
        return future


def _reset_audit(real_cls) -> None:
    _AuditedExecutor.delegate_cls = real_cls
    _AuditedExecutor.constructions = 0
    _AuditedExecutor.submissions = 0
    _AuditedExecutor.receipts = []
    _AuditedExecutor.child_dead_on_submit_return = []


def _run_build(mode: str, source: Path, archive: Path) -> dict:
    # Importing the promoted product first is release-critical. It installs the exact operation-scoped r24 policy
    # and canonical-final bindings used by the normal runtime authority. Calling canonical.build directly would
    # silently measure the historical dictionary-dead r24 path and violate the frozen 29,883,732-byte S6 floor.
    from experiments import entropygraph_v030_release_product as product
    from experiments import entropygraph_v030_canonical_final as canonical
    from experiments import entropygraph_v030_prefixgraph_process_executor as process_executor

    expected_tree = str(product.treehash(source))
    original_r25_build = canonical._r25_build
    original_executor = process_executor.PrefixGraphProcessExecutor
    _reset_audit(original_executor)
    if mode == "candidate":
        process_executor.PrefixGraphProcessExecutor = _AuditedExecutor
    elif mode == "control":
        canonical._r25_build = canonical._r25_build_threaded_control
    else:
        raise RuntimeError(f"unsupported measured mode: {mode}")

    sampler = _TreeSampler(0.01)
    baseline_ru = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    sampler.start()
    started = time.perf_counter()
    try:
        stats = dict(product.build(source, archive))
        wall_s = time.perf_counter() - started
        peak_ru = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    finally:
        sampler.stop()
        canonical._r25_build = original_r25_build
        process_executor.PrefixGraphProcessExecutor = original_executor

    verify = dict(product.strong_verify(archive))
    tree = str(verify.get("tree_sha256") or "")
    if not verify.get("ok") or tree != expected_tree:
        raise RuntimeError(f"strong verification mismatch expected={expected_tree} actual={tree}")
    r25 = dict(stats.get("r25") or {})
    receipt = r25.get("prefixgraph_process_receipt")
    if mode == "candidate":
        if _AuditedExecutor.constructions != 1 or _AuditedExecutor.submissions != 1:
            raise RuntimeError("shipping Builder did not exercise exactly one PrefixGraph process executor")
        if len(_AuditedExecutor.receipts) != 1 or receipt != _AuditedExecutor.receipts[0]:
            raise RuntimeError("shipping Builder process receipt did not match audited executor receipt")
        if _AuditedExecutor.child_dead_on_submit_return != [True]:
            raise RuntimeError("PrefixGraph child remained live when synchronous submit returned")
    else:
        if r25.get("prefixgraph_process_receipt") is not None:
            raise RuntimeError("threaded control unexpectedly carried a process receipt")

    return {
        "mode": mode,
        "product_front_door": "experiments.entropygraph_v030_release_product",
        "archive_bytes": archive.stat().st_size,
        "archive_sha256": _sha(archive),
        "selected": stats.get("selected"),
        "format_revision": stats.get("format_revision"),
        "format_profile": stats.get("format_profile"),
        "r24_product_bytes": stats.get("r24_product_bytes"),
        "r25_product_bytes": stats.get("r25_product_bytes"),
        "tree_sha256": tree,
        "expected_tree_sha256": expected_tree,
        "wall_s": wall_s,
        "baseline_parent_ru_maxrss_kib": baseline_ru,
        "parent_peak_ru_maxrss_kib": peak_ru,
        "tree_peak_rss_kib": sampler.peak_kib,
        "tree_peak_processes": sampler.peak_processes,
        "tree_samples": sampler.samples,
        "tree_sampler_errors": sampler.errors,
        "tree_sampler_interval_s": sampler.interval_s,
        "r25_selected": r25.get("selected"),
        "r25_archive_bytes": r25.get("archive_bytes"),
        "r25_candidate_scheduler": r25.get("candidate_scheduler"),
        "prefixgraph_process_receipt": receipt,
        "audited_executor_constructions": _AuditedExecutor.constructions,
        "audited_executor_submissions": _AuditedExecutor.submissions,
        "audited_child_dead_on_submit_return": list(_AuditedExecutor.child_dead_on_submit_return),
        "canonical_r25_build_restored": canonical._r25_build is original_r25_build,
        "executor_restored": process_executor.PrefixGraphProcessExecutor is original_executor,
        "build_stats": stats,
    }


def _run_hostile(kind: str, source: Path, archive: Path) -> dict:
    """Exercise the real fail-closed executor envelope without permitting any partial archive."""
    from experiments import entropygraph_v030_canonical_final as canonical
    from experiments import entropygraph_v030_prefixgraph_process_executor as process_executor

    real_run = process_executor.subprocess.run

    class _Completed:
        def __init__(self, returncode: int, stdout: str, stderr: str):
            self.returncode = returncode
            self.stdout = stdout
            self.stderr = stderr

    if kind == "missing-helper":
        fake = lambda *a, **k: _Completed(127, "", "helper unavailable")
    elif kind == "malformed-receipt":
        fake = lambda *a, **k: _Completed(0, "not-json\n", "")
    else:
        raise RuntimeError(f"unknown hostile kind {kind}")

    archive.unlink(missing_ok=True)
    process_executor.subprocess.run = fake
    error = None
    try:
        with process_executor.PrefixGraphProcessExecutor(timeout_s=30) as executor:
            executor.submit(canonical.RC.PG.build, source, archive).result()
    except Exception as exc:
        error = f"{type(exc).__name__}:{exc}"
    finally:
        process_executor.subprocess.run = real_run
    return {
        "mode": kind,
        "error": error,
        "failed_closed": error is not None and not archive.exists() and not archive.is_symlink(),
        "archive_exists_after_failure": archive.exists() or archive.is_symlink(),
        "subprocess_run_restored": process_executor.subprocess.run is real_run,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("candidate", "control", "missing-helper", "malformed-receipt"), required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    args = parser.parse_args()
    if args.mode in ("candidate", "control"):
        payload = _run_build(args.mode, args.source, args.archive)
    else:
        payload = _run_hostile(args.mode, args.source, args.archive)
    print(json.dumps(payload, separators=(",", ":"), default=str), flush=True)


if __name__ == "__main__":
    main()
