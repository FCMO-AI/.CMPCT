"""Deterministic independent libzstd pointer-semantics differential; not product evidence."""
from __future__ import annotations

import ctypes
import ctypes.util
import hashlib
import json
import random
import struct
from pathlib import Path

z = ctypes.CDLL(ctypes.util.find_library("zstd"))
z.ZSTD_decompress.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p, ctypes.c_size_t]
z.ZSTD_decompress.restype = ctypes.c_size_t
z.ZSTD_compressBound.argtypes = [ctypes.c_size_t]
z.ZSTD_compressBound.restype = ctypes.c_size_t
z.ZSTD_compress.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p, ctypes.c_size_t, ctypes.c_int]
z.ZSTD_compress.restype = ctypes.c_size_t
z.ZSTD_isError.argtypes = [ctypes.c_size_t]
z.ZSTD_isError.restype = ctypes.c_uint
z.ZSTD_getErrorName.argtypes = [ctypes.c_size_t]
z.ZSTD_getErrorName.restype = ctypes.c_char_p


def encode(data: bytes) -> bytes:
    dst = ctypes.create_string_buffer(z.ZSTD_compressBound(len(data)))
    n = z.ZSTD_compress(dst, len(dst), ctypes.c_char_p(data), len(data), 3)
    assert not z.ZSTD_isError(n)
    return dst.raw[:n]


def decode(data: bytes, borrow: bool) -> tuple:
    src = ctypes.c_char_p(data) if borrow else ctypes.create_string_buffer(data)
    dest = ctypes.create_string_buffer(1)
    n = z.ZSTD_decompress(dest, 1, src, len(data))
    is_error = bool(z.ZSTD_isError(n))
    return (
        is_error,
        z.ZSTD_getErrorName(n).decode() if is_error else None,
        None if is_error else int(n),
        dest.raw[:int(n)] if not is_error else None,
    )


def main() -> None:
    rng = random.Random(45045)
    counts = {"valid-empty": 0, "valid-one": 0, "skippable": 0,
              "magic-flip": 0, "truncated": 0, "appended-nul": 0, "random": 0}
    accepted = 0
    fingerprint = hashlib.sha256()
    for i in range(5000):
        k = i % 7
        if k == 0:
            name, specimen = "valid-empty", encode(b"")
        elif k == 1:
            name, specimen = "valid-one", encode(bytes((rng.randrange(256),)))
        elif k == 2:
            name = "skippable"
            size = rng.randrange(0, 4097)
            specimen = struct.pack("<II", 0x184D2A50, size) + rng.randbytes(size)
        elif k == 3:
            name = "magic-flip"
            encoded = encode(b"")
            specimen = bytes((encoded[0] ^ 1,)) + encoded[1:]
        elif k == 4:
            name = "truncated"
            encoded = encode(b"")
            specimen = encoded[:rng.randrange(len(encoded))]
        elif k == 5:
            name, specimen = "appended-nul", encode(b"") + bytes((0,))
        else:
            name, specimen = "random", rng.randbytes(rng.randrange(0, 8193))
        copied, borrowed = decode(specimen, False), decode(specimen, True)
        if copied != borrowed:
            raise AssertionError((i, name, copied, borrowed))
        counts[name] += 1
        accepted += int(not copied[0])
        fingerprint.update(len(specimen).to_bytes(4, "little"))
        fingerprint.update(specimen)
    result = {
        "schema": "cmpct-j24g45-independent-libzstd-pointer-fuzz-v1",
        "seed": 45045,
        "cases": 5000,
        "categories": counts,
        "successful_decode_cases": accepted,
        "input_stream_sha256": fingerprint.hexdigest(),
        "comparison": "ctypes copied vs borrowed input pointers; 1-byte capacity; error name/status/output equivalent",
        "libzstd": ctypes.util.find_library("zstd"),
        "scope": "local system C codec boundary only, not CMPCT product or its package-native Rust ABI",
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
