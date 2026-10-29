"""J24G42: read-only Darwin filesystem-compression xattr visibility O0.

No CMPCT product mutation, no user-data scanning. The instrument distinguishes
an observable native metadata enumeration gap from ordinary xattr fidelity.
"""
from __future__ import annotations

import argparse
import ctypes
import errno
import json
import os
from pathlib import Path
import platform
import stat
import subprocess
import sys
import tempfile
import time

DEFAULT_FLAGS = 0x0001      # Darwin XATTR_NOFOLLOW
SHOW_COMPRESSION = 0x0020   # Darwin XATTR_SHOWCOMPRESSION
MAX_LIST = 4 * 1024 * 1024
MAX_FILES = 6000
MAX_DIRS = 1200
MAX_SECONDS = 90
MAX_COMPRESSED = 8
ROOTS = (
    "/usr/bin", "/bin", "/usr/sbin",
    "/System/Library/CoreServices",
    "/System/Library/Frameworks",
    "/System/Library/PrivateFrameworks",
)
COMPRESSION_KEYS = {"com.apple.decmpfs", "com.apple.ResourceFork"}


def native_names(api, path: str, flags: int):
    raw_path = os.fsencode(path)
    for attempt in range(3):
        ctypes.set_errno(0)
        n = api(raw_path, None, 0, flags)
        if n < 0:
            err = ctypes.get_errno() or errno.EIO
            raise OSError(err, os.strerror(err), path)
        if n > MAX_LIST:
            raise OSError(errno.E2BIG, "native name-list limit", path)
        buf = ctypes.create_string_buffer(max(n, 1))
        ctypes.set_errno(0)
        got = api(raw_path, buf, n, flags)
        if got < 0:
            err = ctypes.get_errno() or errno.EIO
            if err == errno.ERANGE and attempt < 2:
                continue
            raise OSError(err, os.strerror(err), path)
        if got > n:
            raise OSError(errno.EIO, "native list length exceeded probe", path)
        payload = buf.raw[:got]
        if not payload:
            return []
        if not payload.endswith(b"\0"):
            raise OSError(errno.EIO, "native unterminated name list", path)
        names = payload[:-1].split(b"\0")
        if any(not x for x in names):
            raise OSError(errno.EIO, "native empty name", path)
        return sorted(x.decode("utf-8", "strict") for x in names)
    raise AssertionError("bounded retry exhausted")


def native_api():
    lib = ctypes.CDLL(None, use_errno=True)
    fn = lib.listxattr
    fn.argtypes = [ctypes.c_char_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.c_int]
    fn.restype = ctypes.c_ssize_t
    return fn


def candidates():
    dirs = list(ROOTS)
    seen_dirs = set()
    seen_files = set()
    visited = 0
    walked = 0
    start = time.monotonic()
    while dirs and visited < MAX_FILES and walked < MAX_DIRS:
        if time.monotonic() - start > MAX_SECONDS:
            break
        directory = dirs.pop(0)
        try:
            st = os.stat(directory, follow_symlinks=False)
            key = (st.st_dev, st.st_ino)
            if key in seen_dirs or not stat.S_ISDIR(st.st_mode):
                continue
            seen_dirs.add(key)
            with os.scandir(directory) as it:
                entries = sorted(it, key=lambda x: x.name)
        except OSError:
            continue
        walked += 1
        for ent in entries:
            if visited >= MAX_FILES or time.monotonic() - start > MAX_SECONDS:
                break
            try:
                st = ent.stat(follow_symlinks=False)
            except OSError:
                continue
            if stat.S_ISDIR(st.st_mode):
                if len(dirs) < MAX_DIRS * 3:
                    dirs.append(ent.path)
            elif stat.S_ISREG(st.st_mode):
                key = (st.st_dev, st.st_ino)
                if key in seen_files:
                    continue
                seen_files.add(key)
                visited += 1
                if getattr(st, "st_flags", 0) & getattr(stat, "UF_COMPRESSED", 0x20):
                    yield ent.path, int(st.st_flags), visited, walked
    # Counts are observational only; no assertion that a host must have compressed files.


