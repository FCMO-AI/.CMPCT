from __future__ import annotations

import base64
import ctypes
import hashlib
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB = ROOT / "native/cmpct-core/target/release/libcmpct_core.so"
FIXTURE = ROOT / "tests/conformance/v24-pack.json"


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


def _path(lib, handle, index: int) -> str:
    needed = ctypes.c_size_t()
    assert lib.cmpct_entry_path(handle, index, None, 0, ctypes.byref(needed)) == 0
    buf = ctypes.create_string_buffer(needed.value + 1)
    assert lib.cmpct_entry_path(handle, index, buf, len(buf), ctypes.byref(needed)) == 0
    return buf.value.decode()


def _read(lib, handle, index: int, offset: int, length: int):
    out = ctypes.create_string_buffer(length)
    got = ctypes.c_size_t()
    status = lib.cmpct_entry_read_range(
        handle, index, offset, out, length, ctypes.byref(got)
    )
    return status, got.value, out.raw[: got.value]


def main() -> None:
    fixture = json.loads(FIXTURE.read_text())["vector"]
    archive_bytes = base64.b64decode(fixture["archive_base64"])
    assert hashlib.sha256(archive_bytes).hexdigest() == fixture["archive_sha256"]

    lib = _load_lib()
    with tempfile.TemporaryDirectory(prefix="cmpct-pack-golden-") as td:
        archive = Path(td) / "pack.cmpct"
        archive.write_bytes(archive_bytes)
        handle = ctypes.c_void_p()
        assert lib.cmpct_open(str(archive).encode(), ctypes.byref(handle)) == 0
        try:
            count = lib.cmpct_entry_count(handle)
            paths = [_path(lib, handle, index) for index in range(count)]
            assert paths == [item["name"] for item in fixture["files"]]

            for item in fixture["files"]:
                index = paths.index(item["name"])
                whole = bytes.fromhex(item["hex"])
                status, got_n, got = _read(lib, handle, index, 0, len(whole))
                assert status == 0, (item["name"], status)
                assert got_n == len(whole)
                assert got == whole
                assert hashlib.sha256(got).hexdigest() == item["sha256"]

                for range_vector in item["ranges"]:
                    want = bytes.fromhex(range_vector["hex"])
                    status, got_n, got = _read(
                        lib,
                        handle,
                        index,
                        range_vector["offset"],
                        range_vector["length"],
                    )
                    assert status == 0, (item["name"], status)
                    assert got_n == len(want)
                    assert got == want

                # Footnote: S_PACK is a slice of a shared blob, but its public range contract is still
                # a logical-file contract. Crossing a member boundary must be typed Range rather than
                # leaking bytes from the next packed file.
                status, got_n, _ = _read(lib, handle, index, len(whole) - 1, 2)
                assert status == -6, (item["name"], status)
                assert got_n == 0
        finally:
            lib.cmpct_close(handle)


if __name__ == "__main__":
    main()
