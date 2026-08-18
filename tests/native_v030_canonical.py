#!/usr/bin/env python3
"""Canonical CMP25 native acceptance against builder-independent fixed bytes."""
from __future__ import annotations

import base64
import ctypes
import hashlib
import json
import os
from pathlib import Path
import stat
import struct
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "conformance" / "v030-r25-canonical.json"
CLI = ROOT / "native" / "cmpct-portable" / "target" / "release" / "cmpct-portable"
LIB = ROOT / "native" / "cmpct-portable" / "target" / "release" / "libcmpct_portable.so"
G04_HEADER = struct.Struct("<8sQQIQQ32s32s")
G04_FOOTER = struct.Struct("<8sQQ32s32s")
PG_HEADER = struct.Struct("<8sQQ32s")
PG_FOOTER = struct.Struct("<8sQQ32s")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run(*args: str, check: bool = True, text: bool = False):
    return subprocess.run([str(CLI), *args], check=check, capture_output=True, text=text)


def materialize(tmp: Path, name: str, row: dict) -> Path:
    raw = base64.b64decode(row["archive_base64"], validate=True)
    assert sha(raw) == row["archive_sha256"]
    path = tmp / f"canonical-{name}.cmpct"
    path.write_bytes(raw)
    return path


def info(path: Path) -> dict[str, str]:
    return dict(line.split("=", 1) for line in run("info", str(path), text=True).stdout.strip().splitlines())


def listed(path: Path) -> list[tuple[int, int, int, str]]:
    rows = []
    for line in run("list", str(path), text=True).stdout.strip().splitlines():
        index, kind, size, rel = line.split("\t", 3)
        rows.append((int(index), int(kind), int(size), rel))
    return rows


def assert_product_view(name: str, path: Path, fixture: dict, tmp: Path) -> None:
    row = fixture[name]
    fs = fixture["filesystem"]
    metadata = info(path)
    assert metadata["profile"] == row["profile"]
    assert int(metadata["revision"]) == 25
    assert metadata["tail_metadata_authenticated"] == "true"

    rows = listed(path)
    assert {rel for _, _, _, rel in rows} == set(fs["entries"])
    assert fs["internal_path"] not in {rel for _, _, _, rel in rows}
    by_path = {rel: (kind, size) for _, kind, size, rel in rows}
    for rel, expected in fs["entries"].items():
        assert by_path[rel] == (expected["kind"], expected["size"])

    run("verify", str(path))
    regular = fs["entries"]["dir/hello.bin"]
    raw = run("read", str(path), "dir/hello.bin").stdout
    assert len(raw) == regular["size"] and sha(raw) == regular["sha256"]
    assert run("read", str(path), "dir/hello-hard.bin").stdout == raw
    assert run("read", str(path), "link.bin").stdout == b"dir/hello.bin"

    for rel in ("dir/hello.bin", "dir/hello-hard.bin"):
        stats = dict(line.split("=", 1) for line in run("member-stats", str(path), rel, text=True).stdout.strip().splitlines())
        assert int(stats["logical_bytes"]) == regular["size"]
        assert float(stats["amplification"]) <= 8.0

    destination = tmp / f"extract-{name}"
    run("extract", str(path), str(destination))
    restored = (destination / "dir/hello.bin").read_bytes()
    assert sha(restored) == regular["sha256"]
    assert (destination / "dir/hello-hard.bin").read_bytes() == restored
    if os.name == "posix":
        left = os.stat(destination / "dir/hello.bin")
        right = os.stat(destination / "dir/hello-hard.bin")
        assert left.st_ino == right.st_ino
        assert stat.S_IMODE(left.st_mode) == 0o640
        assert (destination / "link.bin").is_symlink()
        assert os.readlink(destination / "link.bin") == "dir/hello.bin"

    # Canonical fixture deliberately contains a symlink. Ordinary ZIP has no one portable symlink semantic;
    # refusing export is safer than silently changing the logical tree to make the gate green.
    exported = tmp / f"canonical-{name}.zip"
    assert run("export-zip", str(path), str(exported), check=False).returncode != 0


