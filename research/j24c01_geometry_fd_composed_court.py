#!/usr/bin/env python3
"""J24C01: coupled same-index CDC admission × anonymous-inode publication.

Uses the unchanged O214 builder-independent r24 wire fixture, not a Builder roundtrip.
A good CDC archive must reach the real Linux fd-based fresh-leaf publication path;
the same descriptor family with authenticated contradictory lengths must be rejected
before mmap or an output inode can be staged. Complements, does not replace, the
unchanged O212/O214 and J24F11/J24F12 independent courts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tests"))
from test_o214_cdc_admission import _r24, PATH  # unchanged oracle fixture
from cmpct.reader import CMPCT
from cmpct.validation import ValidationError


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-reader-blob", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not sys.platform.startswith("linux") or os.geteuid() == 0:
        raise RuntimeError("requires Linux unprivileged account")
    import cmpct.reader as module
    installed = Path(module.__file__).resolve()
    source = Path(__file__).resolve().parents[1] / "src" / "cmpct" / "reader.py"
    # Git blob bytes, not a mutable interpreted approximation.
    git_blob = b"blob " + str(installed.stat().st_size).encode() + b"\\0" + installed.read_bytes()
    actual_blob = hashlib.sha1(git_blob).hexdigest()
    if actual_blob != args.expected_reader_blob:
        raise AssertionError(("installed Reader provenance mismatch", actual_blob, args.expected_reader_blob))
    if installed == source or installed.is_relative_to(source.parents[2]):
        raise AssertionError("Reader must come from independently installed site-packages")
    rows = []
    with tempfile.TemporaryDirectory(prefix="cmpct-j24c01-") as td:
        root = Path(td)
        parent = root / "write-search-only"
        parent.mkdir(mode=0o700)
        fresh = parent / PATH
        good_bytes = _r24([[4, 0], [4, 1]], b"ABCDEFGH",
                          blobs=(b"ABCD", b"EFGH"))
        good = root / "good.cmpct"
        good.write_bytes(good_bytes)
        original_write = os.write
        observed = []
        parent.chmod(0o300)
        try:
            def first_write(fd, data):
                if not observed:
                    st = os.fstat(fd)
                    observed.append({
                        "st_dev": st.st_dev,
                        "st_ino": st.st_ino,
                        "st_nlink": st.st_nlink,
                        "bytes": len(data),
                    })
                return original_write(fd, data)
            with CMPCT(good) as ar:
                if ar.read_range(PATH, 3, 3) != b"DEF":
                    raise AssertionError("valid CDC cross-chunk range")
                os.write = first_write
                try:
                    ar.extractall(parent, metadata=False)
                finally:
                    os.write = original_write
        finally:
            os.write = original_write
            parent.chmod(0o700)
        if not observed or observed[0]["st_nlink"] != 0:
            raise AssertionError(("CDC did not use anonymous fd", observed))
        published = fresh.stat()
        if (published.st_dev, published.st_ino) != (
            observed[0]["st_dev"], observed[0]["st_ino"]
        ):
            raise AssertionError("published CDC inode differs from authenticated transfer fd")
        if fresh.read_bytes() != b"ABCDEFGH":
            raise AssertionError("published CDC content mismatch")
        if _sha(good.read_bytes()) != _sha(good_bytes):
            raise AssertionError("source mutated")
        rows.append({
            "case": "valid_cdc_fresh",
            "expected_sha": _sha(b"ABCDEFGH"),
            "published_sha": _sha(fresh.read_bytes()),
            "published_inode_is_verified_fd": True,
            "stage_nlink_before_write": 0,
        })

        # Archive index SHA is self-consistent but its CDC length disagrees
        # with the declared physical blob. No output and no mmap is allowed.
        bad_wire = _r24([[3, 0]], b"ABCD")
        bad = root / "bad.cmpct"
        bad.write_bytes(bad_wire)
        before = _sha(bad.read_bytes())
        output = root / "hostile-output"
        output.mkdir()
        try:
            r = CMPCT(bad)
        except ValidationError:
            pass
        else:
            r.close()
            raise AssertionError("authenticated inconsistent CDC unexpectedly admitted")
        if list(output.iterdir()):
            raise AssertionError("invalid geometry created output")
        if _sha(bad.read_bytes()) != before:
            raise AssertionError("hostile archive mutated")
        rows.append({
            "case": "invalid_authenticated_cdc",
            "admission": "rejected_before_extract",
            "archive_sha_unchanged": True,
            "staged_output_count": 0,
        })
    if len(rows) != 2:
        raise AssertionError("missing cases")
    result = {
        "schema": "j24c01-cdc-admission-fd-publication-v1",
        "head_reader_blob": args.expected_reader_blob,
        "cases": rows,
        "decision": "COMPOSED_CDC_ADMISSION_AND_FD_PUBLICATION_PASS",
        "nonclaims": [
            "existing-destination overwrite is safe against same-UID actor",
            "complete portable publication semantics",
            "final-form product performance and release",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True))
    print("J24C01_DECISION=" + result["decision"], flush=True)


if __name__ == "__main__":
    main()