def check_synthetic_positive(api):
    from cmpct import _xattrs
    key = "com.fcmo.j24g42"
    value = b"\x00xattr visibility probe\xff"
    with tempfile.TemporaryDirectory(prefix="j24g42-") as td:
        leaf = Path(td) / "positive.bin"
        leaf.write_bytes(b"J24G42 plain data")
        created = subprocess.run(
            ["/usr/bin/xattr", "-wx", key, value.hex(), str(leaf)],
            capture_output=True, text=True,
        )
        if created.returncode:
            return {"ok": False, "reason": "synthetic xattr write failed",
                    "stderr": created.stderr[:400]}
        standard = native_names(api, str(leaf), DEFAULT_FLAGS)
        augmented = native_names(api, str(leaf), DEFAULT_FLAGS | SHOW_COMPRESSION)
        adapted = sorted(_xattrs.listxattr(leaf, follow_symlinks=False))
        got = _xattrs.getxattr(leaf, key, follow_symlinks=False)
        ok = key in standard and key in augmented and key in adapted and got == value
        return {"ok": ok, "native_default_contains": key in standard,
                "native_show_contains": key in augmented,
                "candidate_provider_contains": key in adapted,
                "value_identity": got == value}


def run(head):
    record = {
        "schema": "j24g42-darwin-compressed-xattr-visibility-v1",
        "source_head": head, "platform": sys.platform,
        "os": platform.platform(), "python": sys.version.split()[0],
        "darwin_constants": {"NOFOLLOW": DEFAULT_FLAGS, "SHOWCOMPRESSION": SHOW_COMPRESSION,
                             "UF_COMPRESSED": getattr(stat, "UF_COMPRESSED", None)},
        "scan_bounds": {"files": MAX_FILES, "dirs": MAX_DIRS,
                         "seconds": MAX_SECONDS, "compressed_cases": MAX_COMPRESSED},
        "specimens": [],
    }
    if sys.platform != "darwin":
        record.update(decision="INCONCLUSIVE_NON_DARWIN")
        return record
    fn = native_api()
    try:
        record["synthetic_control"] = check_synthetic_positive(fn)
    except (OSError, ValueError) as exc:
        record["synthetic_control"] = {"ok": False, "error": repr(exc)}
    for path, flags, visited, walked in candidates():
        case = {"path": path, "st_flags": flags, "regular_file_ordinal": visited,
                "directory_ordinal": walked}
        try:
            normal = native_names(fn, path, DEFAULT_FLAGS)
            special = native_names(fn, path, DEFAULT_FLAGS | SHOW_COMPRESSION)
            from cmpct import _xattrs
            adapted = sorted(_xattrs.listxattr(path, follow_symlinks=False))
            extra = sorted(set(special) - set(normal))
            case.update(native_default_names=normal, native_show_names=special,
                        provider_matches_default=(adapted == normal),
                        newly_visible_names=extra,
                        compression_hidden=bool(COMPRESSION_KEYS.intersection(extra)))
        except (OSError, UnicodeError) as exc:
            case["error"] = repr(exc)
        record["specimens"].append(case)
        if case.get("compression_hidden") or len(record["specimens"]) >= MAX_COMPRESSED:
            break
    record["compressed_observed"] = len(record["specimens"])
    record["compressed_successful"] = sum("native_show_names" in x for x in record["specimens"])
    record["hidden_positive"] = any(x.get("compression_hidden") for x in record["specimens"])
    if not record["synthetic_control"].get("ok"):
        record["decision"] = "INCONCLUSIVE_CONTROL_FAILURE"
    elif record["hidden_positive"]:
        record["decision"] = "VISIBILITY_GAP_POSITIVE"
    elif record["compressed_successful"] >= 3:
        record["decision"] = "NO_GAP_OBSERVED_ON_SAMPLED_HOST"
    else:
        record["decision"] = "INCONCLUSIVE_INSUFFICIENT_COMPRESSED_SPECIMENS"
    return record


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-head", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = run(args.source_head)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"decision": result["decision"],
                      "compressed_observed": result.get("compressed_observed", 0),
                      "compressed_successful": result.get("compressed_successful", 0),
                      "hidden_positive": result.get("hidden_positive", False),
                      "synthetic_control": result.get("synthetic_control")}, sort_keys=True))
    # Outcome may honestly be inconclusive; fail only on instrument/control errors.
    if result["decision"] == "INCONCLUSIVE_CONTROL_FAILURE":
        sys.exit(2)