def recovery_variants(name: str, original: bytes) -> dict[str, tuple[bytes, bool]]:
    if name == "g04":
        header_size = G04_HEADER.size
        primary_size = G04_HEADER.unpack_from(original, 0)[1]
        footer_off = len(original) - G04_FOOTER.size
        tail_size = G04_FOOTER.unpack_from(original, footer_off)[1]
    else:
        header_size = PG_HEADER.size
        primary_size = PG_HEADER.unpack_from(original, 0)[1]
        footer_off = len(original) - PG_FOOTER.size
        tail_size = PG_FOOTER.unpack_from(original, footer_off)[1]
    tail_meta = footer_off - tail_size
    primary = bytearray(original); tail = bytearray(original); both = bytearray(original); payload = bytearray(original)
    p_index = header_size + min(8, primary_size - 1)
    t_index = tail_meta + min(8, tail_size - 1)
    primary[p_index] ^= 0x40
    tail[t_index] ^= 0x40
    both[p_index] ^= 0x40; both[t_index] ^= 0x40
    payload_start = header_size + primary_size
    payload[payload_start + (tail_meta - payload_start) // 2] ^= 0x01
    return {
        "primary-damaged": (bytes(primary), True),
        "tail-damaged": (bytes(tail), True),
        "both-metadata-damaged": (bytes(both), False),
        "payload-damaged": (bytes(payload), False),
    }


def assert_recovery(name: str, path: Path, tmp: Path) -> None:
    for label, (raw, should_verify) in recovery_variants(name, path.read_bytes()).items():
        candidate = tmp / f"canonical-{name}-{label}.cmpct"
        candidate.write_bytes(raw)
        result = run("verify", str(candidate), check=False, text=True)
        assert (result.returncode == 0) is should_verify, (name, label, result.stdout, result.stderr)


def assert_c_abi(path: Path, fixture: dict) -> None:
    lib = ctypes.CDLL(str(LIB))
    handle = ctypes.c_void_p()
    lib.cmpct_portable_open.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_void_p)]
    lib.cmpct_portable_open.restype = ctypes.c_int32
    lib.cmpct_portable_close.argtypes = [ctypes.c_void_p]
    lib.cmpct_portable_revision.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint32)]
    lib.cmpct_portable_revision.restype = ctypes.c_int32
    lib.cmpct_portable_entry_count.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_size_t)]
    lib.cmpct_portable_entry_count.restype = ctypes.c_int32
    lib.cmpct_portable_verify.argtypes = [ctypes.c_void_p]
    lib.cmpct_portable_verify.restype = ctypes.c_int32
    assert lib.cmpct_portable_open(str(path).encode(), ctypes.byref(handle)) == 0
    try:
        revision = ctypes.c_uint32()
        count = ctypes.c_size_t()
        assert lib.cmpct_portable_revision(handle, ctypes.byref(revision)) == 0 and revision.value == 25
        assert lib.cmpct_portable_entry_count(handle, ctypes.byref(count)) == 0
        assert count.value == len(fixture["filesystem"]["entries"])
        assert lib.cmpct_portable_verify(handle) == 0
    finally:
        lib.cmpct_portable_close(handle)


def main() -> None:
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert fixture["schema"] == "cmpct-v030-native-canonical-golden-v1"
    assert CLI.is_file() and LIB.is_file()
    with tempfile.TemporaryDirectory(prefix="cmpct-v030-canonical-") as td:
        tmp = Path(td)
        for name in ("g04", "prefixgraph"):
            path = materialize(tmp, name, fixture[name])
            assert_product_view(name, path, fixture, tmp)
            assert_recovery(name, path, tmp)
            assert_c_abi(path, fixture)
    print("v0.30 canonical CMP25 native acceptance: ok")


if __name__ == "__main__":
    main()

# Footnote: the golden archive bytes come from an independent primitive grammar generator, not the product
# encoder. Recovery, user/internal view separation, <=8x member locality, extraction and the C ABI therefore
# receive an independent byte-level oracle rather than a self-consistency test.
