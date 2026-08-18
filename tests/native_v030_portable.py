#!/usr/bin/env python3
"""Cross-language conformance gate for the shared v0.30 portable reader.

The committed fixture is intentionally builder-independent: the exact archive bytes are fixed acceptance
oracles. This test asks both the Python release reader and the Rust CLI/ABI to consume those same bytes,
then mutates copies to exercise recovery and corruption refusal.
"""
from __future__ import annotations

import base64
import ctypes
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import zipfile

from experiments import entropygraph_v030_release_reader as PYREADER

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "conformance" / "v030-r25-portable.json"
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


def materialize_fixture(tmp: Path, name: str, row: dict) -> Path:
    data = base64.b64decode(row["archive_base64"], validate=True)
    assert sha(data) == row["archive_sha256"], (name, sha(data), row["archive_sha256"])
    path = tmp / f"{name}.cmpct"
    path.write_bytes(data)
    return path


def native_read(path: Path, member: str) -> bytes:
    return run("read", str(path), member).stdout


def assert_fixed_vector(name: str, path: Path, row: dict, tmp: Path) -> None:
    # Footnote: two independent reader implementations consume the exact same committed bytes. Agreement
    # here is materially stronger than building one archive twice with code that could share the same bug.
    py = PYREADER.strong_verify(path)
    assert py.get("ok") is True, (name, py)
    assert py["tree_sha256"] == row["tree_sha256"], (name, py)

    info = run("info", str(path), text=True).stdout
    assert f"entries={len(row['files'])}" in info
    assert "tail_metadata_authenticated=true" in info
    run("verify", str(path))

    for member, expected in row["files"].items():
        raw = native_read(path, member)
        assert len(raw) == expected["size"], (name, member, len(raw), expected["size"])
        assert sha(raw) == expected["sha256"], (name, member)
        stats = run("member-stats", str(path), member, text=True).stdout
        values = dict(line.split("=", 1) for line in stats.strip().splitlines())
        assert int(values["logical_bytes"]) == expected["size"]
        assert float(values["amplification"]) <= 8.0, (name, member, values)

    extracted = tmp / f"{name}-extract"
    run("extract", str(path), str(extracted))
    for member, expected in row["files"].items():
        raw = (extracted / member).read_bytes()
        assert len(raw) == expected["size"]
        assert sha(raw) == expected["sha256"]

    exported = tmp / f"{name}.zip"
    run("export-zip", str(path), str(exported))
    with zipfile.ZipFile(exported) as zf:
        assert sorted(zf.namelist()) == sorted(row["files"])
        for member, expected in row["files"].items():
            raw = zf.read(member)
            assert len(raw) == expected["size"]
            assert sha(raw) == expected["sha256"]


