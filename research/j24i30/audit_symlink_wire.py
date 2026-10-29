#!/usr/bin/env python3
"""J24I30 detached physical r24 referee.

No imports of CMPCT Builder/Reader/codec, Rust, or the test converter. Physical
and both re-signed indexes are checked with standard framing and separate codecs.
"""
from __future__ import annotations
import argparse
import binascii
import hashlib
import json
from pathlib import Path
import struct
import zlib

import msgpack
import zstandard as zstd

H = struct.Struct("<8sHHQQQ32s")
B = struct.Struct("<4sBBHQQII32s")
F = struct.Struct("<8sBBBBQQQ32s")
S_BLOB = 0
K_SYMLINK = 2

def sha(b: bytes) -> bytes:
    return hashlib.sha256(b).digest()

def parse(path: Path) -> dict:
    data = path.read_bytes()
    assert len(data) >= H.size + F.size, "short archive"
    magic, version, flags, cs, us, span, index_sha = H.unpack_from(data)
    assert (magic, version, flags) == (b"CMPCT24\0", 24, 0)
    assert cs < 2**26 and us < 2**26 and span < 2**30
    p0 = H.size
    p1 = p0 + cs
    p2 = p1 + span
    assert p2 + F.size <= len(data)
    compressed = data[p0:p1]
    raw_index = zstd.ZstdDecompressor().decompress(compressed, max_output_size=us)
    assert len(raw_index) == us and sha(raw_index) == index_sha
    index = msgpack.unpackb(raw_index, raw=False)
    footer_at = len(data) - F.size
    fm, kind, codec, ff, reserved, tcs, tus, parent, tailsha = F.unpack_from(data, footer_at)
    assert (fm, kind, codec, ff, reserved, parent) == (b"CMPTF24\0", 0, 1, 0, 0, 0)
    assert tcs == cs and tus == us and tailsha == index_sha
    assert data[footer_at-tcs:footer_at] == compressed
    assert p2 == footer_at - tcs
    assert len(index["files"]) == 1 and len(index["blobs"]) == 1
    row = index["files"][0]
    assert row[0] == "link" and row[1] == K_SYMLINK and row[6][0] == S_BLOB
    off, usize, csize, codec_id, meta_len = index["blobs"][0]
    assert 0 <= off <= span and 0 <= csize <= span
    pm, bc, bflags, reserved, bus, bcs, bmeta, crc, physical_sha = B.unpack_from(data, p1+off)
    assert (pm,bc,bflags,reserved) == (b"CMA4",codec_id,0,0)
    assert (bus,bcs,bmeta)==(usize,csize,meta_len)
    payload_at = p1+off+B.size+meta_len
    assert payload_at+csize <= p2
    compressed_payload = data[payload_at:payload_at+csize]
    if codec_id == 0:
        decoded = compressed_payload
    elif codec_id == 1:
        decoded = zstd.ZstdDecompressor().decompress(compressed_payload, max_output_size=usize)
    elif codec_id == 4:
        decoded = zlib.decompress(compressed_payload, -15)
    else:
        raise AssertionError("unexpected symlink codec")
    assert len(decoded) == usize and row[4] == usize
    record_ok = ((binascii.crc32(decoded) & 0xffffffff) == crc and sha(decoded)==physical_sha)
    present = row[5]
    assert present is None or isinstance(present,bytes) and len(present) in (0,32)
    return {
        "file":path.name, "whole_sha256":sha(data).hex(),
        "index_sha256":index_sha.hex(),
        "physical_sha256":sha(data[p1:p2]).hex(),
        "decoded_sha256":sha(decoded).hex(),
        "physical_record_valid":record_ok,
        "logical_row_sha":None if present is None else present.hex(),
        "logical_row_matches_decoded":None if present is None or not present else present==sha(decoded),
        "compressed_bytes":csize,
        "decoded_bytes":len(decoded),
        "decoded_literal_hex":decoded.hex(),
        "index_wire_bytes":us,
    }

def main() -> None:
    arg=argparse.ArgumentParser()
    arg.add_argument("--case-dir",type=Path,required=True)
    ns=arg.parse_args()
    base=ns.case_dir
    names=("original","present-correct","present-empty","present-foreign","physical-wrong")
    outcomes={n:parse(base/(n+".cmpct")) for n in names}
    control=outcomes["original"]
    assert control["physical_record_valid"]
    assert bytes.fromhex(control["decoded_literal_hex"])==b"relative-symlink-target.txt"
    for n in names:
        x=outcomes[n]
        assert x["decoded_bytes"]==control["decoded_bytes"]
        if n!="physical-wrong":
            assert x["physical_sha256"]==control["physical_sha256"]
            assert x["physical_record_valid"]
            assert x["decoded_sha256"]==control["decoded_sha256"]
        else:
            assert not x["physical_record_valid"]
            assert x["index_sha256"]==control["index_sha256"]
    assert outcomes["present-correct"]["logical_row_matches_decoded"] is True
    assert outcomes["present-empty"]["logical_row_sha"]==""
    assert outcomes["present-foreign"]["logical_row_matches_decoded"] is False
    assert outcomes["present-foreign"]["index_sha256"]!=control["index_sha256"]
    receipt={"schema":"cmpct-j24i30-independent-r24-audit-v1",
             "result":"PASS; authenticated index variants, one physically corrupted negative",
             "cases":[outcomes[n] for n in names]}
    (base/"independent-physical-audit.json").write_text(
        json.dumps(receipt,sort_keys=True,indent=2)+"\n",encoding="utf-8"
    )
    print(json.dumps(receipt,sort_keys=True,indent=2))

if __name__=="__main__":
    main()
