#!/usr/bin/env python3
"""Windows-only O0: independent-process byte-range lease alias and Reader-compatibility oracle.

Not a CMPCT product implementation. Standard-library msvcrt is the proposed
primitive. Evidence generated here never claims network-share or native parity.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import tempfile
import time
from pathlib import Path


def _msvcrt():
    import msvcrt  # type: ignore[import-not-found]
    return msvcrt


def _open_rw(path: Path) -> int:
    return os.open(str(path), os.O_RDWR | getattr(os, "O_BINARY", 0))


def _lock_nonblock(fd: int, offset: int) -> None:
    os.lseek(fd, offset, os.SEEK_SET)
    _msvcrt().locking(fd, _msvcrt().LK_NBLCK, 1)


def _unlock(fd: int, offset: int) -> None:
    os.lseek(fd, offset, os.SEEK_SET)
    _msvcrt().locking(fd, _msvcrt().LK_UNLCK, 1)


def _child(mode: str, path: Path, offset: int) -> int:
    result = {"mode": mode, "path": path.name, "offset": offset, "pid": os.getpid()}
    if mode == "lock":
        fd = _open_rw(path)
        try:
            try:
                _lock_nonblock(fd, offset)
                result["acquired"] = True
                _unlock(fd, offset)
            except OSError as exc:
                result.update(acquired=False, error=repr(exc),
                              errno=exc.errno, winerror=getattr(exc, "winerror", None))
        finally:
            os.close(fd)
    elif mode == "read":
        try:
            with path.open("rb") as f:
                result["head_hex"] = f.read(8).hex()
                result["read_ok"] = True
        except OSError as exc:
            result.update(read_ok=False, error=repr(exc),
                          errno=exc.errno, winerror=getattr(exc, "winerror", None))
    else:
        raise ValueError(mode)
    print(json.dumps(result, sort_keys=True), flush=True)
    return 0


def _run_child(mode: str, path: Path, offset: int) -> dict:
    start = time.perf_counter_ns()
    process = subprocess.run([sys.executable, str(Path(__file__).resolve()),
                              "--child", mode, str(path), str(offset)],
                             capture_output=True, text=True, timeout=25, check=False)
    wall_ms = (time.perf_counter_ns() - start) / 1_000_000
    assert process.returncode == 0, (
        f"child failed ({mode}, {path}, {offset}): {process.stderr!r} {process.stdout!r}"
    )
    lines = process.stdout.strip().splitlines()
    assert len(lines) == 1, f"invalid child reply: {process.stdout!r}"
    out = json.loads(lines[0])
    out["wall_ms"] = wall_ms
    return out


def _run_oracle() -> dict:
    assert os.name == "nt", "Windows-only oracle; no substitute platform allowed"
    sample = b"CMPCT24\0" + bytes(range(256)) * 64
    output = {
        "platform": platform.platform(),
        "python": sys.version,
        "test": "msvcrt nonblocking one-byte lock; independent processes; true hardlink alias",
        "seed_sha256": hashlib.sha256(sample).hexdigest(),
        "trials": [],
    }
    with tempfile.TemporaryDirectory(prefix="cmpct-win-lock-o0-") as tmp:
        p = Path(tmp) / "original.cmpct"
        alias = Path(tmp) / "alias.cmpct"
        p.write_bytes(sample)
        os.link(p, alias)
        assert os.stat(p).st_ino == os.stat(alias).st_ino
        assert _run_child("read", p, 0)["read_ok"]
        for offset in (0, 1 << 60):
            unlocked = _run_child("lock", p, offset)
            assert unlocked.get("acquired") is True, (
                f"nonblocking lock primitive unavailable before contention at {offset}: {unlocked}"
            )
            for trial in range(3):
                fd = _open_rw(p)
                locked = False
                try:
                    _lock_nonblock(fd, offset)
                    locked = True
                    # Neither seek nor LockFileEx-style byte lock may extend archive.
                    assert p.stat().st_size == len(sample)
                    conflict_original = _run_child("lock", p, offset)
                    conflict_alias = _run_child("lock", alias, offset)
                    reader = _run_child("read", alias, 0)
                    row = dict(offset=offset, trial=trial,
                               blocked_same=not conflict_original["acquired"],
                               blocked_alias=not conflict_alias["acquired"],
                               header_read=reader,
                               conflict_same=conflict_original,
                               conflict_alias=conflict_alias)
                    output["trials"].append(row)
                    assert not conflict_original["acquired"], row
                    assert not conflict_alias["acquired"], row
                    if offset:
                        assert reader["read_ok"], (
                            "far-offset lock interfered with independent ordinary header read", row
                        )
                        assert reader["head_hex"] == sample[:8].hex(), row
                finally:
                    if locked:
                        _unlock(fd, offset)
                    os.close(fd)
                after = _run_child("lock", alias, offset)
                assert after.get("acquired") is True, (
                    "range lock not released when ownership ended", after
                )
                assert p.read_bytes() == sample
                assert alias.read_bytes() == sample
                assert p.stat().st_size == len(sample)
        output["decision"] = "FAR_OFFSET_PRIMITIVE_SUPPORTED_FOR_LOCAL_HARDLINK_TEST_ONLY"
        output["byte0_read_observations"] = [
            x["header_read"]["read_ok"] for x in output["trials"] if x["offset"] == 0
        ]
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--child", nargs=3, metavar=("MODE", "PATH", "OFFSET"))
    parser.add_argument("--output", type=Path, default=Path("windows-lock-oracle.json"))
    args = parser.parse_args()
    if args.child:
        mode, path, offset = args.child
        return _child(mode, Path(path), int(offset))
    try:
        result = _run_oracle()
    except BaseException as exc:
        # A red result is a valid scientific falsification, never a hidden skip.
        fail = {"status": "FAILED", "error": repr(exc), "platform": platform.platform()}
        args.output.write_text(json.dumps(fail, indent=2) + "\n", encoding="utf-8")
        raise
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("platform", "decision", "seed_sha256")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
