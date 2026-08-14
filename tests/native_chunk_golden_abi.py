from __future__ import annotations

import base64
import ctypes
import json
import tempfile
from pathlib import Path

from cmpct.reader import CMPCT

ROOT = Path(__file__).resolve().parents[1]
LIB = ROOT / "native/cmpct-core/target/release/libcmpct_core.so"
VECTORS = ROOT / "tests/conformance/v24-chunk-maps.json"


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


def main() -> None:
    manifest = json.loads(VECTORS.read_text())
    lib = _load_lib()
    with tempfile.TemporaryDirectory(prefix="cmpct-native-chunks-") as td:
        root = Path(td)
        for vector in manifest["vectors"]:
            archive = root / f"storage-{vector['storage_kind']}.cmpct"
            archive.write_bytes(base64.b64decode(vector["archive_base64"]))
            handle = _open(lib, archive)
            try:
                assert lib.cmpct_entry_count(handle) == 1
                want = bytes.fromhex(vector["range"]["hex"])
                status, got_n, got = _read(
                    lib,
                    handle,
                    vector["range"]["offset"],
                    vector["range"]["length"],
                )
                assert status == 0, (vector["name"], status)
                assert got_n == len(want)
                assert got == want

                # A complete chunked read exercises the logical whole-file SHA gate in addition to
                # per-blob framing/hash checks used by selective reads.
                with CMPCT(archive) as ar:
                    expected = ar.read(vector["name"])
                status, got_n, got = _read(lib, handle, 0, vector["logical_size"])
                assert status == 0, (vector["name"], status)
                assert got_n == len(expected)
                assert got == expected
            finally:
                lib.cmpct_close(handle)

            # Mutate only the first physical blob SHA. Its compressed bytes remain decodable, but a
            # range touching that chunk must fail before bytes cross the ABI.
            with CMPCT(archive) as ar:
                row = ar.by[vector["name"]]
                first_blob = row[6][1][0] if vector["storage_kind"] == 1 else row[6][1][0][1]
                blob_pos = ar.record_base + ar.blobs[first_blob][0]
            corrupt = bytearray(archive.read_bytes())
            corrupt[blob_pos + 32] ^= 1
            corrupt_path = root / f"storage-{vector['storage_kind']}-corrupt.cmpct"
            corrupt_path.write_bytes(corrupt)
            handle = _open(lib, corrupt_path)
            try:
                status, got_n, _ = _read(
                    lib,
                    handle,
                    vector["range"]["offset"],
                    vector["range"]["length"],
                )
                assert status == -3, (vector["name"], status)
                assert got_n == 0
            finally:
                lib.cmpct_close(handle)


if __name__ == "__main__":
    main()
