from __future__ import annotations

import base64
import ctypes
import hashlib
import json
import tempfile
from pathlib import Path

from cmpct.reader import CMPCT

ROOT = Path(__file__).resolve().parents[1]
LIB = ROOT / "native/cmpct-core/target/release/libcmpct_core.so"
VECTOR = ROOT / "tests/conformance/v24-sparse.json"


def _load_lib():
    lib = ctypes.CDLL(str(LIB))
    lib.cmpct_open.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_void_p)]
    lib.cmpct_open.restype = ctypes.c_int32
    lib.cmpct_entry_count.argtypes = [ctypes.c_void_p]
    lib.cmpct_entry_count.restype = ctypes.c_size_t
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


def _read(lib, handle, offset: int, length: int):
    out = ctypes.create_string_buffer(length)
    got = ctypes.c_size_t()
    status = lib.cmpct_entry_read_range(handle, 0, offset, out, length, ctypes.byref(got))
    return status, got.value, out.raw[: got.value]


def _corrupt_blob_identity(archive: Path, blob_index: int, output: Path) -> None:
    with CMPCT(archive) as ar:
        blob_pos = ar.record_base + ar.blobs[blob_index][0]
    data = bytearray(archive.read_bytes())
    data[blob_pos + 32] ^= 1
    output.write_bytes(data)


def main() -> None:
    manifest = json.loads(VECTOR.read_text())
    member = manifest["member"]
    lib = _load_lib()
    with tempfile.TemporaryDirectory(prefix="cmpct-native-sparse-") as td:
        root = Path(td)
        archive = root / manifest["archive"]["name"]
        archive.write_bytes(base64.b64decode(manifest["archive"]["base64"]))
        assert hashlib.sha256(archive.read_bytes()).hexdigest() == manifest["archive"]["sha256"]

        handle = _open(lib, archive)
        try:
            assert lib.cmpct_entry_count(handle) == 1
            for case in member["ranges"]:
                want = bytes.fromhex(case["hex"])
                status, got_n, got = _read(lib, handle, case["offset"], case["length"])
                assert status == 0, (case, status)
                assert got_n == len(want)
                assert got == want

            # A complete sparse read exercises zero synthesis for every hole plus the logical whole-file
            # SHA gate; it must agree exactly with the Python executable specification.
            with CMPCT(archive) as ar:
                expected = ar.read(member["path"])
            status, got_n, got = _read(lib, handle, 0, member["size"])
            assert status == 0
            assert got_n == len(expected)
            assert got == expected
            assert hashlib.sha256(got).hexdigest() == member["sha256"]
        finally:
            lib.cmpct_close(handle)

        # Corrupt a blob in the second extent, then read only the first extent. A range-local sparse
        # implementation must not decode or authenticate unrelated stored data merely because it shares
        # the same logical file.
        untouched = root / "sparse-untouched-corrupt.cmpct"
        _corrupt_blob_identity(archive, 1, untouched)
        handle = _open(lib, untouched)
        try:
            case = member["ranges"][0]
            status, got_n, got = _read(lib, handle, case["offset"], case["length"])
            assert status == 0, status
            assert got_n == case["length"]
            assert got == bytes.fromhex(case["hex"])
        finally:
            lib.cmpct_close(handle)

        # Corrupt the RAW blob actually touched by that same range. The native core must refuse the
        # bytes. Use a full read of the physical RAW chunk so its complete identity is authenticated by
        # the logical whole-file gate rather than claiming partial RAW authentication that revision 24
        # cannot provide.
        touched = root / "sparse-touched-corrupt.cmpct"
        _corrupt_blob_identity(archive, 0, touched)
        handle = _open(lib, touched)
        try:
            status, got_n, _ = _read(lib, handle, 0, member["size"])
            assert status == -3, status
            assert got_n == 0
        finally:
            lib.cmpct_close(handle)


if __name__ == "__main__":
    main()
