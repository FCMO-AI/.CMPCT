#!/usr/bin/env python3
"""Canonical CMP25 native acceptance tests against builder-independent fixed bytes."""
from __future__ import annotations

import base64
import ctypes
import hashlib
import json
import os
from pathlib import Path
import shutil
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
    assert sha(raw) == row["archive_sha256"], (name, sha(raw), row["archive_sha256"])
    path = tmp / f"canonical-{name}.cmpct"
    path.write_bytes(raw)
    return path


def parse_info(path: Path) -> dict[str, str]:
    result = run("info", str(path), text=True).stdout
    return dict(line.split("=", 1) for line in result.strip().splitlines())


def list_rows(path: Path) -> list[tuple[int, int, int, str]]:
    rows = []
    for line in run("list", str(path), text=True).stdout.strip().splitlines():
        index, kind, size, rel = line.split("\t", 3)
        rows.append((int(index), int(kind), int(size), rel))
    return rows


def assert_product_view(name: str, path: Path, fixture: dict, tmp: Path) -> None:
    row = fixture[name]
    fs = fixture["filesystem"]
    info = parse_info(path)
    assert info["profile"] == row["profile"], (name, info)
    assert int(info["revision"]) == 25, (name, info)
    assert info["tail_metadata_authenticated"] == "true", (name, info)

    rows = list_rows(path)
    expected = fs["entries"]
    assert len(rows) == len(expected), (name, rows, expected)
    paths = {rel for _, _, _, rel in rows}
    assert paths == set(expected), (name, paths, expected)
    assert fs["internal_path"] not in paths

    by_path = {rel: (index, kind, size) for index, kind, size, rel in rows}
    for rel, expected_row in expected.items():
        _, kind, size = by_path[rel]
        assert kind == expected_row["kind"], (name, rel, kind, expected_row)
        assert size == expected_row["size"], (name, rel, size, expected_row)

    run("verify", str(path))

    regular = expected["dir/hello.bin"]
    raw = run("read", str(path), "dir/hello.bin").stdout
    assert len(raw) == regular["size"] and sha(raw) == regular["sha256"]
    hard = run("read", str(path), "dir/hello-hard.bin").stdout
    assert hard == raw
    link = run("read", str(path), "link.bin").stdout
    assert link == expected["link.bin"]["target"].encode()
    directory = run("read", str(path), "dir", check=False, text=True)
    assert directory.returncode != 0

    for rel in ("dir/hello.bin", "dir/hello-hard.bin"):
        stats = dict(
            line.split("=", 1)
            for line in run("member-stats", str(path), rel, text=True).stdout.strip().splitlines()
        )
        assert int(stats["logical_bytes"]) == regular["size"]
        assert float(stats["amplification"]) <= 8.0, (name, rel, stats)

    destination = tmp / f"extract-{name}"
    run("extract", str(path), str(destination))
    assert (destination / "dir").is_dir()
    restored = (destination / "dir/hello.bin").read_bytes()
    assert sha(restored) == regular["sha256"]
    assert (destination / "dir/hello-hard.bin").read_bytes() == restored
    if os.name == "posix":
        left = os.stat(destination / "dir/hello.bin")
        right = os.stat(destination / "dir/hello-hard.bin")
        assert left.st_ino == right.st_ino, (name, left.st_ino, right.st_ino)
        assert stat.S_IMODE(left.st_mode) == 0o640
        link_path = destination / "link.bin"
        assert link_path.is_symlink()
        assert os.readlink(link_path) == expected["link.bin"]["target"]

    # Canonical fixture deliberately contains a symlink. ZIP has no single portable
    # symlink semantic, so the exporter must refuse instead of silently changing data.
    exported = tmp / f"canonical-{name}.zip"
    zip_result = run("export-zip", str(path), str(exported), check=False, text=True)
    assert zip_result.returncode != 0, (name, zip_result.stdout, zip_result.stderr)


def recovery_variants(name: str, original: bytes) -> dict[str, tuple[bytes, bool]]:
    if name == "g04":
        header_size = G04_HEADER.size
        mcs = G04_HEADER.unpack_from(original, 0)[1]
        footer_off = len(original) - G04_FOOTER.size
        tail_mcs = G04_FOOTER.unpack_from(original, footer_off)[1]
    else:
        header_size = PG_HEADER.size
        mcs = PG_HEADER.unpack_from(original, 0)[1]
        footer_off = len(original) - PG_FOOTER.size
        tail_mcs = PG_FOOTER.unpack_from(original, footer_off)[1]
    tail_meta = footer_off - tail_mcs
    assert mcs > 8 and tail_mcs > 8 and tail_meta > header_size + mcs

    primary = bytearray(original)
    tail = bytearray(original)
    both = bytearray(original)
    payload = bytearray(original)
    p_index = header_size + min(8, mcs - 1)
    t_index = tail_meta + min(8, tail_mcs - 1)
    primary[p_index] ^= 0x40
    tail[t_index] ^= 0x40
    both[p_index] ^= 0x40
    both[t_index] ^= 0x40
    payload_start = header_size + mcs
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
        assert (result.returncode == 0) is should_verify, (
            name,
            label,
            result.stdout,
            result.stderr,
        )


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
    lib.cmpct_portable_entry_path.argtypes = [
        ctypes.c_void_p,
        ctypes.c_size_t,
        ctypes.c_void_p,
        ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_size_t),
    ]
    lib.cmpct_portable_entry_path.restype = ctypes.c_int32
    lib.cmpct_portable_verify.argtypes = [ctypes.c_void_p]
    lib.cmpct_portable_verify.restype = ctypes.c_int32

    assert lib.cmpct_portable_open(str(path).encode(), ctypes.byref(handle)) == 0
    try:
        revision = ctypes.c_uint32()
        assert lib.cmpct_portable_revision(handle, ctypes.byref(revision)) == 0
        assert revision.value == 25
        count = ctypes.c_size_t()
        assert lib.cmpct_portable_entry_count(handle, ctypes.byref(count)) == 0
        assert count.value == len(fixture["filesystem"]["entries"])
        seen = set()
        for index in range(count.value):
            required = ctypes.c_size_t()
            assert lib.cmpct_portable_entry_path(handle, index, None, 0, ctypes.byref(required)) == 0
            buf = ctypes.create_string_buffer(required.value + 1)
            assert lib.cmpct_portable_entry_path(handle, index, buf, len(buf), ctypes.byref(required)) == 0
            seen.add(buf.raw[: required.value].decode())
        assert seen == set(fixture["filesystem"]["entries"])
        assert fixture["filesystem"]["internal_path"] not in seen
        assert lib.cmpct_portable_verify(handle) == 0
    finally:
        lib.cmpct_portable_close(handle)


def main() -> None:
    fixture = json.loads(FIXTURE.read_text())
    assert fixture["schema"] == "cmpct-v030-native-canonical-golden-v1"
    assert CLI.is_file(), CLI
    assert LIB.is_file(), LIB
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
