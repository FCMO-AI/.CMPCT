#!/usr/bin/env python3
"""J24I66: three-host actual native C ABI, authenticated held-index ownership.

Experimental cross-platform court: no Python CMPCT imports and no Builder input.
Fixed independently authenticated J24I63 A/B r24 archives; no new format.
The stable same-inode overwrite is NOT a concurrent-write atomicity claim.
"""
from __future__ import annotations

import argparse
import base64
import ctypes
import hashlib
import json
import os
import platform
import subprocess
import sys
import tempfile
from pathlib import Path


A_SHA = "5d1638fbe6e7b185dbbb04d5cf37c6a49dd90bad8bebc156fa072a3195c1893d"
B_SHA = "9528d510467ae30694d0ea7d69b0ca6b4896e84ebc99f399d498843f1aca79bc"
A_B64 = "Q01QQ1QyNAAYAAAAPQAAAAAAAAA0AAAAAAAAAIAAAAAAAAAA7iAGrptkJliJ9cTAcAWIQapAtZJF7U1QOGO+9EdH5DAotS/9IDShAQCEoXYYpWZpbGVzkZencmF3LmJpbgDNAaQAQMCSAAClYmxvYnORlQBAQAAAp3JlY2lwZXOQQ01BNAAAAABAAAAAAAAAAEAAAAAAAAAAAAAAAIzODhD96rms83EDYr0mWM3Jop6PnHV/z5gRYDqMRHzR2RURCAABAgMEBQYHCAkKCwwNDg8QERITFBUWFxgZGhscHR4fICEiIyQlJicoKSorLC0uLzAxMjM0NTY3ODk6Ozw9Pj8otS/9IDShAQCEoXYYpWZpbGVzkZencmF3LmJpbgDNAaQAQMCSAAClYmxvYnORlQBAQAAAp3JlY2lwZXOQQ01QVEYyNAAAAQAAPQAAAAAAAAA0AAAAAAAAAAAAAAAAAAAA7iAGrptkJliJ9cTAcAWIQapAtZJF7U1QOGO+9EdH5DA="
B_B64 = "Q01QQ1QyNAAYAAAAPQAAAAAAAAA0AAAAAAAAAIAAAAAAAAAApfRMLy7djVVR4Pec6y5AlIX5Na5rcBwXseiREqplkD4otS/9IDShAQCEoXYYpWZpbGVzkZenbmV3LmJpbgDNAaQAQMCSAAClYmxvYnORlQBAQAAAp3JlY2lwZXOQQ01BNAAAAABAAAAAAAAAAEAAAAAAAAAAAAAAAIzODhD96rms83EDYr0mWM3Jop6PnHV/z5gRYDqMRHzR2RURCAABAgMEBQYHCAkKCwwNDg8QERITFBUWFxgZGhscHR4fICEiIyQlJicoKSorLC0uLzAxMjM0NTY3ODk6Ozw9Pj8otS/9IDShAQCEoXYYpWZpbGVzkZenbmV3LmJpbgDNAaQAQMCSAAClYmxvYnORlQBAQAAAp3JlY2lwZXOQQ01QVEYyNAAAAQAAPQAAAAAAAAA0AAAAAAAAAAAAAAAAAAAApfRMLy7djVVR4Pec6y5AlIX5Na5rcBwXseiREqplkD4="
ROOT = Path(__file__).resolve().parents[1]


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def native_paths() -> tuple[Path, Path]:
    prefix = ROOT / "native" / "cmpct-core" / "target" / "release"
    if sys.platform == "win32":
        return prefix / "cmpct_core.dll", prefix / "cmpct-native.exe"
    if sys.platform == "darwin":
        return prefix / "libcmpct_core.dylib", prefix / "cmpct-native"
    return prefix / "libcmpct_core.so", prefix / "cmpct-native"


def overwrite_same_inode(path: Path, body: bytes, prior: os.stat_result) -> dict:
    assert len(body) == prior.st_size == 386, "must not change length"
    with path.open("r+b", buffering=0) as writable:
        assert writable.write(body) == len(body), "incomplete in-place write"
        os.fsync(writable.fileno())
    new = path.stat()
    assert (new.st_dev, new.st_ino) == (prior.st_dev, prior.st_ino), (
        "underlying file identity changed", prior, new
    )
    assert new.st_size == prior.st_size
    assert digest(path.read_bytes()) == digest(body)
    return {"dev": new.st_dev, "ino": new.st_ino, "size": new.st_size, "sha256": digest(body)}


