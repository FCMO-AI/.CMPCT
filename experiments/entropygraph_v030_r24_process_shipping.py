from __future__ import annotations
"""Shipping-seam adapter for child-owned canonical r24 prebuilds.

This module is intentionally small: it replaces only the ownership primitive behind the
existing release-product prebuild registry. Selection, publication, fallback, verification,
and archive bytes remain owned by the mature release product.
"""
import os
from pathlib import Path
import threading
from typing import Any

from experiments.entropygraph_v030_r24_process_prebuild import R24PrebuildProcess


class R24ProcessPrebuildRegistry:
    """One-shot registry preserving the mature prebuild key/publication contract."""

    def __init__(self, *, timeout_s: float = 120.0):
        self.timeout_s = float(timeout_s)
        if self.timeout_s <= 0:
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
