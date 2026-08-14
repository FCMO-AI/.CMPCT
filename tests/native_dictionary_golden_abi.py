from __future__ import annotations

import base64
import ctypes
import json
import tempfile
from pathlib import Path

from cmpct.reader import CMPCT

ROOT = Path(__file__).resolve().parents[1]
LIB = ROOT / "native/cmpct-core/target/release/libcmpct_core.so"
VECTOR = ROOT / "tests/conformance/v24-zstd-dictionary.json"


def _load_lib():
    lib = ctypes.CDLL(str(LIB))
    lib.cmpct_open.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_void_p)]
    lib.cmpct_open.restype = ctypes.c_int32
    lib.cmpct_entry_count.argtypes = [ctypes.c_void_p]
    lib.cmpct_entry_count.restype = ctypes.c_size_t
    lib.cmpct_entry_path.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
    lib.cmpct_entry_path.restype = ctypes.c_int32
    lib.cmpct_entry_read_range.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_uint64, ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
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


def main() -> None:
    vector = json.loads(VECTOR.read_text())["vector"]
    archive_bytes = base64.b64decode(vector["archive_base64"])
    lib = _load_lib()

    with tempfile.TemporaryDirectory(prefix="cmpct-native-dictionary-") as td:
        root = Path(td)
        archive = root / "dictionary.cmpct"
        archive.write_bytes(archive_bytes)

        handle = _open(lib, archive)
        try:
            assert lib.cmpct_entry_count(handle) == 1
            assert _entry_path(lib, handle, 0) == vector["name"]
            want = bytes.fromhex(vector["range"]["hex"])
            status, got_n, got = _read_range(
                lib,
                handle,
                vector["range"]["offset"],
                vector["range"]["length"],
            )
            assert status == 0, status
            assert got_n == len(want)
            assert got == want

            # Full reads additionally prove exact decode length/content, not merely a fortunate slice.
            status, got_n, got = _read_range(lib, handle, 0, vector["logical_size"])
            assert status == 0, status
            assert got_n == vector["logical_size"]
            with CMPCT(archive) as ar:
                assert got == ar.read(vector["name"])
                dict_index = ar.index["dict_blob"]
                member_index = ar.by[vector["name"]][6][1]
                dict_pos = ar.record_base + ar.blobs[dict_index][0]
                member_pos = ar.record_base + ar.blobs[member_index][0]
        finally:
            lib.cmpct_close(handle)

        # Footnote: dictionary bytes are an authenticated dependency of codec 3. Corrupting only the
        # dictionary payload must fail the member read even though the primary index and member frame
        # still authenticate and the archive remains structurally openable.
        corrupt_dict = bytearray(archive_bytes)
        corrupt_dict[dict_pos + 64 + 17] ^= 1
        corrupt_dict_path = root / "dictionary-corrupt-payload.cmpct"
        corrupt_dict_path.write_bytes(corrupt_dict)
        handle = _open(lib, corrupt_dict_path)
        try:
            status, got_n, _ = _read_range(lib, handle, 0, 32)
            assert status == -3, status
            assert got_n == 0
        finally:
            lib.cmpct_close(handle)

        # Mutating only the member's physical SHA leaves the Zstd-with-dictionary stream decodable;
        # returning bytes would therefore expose a missing strong-integrity check in the native path.
        corrupt_member = bytearray(archive_bytes)
        corrupt_member[member_pos + 32] ^= 1
        corrupt_member_path = root / "dictionary-member-corrupt-hash.cmpct"
        corrupt_member_path.write_bytes(corrupt_member)
        handle = _open(lib, corrupt_member_path)
        try:
            status, got_n, _ = _read_range(lib, handle, 0, 32)
            assert status == -3, status
            assert got_n == 0
        finally:
            lib.cmpct_close(handle)


if __name__ == "__main__":
    main()
