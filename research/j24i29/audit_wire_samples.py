#!/usr/bin/env python3
"""Detached, Reader/Builder/codec-free referee for frozen r24 hardlink SHA samples.

Uses only stdlib struct/hashlib/zlib plus third-party MessagePack and Zstandard.
Physical sample files are preserved from the installed scientific court.
"""
from __future__ import annotations

import binascii
import hashlib
import json
from pathlib import Path
import struct
import sys
import zlib

import msgpack
import zstandard as zstd

HDR = struct.Struct("<8sHHQQQ32s")
FTR = struct.Struct("<8sBBBBQQQ32s")
BHDR = struct.Struct("<4sBBHQQII32s")
CODECS = (0, 1, 4)
LABELS = ("none", "empty", "matching", "contradictory")


def digest(data):
    return hashlib.sha256(data).digest()


def unpack_archive(path):
    b = Path(path).read_bytes()
    assert len(b) >= HDR.size + FTR.size
    magic, ver, flags, cs, us, span, ih = HDR.unpack_from(b)
    assert (magic, ver, flags) == (b"CMPCT24\0", 24, 0)
    assert cs > 0 and us > 0
    compressed = b[HDR.size:HDR.size + cs]
    assert len(compressed) == cs
    wire = zstd.ZstdDecompressor().decompress(compressed, max_output_size=us)
    assert len(wire) == us and digest(wire) == ih
    idx = msgpack.unpackb(wire, raw=False)
    assert idx["v"] == 24 and len(idx["blobs"]) == 1
    physical = b[HDR.size + cs:HDR.size + cs + span]
    assert len(physical) == span
    fm, kind, fcodec, ff, reserved, tail_cs, tail_us, parent, tail_h = FTR.unpack_from(b, len(b) - FTR.size)
    assert (fm, kind, fcodec, ff, reserved, parent) == (b"CMPTF24\0", 0, 1, 0, 0, 0)
    assert (tail_cs, tail_us, tail_h) == (cs, us, ih)
    assert b[len(b) - FTR.size - tail_cs:len(b) - FTR.size] == compressed
    off, logical_size, payload_size, codec, meta_size = idx["blobs"][0]
    assert off >= 0 and logical_size >= 0 and payload_size >= 0 and meta_size >= 0
    assert codec in CODECS
    m, c, flags, reserved, usize, csize, mlen, crc, h = BHDR.unpack_from(physical, off)
    assert (m, c, flags, reserved, usize, csize, mlen) == (
        b"CMA4", codec, 0, 0, logical_size, payload_size, meta_size
    )
    start = off + BHDR.size + mlen
    compressed_blob = physical[start:start + csize]
    assert len(compressed_blob) == csize and start + csize == len(physical)
    if codec == 0:
        raw = compressed_blob
    elif codec == 1:
        raw = zstd.ZstdDecompressor().decompress(compressed_blob, max_output_size=usize)
    else:
        raw = zlib.decompress(compressed_blob, -15)
    assert len(raw) == usize
    assert binascii.crc32(raw) & 0xffffffff == crc
    assert digest(raw) == h
    return {"sha":digest(b).hex(), "idx":idx, "physical":physical,
            "physical_sha":digest(physical).hex(), "raw":raw, "codec":codec}


def run(samples, receipt):
    rows = json.loads(Path(receipt).read_text())
    assert rows["schema"] == "cmpct-j24i29-wire-alias-sha-v1"
    cases = rows["cases"]
    assert len(cases) == 12, ("receipt entries", len(cases))
    keyed = {(int(row["codec"]), row["case"]): row for row in cases}
    assert len(keyed) == 12
    observations = []
    for codec in CODECS:
        original = unpack_archive(Path(samples) / f"{codec}-original.cmpct")
        assert original["codec"] == codec
        assert len(original["idx"]["files"]) == 1
        owner = original["idx"]["files"][0]
        assert owner[1] == 0 and owner[6][0] == 0
        assert owner[5] is None
        assert owner[4] == len(original["raw"])
        for label in LABELS:
            got = unpack_archive(Path(samples) / f"{codec}-{label}.cmpct")
            assert got["codec"] == codec
            assert got["physical"] == original["physical"]
            assert got["raw"] == original["raw"]
            assert len(got["idx"]["files"]) == 2
            owners = [x for x in got["idx"]["files"] if x[1] == 0]
            aliases = [x for x in got["idx"]["files"] if x[1] == 3]
            assert len(owners) == len(aliases) == 1
            assert owners[0] == owner
            alias = aliases[0]
            assert alias[6] == [owner[0]]
            assert alias[4] == owner[4]
            if label == "none":
                assert alias[5] is None
            elif label == "empty":
                assert alias[5] == b""
            elif label == "matching":
                assert alias[5] == digest(original["raw"])
            else:
                assert isinstance(alias[5], bytes) and len(alias[5]) == 32
                assert alias[5] != digest(original["raw"])
            rec = keyed[(codec, label)]
            assert rec["original_archive_sha256"] == original["sha"]
            assert rec["result_archive_sha256"] == got["sha"]
            assert rec["physical_blob_sha256"] == got["physical_sha"]
            assert rec["logical_owner_sha256"] == digest(got["raw"]).hex()
            assert rec["alias_row_sha256"] == (
                None if alias[5] is None else alias[5].hex()
            )
            assert rec["preflight_files"] == 2
            assert rec["verify_count"] == 2
            assert rec["present_alias_contradiction_accepted"] == (
                label == "contradictory"
            )
            observations.append({
                "codec": codec, "variant": label, "archive_sha256": got["sha"],
                "physical_sha256": got["physical_sha"],
                "contradictory_present_alias_sha": label == "contradictory",
                "installed_reader_verified_count": rec["verify_count"],
            })
    return {"schema": "cmpct-j24i29-detached-wire-referee-v1",
            "method": "no CMPCT imports; fully decoded physical original/derivative snapshots",
            "status": "PASS", "archives_checked": 15, "aliases_checked": len(observations),
            "contradictions_accepted": sum(o["contradictory_present_alias_sha"] for o in observations),
            "original_inputs_unchanged": True, "observations": observations}


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: audit_wire_samples.py SAMPLES_DIR RECEIPT_JSON")
    print(json.dumps(run(sys.argv[1], sys.argv[2]), indent=2, sort_keys=True))
