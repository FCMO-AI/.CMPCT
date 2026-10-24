#!/usr/bin/env python3
"""Independently assemble frozen revision-24 S_PACK vectors without importing CMPCT.

Regeneration requires Python, msgpack, and system libzstd. This is a provenance
instrument, not a production encoder, a released archive format, or a benchmark.
Never replace the committed conformance archive merely because a new library
version emits different compressed bytes.
"""
from __future__ import annotations

import base64
import binascii
import ctypes
import ctypes.util
import hashlib
import json
import struct
from pathlib import Path

import msgpack

MAGIC = b"CMPCT24\0"
FMAGIC = b"CMPTF24\0"
BMAGIC = b"CMA4"
HDR = struct.Struct("<8sHHQQQ32s")
BHDR = struct.Struct("<4sBBHQQII32s")
FTR = struct.Struct("<8sBBBBQQQ32s")


def sha256(payload: bytes) -> bytes:
    return hashlib.sha256(payload).digest()


def zstd_codec():
    path = ctypes.util.find_library("zstd")
    if not path:
        raise RuntimeError("system libzstd required to regenerate the fixture")
    lib = ctypes.CDLL(path)
    lib.ZSTD_compressBound.argtypes = [ctypes.c_size_t]
    lib.ZSTD_compressBound.restype = ctypes.c_size_t
    lib.ZSTD_compress.argtypes = [
        ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p,
        ctypes.c_size_t, ctypes.c_int,
    ]
    lib.ZSTD_compress.restype = ctypes.c_size_t
    lib.ZSTD_decompress.argtypes = [
        ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p, ctypes.c_size_t,
    ]
    lib.ZSTD_decompress.restype = ctypes.c_size_t
    lib.ZSTD_isError.argtypes = [ctypes.c_size_t]
    lib.ZSTD_isError.restype = ctypes.c_uint

    def compress(raw: bytes) -> bytes:
        dest = ctypes.create_string_buffer(lib.ZSTD_compressBound(len(raw)))
        source = ctypes.create_string_buffer(raw, len(raw))
        n = lib.ZSTD_compress(dest, len(dest), source, len(raw), 12)
        if lib.ZSTD_isError(n):
            raise RuntimeError("zstd compression failure")
        return dest.raw[:n]

    def decompress(encoded: bytes, want: int) -> bytes:
        dest = ctypes.create_string_buffer(want)
        source = ctypes.create_string_buffer(encoded, len(encoded))
        n = lib.ZSTD_decompress(dest, len(dest), source, len(encoded))
        if lib.ZSTD_isError(n) or n != want:
            raise RuntimeError("zstd decompression failure")
        return dest.raw[:n]
    return compress, decompress


