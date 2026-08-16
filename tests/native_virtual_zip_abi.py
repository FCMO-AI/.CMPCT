from __future__ import annotations

import base64
import ctypes
import hashlib
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB = ROOT / "native/cmpct-core/target/release/libcmpct_core.so"
VECTORS = (
    ROOT / "tests/conformance/v24-virtual-zip.json",
    ROOT / "tests/conformance/v24-virtual-zip-deflate-mode1.json",
)
UNSUPPORTED_VECTORS = (
    ROOT / "tests/conformance/v24-virtual-zip-deflate-mode0.json",
)

CMPCT_OK = 0
CMPCT_FORMAT = -3
CMPCT_RANGE = -6
CMPCT_UNSUPPORTED = -7


def _load_lib():
    lib = ctypes.CDLL(str(LIB))
    lib.cmpct_open.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_void_p)]
    lib.cmpct_open.restype = ctypes.c_int32
    lib.cmpct_entry_count.argtypes = [ctypes.c_void_p]
    lib.cmpct_entry_count.restype = ctypes.c_size_t
    lib.cmpct_entry_path.argtypes = [
        ctypes.c_void_p,
        ctypes.c_size_t,
        ctypes.c_void_p,
        ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_size_t),
    ]
    lib.cmpct_entry_path.restype = ctypes.c_int32
    lib.cmpct_entry_read_range.argtypes = [
        ctypes.c_void_p,
        ctypes.c_size_t,
        ctypes.c_uint64,
        ctypes.c_void_p,
        ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_size_t),
    ]
    lib.cmpct_entry_read_range.restype = ctypes.c_int32
    lib.cmpct_close.argtypes = [ctypes.c_void_p]
    return lib


def _open(lib, path: Path):
    handle = ctypes.c_void_p()
    status = lib.cmpct_open(str(path).encode(), ctypes.byref(handle))
    assert status == CMPCT_OK, (path, status)
    return handle


def _entry_path(lib, handle, index: int) -> str:
    needed = ctypes.c_size_t()
    assert lib.cmpct_entry_path(handle, index, None, 0, ctypes.byref(needed)) == CMPCT_OK
    buf = ctypes.create_string_buffer(needed.value + 1)
    assert lib.cmpct_entry_path(handle, index, buf, len(buf), ctypes.byref(needed)) == CMPCT_OK
    return buf.value.decode()


def _read_range(lib, handle, offset: int, length: int):
    out = ctypes.create_string_buffer(length)
    got = ctypes.c_size_t()
    status = lib.cmpct_entry_read_range(handle, 0, offset, out, length, ctypes.byref(got))
    return status, got.value, out.raw[: got.value]


