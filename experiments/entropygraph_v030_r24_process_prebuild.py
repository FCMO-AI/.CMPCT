from __future__ import annotations
"""One-shot process owner for the shipping r24 prebuild.

The child owns all r24 Builder heap generations, writes the canonical candidate directly to
its final staging path, and returns only the small build-stats mapping.  No archive bytes cross
IPC.  This module does not decide selection or release policy.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

DEFAULT_TIMEOUT_S = 120.0


class R24PrebuildProcess:
    def __init__(self, root: Path, out: Path, *, timeout_s: float = DEFAULT_TIMEOUT_S):
        self.root = Path(root)
        self.out = Path(out)
        self.timeout_s = float(timeout_s)
        self._proc: subprocess.Popen[str] | None = None

    def start(self) -> "R24PrebuildProcess":
        if self._proc is not None:
            raise RuntimeError("r24 prebuild process already started")
        self.out.parent.mkdir(parents=True, exist_ok=True)
        self._proc = subprocess.Popen(
            [sys.executable, "-m", __name__, "--worker", "--root", str(self.root), "--out", str(self.out)],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            close_fds=(os.name != "nt"),
        )
        return self

    def result(self) -> dict[str, Any]:
        if self._proc is None:
            raise RuntimeError("r24 prebuild process was not started")
        proc = self._proc
        try:
            stdout, stderr = proc.communicate(timeout=self.timeout_s)
        except subprocess.TimeoutExpired:
            proc.kill()
            stdout, stderr = proc.communicate()
            self.out.unlink(missing_ok=True)
            raise TimeoutError(f"r24 prebuild exceeded {self.timeout_s:.3f}s")
        if proc.returncode != 0:
            self.out.unlink(missing_ok=True)
            tail = stderr[-4000:].strip()
            raise RuntimeError(f"r24 prebuild child failed rc={proc.returncode}: {tail}")
        rows = [line for line in stdout.splitlines() if line.strip()]
        if not rows:
            self.out.unlink(missing_ok=True)
            raise RuntimeError("r24 prebuild child returned no receipt")
        receipt = json.loads(rows[-1])
        if receipt.get("schema") != "cmpct-v030-r24-prebuild-process-v1" or not isinstance(receipt.get("stats"), dict):
            self.out.unlink(missing_ok=True)
            raise RuntimeError("r24 prebuild child returned malformed receipt")
        if not self.out.is_file():
            raise RuntimeError("r24 prebuild child reported success without candidate")
        return receipt["stats"]

    def close(self) -> None:
        proc = self._proc
        if proc is not None and proc.poll() is None:
            proc.kill()
            proc.communicate()
        self._proc = None

    def __enter__(self) -> "R24PrebuildProcess":
        return self.start()

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()


def _worker(root: Path, out: Path) -> None:
    # Import inside the child so the parent never owns Builder's r24 heap generations.
    from experiments import entropygraph_v030_release_product_base as product

    stats = product._locality_bounded_r24_build(Path(root), Path(out))
    print(json.dumps({"schema": "cmpct-v030-r24-prebuild-process-v1", "stats": stats}, separators=(",", ":"), default=str))


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
