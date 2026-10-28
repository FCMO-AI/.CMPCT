#!/usr/bin/env python3
"""Materialize a historical worktree's package-owned cmpct_core for parity benchmarks.

The historical Python worktree is not executable after cmpct_core became package-owned unless
its own native payload is built. Build through normal isolated PEP 517 so setuptools-rust from
build-system.requires is honored; --no-build-isolation can silently produce a pure wheel.
The optional receipt makes source, wheel, native payload and physical ownership auditable.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("worktree", type=Path)
    ap.add_argument("--receipt", type=Path)
    ns = ap.parse_args()
    worktree = ns.worktree.resolve()
    package = worktree / "src" / "cmpct"
    if not (worktree / "pyproject.toml").is_file() or not package.is_dir():
        raise SystemExit(f"not a CMPCT source worktree: {worktree}")

    with tempfile.TemporaryDirectory(prefix="cmpct-base-wheel-") as td:
        out = Path(td)
        subprocess.run(
            [sys.executable, "-m", "pip", "wheel", "--no-deps", "--wheel-dir", str(out), str(worktree)],
            check=True,
        )
        wheels = list(out.glob("*.whl"))
        if len(wheels) != 1:
            raise SystemExit(f"expected exactly one base wheel, got {len(wheels)}")
        wheel = wheels[0]
        wheel_bytes = wheel.read_bytes()
        with zipfile.ZipFile(wheel) as zf:
            members = [n for n in zf.namelist() if n.startswith("cmpct/cmpct_core") and not n.endswith("/")]
            if len(members) != 1:
                raise SystemExit(f"expected exactly one cmpct_core wheel payload, got {members}")
            member = members[0]
            payload = zf.read(member)

    for stale in package.glob("cmpct_core*"):
        if stale.is_file():
            stale.unlink()
    target = package / Path(member).name
    target.write_bytes(payload)

    env = os.environ.copy()
    env["PYTHONPATH"] = str(worktree / "src")
    probe = subprocess.check_output(
        [sys.executable, "-c", "from cmpct import native_codec; print(native_codec._library_path().resolve())"],
        cwd=worktree,
        env=env,
        text=True,
    ).strip()
    loaded = Path(probe).resolve()
    if loaded != target.resolve() or worktree not in loaded.parents:
        raise SystemExit(f"base native ownership mismatch: loaded={loaded}, expected={target.resolve()}")

    receipt = {
        "worktree": str(worktree),
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=worktree, text=True).strip(),
        "wheel_name": wheel.name,
        "wheel_sha256": sha256(wheel_bytes),
        "native_path": str(target.resolve()),
        "native_bytes": len(payload),
        "native_sha256": sha256(payload),
    }
    text = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if ns.receipt:
        ns.receipt.parent.mkdir(parents=True, exist_ok=True)
        ns.receipt.write_text(text)
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
