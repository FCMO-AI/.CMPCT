#!/usr/bin/env python3
"""J24G40: distinguish OS xattr fixture admission from actual CMPCT metadata loss.

Research court only. Original J24I06 test remains untouched.
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import sys
import tempfile
from pathlib import Path

from cmpct.builder import Builder
from cmpct.reader import CMPCT
from cmpct.transactions import _compaction_source_metadata, compact_archive

KEYS = ("user.cmpct-j24i06", "com.fcmo.cmpct-j24i06")
VALUE = b"J24G40 PORTABLE XATTR EXACT BYTES\x00\xff"
DATA = b"J24G40 authentic CMPCT payload\n" * 13


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def probe_one(work: Path, key: str) -> dict:
    root = work / "root"
    root.mkdir()
    member = root / "blob.bin"
    member.write_bytes(DATA)
    out = {"key": key, "os_set": False, "os_list": False,
           "os_get": False, "builder_capture": None, "compaction_preserve": None,
           "source_sha_unchanged": None, "content_identical": None}
    if not all(hasattr(os, name) for name in ("setxattr", "listxattr", "getxattr")):
        out["os_error"] = "Python xattr functions absent"
        return out

    try:
        os.setxattr(member, key, VALUE)
        out["os_set"] = True
    except (OSError, ValueError, TypeError) as ex:
        out["os_error"] = {"class": type(ex).__name__,
                           "errno": getattr(ex, "errno", None),
                           "strerror": getattr(ex, "strerror", str(ex))}
        return out

    names = os.listxattr(member, follow_symlinks=False)
    out["os_list"] = key in names
    try:
        got = os.getxattr(member, key, follow_symlinks=False)
        out["os_get"] = got == VALUE
    except OSError as ex:
        out["os_get_error"] = {"errno": ex.errno, "strerror": ex.strerror}
    if not (out["os_list"] and out["os_get"]):
        # A successful setxattr without independent readback cannot be used as
        # an admissible product metadata fixture.
        return out

    source, compacted = work / "before.cmpct", work / "after.cmpct"
    Builder(root, workers=1, reproducible=False).build(source)
    initial_wire_sha = sha(source)
    with CMPCT(source) as ar:
        before = _compaction_source_metadata(ar)
        out["original_verify"] = ar.verify()
        out["builder_capture"] = before["blob.bin"][5].get(key) == VALUE
        out["before_fsmeta_keys"] = sorted(before["blob.bin"][5])
        out["before_logical_sha"] = ar.file_sha256("blob.bin").hex()
        out["before_payload_sha"] = hashlib.sha256(ar.read("blob.bin")).hexdigest()

    # Test the *existing* owner implementation without altering source,
    # interpreting the return as a metrics dict, not a path.
    try:
        out["compact_metrics"] = compact_archive(source, compacted)
        with CMPCT(compacted) as ar:
            after = _compaction_source_metadata(ar)
            out["compacted_verify"] = ar.verify()
            out["compaction_preserve"] = before == after
            out["after_fsmeta_keys"] = sorted(after["blob.bin"][5])
            out["content_identical"] = ar.read("blob.bin") == DATA
            out["after_logical_sha"] = ar.file_sha256("blob.bin").hex()
    except Exception as ex:
        out["compaction_error"] = {"class": type(ex).__name__, "message": str(ex)}
        out["compaction_preserve"] = False
        out["content_identical"] = False

    out["source_sha_unchanged"] = sha(source) == initial_wire_sha
    out["source_archive_bytes"] = source.stat().st_size
    if compacted.exists():
        out["compacted_archive_bytes"] = compacted.stat().st_size
    return out


def main() -> int:
    report = {
        "court": "J24G40-xattr-portability-root-cause",
        "source": "unmodified J24G38 #745 product, J24I06 inherited test retained",
        "platform": platform.platform(),
        "os_name": os.name,
        "sys_platform": sys.platform,
        "uid": os.geteuid() if hasattr(os, "geteuid") else None,
        "cases": [],
    }
    with tempfile.TemporaryDirectory(prefix="j24g40-") as td:
        for i, key in enumerate(KEYS):
            p = Path(td) / f"case-{i}"
            p.mkdir()
            report["cases"].append(probe_one(p, key))

    primary_key = KEYS[1] if sys.platform == "darwin" else KEYS[0]
    primary = next(c for c in report["cases"] if c["key"] == primary_key)
    old = report["cases"][0]
    report["primary_key"] = primary_key
    report["original_literal_user_key_admitted"] = bool(old["os_set"] and old["os_list"] and old["os_get"])
    report["primary_key_admitted"] = bool(primary["os_set"] and primary["os_list"] and primary["os_get"])
    report["primary_builder_capture"] = primary["builder_capture"]
    report["primary_compaction_preserve"] = primary["compaction_preserve"]
    report["primary_content_identity"] = primary["content_identical"]
    report["hypothesis_classification"] = (
        "OS_NAME_MISMATCH" if sys.platform == "darwin" and
        not report["original_literal_user_key_admitted"] and report["primary_key_admitted"]
        else "BOTH_KEYS_ADMITTED" if all(c["os_set"] and c["os_list"] and c["os_get"] for c in report["cases"])
        else "NO_NATIVE_XATTR_CAPABILITY" if not report["primary_key_admitted"]
        else "NATIVE_KEY_SUPPORTED_OTHER_CAUSE"
    )
    print(json.dumps(report, sort_keys=True, indent=2, default=str))
    # Do not turn absent capability into an empty/successful fixture, and do not
    # turn real metadata loss into a green infrastructure diagnostic.
    if not report["primary_key_admitted"]:
        raise AssertionError("NO_NATIVE_XATTR_CAPABILITY: cannot assert xattr-preserving compaction")
    for key in ("primary_builder_capture", "primary_compaction_preserve",
                "primary_content_identity"):
        if report[key] is not True:
            raise AssertionError(f"genuine xattr/product invariant failed: {key}")
    if primary["source_sha_unchanged"] is not True:
        raise AssertionError("compaction mutated original source")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
