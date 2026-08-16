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
    ROOT / "tests/conformance/v24-virtual-zip-deflate-mode0.json",
    ROOT / "tests/conformance/v24-virtual-zip-deflate-mode2.json",
)


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
    assert status == 0, (path, status)
    return handle


def _entry_path(lib, handle, index: int) -> str:
    needed = ctypes.c_size_t()
    assert lib.cmpct_entry_path(handle, index, None, 0, ctypes.byref(needed)) == 0
    buf = ctypes.create_string_buffer(needed.value + 1)
    assert lib.cmpct_entry_path(handle, index, buf, len(buf), ctypes.byref(needed)) == 0
    return buf.value.decode()


def _read_range(lib, handle, offset: int, length: int):
    out = ctypes.create_string_buffer(length)
    got = ctypes.c_size_t()
    status = lib.cmpct_entry_read_range(handle, 0, offset, out, length, ctypes.byref(got))
    return status, got.value, out.raw[: got.value]


def _stream_mode(vector: dict) -> int:
    modes = vector.get("recipe", {}).get("payload_stream_modes")
    if modes:
        return int(modes[0])
    # The first stored-payload fixture predates the explicit field but is canonically mode 0 STORED.
    return 0


def _physical_corruption_target(vector: dict) -> bytes:
    method = int(vector["member"]["method"])
    if method == 0:
        # ZIP_STORED projects the logical member bytes directly.
        return b"hello-cmpct\n"
    mode = _stream_mode(vector)
    if mode in (0, 1):
        # Mode 0 stores the exact stream as the physical codec-4 payload; mode 1 stores it as a
        # retained ordinary blob. Corrupting those bytes exercises the source actually projected.
        return bytes.fromhex(vector["member"]["exact_deflate_hex"])
    if mode == 2:
        # Mode 2 stores no duplicate RFC-1951 stream. Its source is authenticated logical content,
        # which the native core must validate before asking stock zlib to regenerate exact bytes.
        return b"hello-cmpct\n"
    raise AssertionError(f"unknown fixed stream mode {mode}")


def _exercise_vector(lib, root: Path, fixture_path: Path) -> None:
    vector = json.loads(fixture_path.read_text())["vector"]
    archive_bytes = base64.b64decode(vector["archive_base64"])
    assert hashlib.sha256(archive_bytes).hexdigest() == vector["archive_sha256"]

    archive = root / f"{fixture_path.stem}.cmpct"
    archive.write_bytes(archive_bytes)
    handle = _open(lib, archive)
    try:
        assert lib.cmpct_entry_count(handle) == 1
        assert _entry_path(lib, handle, 0) == vector["name"]

        # Every frozen range crosses or isolates meaningful recipe boundaries. All four revision-24
        # payload forms therefore share one externally identical seekable virtual-member contract.
        for range_vector in vector["ranges"]:
            want = bytes.fromhex(range_vector["hex"])
            status, got_n, got = _read_range(
                lib,
                handle,
                range_vector["offset"],
                range_vector["length"],
            )
            assert status == 0, (fixture_path.name, status)
            assert got_n == len(want)
            assert got == want

        # Complete-member acceptance is anchored to builder-independent nested-ZIP identity rather
        # than Python reconstruction. This is the cross-implementation byte-exactness boundary.
        status, got_n, got = _read_range(lib, handle, 0, vector["logical_size"])
        assert status == 0, (fixture_path.name, status)
        assert got_n == vector["logical_size"]
        assert hashlib.sha256(got).hexdigest() == vector["logical_sha256"]
        assert got[:4] == b"PK\x03\x04"
        assert b"hello.txt" in got
        assert b"PK\x05\x06" in got

        # Bounds stay typed at the public ABI instead of becoming a short or partially filled read.
        status, got_n, _ = _read_range(lib, handle, vector["logical_size"] - 1, 2)
        assert status == -6, (fixture_path.name, status)
        assert got_n == 0
    finally:
        lib.cmpct_close(handle)

    target = _physical_corruption_target(vector)
    payload_pos = archive_bytes.find(target)
    assert payload_pos >= 0, (fixture_path.name, target.hex())
    assert archive_bytes.find(target, payload_pos + 1) == -1, "fixed corruption target must be unique"
    corrupt = bytearray(archive_bytes)
    corrupt[payload_pos] ^= 1
    corrupt_path = root / f"{fixture_path.stem}-corrupt-source.cmpct"
    corrupt_path.write_bytes(corrupt)

    handle = _open(lib, corrupt_path)
    try:
        status, got_n, _ = _read_range(lib, handle, 0, vector["logical_size"])
        assert status == -3, (fixture_path.name, status)
        assert got_n == 0
    finally:
        lib.cmpct_close(handle)


def main() -> None:
    lib = _load_lib()
    with tempfile.TemporaryDirectory(prefix="cmpct-native-vzip-") as td:
        root = Path(td)
        for fixture_path in VECTORS:
            _exercise_vector(lib, root, fixture_path)


if __name__ == "__main__":
    main()
