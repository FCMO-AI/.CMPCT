#!/usr/bin/env python3
"""J24I33 detached physical revision-24 auditor; no CMPCT imports."""
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

HDR = struct.Struct("<8sHHQQQ32s")
BHDR = struct.Struct("<4sBBHQQII32s")
FTR = struct.Struct("<8sBBBBQQQ32s")

def h(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()

def audit(path: Path) -> dict:
    data = path.read_bytes()
    assert len(data) > HDR.size + FTR.size
    magic, version, flags, cs, us, ds, want_index = HDR.unpack_from(data)
    assert (magic, version, flags) == (b"CMPCT24\x00", 24, 0)
    assert cs < 2**26 and us < 2**26 and ds < 2**30
    data_base = HDR.size + cs
    data_end = data_base + ds
    assert data_end + cs + FTR.size == len(data), "wrong dual-index or extra bytes"
    encoded_index = data[HDR.size:data_base]
    raw_index = zstd.ZstdDecompressor().decompress(encoded_index, max_output_size=us)
    assert len(raw_index) == us and h(raw_index) == want_index
    index = msgpack.unpackb(raw_index, raw=False)
    assert index["v"] == 24
    assert data[data_end:data_end+cs] == encoded_index, "tail index differs"
    footer = FTR.unpack_from(data, len(data) - FTR.size)
    assert footer == (b"CMPTF24\x00", 0, 1, 0, 0, cs, us, 0, want_index)
    assert len(index["blobs"]) == 1, "expected one physical blob"
    off, usize, csize, codec, metalen = index["blobs"][0]
    assert off == 0, "unexpected data-offset gap"
    pm, bc, flags, reserved, bus, bcs, bmeta, crc, want_phys = BHDR.unpack_from(data, data_base)
    assert (pm, bc, flags, reserved) == (b"CMA4", codec, 0, 0)
    assert (bus, bcs, bmeta) == (usize, csize, metalen)
    payload_at = data_base + BHDR.size + metalen
    assert payload_at + csize == data_end, "unaccounted physical bytes"
    comp = data[payload_at:payload_at+csize]
    if codec == 0:
        raw = comp
    elif codec == 1:
        raw = zstd.ZstdDecompressor().decompress(comp, max_output_size=usize)
    elif codec == 4:
        raw = zlib.decompress(comp, -15)
    else:
        raise AssertionError("unexpected physical codec")
    assert len(raw) == usize
    assert h(raw) == want_phys
    assert (binascii.crc32(raw) & 0xffffffff) == crc
    rows = index["files"]
    file_rows = [row for row in rows if row[1] == 0]
    assert len(file_rows) == 1
    assert file_rows[0][4] == usize
    assert file_rows[0][6] == [0, 0], "not direct Blob storage"
    dirs = [row for row in rows if row[1] == 1]
    return {
        "name": path.name, "archive_sha256": h(data).hex(),
        "physical_sha256": h(data[data_base:data_end]).hex(),
        "index_sha256": want_index.hex(), "payload_sha256": h(raw).hex(),
        "payload_size": len(raw), "physical_size": ds, "codec": codec,
        "files": [{"path": row[0], "kind": row[1],
                   "hash": (row[5].hex() if isinstance(row[5], bytes) else None)}
                  for row in rows],
        "directory_hashes": [row[5].hex() if isinstance(row[5], bytes) else None for row in dirs],
    }

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--case-dir", type=Path, required=True)
    args = ap.parse_args()
    d = args.case_dir
    names = ("real-nested", "inserted-empty", "invalid-one-byte", "flat")
    records = {name: audit(d / (name + ".cmpct")) for name in names}
    authentic = records["real-nested"]
    assert authentic["directory_hashes"] == [None, None], authentic
    assert [r["kind"] for r in authentic["files"]] == [1, 1, 0]
    for derived, expect in (("inserted-empty", ["", ""]), ("invalid-one-byte", ["58", "58"])):
        row = records[derived]
        assert row["directory_hashes"] == expect
        assert row["physical_sha256"] == authentic["physical_sha256"]
        assert row["payload_sha256"] == authentic["payload_sha256"]
        assert row["archive_sha256"] != authentic["archive_sha256"]
    control = records["flat"]
    assert control["directory_hashes"] == []
    assert control["payload_sha256"] == authentic["payload_sha256"]
    receipt = json.loads((d / "python-observations.json").read_text())
    assert receipt["source_payload_sha256"] == authentic["payload_sha256"]
    for row in receipt["cases"]:
        assert row["archive_sha256"] == records[row["case"]]["archive_sha256"]
        assert row["physical_sha256"] == records[row["case"]]["physical_sha256"]
    result = {
        "schema": "cmpct-j24i33-detached-r24-directory-referee-v1",
        "result": "PASS: exact physical custody, authentic serialized nil, derived empty mismatch",
        "science_only": True,
        "cases": list(records.values()),
    }
    (d / "independent-physical-audit.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, sort_keys=True, indent=2))

if __name__ == "__main__":
    main()
