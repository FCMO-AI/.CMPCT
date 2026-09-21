from __future__ import annotations
"""Shipping-seam adapter for child-owned canonical r24 prebuilds.

This module replaces only the ownership primitive behind the existing release-product
prebuild seam. Selection, publication, fallback, verification, and archive bytes remain
owned by the mature release product.
"""
import os
from pathlib import Path
import threading
import time
from typing import Any

from experiments.entropygraph_v030_r24_process_prebuild import R24PrebuildProcess


class R24ProcessPrebuildRegistry:
    """One-shot registry preserving the mature prebuild key/publication contract."""

    def __init__(self, *, timeout_s: float | None = None):
        self.timeout_s = None if timeout_s is None else float(timeout_s)
        if self.timeout_s is not None and self.timeout_s <= 0:
            raise ValueError("r24 process registry timeout must be positive")
        self._lock = threading.Lock()
        self._pending: dict[str, tuple[R24PrebuildProcess, Path]] = {}

    @staticmethod
    def key(path: Path) -> str:
        return os.fspath(Path(path).parent.absolute())

    def start(self, root: Path, staging_root: Path) -> None:
        staging_root = Path(staging_root)
        key = self.key(staging_root)
        prebuilt = staging_root.parent / "prebuilt-canonical-r24.cmpct"
        with self._lock:
            if key in self._pending:
                raise RuntimeError("duplicate canonical r24 prebuild key")
            proc = R24PrebuildProcess(Path(root), prebuilt, timeout_s=self.timeout_s)
            proc.start()
            self._pending[key] = (proc, prebuilt)

    def consume(self, out: Path) -> dict[str, Any] | None:
        out = Path(out)
        key = self.key(out)
        with self._lock:
            pending = self._pending.pop(key, None)
        if pending is None:
            return None
        proc, prebuilt = pending
        try:
            stats = dict(proc.result())
            os.replace(prebuilt, out)
            return {
                **stats,
                "archive_bytes": out.stat().st_size,
                "r24_prebuild_overlap": "filesystem-manifest-capture",
                "r24_prebuild_reused": True,
                "r24_prebuild_owner": "child-process-v1",
            }
        finally:
            proc.close()
            prebuilt.unlink(missing_ok=True)

    def discard(self, path: Path) -> bool:
        key = self.key(Path(path))
        with self._lock:
            pending = self._pending.pop(key, None)
        if pending is None:
            return False
        proc, prebuilt = pending
        try:
            proc.close()
        finally:
            prebuilt.unlink(missing_ok=True)
        return True

    def close_all(self) -> None:
        with self._lock:
            pending = list(self._pending.values())
            self._pending.clear()
        for proc, prebuilt in pending:
            try:
                proc.close()
            finally:
                prebuilt.unlink(missing_ok=True)


def install_into_release_base(base_impl, *, timeout_s: float | None = None) -> R24ProcessPrebuildRegistry:
    """Replace the mature thread owner at its existing canonical-final seam.

    The preserved pre-profile function is used deliberately: calling the already-patched
    thread wrapper would create a duplicate r24 build. Profile-ineligible inputs keep the
    child alive because canonical-final immediately consumes r24 fallback. Other profile
    preparation failures kill the child and remove its staging artifact before propagating.

    Shipping intentionally has no fixed child timeout by default. The inherited in-process
    builder had no size-independent deadline either, and imposing one here would turn large
    valid archives into a new correctness failure. Tests and bounded callers may opt into a
    positive timeout explicitly.

    The promoted Logs terminal is also installed here because this is the release-product
    ownership seam. Its r24 and Logs candidates are materialized sequentially: replicated
    A/B evidence showed the old two-thread overlap inflated parent RSS while process-tree
    ownership gained nothing. Candidate implementations, admission, publication, and bytes
    remain unchanged; only their lifetime overlap is removed.
    """
    registry = R24ProcessPrebuildRegistry(timeout_s=timeout_s)
    original_prepare = base_impl._ORIGINAL_PREPARE_PROFILE_TREE

    def prepare(root: Path, staging_root: Path) -> dict:
        registry.start(Path(root), Path(staging_root))
        try:
            return original_prepare(root, staging_root)
        except base_impl.C.ProfileNotEligible:
            raise
        except Exception:
            registry.discard(Path(staging_root))
            raise

    def consume_or_build(root: Path, out: Path) -> dict:
        stats = registry.consume(Path(out))
        if stats is not None:
            return stats
        return base_impl._locality_bounded_r24_build(root, out)

    base_impl.C._prepare_profile_tree = prepare
    base_impl.C._r24_build = consume_or_build

    # Importing the Logs wrapper here is acyclic: it depends on the preserved base module,
    # not on the public release-product facade currently installing this shipping seam.
    from experiments import entropygraph_v030_release_product_logs_candidate as logs_impl

    def sequential_logs_candidates(root: Path, temp: Path) -> tuple[dict, dict, Path, Path, float]:
        """Materialize the two exact candidates without overlapping their live buffers."""
        r24_path = temp / "candidate-r24.cmpct"
        logs_path = temp / "candidate-logs.cmpct"
        started = time.perf_counter()
        # Keep this order explicit: the replicated control tested r24 then Logs, not merely
        # "no threads". Changing order is a new experiment and must earn its own evidence.
        r24 = logs_impl._build_r24(root, r24_path)
        logs = logs_impl._build_logs(root, logs_path)
        return r24, logs, r24_path, logs_path, time.perf_counter() - started

    logs_impl._parallel_candidates = sequential_logs_candidates
    return registry
