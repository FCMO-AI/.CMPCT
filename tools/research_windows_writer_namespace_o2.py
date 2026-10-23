#!/usr/bin/env python3
"""Windows O2: independently replace pathname while old archive inode handle is held.

This is a research-only OS semantics discriminator. Never a product write lock.
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
import traceback
from pathlib import Path

import research_windows_byte_range_lock_oracle as primitives

SENTINEL = 1 << 60
ORIGINAL = b"CMPCT24\0" + b"original archive mock bytes-" * 30
REPLACEMENT = b"CMPCT24\0" + b"new independent inode bytes-" * 31


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _replace_child(from_path: Path, dest: Path) -> int:
    outcome = {"pid": os.getpid(), "mode": "replace"}
    try:
        os.replace(from_path, dest)
        outcome["replace_ok"] = True
    except OSError as exc:
        outcome.update(replace_ok=False, error=repr(exc), errno=exc.errno,
                       winerror=getattr(exc, "winerror", None))
    print(json.dumps(outcome, sort_keys=True), flush=True)
    return 0


def _attempt_replace(replacement: Path, dest: Path) -> dict:
    p = subprocess.run([sys.executable, str(Path(__file__).resolve()),
                        "--child-replace", str(replacement), str(dest)],
                       capture_output=True, text=True, timeout=25, check=False)
    assert p.returncode == 0, (p.returncode, p.stderr, p.stdout)
    ls = p.stdout.strip().splitlines()
    assert len(ls) == 1, p.stdout
    return json.loads(ls[0])


def _trial(base: Path, variant: str) -> dict:
    root = base / variant
    root.mkdir()
    original = root / "archive.cmpct"
    alias = root / "archive-alias.cmpct"
    newcomer = root / "replacement.cmpct"
    original.write_bytes(ORIGINAL)
    os.link(original, alias)
    newcomer.write_bytes(REPLACEMENT)
    before_inode = original.stat().st_ino
    assert alias.stat().st_ino == before_inode
    fd = None
    held = False
    locked = False
    try:
        if variant != "no_handle":
            fd = os.open(original, os.O_RDWR | os.O_APPEND | getattr(os, "O_BINARY", 0))
            held = True
            assert os.fstat(fd).st_ino == before_inode
        if variant == "held_sentinel":
            primitives._lock_nonblock(fd, SENTINEL)
            locked = True
            assert primitives._run_child("read", alias, 0)["read_ok"]

        child = _attempt_replace(newcomer, original)
        changed = bool(child["replace_ok"])
        assert original.exists()
        assert alias.read_bytes() == ORIGINAL, "hardlink victim physically modified"
        assert os.fstat(fd).st_ino == before_inode if held else True
        assert original.read_bytes() == (REPLACEMENT if changed else ORIGINAL)
        assert newcomer.exists() != changed
        if changed:
            assert original.stat().st_ino != before_inode, (
                "successful replace did not produce an independent physical inode"
            )
        else:
            assert original.stat().st_ino == before_inode
        fresh_lock = old_alias_lock = None
        if locked:
            fresh_lock = primitives._run_child("lock", original, SENTINEL)
            old_alias_lock = primitives._run_child("lock", alias, SENTINEL)
            assert not old_alias_lock["acquired"], old_alias_lock
            if changed:
                assert fresh_lock["acquired"], (
                    "successful pathname replacement did not split original inode lease", fresh_lock
                )
            else:
                assert not fresh_lock["acquired"], fresh_lock
        out = dict(variant=variant, original_open=held, sentinel_locked=locked,
                   before_inode=before_inode,
                   owner_fd_inode=os.fstat(fd).st_ino if held else None,
                   dest_inode=original.stat().st_ino,
                   alias_inode=alias.stat().st_ino,
                   replacement_succeeded=changed,
                   replace_subprocess=child,
                   output_sha256=digest(original.read_bytes()),
                   alias_sha256=digest(alias.read_bytes()),
                   expected_old_sha256=digest(ORIGINAL),
                   expected_new_sha256=digest(REPLACEMENT),
                   new_inode_lock=fresh_lock, old_alias_lock=old_alias_lock)
        return out
    finally:
        if locked:
            primitives._unlock(fd, SENTINEL)
        if fd is not None:
            os.close(fd)


def _run() -> dict:
    assert os.name == "nt", "Windows host required"
    report = {"platform": platform.platform(), "python": sys.version,
              "question": "is pathname replacement denied by open-handle share mode or lock",
              "observations": []}
    with tempfile.TemporaryDirectory(prefix="cmpct-win-rebind-o2-") as temp:
        for variant in ("no_handle", "held_only", "held_sentinel"):
            report["observations"].append(_trial(Path(temp), variant))
    assert report["observations"][0]["replacement_succeeded"], (
        "no-handle baseline unable to replace; experiment environmental blocker"
    )
    c1 = report["observations"][1]["replacement_succeeded"]
    c2 = report["observations"][2]["replacement_succeeded"]
    report["decision"] = (
        "SENTINEL_HELD_HANDLE_ALLOWS_NAMESPACE_REBIND" if c2 else
        "SENTINEL_BLOCKS_WHERE_HELD_HANDLE_DOES_NOT" if c1 else
        "ORDINARY_OPEN_HANDLE_DENIES_REPLACEMENT_LOCALLY"
    )
    return report


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--child-replace", nargs=2)
    ap.add_argument("--output", type=Path, default=Path("windows-namespace-o2.json"))
    args = ap.parse_args()
    if args.child_replace:
        return _replace_child(Path(args.child_replace[0]), Path(args.child_replace[1]))
    try:
        result = _run()
    except BaseException as exc:
        result = {"status": "FAILED", "error": repr(exc),
                  "traceback": traceback.format_exc(), "platform": platform.platform()}
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        raise
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"platform": result["platform"], "decision": result["decision"]},
                     indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
