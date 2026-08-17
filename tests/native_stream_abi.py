from __future__ import annotations

import ctypes
import tempfile
from pathlib import Path

from cmpct.builder import Builder

ROOT = Path(__file__).resolve().parents[1]
LIB = ROOT / "native/cmpct-core/target/release/libcmpct_core.so"


def _load_lib():
    lib = ctypes.CDLL(str(LIB))
    lib.cmpct_open.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_void_p)]
    lib.cmpct_open.restype = ctypes.c_int32
    lib.cmpct_close.argtypes = [ctypes.c_void_p]
    lib.cmpct_entry_count.argtypes = [ctypes.c_void_p]
    lib.cmpct_entry_count.restype = ctypes.c_size_t
    lib.cmpct_entry_path.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
    lib.cmpct_entry_path.restype = ctypes.c_int32
    lib.cmpct_entry_stream_open.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_void_p)]
    lib.cmpct_entry_stream_open.restype = ctypes.c_int32
    lib.cmpct_stream_read.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
    lib.cmpct_stream_read.restype = ctypes.c_int32
    lib.cmpct_stream_close.argtypes = [ctypes.c_void_p]
    return lib


def _path(lib, archive, index: int) -> str:
    needed = ctypes.c_size_t()
    assert lib.cmpct_entry_path(archive, index, None, 0, ctypes.byref(needed)) == 0
    buf = ctypes.create_string_buffer(needed.value + 1)
    assert lib.cmpct_entry_path(archive, index, buf, len(buf), ctypes.byref(needed)) == 0
    return buf.value.decode()


def main() -> None:
    lib = _load_lib()
    payload = (b"CMPCT-stream-" * 8192) + b"tail"
    with tempfile.TemporaryDirectory(prefix="cmpct-stream-abi-") as td:
        root = Path(td) / "source"
        root.mkdir()
        (root / "payload.bin").write_bytes(payload)
        archive_path = Path(td) / "stream.cmpct"
        Builder(root).build(archive_path)

        archive = ctypes.c_void_p()
        assert lib.cmpct_open(str(archive_path).encode(), ctypes.byref(archive)) == 0
        try:
            paths = [_path(lib, archive, i) for i in range(lib.cmpct_entry_count(archive))]
            index = paths.index("payload.bin")
            stream = ctypes.c_void_p()
            assert lib.cmpct_entry_stream_open(archive, index, ctypes.byref(stream)) == 0
            assert stream.value
            try:
                out = bytearray()
                buffer = ctypes.create_string_buffer(37)
                while True:
                    got = ctypes.c_size_t()
                    assert lib.cmpct_stream_read(stream, buffer, len(buffer), ctypes.byref(got)) == 0
                    if got.value == 0:
                        break
                    assert 0 < got.value <= len(buffer)
                    out.extend(buffer.raw[: got.value])
                assert bytes(out) == payload

                # EOF remains stable instead of wrapping the stream cursor or re-reading data.
                got = ctypes.c_size_t(123)
                assert lib.cmpct_stream_read(stream, buffer, len(buffer), ctypes.byref(got)) == 0
                assert got.value == 0
            finally:
                lib.cmpct_stream_close(stream)

            # Invalid entry indexes must fail before allocating a stream handle.
            bad = ctypes.c_void_p()
            assert lib.cmpct_entry_stream_open(archive, 10_000_000, ctypes.byref(bad)) == -6
            assert not bad.value
        finally:
            lib.cmpct_close(archive)


if __name__ == "__main__":
    main()