def court(receipt: dict) -> None:
    a = base64.b64decode(A_B64, validate=True)
    b = base64.b64decode(B_B64, validate=True)
    assert len(a) == len(b) == 386
    assert digest(a) == A_SHA and digest(b) == B_SHA
    assert a[129:257] == b[129:257] and a[129:133] == b"CMA4"
    assert a[:68] != b[:68], "authenticated header control did not change"
    receipt["fixtures"] = {
        "a_sha256": A_SHA,
        "b_sha256": B_SHA,
        "length": 386,
        "identical_cma4_bytes": 128,
    }
    library, cli = native_paths()
    assert library.is_file() and cli.is_file(), (library, cli)
    receipt["native"] = {"library": str(library), "sha256": digest(library.read_bytes())}
    lib = ctypes.CDLL(str(library))
    lib.cmpct_open.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_void_p)]
    lib.cmpct_open.restype = ctypes.c_int32
    lib.cmpct_verify_complete.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_size_t)]
    lib.cmpct_verify_complete.restype = ctypes.c_int32
    lib.cmpct_close.argtypes = [ctypes.c_void_p]
    lib.cmpct_close.restype = None

    def open_handle(path: Path) -> ctypes.c_void_p:
        handle = ctypes.c_void_p()
        result = lib.cmpct_open(os.fsencode(path), ctypes.byref(handle))
        assert result == 0 and handle.value, ("native open failed", result, path)
        return handle

    def verify(handle: ctypes.c_void_p) -> tuple[int, int]:
        count = ctypes.c_size_t(999)
        status = int(lib.cmpct_verify_complete(handle, ctypes.byref(count)))
        return status, count.value

    def fresh(path: Path) -> tuple[int, int]:
        handle = open_handle(path)
        try:
            return verify(handle)
        finally:
            lib.cmpct_close(handle)

    def cli_verify(path: Path) -> dict:
        run = subprocess.run([str(cli), "verify", str(path)], capture_output=True, check=False)
        assert run.returncode == 0, (path, run.returncode, run.stderr[:200])
        obj = json.loads(run.stdout)
        assert obj == {"revision": 24, "verified": 1}, obj
        return obj

    with tempfile.TemporaryDirectory(prefix="cmpct-j24i66-") as tmp:
        p = Path(tmp) / "held-A.cmpct"
        q = Path(tmp) / "fresh-B.cmpct"
        p.write_bytes(a)
        q.write_bytes(b)
        receipt["fresh_a"] = fresh(p)
        receipt["fresh_b"] = fresh(q)
        assert receipt["fresh_a"] == (0, 1) and receipt["fresh_b"] == (0, 1)
        receipt["cli_a"] = cli_verify(p)
        receipt["cli_b"] = cli_verify(q)
        original = p.stat()
        receipt["original_identity"] = {
            "dev": original.st_dev, "ino": original.st_ino, "size": original.st_size
        }

        held = open_handle(p)
        try:
            assert verify(held) == (0, 1)
            receipt["after_b_rewrite"] = overwrite_same_inode(p, b, original)
            receipt["held_a_over_b"] = verify(held)
            receipt["fresh_b_after_rewrite"] = fresh(p)
            assert receipt["held_a_over_b"] == (-7, 0), receipt["held_a_over_b"]
            assert receipt["fresh_b_after_rewrite"] == (0, 1)
            receipt["cli_after_b_rewrite"] = cli_verify(p)
            receipt["after_a_restore"] = overwrite_same_inode(p, a, original)
            receipt["held_a_restored"] = verify(held)
            receipt["fresh_a_restored"] = fresh(p)
            assert receipt["held_a_restored"] == (0, 1)
            assert receipt["fresh_a_restored"] == (0, 1)
            receipt["cli_a_restored"] = cli_verify(p)
            bad_count = ctypes.c_size_t(999)
            receipt["null_handle"] = [
                int(lib.cmpct_verify_complete(None, ctypes.byref(bad_count))),
                bad_count.value,
            ]
            assert receipt["null_handle"] == [-1, 0]
        finally:
            lib.cmpct_close(held)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    result = {
        "schema": "cmpct-j24i66-native-held-index-3os-v1",
        "source_sha": os.environ.get("EVIDENCE_HEAD", ""),
        "runner_os": os.environ.get("RUNNER_OS", platform.system()),
        "runner_arch": os.environ.get("RUNNER_ARCH", platform.machine()),
        "python": platform.python_version(),
        "passed": False,
        "error": None,
    }
    try:
        assert len(result["source_sha"]) == 40, "missing exact Git source SHA"
        court(result)
        result["passed"] = True
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
