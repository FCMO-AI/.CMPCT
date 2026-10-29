"""Independent CMPCT r24 physical-output auditor for J24I14 (no CMPCT imports).

Inspect exact bytes for the pre-registered small sparse compaction A/B/B/A fixture.
Python standard library + msgpack + ambient libzstd (separate implementation).
This is a scientific/hostile referee, not a general r24 reader.
"""
from __future__ import annotations

import binascii
import ctypes
import ctypes.util
import hashlib
import json
import pathlib
import struct
import sys
import zlib

import msgpack

HDR = struct.Struct("<8sHHQQQ32s")
FTR = struct.Struct("<8sBBBBQQQ32s")
BHDR = struct.Struct("<4sBBHQQII32s")
libpath = ctypes.util.find_library("zstd")
assert libpath, "independent libzstd unavailable: skip product claim"
lib = ctypes.CDLL(libpath)
lib.ZSTD_decompress.argtypes = (ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p, ctypes.c_size_t)
lib.ZSTD_decompress.restype = ctypes.c_size_t
lib.ZSTD_isError.argtypes = (ctypes.c_size_t,)
lib.ZSTD_isError.restype = ctypes.c_uint


def zstd(payload: bytes, logical: int) -> bytes:
    out = ctypes.create_string_buffer(logical)
    source = ctypes.create_string_buffer(payload)
    n = lib.ZSTD_decompress(out, logical, source, len(payload))
    assert not lib.ZSTD_isError(n) and n == logical, ("Zstd mismatch", n, logical)
    return out.raw[:n]


def zeros(digest, count: int):
    block = b"\0" * (1 << 20)
    while count:
        n = min(count, len(block))
        digest.update(block[:n])
        count -= n


def check_physical(path: pathlib.Path):
    archive = path.read_bytes()
    magic, ver, flags, compressed, logical, physical, index_sha = HDR.unpack_from(archive)
    assert magic == b"CMPCT24\0" and ver == 24 and flags == 0
    index_start = HDR.size
    encoded = archive[index_start:index_start+compressed]
    index_bytes = zstd(encoded, logical)
    assert hashlib.sha256(index_bytes).digest() == index_sha
    index = msgpack.unpackb(index_bytes, raw=False)
    assert index["v"] == 24 and not index["recipes"]
    records_end = index_start + compressed + physical
    assert len(archive) == records_end + compressed + FTR.size
    assert archive[records_end:records_end+compressed] == encoded
    footer = FTR.unpack_from(archive, len(archive) - FTR.size)
    assert footer[0] == b"CMPTF24\0" and footer[1:5] == (0, 1, 0, 0)
    assert footer[5:8] == (compressed, logical, 0) and footer[8] == index_sha
    blobs = []
    for offset, size, csize, codec, meta in index["blobs"]:
        at = index_start + compressed + offset
        assert at + BHDR.size + meta + csize <= records_end
        marker, actual_codec, flags, reserved, rus, rcs, rmeta, crc, want = BHDR.unpack_from(archive, at)
        assert marker == b"CMA4" and flags == reserved == 0
        assert actual_codec == codec and (rus, rcs, rmeta) == (size, csize, meta)
        payload = archive[at+BHDR.size+meta:at+BHDR.size+meta+csize]
        if codec == 0:
            data = payload
        elif codec == 1:
            data = zstd(payload, size)
        elif codec == 4:
            data = zlib.decompress(payload, -15)
        else:
            raise AssertionError("unhandled independent fixture codec")
        assert len(data) == size
        assert binascii.crc32(data) & 0xffffffff == crc
        assert hashlib.sha256(data).digest() == want
        blobs.append(data)
    checked = 0
    for row in index["files"]:
        name, kind, mode, mtime, size, want, storage = row
        assert kind == 0 and name in ("small.bin", "sparse.bin")
        if storage[0] == 0:
            data = blobs[storage[1]]
            assert len(data) == size
            logical_sha = hashlib.sha256(data).digest()
        elif storage[0] == 3:
            d = hashlib.sha256()
            cursor = 0
            for start, length, ids in storage[1]:
                assert cursor <= start and 0 < length <= size - start
                zeros(d, start - cursor)
                assert sum(len(blobs[bid]) for bid in ids) == length
                for bid in ids:
                    d.update(blobs[bid])
                cursor = start + length
            zeros(d, size - cursor)
            logical_sha = d.digest()
            assert logical_sha == bytes(want)
        else:
            raise AssertionError("unexpected storage in independent fixture")
        checked += 1
    assert checked == 2 and len(blobs) == 3
    return {"archive": path.name, "physical_blobs": len(blobs), "logical_hashes": checked, "index_sha": index_sha.hex()}


def main():
    root = pathlib.Path(sys.argv[1])
    targets = sorted(root.glob("output-*.cmpct"))
    assert len(targets) == 8
    results = [check_physical(path) for path in targets]
    report = {"status": "PASS", "source": "independent libzstd + struct + MessagePack",
              "output_archives": len(targets),
              "physical_records": sum(x["physical_blobs"] for x in results),
              "logical_stream_hashes": sum(x["logical_hashes"] for x in results),
              "release_credit": False}
    (root/"detached-wire-referee.json").write_text(json.dumps(report, sort_keys=True, indent=2)+"\n")
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
