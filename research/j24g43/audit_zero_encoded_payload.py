#!/usr/bin/env python3
"""Independent r24 wire auditor for J24G43. Imports no cmpct source."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import struct
import zlib
import msgpack
import zstandard as zstd

HDR=struct.Struct("<8sHHQQQ32s")
BHDR=struct.Struct("<4sBBHQQII32s")
FTR=struct.Struct("<8sBBBBQQQ32s")
EMPTY=hashlib.sha256(b"").digest()

def h(data):
    return hashlib.sha256(data).digest()

def parse(archive:bytes):
    magic,rev,flags,cs,us,span,claimed=HDR.unpack_from(archive)
    assert (magic,rev,flags)==(b"CMPCT24\0",24,0)
    assert 0 < cs < (1<<20) and 0 < us < (1<<20) and 0 < span < (1<<20)
    idx_compressed=archive[HDR.size:HDR.size+cs]
    idx=zstd.ZstdDecompressor().decompress(idx_compressed,max_output_size=us+1)
    assert len(idx)==us and h(idx)==claimed
    table=msgpack.unpackb(idx,raw=False)
    assert len(table["files"])==len(table["blobs"])==1
    row=table["files"][0]
    desc=table["blobs"][0]
    assert row[0]=="empty.bin" and row[1]==0 and row[4]==0
    assert row[6][0]==0
    assert desc[0]==0 and desc[1]==0 and desc[4]==0
    body=archive[HDR.size+cs:HDR.size+cs+span]
    assert len(body)==span
    bmagic,codec,flags2,reserved,usize,csize,mlen,crc,physical_sha=BHDR.unpack_from(body)
    assert (bmagic,flags2,reserved,usize,mlen,crc,physical_sha)==(b"CMA4",0,0,0,0,0,EMPTY)
    assert (codec,csize)==(desc[3],desc[2])
    assert span==BHDR.size+csize
    payload=body[BHDR.size:]
    assert len(payload)==csize
    fmagic,kind,fc,ff,fr,tcs,tus,parent,tailsha=FTR.unpack_from(archive,len(archive)-FTR.size)
    assert (fmagic,kind,fc,ff,fr,parent)==(b"CMPTF24\0",0,1,0,0,0)
    assert tcs==cs and tus==us and tailsha==claimed
    assert archive[HDR.size+cs+span:-FTR.size]==idx_compressed
    if codec==0:
        assert csize==0 and payload==b""
        valid=True
    elif codec==1:
        try:
            decoded=zstd.ZstdDecompressor().decompress(payload,max_output_size=1)
            valid=decoded==b""
        except zstd.ZstdError:
            valid=False
    else:
        raise AssertionError("unexpected codec")
    return {"archive_sha256":h(archive).hex(),"index_sha256":claimed.hex(),
            "physical_header_sha256":physical_sha.hex(),"physical_crc32":crc,
            "codec":codec,"encoded_len":csize,"encoded_payload_hex":payload.hex(),
            "empty_payload_decoder_valid":valid,"index":table}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--case-dir",type=Path,required=True)
    path=ap.parse_args().case_dir
    items={name:(path/(name+".cmpct")).read_bytes() for name in
           ("source-raw","valid-zstd-empty","corrupt-zstd-empty")}
    results={name:parse(data) for name,data in items.items()}
    assert results["source-raw"]["codec"]==0 and results["source-raw"]["empty_payload_decoder_valid"]
    assert results["valid-zstd-empty"]["codec"]==1 and results["valid-zstd-empty"]["empty_payload_decoder_valid"]
    assert results["corrupt-zstd-empty"]["codec"]==1 and not results["corrupt-zstd-empty"]["empty_payload_decoder_valid"]
    v=items["valid-zstd-empty"];c=items["corrupt-zstd-empty"]
    assert len(v)==len(c)
    positions=[i for i,(x,y) in enumerate(zip(v,c)) if x!=y]
    header=HDR.unpack_from(v)
    expected_offset=HDR.size+header[3]+BHDR.size
    assert positions==[expected_offset],positions
    assert (v[expected_offset]^c[expected_offset])==1
    assert results["valid-zstd-empty"]["index_sha256"]==results["corrupt-zstd-empty"]["index_sha256"]
    assert results["valid-zstd-empty"]["physical_header_sha256"]==results["corrupt-zstd-empty"]["physical_header_sha256"]
    assert results["valid-zstd-empty"]["physical_crc32"]==results["corrupt-zstd-empty"]["physical_crc32"]
    assert results["valid-zstd-empty"]["index"]==results["corrupt-zstd-empty"]["index"]
    output={"schema":"cmpct-j24g43-detached-zero-compressed-physical-referee-v1",
            "result":"PASS: genuine empty Builder source; valid re-indexed Zstd empty; one-byte invalid Zstd frame with unchanged SHA/CRC/index/footer",
            "mutation_offset":expected_offset,
            "source":results["source-raw"],
            "valid":results["valid-zstd-empty"],
            "invalid":results["corrupt-zstd-empty"]}
    (path/"detached-wire-audit.json").write_text(json.dumps(output,sort_keys=True,indent=2)+"\n")
    print(json.dumps({"result":output["result"],"mutation_offset":expected_offset,
                      "source_sha256":results["source-raw"]["archive_sha256"],
                      "valid_sha256":results["valid-zstd-empty"]["archive_sha256"],
                      "invalid_sha256":results["corrupt-zstd-empty"]["archive_sha256"]},sort_keys=True))

if __name__=="__main__":
    main()