def recovery_copies(name: str, original: bytes) -> tuple[bytes, bytes, bytes, bytes]:
    primary = bytearray(original)
    tail = bytearray(original)
    both = bytearray(original)
    payload = bytearray(original)
    if name == "g04":
        mcs = G04_HEADER.unpack_from(original, 0)[1]
        footer_off = len(original) - G04_FOOTER.size
        tail_mcs = G04_FOOTER.unpack_from(original, footer_off)[1]
        tail_meta = footer_off - tail_mcs
        primary_meta = G04_HEADER.size
    else:
        mcs = PG_HEADER.unpack_from(original, 0)[1]
        footer_off = len(original) - PG_FOOTER.size
        tail_mcs = PG_FOOTER.unpack_from(original, footer_off)[1]
        tail_meta = footer_off - tail_mcs
        primary_meta = PG_HEADER.size
    assert mcs and tail_mcs

    # Damage compressed metadata itself, not only the magic: this proves the alternate authenticated copy
    # can be parsed independently. The combined case damages both copies and must fail closed.
    primary[primary_meta + min(8, mcs - 1)] ^= 0x40
    tail[tail_meta + min(8, tail_mcs - 1)] ^= 0x40
    both[:] = primary
    both[tail_meta + min(8, tail_mcs - 1)] ^= 0x40

    # Payload corruption sits between the two metadata copies. Metadata still authenticates, so member/verify
    # must refuse at the physical leaf/hash boundary rather than silently falling back to a different file.
    payload_start = primary_meta + mcs
    if tail_meta > payload_start:
        payload[payload_start + (tail_meta - payload_start) // 2] ^= 0x01
    return bytes(primary), bytes(tail), bytes(both), bytes(payload)


def assert_recovery(name: str, path: Path, tmp: Path) -> None:
    primary, tail, both, payload = recovery_copies(name, path.read_bytes())
    variants = {
        "primary-damaged": (primary, True),
        "tail-damaged": (tail, True),
        "both-metadata-damaged": (both, False),
        "payload-damaged": (payload, False),
    }
    for label, (data, should_verify) in variants.items():
        candidate = tmp / f"{name}-{label}.cmpct"
        candidate.write_bytes(data)
        result = run("verify", str(candidate), check=False, text=True)
        assert (result.returncode == 0) is should_verify, (name, label, result.stderr, result.stdout)
        py = PYREADER.strong_verify(candidate)
        assert bool(py.get("ok")) is should_verify, (name, label, py)


def assert_c_abi(path: Path, row: dict) -> None:
    lib = ctypes.CDLL(str(LIB))
    handle = ctypes.c_void_p()
    lib.cmpct_portable_open.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_void_p)]
    lib.cmpct_portable_open.restype = ctypes.c_int32
    lib.cmpct_portable_close.argtypes = [ctypes.c_void_p]
    lib.cmpct_portable_entry_count.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_size_t)]
    lib.cmpct_portable_entry_count.restype = ctypes.c_int32
    lib.cmpct_portable_entry_path.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
    lib.cmpct_portable_entry_path.restype = ctypes.c_int32
    lib.cmpct_portable_entry_read.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t), ctypes.c_void_p]
    lib.cmpct_portable_entry_read.restype = ctypes.c_int32
    lib.cmpct_portable_verify.argtypes = [ctypes.c_void_p]
    lib.cmpct_portable_verify.restype = ctypes.c_int32

    assert lib.cmpct_portable_open(str(path).encode(), ctypes.byref(handle)) == 0
    try:
        count = ctypes.c_size_t()
        assert lib.cmpct_portable_entry_count(handle, ctypes.byref(count)) == 0
        assert count.value == len(row["files"])
        for index in range(count.value):
            required = ctypes.c_size_t()
            assert lib.cmpct_portable_entry_path(handle, index, None, 0, ctypes.byref(required)) == 0
            pbuf = ctypes.create_string_buffer(required.value + 1)
            assert lib.cmpct_portable_entry_path(handle, index, pbuf, len(pbuf), ctypes.byref(required)) == 0
            member = pbuf.raw[: required.value].decode()
            expected = row["files"][member]
            out = ctypes.create_string_buffer(expected["size"])
            written = ctypes.c_size_t()
            assert lib.cmpct_portable_entry_read(handle, index, out, len(out), ctypes.byref(written), None) == 0
            assert written.value == expected["size"]
            assert sha(out.raw[: written.value]) == expected["sha256"]
        assert lib.cmpct_portable_verify(handle) == 0
    finally:
        lib.cmpct_portable_close(handle)


def main() -> None:
    fixture = json.loads(FIXTURE.read_text())
    assert fixture["schema"] == "cmpct-v030-native-golden-v1"
    assert CLI.is_file(), CLI
    assert LIB.is_file(), LIB
    with tempfile.TemporaryDirectory(prefix="cmpct-v030-native-") as td:
        tmp = Path(td)
        for name in ("g04", "prefixgraph"):
            row = fixture[name]
            path = materialize_fixture(tmp, name, row)
            assert_fixed_vector(name, path, row, tmp)
            assert_recovery(name, path, tmp)
            assert_c_abi(path, row)
    print("v0.30 native portable conformance: ok")


if __name__ == "__main__":
    main()
