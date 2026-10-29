#!/usr/bin/env python3
"""J24G40 independent Darwin native-xattr witness, never a product green."""
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile

from cmpct.builder import Builder
from cmpct.reader import CMPCT
from cmpct.transactions import _compaction_source_metadata, compact_archive


def cmd(*argv):
    p = subprocess.run(argv, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return {"argv": list(argv[:2]), "returncode": p.returncode,
            "stdout": p.stdout.strip(), "stderr": p.stderr.strip()}


def run():
    report = {
        "court": "J24G40-native-darwin-xattr-capability",
        "platform": platform.platform(),
        "has_python_setxattr": hasattr(os, "setxattr"),
        "has_python_listxattr": hasattr(os, "listxattr"),
        "has_python_getxattr": hasattr(os, "getxattr"),
        "classification": "NOT_YET_TESTED",
    }
    if sys.platform != "darwin":
        report["classification"] = "NOT_DARWIN"
        return report
    exe = shutil.which("xattr")
    report["native_xattr_command"] = bool(exe)
    if not exe:
        report["classification"] = "NATIVE_TOOL_UNAVAILABLE"
        return report
    key = "com.fcmo.cmpct-j24g40"
    value = "J24G40 POSIX metadata exactness witness"
    with tempfile.TemporaryDirectory(prefix="j24g40-macos-native-") as td:
        root = Path(td) / "input"
        root.mkdir()
        member = root / "test.dat"
        original_bytes = b"J24G40-NATIVE-XATTR" * 17
        member.write_bytes(original_bytes)
        write = cmd(exe, "-w", key, value, str(member))
        read = cmd(exe, "-p", key, str(member))
        listed = cmd(exe, str(member))
        report["write_status"] = write
        report["read_status"] = read
        report["list_status"] = listed
        report["native_set_get_list_success"] = (
            write["returncode"] == 0 and read["returncode"] == 0
            and listed["returncode"] == 0 and read["stdout"] == value
            and key in listed["stdout"].splitlines()
        )
        if not report["native_set_get_list_success"]:
            report["classification"] = "OS_TOOL_OR_FILESYSTEM_NO_XATTR"
            return report
        archive = Path(td) / "before.cmpct"
        compacted = Path(td) / "after.cmpct"
        Builder(root,workers=1,reproducible=False).build(archive)
        with CMPCT(archive) as ar:
            initial = _compaction_source_metadata(ar)
            report["builder_xattr_keys"] = sorted(initial["test.dat"][5])
            report["builder_has_native_xattr"] = initial["test.dat"][5].get(key) == value.encode()
            report["builder_verify"] = ar.verify()
            report["logical_bytes_correct"] = ar.read("test.dat") == original_bytes
        source_sha = hashlib.sha256(archive.read_bytes()).hexdigest()
        try:
            compact_archive(archive,compacted)
            with CMPCT(compacted) as ar:
                after = _compaction_source_metadata(ar)
                report["after_xattr_keys"] = sorted(after["test.dat"][5])
                report["compacted_verify"] = ar.verify()
                report["compacted_contents_correct"] = ar.read("test.dat") == original_bytes
        except Exception as ex:
            report["compaction_error"] = {"type":type(ex).__name__,"message":str(ex)}
        report["source_sha_unchanged"] = hashlib.sha256(archive.read_bytes()).hexdigest() == source_sha
        report["classification"] = (
            "OS_NATIVE_XATTR_LOST_AT_BUILDER_ADMISSION"
            if not report["builder_has_native_xattr"] and report["logical_bytes_correct"]
            else "BUILDER_CAPTURE_PRESENT"
            if report["builder_has_native_xattr"] else "AMBIGUOUS_OR_FAILED"
        )
    return report


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    # The negative outcome is an independent scientific observation, not a
    # purported product pass. Require the native OS control before judging.
    if sys.platform == "darwin":
        if not result.get("native_set_get_list_success"):
            raise SystemExit("native macOS xattr capability unproved; not a product pass")
        if not result.get("logical_bytes_correct") or not result.get("source_sha_unchanged"):
            raise SystemExit("test failed basic content/source identity")