def _exercise_vector(lib, root: Path, fixture_path: Path) -> None:
    vector = json.loads(fixture_path.read_text())["vector"]
    # Pin the fixture contract itself: these are S_VZIP acceptance vectors, not generic archives that
    # merely happen to contain nested ZIP bytes. That keeps parser-identity regressions visible.
    assert vector["storage_kind"] == 2, vector["storage_kind"]
    archive_bytes = base64.b64decode(vector["archive_base64"])
    assert hashlib.sha256(archive_bytes).hexdigest() == vector["archive_sha256"]

    archive = root / f"{fixture_path.stem}.cmpct"
    archive.write_bytes(archive_bytes)
    handle = _open(lib, archive)
    try:
        assert lib.cmpct_entry_count(handle) == 1
        assert _entry_path(lib, handle, 0) == vector["name"]

        # The frozen ranges deliberately include a skeleton/payload/skeleton crossing and a
        # central-directory-only read. Stored and retained-Deflate payloads must therefore share the
        # same range-local projection behavior through the public handler ABI.
        for range_vector in vector["ranges"]:
            want = bytes.fromhex(range_vector["hex"])
            status, got_n, got = _read_range(
                lib,
                handle,
                range_vector["offset"],
                range_vector["length"],
            )
            assert status == CMPCT_OK, status
            assert got_n == len(want)
            assert got == want

        # Footnote: complete-member acceptance is anchored to each builder-independent nested-ZIP
        # identity rather than Python reconstruction. This makes the public ABI a true second
        # implementation boundary instead of a round-trip agreement test.
        status, got_n, got = _read_range(lib, handle, 0, vector["logical_size"])
        assert status == CMPCT_OK, status
        assert got_n == vector["logical_size"]
        assert hashlib.sha256(got).hexdigest() == vector["logical_sha256"]
        assert got[:4] == b"PK\x03\x04"
        assert b"hello.txt" in got
        assert b"PK\x05\x06" in got

        # Bounds stay typed at the public ABI instead of becoming a short or partially filled read.
        status, got_n, _ = _read_range(lib, handle, vector["logical_size"] - 1, 2)
        assert status == CMPCT_RANGE, status
        assert got_n == 0
    finally:
        lib.cmpct_close(handle)

    # Corrupt the actual projected payload bytes without touching authenticated index/recipe metadata.
    # Partial RAW-blob semantics intentionally authenticate only touched framing, but a complete
    # virtual-member read has the stronger recipe SHA-256 boundary and must therefore fail closed.
    if vector["member"]["method"] == 0:
        payload = b"hello-cmpct\n"
    else:
        payload = bytes.fromhex(vector["member"]["exact_deflate_hex"])
    payload_pos = archive_bytes.find(payload)
    assert payload_pos >= 0
    assert archive_bytes.find(payload, payload_pos + 1) == -1, "fixed payload must be unique"
    corrupt = bytearray(archive_bytes)
    corrupt[payload_pos] ^= 1
    corrupt_path = root / f"{fixture_path.stem}-corrupt-payload.cmpct"
    corrupt_path.write_bytes(corrupt)

    handle = _open(lib, corrupt_path)
    try:
        status, got_n, _ = _read_range(lib, handle, 0, vector["logical_size"])
        assert status == CMPCT_FORMAT, status
        assert got_n == 0
    finally:
        lib.cmpct_close(handle)


def _exercise_explicitly_unsupported_vector(lib, root: Path, fixture_path: Path) -> None:
    """Keep independently frozen representations visible at the public ABI before dispatch lands.

    Footnote: a valid revision-24 archive containing an as-yet ungated native representation should
    still open and enumerate. The member read must return the typed unsupported status, never a format
    error or guessed reconstruction. This turns the remaining mode-0 wiring gap into an executable
    contract instead of leaving it outside the native test surface.
    """
    vector = json.loads(fixture_path.read_text())["vector"]
    assert vector["storage_kind"] == 2, vector["storage_kind"]
    archive_bytes = base64.b64decode(vector["archive_base64"])
    assert hashlib.sha256(archive_bytes).hexdigest() == vector["archive_sha256"]

    archive = root / f"{fixture_path.stem}-unsupported.cmpct"
    archive.write_bytes(archive_bytes)
    handle = _open(lib, archive)
    try:
        assert lib.cmpct_entry_count(handle) == 1
        assert _entry_path(lib, handle, 0) == vector["name"]
        status, got_n, got = _read_range(lib, handle, 0, vector["logical_size"])
        # CmpctStatus::Unsupported is -7. Keep the C-facing test anchored to the public enum instead
        # of accidentally treating UTF-8 failure (-5) as representation refusal.
        assert status == CMPCT_UNSUPPORTED, status
        assert got_n == 0
        assert got == b""
    finally:
        lib.cmpct_close(handle)


def main() -> None:
    lib = _load_lib()
    with tempfile.TemporaryDirectory(prefix="cmpct-native-vzip-") as td:
        root = Path(td)
        for fixture_path in VECTORS:
            _exercise_vector(lib, root, fixture_path)
        for fixture_path in UNSUPPORTED_VECTORS:
            _exercise_explicitly_unsupported_vector(lib, root, fixture_path)


if __name__ == "__main__":
    main()
