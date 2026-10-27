#!/usr/bin/env python3
"""J24F12: authentic revision-24 Reader Linux write+search-only parent court.

The destination parent can create/traverse files but cannot be listed/opened
O_RDONLY. Linux anonymous temp files must use O_PATH parent *capability*;
a successful staged pathname fallback is not sufficient for fresh-leaf admission.
"""
from __future__ import annotations
import argparse
import errno
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import tempfile

from j24f04_raw_chunk_immutable_transfer import independent_revision24, blob_sha


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run_case(root: Path, kind: int, existing: bool) -> dict:
    from cmpct.reader import CMPCT

    chunks = [hashlib.shake_256(f"j24f12-{kind}-{i}".encode()).digest(100007 + i * 223)
              for i in range(3)]
    original = b"".join(chunks)
    name, archive, _ = independent_revision24(chunks, kind)
    source = root / "source.cmpct"
    source.write_bytes(archive)
    archive_sha = digest(archive)
    out = root / "write_search_only"
    out.mkdir(mode=0o700)
    leaf = out / name
    if existing:
        leaf.write_bytes(b"J24F12 existing file control")
    out.chmod(0o300)
    spy_log = []
    original_write = os.write
    try:
        # The historical parentfd open fails, although parent path writes are legal.
        assert os.geteuid() != 0, "run as ordinary unprivileged Linux account"
        try:
            parent_read_fd = os.open(out, os.O_RDONLY | os.O_DIRECTORY)
        except PermissionError as exc:
            assert exc.errno == errno.EACCES
        else:
            os.close(parent_read_fd)
            raise AssertionError("fixture does not distinguish O_RDONLY permission")

        # Confirm ordinary in-directory exclusive creation is allowed.
        fd, probe = tempfile.mkstemp(prefix=".j24f12-probe-", dir=out)
        os.close(fd)
        os.unlink(probe)

        def inspect_write(fd, data):
            if not spy_log:
                info = os.fstat(fd)
                spy_log.append({
                    "st_dev": info.st_dev, "st_ino": info.st_ino,
                    "st_nlink": info.st_nlink, "first_write_bytes": len(data),
                })
            return original_write(fd, data)

        with CMPCT(source) as reader:
            assert reader.by[name][6][0] == kind
            assert reader.by[name][4] == len(original)
            os.write = inspect_write
            try:
                reader.extractall(out, metadata=False)
            finally:
                os.write = original_write
    finally:
        os.write = original_write
        out.chmod(0o700)

    assert spy_log, "real extraction never wrote"
    stage = spy_log[0]
    assert 0 < stage["first_write_bytes"] <= 65536
    assert stage["st_nlink"] == (1 if existing else 0), (
        "fresh leaf must remain unnamed until verified; existing leaf keeps legacy stage", stage
    )
    st = leaf.stat()
    assert (st.st_dev, st.st_ino) == (stage["st_dev"], stage["st_ino"]), (
        "published inode must be the verified source descriptor"
    )
    assert leaf.read_bytes() == original
    assert digest(source.read_bytes()) == archive_sha
    assert not [p.name for p in out.iterdir() if ".cmpct-part-" in p.name]
    return {
        "kind": kind,
        "scenario": "existing" if existing else "fresh",
        "parent_mode": "0300",
        "uid": os.geteuid(),
        "parent_read_open": "EACCES",
        "anonymous_at_first_write": not existing,
        "first_write_bytes": stage["first_write_bytes"],
        "same_published_inode": True,
        "logical_sha": digest(original),
        "published_sha": digest(leaf.read_bytes()),
        "archive_sha": archive_sha,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--expected-blob", required=True)
    args = ap.parse_args()
    assert sys.platform.startswith("linux") and hasattr(os, "O_PATH") and hasattr(os, "O_TMPFILE")
    import cmpct.reader as module
    installed = Path(module.__file__).resolve()
    assert installed.is_relative_to(Path(sys.prefix)), installed
    assert blob_sha(installed.read_bytes()) == args.expected_blob
    cases = []
    with tempfile.TemporaryDirectory(prefix="cmpct-j24f12-") as temp:
        for kind in (1, 5):
            for existing in (False, True):
                root = Path(temp) / f"{kind}-{int(existing)}"
                root.mkdir()
                case = run_case(root, kind, existing)
                cases.append(case)
                print("J24F12_CASE=" + json.dumps(case, sort_keys=True), flush=True)
    assert len(cases) == 4
    result = {
        "schema": "j24f12-write-search-parent-v1",
        "source_blob": args.expected_blob,
        "cases": cases,
        "decision": "WX_ONLY_PARENT_EXACT_FD_TRANSFER_PASS",
        "nonclaims": ["existing-target concurrent publication safety",
                      "portable filesystem support", "macOS/Windows",
                      "complete performance", "release approval"],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True))
    print("J24F12_DECISION=" + result["decision"], flush=True)


if __name__ == "__main__":
    main()
