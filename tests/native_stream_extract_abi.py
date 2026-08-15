from __future__ import annotations

import ctypes
import os
import tempfile
from pathlib import Path

from cmpct.builder import Builder

ROOT = Path(__file__).resolve().parents[1]
LIB = ROOT / "native/cmpct-core/target/release/libcmpct_core.so"


class EntryInfo(ctypes.Structure):
    _fields_ = [
        ("kind", ctypes.c_uint8),
        ("reserved", ctypes.c_uint8 * 3),
        ("mode", ctypes.c_uint32),
        ("size", ctypes.c_uint64),
        ("mtime_ns", ctypes.c_int64),
    ]


def _load_lib():
    lib = ctypes.CDLL(str(LIB))
    lib.cmpct_open.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_void_p)]
    lib.cmpct_open.restype = ctypes.c_int32
    lib.cmpct_close.argtypes = [ctypes.c_void_p]
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
    lib.cmpct_entry_info.argtypes = [
        ctypes.c_void_p,
        ctypes.c_size_t,
        ctypes.POINTER(EntryInfo),
    ]
    lib.cmpct_entry_info.restype = ctypes.c_int32
    lib.cmpct_preflight.argtypes = [ctypes.c_void_p]
    lib.cmpct_preflight.restype = ctypes.c_int32
    lib.cmpct_entry_stream_open.argtypes = [
        ctypes.c_void_p,
        ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_void_p),
    ]
    lib.cmpct_entry_stream_open.restype = ctypes.c_int32
    lib.cmpct_stream_read.argtypes = [
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_size_t),
    ]
    lib.cmpct_stream_read.restype = ctypes.c_int32
    lib.cmpct_stream_close.argtypes = [ctypes.c_void_p]
    lib.cmpct_extract_all.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
    lib.cmpct_extract_all.restype = ctypes.c_int32
    return lib


def _path(lib, handle, index: int) -> str:
    needed = ctypes.c_size_t()
    assert lib.cmpct_entry_path(handle, index, None, 0, ctypes.byref(needed)) == 0
    buf = ctypes.create_string_buffer(needed.value + 1)
    assert lib.cmpct_entry_path(handle, index, buf, len(buf), ctypes.byref(needed)) == 0
    return buf.value.decode()


def _stream(lib, handle, index: int, chunk_size: int = 37) -> bytes:
    stream = ctypes.c_void_p()
    assert lib.cmpct_entry_stream_open(handle, index, ctypes.byref(stream)) == 0
    assert stream.value
    out = bytearray()
    try:
        buffer = ctypes.create_string_buffer(chunk_size)
        while True:
            got = ctypes.c_size_t()
            status = lib.cmpct_stream_read(
                stream, buffer, len(buffer), ctypes.byref(got)
            )
            assert status == 0, status
            if got.value == 0:
                break
            assert 0 < got.value <= chunk_size
            out += buffer.raw[: got.value]
    finally:
        lib.cmpct_stream_close(stream)
    return bytes(out)


def main() -> None:
    lib = _load_lib()
    with tempfile.TemporaryDirectory(prefix="cmpct-native-stream-") as td:
        root = Path(td) / "source"
        root.mkdir()
        (root / "dir").mkdir()
        (root / "dir" / "small.txt").write_text("small native stream\n")
        (root / "large.bin").write_bytes((b"0123456789abcdef" * (2 * 1024 * 1024)) + b"tail")
        (root / "target.txt").write_text("hardlink-target\n")
        os.link(root / "target.txt", root / "hardlink.txt")
        os.symlink("../target.txt", root / "dir" / "symlink.txt")

        archive_path = Path(td) / "tree.cmpct"
        Builder(root).build(archive_path)
        handle = ctypes.c_void_p()
        assert lib.cmpct_open(str(archive_path).encode(), ctypes.byref(handle)) == 0
        try:
            # Preflight is a permanent public ABI contract, not merely an internal constructor side
            # effect. Platform extractors may call it explicitly before choosing a destination.
            assert lib.cmpct_preflight(handle) == 0

            paths = [_path(lib, handle, i) for i in range(lib.cmpct_entry_count(handle))]
            large_index = paths.index("large.bin")
            assert _stream(lib, handle, large_index, 64 * 1024) == (root / "large.bin").read_bytes()

            # Tiny chunks stress sequential offset accounting rather than merely proxying one full
            # range request through the stream handle.
            small_index = paths.index("dir/small.txt")
            assert _stream(lib, handle, small_index, 3) == (root / "dir" / "small.txt").read_bytes()

            destination = Path(td) / "extracted"
            assert lib.cmpct_extract_all(handle, str(destination).encode()) == 0
            assert (destination / "dir" / "small.txt").read_bytes() == (root / "dir" / "small.txt").read_bytes()
            assert (destination / "large.bin").read_bytes() == (root / "large.bin").read_bytes()
            assert (destination / "target.txt").read_bytes() == b"hardlink-target\n"
            assert (destination / "hardlink.txt").read_bytes() == b"hardlink-target\n"
            assert os.stat(destination / "target.txt").st_ino == os.stat(destination / "hardlink.txt").st_ino
            assert os.path.islink(destination / "dir" / "symlink.txt")
            assert os.readlink(destination / "dir" / "symlink.txt") == "../target.txt"

            # Extraction intentionally refuses a non-empty destination instead of attempting an
            # unsafe merge with pre-existing symlinks/files that could redirect output paths.
            assert lib.cmpct_extract_all(handle, str(destination).encode()) == -3
        finally:
            lib.cmpct_close(handle)


if __name__ == "__main__":
    main()
