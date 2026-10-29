#!/usr/bin/env python3
"""J24G44 independent physical-r24 evidence auditor (never imports cmpct).

A test may pass by sharing the bug in Builder/Reader. This script instead opens
the *physical* archive bytes, authenticates primary/tail indexes and blob framing,
and uses the independent test-only python-zstandard decompressor. It must accept
the correctly encoded zero frame and reject the single-byte magic corruption.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct

import msgpack
import zstandard as zstd

_HEADER = struct.Struct("<8sHHQQQ32s")
_BLOB = struct.Struct("<4sBBHQQII32s")
_FOOTER = struct.Struct("<8sBBBBQQQ32s")
_EMPTY_SHA = hashlib.sha256(b"").digest()


def _sha(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def _decode(data: bytes, limit: int) -> bytes:
    return zstd.ZstdDecompressor().decompress(data, max_output_size=limit)


def inspect(path: Path) -> dict:
    data = path.read_bytes()
    assert len(data) >= _HEADER.size + _BLOB.size + _FOOTER.size
    magic, version, flags, csize, usize, physical, index_sha = _HEADER.unpack_from(data)
    assert (magic, version, flags) == (b"CMPCT24\x00", 24, 0)
    assert 0 < csize < (1 << 20) and 0 < usize < (1 << 20) and 0 < physical < (1 << 20)
    compressed_index = data[_HEADER.size:_HEADER.size + csize]
    index = _decode(compressed_index, usize + 1)
    assert len(index) == usize and _sha(index) == index_sha
    table = msgpack.unpackb(index, raw=False)
    assert len(table["files"]) == len(table["blobs"]) == 1
    file, desc = table["files"][0], table["blobs"][0]
    assert file[0] == "empty.bin" and file[1] == 0 and file[4] == 0
    assert file[6][0] == 0 and desc[0] == desc[1] == 0
    record = data[_HEADER.size + csize:_HEADER.size + csize + physical]
    assert len(record) >= _BLOB.size
    bmagic, codec, bflags, reserved, size, stored, meta_len, crc, digest = _BLOB.unpack_from(record)
    assert (bmagic, bflags, reserved, size, meta_len, crc, digest) == (
        b"CMA4", 0, 0, 0, 0, 0, _EMPTY_SHA
    )
    assert (desc[1], desc[2], desc[3]) == (size, stored, codec)
    assert physical == _BLOB.size + stored
    encoded = record[_BLOB.size:]
    assert len(encoded) == stored
    fmagic, kind, fcodec, fflags, fres, fcs, fus, parent, fsha = _FOOTER.unpack_from(
        data, len(data) - _FOOTER.size
    )
    assert (fmagic, kind, fcodec, fflags, fres, parent) == (b"CMPTF24\x00", 0, 1, 0, 0, 0)
    assert (fcs, fus, fsha) == (csize, usize, index_sha)
    assert data[_HEADER.size + csize + physical:-_FOOTER.size] == compressed_index

    if codec == 0:
        assert stored == 0
        encoded_valid = True
    elif codec == 1:
        try:
            encoded_valid = _decode(encoded, 1) == b""
        except zstd.ZstdError:
            encoded_valid = False
    else:
        raise AssertionError(f"not direct RAW/ZSTD: {codec}")

    return {
        "archive_sha256": _sha(data).hex(),
        "bytes": len(data),
        "codec": codec,
        "encoded_bytes": stored,
        "payload_offset": _HEADER.size + csize + _BLOB.size,
        "decoded_payload_sha256": digest.hex(),
        "index_sha256": index_sha.hex(),
        "physical_crc32": crc,
        "decoded_empty_frame_valid": encoded_valid,
        "index": table,
    }


def audit(root: Path) -> dict:
    original = (root / "physical" / "original.cmpct").read_bytes()
    valid = (root / "physical" / "valid.cmpct").read_bytes()
    corrupt = (root / "physical" / "invalid.cmpct").read_bytes()
    specs = {
        name: inspect(root / "physical" / (name + ".cmpct"))
        for name in ("original", "valid", "invalid")
    }
    receipt = json.loads((root / "physical" / "receipt.json").read_text())
    assert receipt["schema"] == "cmpct-j24g44-python-zero-encoded-physical-regression-v1"
    for name, spec in specs.items():
        assert spec["archive_sha256"] == receipt["sha256"][name]
    assert specs["original"]["codec"] == 0 and specs["original"]["decoded_empty_frame_valid"]
    assert specs["valid"]["codec"] == specs["invalid"]["codec"] == 1
    assert specs["valid"]["decoded_empty_frame_valid"]
    assert not specs["invalid"]["decoded_empty_frame_valid"]
    assert len(valid) == len(corrupt)
    altered = [i for i, (a, b) in enumerate(zip(valid, corrupt)) if a != b]
    assert altered == [receipt["changed_physical_offset"]]
    assert altered == [specs["valid"]["payload_offset"]]
    assert valid[altered[0]] ^ corrupt[altered[0]] == 1
    assert specs["valid"]["index"] == specs["invalid"]["index"]
    assert specs["valid"]["decoded_payload_sha256"] == specs["invalid"]["decoded_payload_sha256"]
    assert specs["valid"]["physical_crc32"] == specs["invalid"]["physical_crc32"] == 0
    assert specs["valid"]["decoded_payload_sha256"] == _EMPTY_SHA.hex()
    assert _sha(original).hex() == receipt["sha256"]["original"]

    return {
        "schema": "j24g44-independent-physical-referee-v1",
        "decision": "PASS: signed valid Zstd empty accepted; corrupt encoded magic rejected by independent decoder",
        "changed_payload_offset": altered[0],
        "archives": {
            name: {key: value for key, value in spec.items() if key != "index"}
            for name, spec in specs.items()
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifacts", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit(args.artifacts)
    if args.output:
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"decision": result["decision"], "changed_payload_offset": result["changed_payload_offset"]}))


if __name__ == "__main__":
    main()