def vector(codec: int, compress, decompress):
    contents = [
        ("alpha.txt", b"alpha: content is not the index\n" * 2),
        ("omega.bin", bytes(range(31)) + b"\0CMA4\0"
         + bytes(range(255, 225, -1))),
        ("zeta.txt", b"end-of-packed-data\n"),
    ]
    raw_pack = bytearray()
    offsets = {}
    for name, payload in contents:
        offsets[name] = len(raw_pack)
        raw_pack.extend(payload)
        if name == "alpha.txt":
            raw_pack.extend(b"INTERSTICE:NOT-A-LOGICAL-MEMBER")
    raw_pack = bytes(raw_pack)
    physical = raw_pack if codec == 0 else compress(raw_pack)
    assert physical if codec == 0 else decompress(physical, len(raw_pack)) == raw_pack
    record = BHDR.pack(
        BMAGIC, codec, 0, 0, len(raw_pack), len(physical), 0,
        binascii.crc32(raw_pack) & 0xffffffff, sha256(raw_pack),
    ) + physical

    rows = [
        [name, 0, 0o644, 0, len(payload), None,
         [4, 0, offsets[name], len(payload)]]
        for name, payload in contents
    ]
    rows.append([
        "alpha-copy.txt", 0, 0o644, 0, len(contents[0][1]), None,
        [4, 0, offsets["alpha.txt"], len(contents[0][1])],
    ])
    rows.sort(key=lambda item: item[0])
    index = {
        "v": 24,
        "files": rows,
        "blobs": [[0, len(raw_pack), len(physical), codec, 0]],
        "recipes": [],
        "dict_blob": None,
        "fsmeta": {"owner": [0, 0], "owner_overrides": [], "xattrs": []},
        "features": ["micro-solid-packs", "sha256", "dual-index"],
    }
    plain_index = msgpack.packb(index, use_bin_type=True)
    compressed_index = compress(plain_index)
    digest = sha256(plain_index)
    archive = (
        HDR.pack(MAGIC, 24, 0, len(compressed_index), len(plain_index),
                 len(record), digest)
        + compressed_index + record + compressed_index
        + FTR.pack(FMAGIC, 0, 1, 0, 0, len(compressed_index),
                   len(plain_index), 0, digest)
    )
    # This unpacking oracle is intentionally *not* the CMPCT Reader.
    magic, rev, flags, clen, ulen, data_span, hash_bytes = HDR.unpack_from(archive)
    assert (magic, rev, flags, clen, ulen, data_span, hash_bytes) == (
        MAGIC, 24, 0, len(compressed_index), len(plain_index),
        len(record), digest,
    )
    assert decompress(archive[HDR.size:HDR.size+clen], ulen) == plain_index
    assert msgpack.unpackb(plain_index, raw=False) == index
    footer = FTR.unpack_from(archive, len(archive)-FTR.size)
    assert footer == (FMAGIC, 0, 1, 0, 0, clen, ulen, 0, digest)
    assert archive[-FTR.size-clen:-FTR.size] == compressed_index

    files = {
        name: {
            "size": len(payload),
            "sha256": sha256(payload).hex(),
            "hex": payload.hex(),
        }
        for name, payload in contents
    }
    files["alpha-copy.txt"] = dict(files["alpha.txt"])
    probes = [
        {"name": "omega.bin", "offset": 4, "length": 29},
        {"name": "alpha-copy.txt", "offset": 7, "length": 17},
        {"name": "zeta.txt", "offset": 3, "length": 13},
    ]
    for probe in probes:
        start, end = probe["offset"], probe["offset"] + probe["length"]
        probe["hex"] = files[probe["name"]]["hex"][start*2:end*2]
    return {
        "name": "pack-raw" if codec == 0 else "pack-zstd",
        "physical_codec": codec,
        "archive_sha256": sha256(archive).hex(),
        "archive_bytes": len(archive),
        "packed_blob_sha256": sha256(raw_pack).hex(),
        "packed_blob_uncompressed_bytes": len(raw_pack),
        "packed_blob_compressed_bytes": len(physical),
        "files": files,
        "ranges": probes,
        "archive_base64": base64.b64encode(archive).decode("ascii"),
    }


def main():
    compress, decompress = zstd_codec()
    records = {
        "schema": "cmpct-v24-independent-pack-golden-v1",
        "format_revision": 24,
        "generation_provenance": {
            "method": "independently assembled struct/MessagePack revision-24 wire; no CMPCT Builder or Reader imports",
            "python": "3.11",
            "msgpack": "1.1.2",
            "index_and_zstd_codec": "system libzstd level 12",
            "purpose": "fixed cross-implementation byte oracle for S_PACK shared-blob slices and offsets",
        },
        "vectors": [vector(codec, compress, decompress) for codec in (0, 1)],
    }
    destination = Path(__file__).with_name("v24-pack.json")
    output = json.dumps(records, sort_keys=True, indent=2) + "\n"
    # Preserve the source-frozen vector: regeneration is a compatibility
    # experiment, never permission to rewrite a historical golden.
    if destination.exists() and destination.read_text(encoding="utf-8") != output:
        raise SystemExit(
            "independent regeneration differs from frozen archive; "
            "preserve existing vector and investigate source/toolchain drift"
        )
    destination.write_text(output, encoding="utf-8")
    for item in records["vectors"]:
        print(item["name"], item["archive_bytes"], item["archive_sha256"])


if __name__ == "__main__":
    main()
