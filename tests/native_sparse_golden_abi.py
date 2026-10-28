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

        # Corrupt the Zstd blob in the second extent. A range touching only the first extent must still
        # succeed; a range that intersects the corrupted extent must fail. Together these assertions
        # prove the sparse ABI path is range-local rather than decoding every stored extent up front.
        corrupt = root / "sparse-second-extent-corrupt.cmpct"
        _corrupt_blob_identity(archive, 1, corrupt)
        handle = _open(lib, corrupt)
        try:
            untouched = member["ranges"][0]
            status, got_n, got = _read(
                lib, handle, untouched["offset"], untouched["length"]
            )
            assert status == 0, status
            assert got_n == untouched["length"]
            assert got == bytes.fromhex(untouched["hex"])

            touched = member["ranges"][1]
            status, got_n, _ = _read(lib, handle, touched["offset"], touched["length"])
            assert status == -3, status
            assert got_n == 0
        finally:
            lib.cmpct_close(handle)


if __name__ == "__main__":
    main()
