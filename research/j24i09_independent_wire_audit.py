#!/usr/bin/env python3
"""J24I09 offline independent audit of a downloaded GitHub-hosted artifact ZIP.

No CMPCT imports or native CMPCT helper. Use stdlib struct, hash, zlib, MessagePack
and the host's system libzstd to audit r24 physical framing and logical bytes.
This is scientific evidence, not an on-host filesystem symlink audit.
"""
from __future__ import annotations

import binascii
import ctypes
import ctypes.util
import hashlib
import json
import os
import struct
import sys
import zipfile
import zlib
from pathlib import Path

import msgpack

HEADER = struct.Struct("<8sHHQQQ32s")
BLOB = struct.Struct("<4sBBHQQII32s")
FOOTER = struct.Struct("<8sBBBBQQQ32s")
EXPECTED_HOST_SHA = "307e4d9d32879f95e17c0e845ffdd1f769fffdc9"
EXPECTED_PRODUCT_BLOBS = {
    "builder-blob.txt": "387192edd783e02bf7a44a38945214bf9d6c183e",
    "transactions-blob.txt": "8d1e46e1fdf408c1d95ce9091e25fa159f0e6264",
}

def sha(raw: bytes) -> bytes:
    return hashlib.sha256(raw).digest()

def zstd_decoder():
    lib = ctypes.CDLL(ctypes.util.find_library("zstd"))
    lib.ZSTD_decompress.restype = ctypes.c_size_t
    lib.ZSTD_decompress.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p, ctypes.c_size_t]
    lib.ZSTD_isError.restype = ctypes.c_uint
    lib.ZSTD_isError.argtypes = [ctypes.c_size_t]
    def decode(src: bytes, expected: int) -> bytes:
        dst = ctypes.create_string_buffer(max(1, expected))
        code = lib.ZSTD_decompress(dst, expected, ctypes.create_string_buffer(src), len(src))
        assert not lib.ZSTD_isError(code) and code == expected, (code, expected)
        return dst.raw[:expected]
    return decode

def wire(raw: bytes, zdec) -> dict:
    assert len(raw) >= HEADER.size + FOOTER.size
    magic, version, flags, compressed_n, logical_n, data_n, index_hash = HEADER.unpack_from(raw)
    assert magic == b"CMPCT24\0" and version == 24
    packed = raw[HEADER.size : HEADER.size + compressed_n]
    index_bytes = zdec(packed, logical_n)
    assert sha(index_bytes) == index_hash
    index = msgpack.unpackb(index_bytes, raw=False)
    fm, kind, codec, flags, reserved, footer_comp, footer_raw, prev, footer_hash = FOOTER.unpack_from(raw, len(raw)-FOOTER.size)
    assert fm == b"CMPTF24\0" and kind == 0 and footer_hash == index_hash
    assert footer_comp == compressed_n and footer_raw == logical_n
    assert raw[len(raw)-FOOTER.size-footer_comp:len(raw)-FOOTER.size] == packed
    datastart = HEADER.size + compressed_n
    assert datastart + data_n + compressed_n + FOOTER.size == len(raw)

    blobs = []
    for descriptor in index["blobs"]:
        off, usize, csize, expected_codec, metalen = descriptor
        tag, codec, flags, reserved, decoded_n, stored_n, payloadmeta_n, crc32, payloadhash = BLOB.unpack_from(raw, datastart+off)
        assert tag == b"CMA4" and (codec,decoded_n,stored_n,payloadmeta_n) == (expected_codec,usize,csize,metalen)
        p = datastart+off+BLOB.size+metalen
        stored = raw[p:p+csize]
        if codec == 0: payload = stored
        elif codec == 1: payload = zdec(stored, usize)
        elif codec == 4: payload = zlib.decompress(stored,-15)
        else: raise AssertionError(("unexpected codec", codec))
        assert len(payload) == usize and sha(payload) == payloadhash
        assert binascii.crc32(payload) & 0xffffffff == crc32
        blobs.append(payload)

    files = []
    for name, kind, mode, mtime, n, row_hash, storage in index["files"]:
        assert kind == 0 and storage[0] == 0, (name, kind, storage)
        payload = blobs[storage[1]]
        assert len(payload) == n
        files.append({"path":name, "bytes":n, "sha256":sha(payload).hex()})
    return {
        "archive_sha256": sha(raw).hex(),
        "archive_bytes": len(raw),
        "index_sha256": index_hash.hex(),
        "physical_blobs": len(blobs),
        "files": files,
    }

def audit_zip(path: Path) -> dict:
    zdec = zstd_decoder()
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        head = z.read("head.txt").decode().strip()
        assert head == os.environ.get("EXACT_HEAD", EXPECTED_HOST_SHA)
        for path_in_zip, git_blob in EXPECTED_PRODUCT_BLOBS.items():
            assert z.read(path_in_zip).decode().strip() == git_blob
        receipt = json.loads(z.read("court.json"))
        entries = ["archives/source.cmpct", "archives/ordinary.cmpct", "archives/outside-after.bin"]
        originals = {name:wire(z.read(name),zdec) for name in entries}
        assert len({v["archive_sha256"] for v in originals.values()}) == 1
        assert all(v["files"][0]["sha256"] == receipt["expected_payload_sha256"] for v in originals.values())
        assert all(v["files"][0]["bytes"] == receipt["ordinary"]["logical"]["logical_bytes"] for v in originals.values())
        assert originals[entries[2]]["archive_sha256"] == receipt["intervened"]["outside_sentinel_final_sha256"]
        assert receipt["ordinary"]["ok"] and receipt["intervened"]["stage_rebound_symlink"]
        assert receipt["intervened"]["outside_sentinel_changed"] and receipt["intervened"]["destination_is_symlink"]
        for mutation, offset in {
            "bad_header":0,
            "bad_primary_index":HEADER.size+11,
            "bad_physical_blob":HEADER.size+HEADER.unpack_from(z.read(entries[0]))[3]+BLOB.size+4,
            "bad_footer":len(z.read(entries[0]))-1,
        }.items():
            corrupt = bytearray(z.read(entries[0]))
            corrupt[offset] ^= 1
            try: wire(bytes(corrupt), zdec)
            except (AssertionError, ValueError, KeyError, IndexError, TypeError): pass
            else: raise AssertionError(("corruption accepted", mutation))
    return {
        "head":head,
        "original_artifact_zip_sha256":sha(path.read_bytes()).hex(),
        "original_zip_crc":"PASS",
        "independent_physical_mutation_rejections":4,
        "physical_archive_witnesses": originals,
        "court_scientific_result":receipt["decision"],
        "product_blobs":EXPECTED_PRODUCT_BLOBS,
        "boundary":"Physical bytes audited independently; live inode/symlink type relies on separate installed-host receipt.",
    }

if __name__ == "__main__":
    result = audit_zip(Path(sys.argv[1]))
    print(json.dumps(result,sort_keys=True,indent=2))
    if len(sys.argv) > 2:
        Path(sys.argv[2]).write_text(json.dumps(result,sort_keys=True,indent=2)+"\n", encoding="utf-8")
