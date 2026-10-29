#!/usr/bin/env python3
"""J24G43 research-only first-party empty Builder -> derived valid Zstd r24 -> corrupt Zstd.

Preregistration predates instrument source. Never modifies frozen goldens or product code.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import zlib
import msgpack
import zstandard as zstd

from cmpct.builder import Builder
from cmpct.reader import CMPCT
from cmpct.codec import HDR, BHDR, FTR, MAGIC, VERSION, BMAGIC, FMAGIC, S_BLOB, CODEC_RAW, CODEC_ZSTD

def h(x: bytes) -> bytes:
    return hashlib.sha256(x).digest()

def observe(path: Path) -> dict:
    try:
        with CMPCT(path) as r:
            n = r.verify()
        return {"accepted": True, "count": n, "error": None}
    except Exception as exc:
        return {"accepted": False, "count": None, "error": type(exc).__name__ + ": " + str(exc)}

def write_derived(raw_archive: bytes, zstd_frame: bytes) -> bytes:
    magic, rev, flags, compressed_index_size, index_size, physical_span, old_sha = HDR.unpack_from(raw_archive)
    assert (magic, rev, flags) == (MAGIC, VERSION, 0)
    index_payload = raw_archive[HDR.size:HDR.size+compressed_index_size]
    index_bytes = zstd.ZstdDecompressor().decompress(index_payload, max_output_size=index_size+1)
    assert len(index_bytes) == index_size and h(index_bytes) == old_sha
    index = msgpack.unpackb(index_bytes, raw=False)
    assert len(index["files"]) == len(index["blobs"]) == 1
    row, desc = index["files"][0], index["blobs"][0]
    assert row[0] == "empty.bin" and row[1] == 0 and row[4] == 0
    assert row[6][0] == S_BLOB and desc[1] == desc[2] == 0 and desc[3] == CODEC_RAW
    original_record = raw_archive[HDR.size+compressed_index_size:HDR.size+compressed_index_size+physical_span]
    assert len(original_record) == physical_span == BHDR.size
    assert BHDR.unpack(original_record)[-1] == h(b"")
    assert BHDR.unpack(original_record)[-2] == 0
    original_footer = raw_archive[-FTR.size:]
    fmagic, kind, fcodec, fflags, fres, tail_cs, tail_us, parent, tail_sha = FTR.unpack(original_footer)
    assert (fmagic, kind, fcodec, fflags, fres, parent) == (FMAGIC, 0, 1, 0, 0, 0)
    assert tail_us == index_size and tail_sha == old_sha
    assert raw_archive[HDR.size+compressed_index_size+physical_span:-FTR.size] == index_payload
    assert len(zstd_frame) > 0 and zstd.ZstdDecompressor().decompress(zstd_frame, max_output_size=1) == b""
    desc[2] = len(zstd_frame)
    desc[3] = CODEC_ZSTD
    changed_index = msgpack.packb(index, use_bin_type=True)
    compressed_index = zstd.ZstdCompressor(level=3).compress(changed_index)
    physical = BHDR.pack(BMAGIC, CODEC_ZSTD, 0, 0, 0, len(zstd_frame), 0, 0, h(b"")) + zstd_frame
    out_head = HDR.pack(MAGIC, VERSION, 0, len(compressed_index), len(changed_index), len(physical), h(changed_index))
    out_tail = FTR.pack(FMAGIC, 0, 1, 0, 0, len(compressed_index), len(changed_index), 0, h(changed_index))
    return out_head + compressed_index + physical + compressed_index + out_tail

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output",type=Path,required=True)
    out=p.parse_args().output.resolve()
    out.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="cmpct-j24g43-") as temporary:
        root=Path(temporary)/"source";root.mkdir()
        (root/"empty.bin").write_bytes(b"")
        original_path=Path(temporary)/"original.cmpct"
        Builder(root,workers=1,reproducible=True).build(original_path)
        original=original_path.read_bytes()
    frame=zstd.ZstdCompressor(level=3).compress(b"")
    valid=write_derived(original,frame)
    header=HDR.unpack_from(valid)
    payload_pos=HDR.size+header[3]+BHDR.size
    assert valid[payload_pos:payload_pos+len(frame)] == frame
    altered=bytearray(valid)
    # Zstd's four-byte magic: flipping its first byte makes decoding fail unambiguously.
    altered[payload_pos] ^= 1
    invalid=bytes(altered)
    assert len(valid) == len(invalid)
    assert [i for i,(a,b) in enumerate(zip(valid,invalid)) if a!=b] == [payload_pos]
    for name,bytes_ in (("source-raw",original),("valid-zstd-empty",valid),("corrupt-zstd-empty",invalid)):
        (out/(name+".cmpct")).write_bytes(bytes_)
    observations={name:{"sha256":h(raw).hex(),"bytes":len(raw),"python":observe(out/(name+".cmpct"))} for name,raw in
                  (("source-raw",original),("valid-zstd-empty",valid),("corrupt-zstd-empty",invalid))}
    assert observations["source-raw"]["python"] == {"accepted":True,"count":1,"error":None}
    assert observations["valid-zstd-empty"]["python"] == {"accepted":True,"count":1,"error":None},observations
    # J24G43a: prospective Python-rejection prediction was FALSIFIED on Ubuntu/macOS.
    # This is a negative integrity observation, not a positive decoder claim.
    assert observations["corrupt-zstd-empty"]["python"] == {"accepted": True, "count": 1, "error": None},observations
    receipt={"schema":"cmpct-j24g43-empty-zstd-native-verify-court-v1",
             "scientific_status":"J24G43a: Python false-positive OBSERVED; native still under test; NOT product fix",
             "initial_python_rejection_prediction_falsified":True,
             "payload_offset":payload_pos,"source_builder_reproducible":True,
             "empty_logical_sha256":h(b"").hex(),"zstd_frame_hex":frame.hex(),
             "observations":observations}
    (out/"python-observations.json").write_text(json.dumps(receipt,sort_keys=True,indent=2)+"\n")
    print(json.dumps(receipt,sort_keys=True,indent=2))

if __name__=="__main__":
    main()
