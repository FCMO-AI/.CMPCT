from __future__ import annotations
"""One-shot process owner for the shipping r24 prebuild.

The child owns all r24 Builder heap generations, writes the canonical candidate directly to
its final staging path, and returns only the small build-stats mapping. No archive bytes cross
IPC. This module does not decide selection or release policy.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any

DEFAULT_TIMEOUT_S: float | None = None
_REPO_ROOT = Path(__file__).resolve().parents[1]


class R24PrebuildProcess:
    def __init__(self, root: Path, out: Path, *, timeout_s: float | None = DEFAULT_TIMEOUT_S):
        self.root = Path(root)
        self.out = Path(out)
        self.timeout_s = None if timeout_s is None else float(timeout_s)
        if self.timeout_s is not None and self.timeout_s <= 0:
            raise ValueError("r24 prebuild timeout must be positive")
        self._proc: subprocess.Popen[str] | None = None
        self._started_at: float | None = None
        self._result_collected = False

    def start(self) -> "R24PrebuildProcess":
        if self._proc is not None:
            raise RuntimeError("r24 prebuild process already started")
        self.out.parent.mkdir(parents=True, exist_ok=True)
        if self.out.exists():
            raise FileExistsError(f"r24 prebuild output already exists: {self.out}")

        env = os.environ.copy()
        inherited_pythonpath = env.get("PYTHONPATH")
        env["PYTHONPATH"] = os.pathsep.join(
            [os.fspath(_REPO_ROOT)] + ([inherited_pythonpath] if inherited_pythonpath else [])
        )
        self._started_at = time.monotonic()
        self._proc = subprocess.Popen(
            [sys.executable, "-m", __name__, "--worker", "--root", str(self.root), "--out", str(self.out)],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            close_fds=(os.name != "nt"),
            env=env,
        )
        return self

    def result(self) -> dict[str, Any]:
        if self._proc is None or self._started_at is None:
            raise RuntimeError("r24 prebuild process was not started")
        proc = self._proc
        remaining_s = (
            None
            if self.timeout_s is None
            else max(0.0, self.timeout_s - (time.monotonic() - self._started_at))
        )
        try:
            stdout, stderr = proc.communicate(timeout=remaining_s)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.communicate()
            self.out.unlink(missing_ok=True)
            raise TimeoutError(f"r24 prebuild exceeded {self.timeout_s:.3f}s total lifetime")
        if proc.returncode != 0:
            self.out.unlink(missing_ok=True)
            raise RuntimeError(f"r24 prebuild child failed rc={proc.returncode}: {stderr[-4000:].strip()}")
        rows = [line for line in stdout.splitlines() if line.strip()]
        if not rows:
            self.out.unlink(missing_ok=True)
            raise RuntimeError("r24 prebuild child returned no receipt")
        try:
            receipt = json.loads(rows[-1])
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            self.out.unlink(missing_ok=True)
            raise RuntimeError("r24 prebuild child returned malformed receipt") from exc
        if (
            not isinstance(receipt, dict)
            or receipt.get("schema") != "cmpct-v030-r24-prebuild-process-v1"
            or not isinstance(receipt.get("stats"), dict)
        ):
            self.out.unlink(missing_ok=True)
            raise RuntimeError("r24 prebuild child returned malformed receipt")
        if not self.out.is_file():
            raise RuntimeError("r24 prebuild child reported success without candidate")
        self._result_collected = True
        return receipt["stats"]

    def close(self) -> None:
        proc = self._proc
        if proc is not None and proc.poll() is None:
            proc.kill()
            proc.communicate()
        if self._proc is not None and not self._result_collected:
            self.out.unlink(missing_ok=True)
        self._proc = None
        self._started_at = None

    def __enter__(self) -> "R24PrebuildProcess":
        return self.start()

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()


def _worker(root: Path, out: Path) -> None:
    root = Path(root)
    out = Path(out)
    if not root.is_dir():
        raise FileNotFoundError(f"r24 prebuild source is not a directory: {root}")
    from experiments import entropygraph_v030_release_product as product

    stats = product._locality_bounded_r24_build(root, out)
    print(
        json.dumps(
            {"schema": "cmpct-v030-r24-prebuild-process-v1", "stats": stats},
            separators=(",", ":"),
            default=str,
        )
    )


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--worker", action="store_true")
    p.add_argument("--root", type=Path)
    p.add_argument("--out", type=Path)
    a = p.parse_args()
    if not a.worker or a.root is None or a.out is None:
        p.error("worker mode requires --root and --out")
    _worker(a.root, a.out)


if __name__ == "__main__":
    main()
