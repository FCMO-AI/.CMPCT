#!/usr/bin/env python3
"""O103: genuine installed-r24 Reader mmap lifetime, child-isolated signal court.

Science PASS (SIGBUS observed) describes an availability defect, NOT safety.
The source-exact preregistration precedes this implementation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import random
import signal
import subprocess
import sys
import tempfile
import time

from cmpct.core import Builder, CMPCT
from cmpct.codec import S_BLOB

MEMBER = "payload.bin"
SIZE = 256 * 1024


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def make_archive(parent: Path, label: str, seed: int) -> tuple[Path, bytes]:
    src = parent / f"source-{label}"
    src.mkdir()
    data = random.Random(seed).randbytes(SIZE)
    (src / MEMBER).write_bytes(data)
    archive = parent / f"{label}.cmpct"
    Builder(src).build(archive)
    with CMPCT(archive) as reader:
        row = reader.by[MEMBER]
        assert row[6][0] == S_BLOB, f"fixture must use physical BLOB, got {row[6]}"
        assert reader.read(MEMBER) == data
        assert reader.verify() == 1
        assert len(reader.mm) > 4096
    return archive, data


def worker(mode: str, path: Path, replacement: Path | None) -> int:
    with CMPCT(path) as reader:
        before = os.fstat(reader.f.fileno())
        print(json.dumps({"phase": "OPENED", "dev": before.st_dev,
                          "ino": before.st_ino, "length": len(reader.mm)}), flush=True)
        if mode == "truncate":
            # Mutate the exact mapped inode after index+mapping were opened,
            # not an alternative pathname which might point to another inode.
            # The Reader deliberately opens its descriptor read-only.  A separate,
            # independent writable descriptor is the authentic concurrent actor.
            # Both descriptors must refer to the same physical object before truncation.
            with open(path, "r+b", buffering=0) as writer:
                actor = os.fstat(writer.fileno())
                assert (before.st_dev, before.st_ino) == (actor.st_dev, actor.st_ino)
                os.ftruncate(writer.fileno(), 0)
            after = os.fstat(reader.f.fileno())
            assert (before.st_dev, before.st_ino) == (after.st_dev, after.st_ino)
            print(json.dumps({"phase": "SAME_INODE_TRUNCATED", "size": after.st_size}),
                  flush=True)
        elif mode == "replace":
            assert replacement is not None
            assert replacement.stat().st_ino != before.st_ino
            os.replace(replacement, path)
            after = path.stat()
            assert (after.st_dev, after.st_ino) != (before.st_dev, before.st_ino)
            print(json.dumps({"phase": "DIFFERENT_INODE_REPLACED",
                              "mapped_ino": before.st_ino, "path_ino": after.st_ino}),
                  flush=True)
        elif mode != "stable":
            raise AssertionError("unsupported test mode")
        # On Linux, accessing a mapped page after truncation can terminate this
        # disposable process with SIGBUS rather than raising Python IOError.
        raw = reader.read(MEMBER)
        verified = reader.verify()
        print(json.dumps({"phase": "READ_AND_VERIFIED", "sha256": digest(raw),
                          "length": len(raw), "verified_files": verified}), flush=True)
    return 0


def case(mode: str, archive: Path, replacement: Path, expected_sha: str) -> dict:
    command = [sys.executable, os.path.abspath(__file__), "--worker", mode,
               "--archive", str(archive), "--replacement", str(replacement)]
    started = time.monotonic()
    try:
        child = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               text=True, timeout=15, check=False)
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        return {"mode": mode, "timeout": True, "wall_seconds": round(time.monotonic()-started, 3),
                "stdout": (exc.stdout or b"").decode(errors="replace")
                          if isinstance(exc.stdout, bytes) else (exc.stdout or ""),
                "stderr": (exc.stderr or b"").decode(errors="replace")
                          if isinstance(exc.stderr, bytes) else (exc.stderr or ""),
                "decision": "INVALID_TIMEOUT"}
    lines = []
    for line in child.stdout.splitlines():
        try:
            lines.append(json.loads(line))
        except json.JSONDecodeError:
            lines.append({"nonjson_stdout": line})
    phases = [x.get("phase") for x in lines]
    out = {"mode": mode, "returncode": child.returncode,
           "signal": signal.Signals(-child.returncode).name if child.returncode < 0
           and -child.returncode in signal.Signals.__members__.values() else None,
           "wall_seconds": round(time.monotonic()-started, 3),
           "events": lines, "stderr_tail": child.stderr[-1000:],
           "source_sha256": expected_sha, "timeout": timed_out}
    if mode == "truncate":
        out["decision"] = ("SAME_INODE_MMAP_SIGBUS_CONFIRMED"
                           if child.returncode == -signal.SIGBUS
                           and "SAME_INODE_TRUNCATED" in phases else "NOT_CONFIRMED")
    else:
        finals = [x for x in lines if x.get("phase") == "READ_AND_VERIFIED"]
        expected_phases = (["OPENED", "READ_AND_VERIFIED"] if mode == "stable"
                           else ["OPENED", "DIFFERENT_INODE_REPLACED", "READ_AND_VERIFIED"])
        out["decision"] = ("CONTROL_VALID" if child.returncode == 0
                           and phases == expected_phases
                           and len(finals) == 1
                           and finals[0].get("sha256") == expected_sha
                           and finals[0].get("length") == SIZE
                           and finals[0].get("verified_files") == 1
                           else "CONTROL_INVALID")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--worker", choices=["stable", "replace", "truncate"])
    ap.add_argument("--archive", type=Path)
    ap.add_argument("--replacement", type=Path)
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    if args.worker:
        if args.archive is None:
            ap.error("--archive is required for a worker")
        return worker(args.worker, args.archive, args.replacement)
    if args.output is None:
        ap.error("--output is required for the parent")
    with tempfile.TemporaryDirectory(prefix="cmpct-o103-science-") as temp:
        root = Path(temp)
        cases = []
        for mode in ("stable", "replace", "truncate"):
            sub = root / mode
            sub.mkdir()
            src_archive, raw = make_archive(sub, "original", 103)
            newer, newer_raw = make_archive(sub, "replacement", 104)
            assert digest(raw) != digest(newer_raw)
            cases.append(case(mode, src_archive, newer, digest(raw)))
    expected = ["CONTROL_VALID", "CONTROL_VALID", "SAME_INODE_MMAP_SIGBUS_CONFIRMED"]
    actual = [x["decision"] for x in cases]
    result = {
        "schema": "cmpct-o103-mmap-lifetime-v1",
        "source_reader_git_blob": "e716233403dabd0966863c45635e18fa5ac6afb8",
        "platform": sys.platform,
        "observations": cases,
        "decision": "READER_MMAP_SAME_INODE_SIGBUS_CONFIRMED" if actual == expected
                    else "READER_MMAP_FALSIFIER_NOT_CONFIRMED",
        "negative_science_not_product_success": True,
        "scope": "installed r24, original Reader, disposable child, same inode truncation",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"decision": result["decision"], "case_decisions": actual,
                      "platform": sys.platform}))
    return 0 if actual == expected else 2


if __name__ == "__main__":
    raise SystemExit(main())
