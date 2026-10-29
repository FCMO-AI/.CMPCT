#!/usr/bin/env python3
"""J24I39: split *already independently audited* Builder r24 codec-2 physical records.

No cmpct import. Extraction is only an oracle input transform, not a product parser or
authenticity gate. The unchanged J24I38 detached auditor must PASS first.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path

import msgpack
import zstandard

HEADER = struct.Struct("<8sHHQQQ32s")
BLOB = struct.Struct("<4sBBHQQII32s")
FOOT = struct.Struct("<8sBBBBQQQ32s")

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--case-dir", type=Path, required=True)
    args = p.parse_args()
    base = args.case_dir
    original = json.loads((base / "manifest.json").read_text())
    audit = json.loads((base / "detached-audit.json").read_text())
    assert original["schema"] == "j24i38-builder-wav-flac-v1"
    assert audit["result"] == "PASS" and audit["independent_of_cmpct_import"] is True
    output = {"schema": "j24i39-independent-split-v1", "records": {}}
    for mib in (8, 32):
        row = original["records"][str(mib)]
        raw = (base / f"builder-wav-{mib}m.cmpct").read_bytes()
        assert sha(raw) == row["archive_sha256"]
        magic, revision, flags, csize, usize, span, digest = HEADER.unpack_from(raw)
        assert (magic, revision, flags) == (b"CMPCT24\x00", 24, 0)
        index = zstandard.ZstdDecompressor().decompress(
            raw[HEADER.size:HEADER.size+csize], max_output_size=usize
        )
        assert len(index) == usize and hashlib.sha256(index).digest() == digest
        index_data = msgpack.unpackb(index, raw=False)
        assert len(index_data["files"]) == len(index_data["blobs"]) == 1
        b = index_data["blobs"][0]
        assert b[0] == 0 and b[3] == 2
        offset = HEADER.size + csize
        mag, codec, bflags, reserved, logical, enc_size, meta_len, crc, hash_bytes = BLOB.unpack_from(raw, offset)
        assert (mag, codec, bflags, reserved) == (b"CMA4", 2, 0, 0)
        assert logical == row["logical_bytes"] and enc_size == row["encoded_bytes"]
        assert crc == row["crc32"] and hash_bytes.hex() == row["payload_sha256"]
        meta_start = offset + BLOB.size
        meta = raw[meta_start:meta_start+meta_len]
        flac = raw[meta_start+meta_len:meta_start+meta_len+enc_size]
        assert len(meta) == meta_len and len(flac) == enc_size and flac[:4] == b"fLaC"
        assert offset + span == meta_start + meta_len + enc_size
        assert raw[offset+span:offset+span+csize] == raw[HEADER.size:HEADER.size+csize]
        foot_pos = offset + span + csize
        assert FOOT.unpack_from(raw, foot_pos) == (b"CMPTF24\x00", 0, 1, 0, 0, csize, usize, 0, digest)
        assert foot_pos + FOOT.size == len(raw)
        metadata = msgpack.unpackb(meta, raw=False)
        assert len(metadata) == 5 and metadata[2:] == [1, 44100, 16]
        meta_path = base / f"oracle-{mib}m.meta"
        flac_path = base / f"oracle-{mib}m.flac"
        meta_path.write_bytes(meta)
        flac_path.write_bytes(flac)
        output["records"][str(mib)] = {
            "logical_bytes": logical, "encoded_bytes": enc_size,
            "payload_sha256": hash_bytes.hex(), "crc32": crc,
            "meta_sha256": sha(meta), "flac_sha256": sha(flac),
            "archive_sha256": sha(raw),
            "meta_path": str(meta_path.name), "flac_path": str(flac_path.name),
            "source": "unmodified Builder J24I38 + detached physical auditor"
        }
    (base / "stream-manifest.json").write_text(json.dumps(output, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"status": "PASS", "records": output["records"]}, sort_keys=True))

if __name__ == "__main__":
    main()
