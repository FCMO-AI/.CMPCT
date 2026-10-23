#!/usr/bin/env python3
"""Research O1: Windows msvcrt far-range lock vs duplicate O_APPEND descriptor semantics.

Never asserts CMPCT Windows support: tests one OS/runtime primitive only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import sys
import tempfile
import traceback
from pathlib import Path

import research_windows_byte_range_lock_oracle as o0

SENTINEL = 1 << 60


def _trial(root: Path, name: str, *, locked: bool, second_len: int) -> dict:
    initial = b"CMPCT24\0" + b"x" * 8192
    part1 = b"G" * 23
    part2 = (bytes(range(256)) * ((second_len // 256) + 1))[:second_len]
    path = root / (name + ".cmpct")
    alias = root / (name + "-hardlink.cmpct")
    path.write_bytes(initial)
    os.link(path, alias)
    fd = os.open(path, os.O_RDWR | os.O_APPEND | getattr(os, "O_BINARY", 0))
    owned = False
    rows = []
    try:
        if locked:
            o0._lock_nonblock(fd, SENTINEL)
            owned = True
            conflict = o0._run_child("lock", alias, SENTINEL)
            assert not conflict["acquired"], conflict
            reader = o0._run_child("read", alias, 0)
            assert reader["read_ok"] and reader["head_hex"] == initial[:8].hex(), reader
        else:
            conflict = None
            reader = o0._run_child("read", alias, 0)
            assert reader["read_ok"], reader

        for chunk in (part1, part2):
            dup = os.dup(fd)
            with os.fdopen(dup, "wb", buffering=0) as stream:
                start_offset = stream.tell()
                n = stream.write(chunk)
                assert n == len(chunk), (n, len(chunk))
                stream.flush()
                os.fsync(stream.fileno())
                after_offset = stream.tell()
            expected_size = len(initial) + sum(x["written"] for x in rows) + len(chunk)
            actual_size = os.fstat(fd).st_size
            row = dict(start_offset=start_offset, tell_after=after_offset,
                       physical_size=actual_size, written=len(chunk),
                       expected_size=expected_size)
            rows.append(row)
            # Never read a potential accidental exabyte sparse allocation.
            assert actual_size == expected_size, (
                "unexpected size; O_APPEND wrote at sentinel or beyond EOF", row
            )
            assert after_offset == expected_size, (
                "post-append tell() is not a truthful footer position", row
            )
            assert path.read_bytes() == initial + part1 + (
                part2 if len(rows) == 2 else b""
            )
            assert alias.read_bytes() == path.read_bytes()
        assert os.fstat(fd).st_size == len(initial) + len(part1) + len(part2)
    finally:
        if owned:
            o0._unlock(fd, SENTINEL)
        os.close(fd)
    if locked:
        after = o0._run_child("lock", alias, SENTINEL)
        assert after["acquired"], after
    expected = initial + part1 + part2
    assert path.read_bytes() == expected
    return dict(name=name, locked=locked, second_len=second_len,
                exact_sha256=hashlib.sha256(expected).hexdigest(),
                total_size=len(expected), rows=rows, conflict=conflict,
                reader=reader)


def _run() -> dict:
    assert os.name == "nt", "must run on actual Windows host"
    report = dict(platform=platform.platform(), python=sys.version,
                  question="msvcrt sentinel lock plus os.dup O_APPEND physical EOF offsets",
                  source_sha=None, observations=[])
    with tempfile.TemporaryDirectory(prefix="cmpct-win-append-o1-") as folder:
        root = Path(folder)
        for size in (17, 65537):
            control = _trial(root, f"control-{size}", locked=False, second_len=size)
            candidate = _trial(root, f"locked-{size}", locked=True, second_len=size)
            assert control["exact_sha256"] == candidate["exact_sha256"]
            assert control["total_size"] == candidate["total_size"]
            assert [row["tell_after"] for row in control["rows"]] == [
                row["tell_after"] for row in candidate["rows"]
            ]
            report["observations"].append({"control": control, "candidate": candidate})
    report["decision"] = "SENTINEL_DUP_APPEND_EOF_AND_TELL_MATCH_CONTROL"
    return report


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, default=Path("windows-sentinel-append-o1.json"))
    args = ap.parse_args()
    try:
        result = _run()
    except BaseException as exc:
        result = dict(status="FAILED", error=repr(exc), traceback=traceback.format_exc(),
                      platform=platform.platform())
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        raise
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("platform", "decision")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
