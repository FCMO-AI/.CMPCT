#!/usr/bin/env python3
"""Independent physical r24 CMA4 referee for J24I55; deliberately no cmpct imports.

Usage: python research/j24i55_physical_referee.py archive.cmpct result.json [audit.json]
Requires msgpack and libzstd only; all evidence verification uses external codec state.
"""
from __future__ import annotations
import ctypes
import ctypes.util
import hashlib
import json
from pathlib import Path
import struct
import sys
import zlib

import msgpack

HDR = struct.Struct("<8sHHQQQ32s")
BLOB = struct.Struct("<4sBBHQQII32s")
FTR = struct.Struct("<8sBBBBQQQ32s")

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def zstd_decoder():
    path = ctypes.util.find_library("zstd")
    assert path, "independent libzstd unavailable"
    lib = ctypes.CDLL(path)
    lib.ZSTD_decompress.argtypes = [ctypes.c_void_p,ctypes.c_size_t,ctypes.c_void_p,ctypes.c_size_t]
    lib.ZSTD_decompress.restype = ctypes.c_size_t
    lib.ZSTD_isError.argtypes = [ctypes.c_size_t]
    lib.ZSTD_isError.restype = ctypes.c_uint
    def decode(src: bytes, size: int):
        out = ctypes.create_string_buffer(max(1,size))
        inp = ctypes.create_string_buffer(src)
        n = lib.ZSTD_decompress(out,size,inp,len(src))
        assert not lib.ZSTD_isError(n) and n == size, ("zstd decode size", n, size)
        return out.raw[:n]
    return decode

def main():
    if len(sys.argv) not in (3,4):
        raise SystemExit("usage: referee ARCHIVE RESULT [AUDIT_JSON]")
    archive = Path(sys.argv[1]).read_bytes()
    result = json.loads(Path(sys.argv[2]).read_text())
    assert sha(archive) == result["physical_archive"]["sha256"]
    assert len(archive) == result["physical_archive"]["size"]
    decode = zstd_decoder()
    magic,version,flags,cs,us,span,indexhash = HDR.unpack_from(archive,0)
    assert (magic,version,flags) == (b"CMPCT24\x00",24,0)
    raw_index = decode(archive[HDR.size:HDR.size+cs],us)
    assert hashlib.sha256(raw_index).digest() == indexhash
    idx = msgpack.unpackb(raw_index,raw=False)
    tail = HDR.size+cs+span
    assert archive[tail:tail+cs] == archive[HDR.size:HDR.size+cs]
    assert FTR.unpack_from(archive,tail+cs) == (b"CMPTF24\x00",0,1,0,0,cs,us,0,indexhash)
    assert len(archive) == tail+cs+FTR.size
    end = 0
    stats = {"RAW":0,"ZSTD":0,"decoded_bytes":0}
    for j,(off,usize,csize,codec,meta_len) in enumerate(idx["blobs"]):
        assert off == end, ("blob offset gap",j,off,end)
        pos=HDR.size+cs+off
        bm,bc,bf,rs,bu,bcs,ml,crc,dig = BLOB.unpack_from(archive,pos)
        assert (bm,bc,bf,rs,bu,bcs,ml)==(b"CMA4",codec,0,0,usize,csize,meta_len)
        compressed=archive[pos+BLOB.size+meta_len:pos+BLOB.size+meta_len+csize]
        if codec == 0:
            plain=compressed;stats["RAW"]+=1
        elif codec == 1:
            plain=decode(compressed,usize);stats["ZSTD"]+=1
        else:
            raise AssertionError(("unsupported external referee codec",j,codec))
        assert len(plain)==usize and zlib.crc32(plain)&0xffffffff==crc
        assert hashlib.sha256(plain).digest()==dig, ("CMA4 SHA mismatch",j)
        stats["decoded_bytes"]+=usize
        end=off+BLOB.size+meta_len+csize
    assert end==span
    observed={s["archive_sha256"] for row in result["observations"] for s in row["samples"]}
    assert observed == {sha(archive)}
    receipt={"schema":"j24i55-physical-referee-v1","evidence_head":result["evidence_head"],
             "archive_sha256":sha(archive),"index_sha256":sha(raw_index),
             "blob_count":len(idx["blobs"]),"file_count":len(idx["files"]),
             "stats":stats,"decision_as_recorded":result["decision"],"physical_proof":"PASS"}
    if len(sys.argv)==4:
        Path(sys.argv[3]).write_text(json.dumps(receipt,sort_keys=True,indent=2)+"\n")
    print("INDEPENDENT_PHYSICAL_PROOF",json.dumps(receipt,sort_keys=True))

if __name__=="__main__":
    main()
