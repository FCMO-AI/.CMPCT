#!/usr/bin/env python3
"""Independently regenerate J24P02 frozen revision-24 links, without CMPCT imports.

Only checks the committed bytes. Toolchain drift is a diagnostic failure and
never permission to update the golden vectors in place.
"""
from __future__ import annotations

import base64
import hashlib
import json
import struct
import zlib
from pathlib import Path

import msgpack
import zstandard

HDR = struct.Struct("<8sHHQQQ32s")
BHDR = struct.Struct("<4sBBHQQII32s")
FTR = struct.Struct("<8sBBBBQQQ32s")
SHA = lambda b: hashlib.sha256(b).digest()
ZC = zstandard.ZstdCompressor(level=12)

OWNER = b"CMPCT independent link-tree conformance, not Builder bytes\n" + bytes(range(35)) + b"\0CMA4\0"
LINK = b"00-owner.bin"


def build(codec: int):
    records = bytearray()
    blobs = []
    for source in (OWNER, LINK):
        physical = source if codec == 0 else ZC.compress(source)
        blobs.append([len(records), len(source), len(physical), codec, 0])
        records.extend(BHDR.pack(
            b"CMA4", codec, 0, 0, len(source), len(physical), 0,
            zlib.crc32(source) & 0xffffffff, SHA(source),
        ))
        records.extend(physical)
    rows = [
        ["tree", 1, 0o755, 0, 0, b"", None],
        ["tree/00-owner.bin", 0, 0o644, 0, len(OWNER), SHA(OWNER), [0, 0]],
        ["tree/10-alias.bin", 3, 0o644, 0, len(OWNER), None, ["tree/00-owner.bin"]],
        ["tree/20-link", 2, 0o777, 0, len(LINK), SHA(LINK), [0, 1]],
    ]
    index = {
        "v": 24, "files": rows, "blobs": blobs, "recipes": [],
        "dict_blob": None,
        "fsmeta": {"owner": [0, 0], "owner_overrides": [], "xattrs": []},
        "features": ["sha256", "dual-index"],
    }
    plain = msgpack.packb(index, use_bin_type=True)
    enc = ZC.compress(plain)
    digest = SHA(plain)
    wire = (HDR.pack(b"CMPCT24\0", 24, 0, len(enc), len(plain), len(records), digest)
            + enc + records + enc
            + FTR.pack(b"CMPTF24\0", 0, 1, 0, 0, len(enc), len(plain), 0, digest))
    return wire


def main():
    path = Path(__file__).with_name("v24-link-tree.json")
    frozen = json.loads(path.read_text(encoding="utf-8"))
    assert frozen["schema"] == "cmpct-v24-fixed-link-tree-wire-v1"
    assert len(frozen["vectors"]) == 2
    for v in frozen["vectors"]:
        data = build(v["codec"])
        if base64.b64encode(data).decode("ascii") != v["archive_base64"]:
            raise AssertionError(f"{v['name']}: generator differs from frozen physical bytes")
        if len(data) != v["archive_bytes"] or SHA(data).hex() != v["archive_sha256"]:
            raise AssertionError(f"{v['name']}: frozen SHA/length mismatch")
        print(v["name"], len(data), SHA(data).hex())
    print("FROZEN_LINK_WIRE_GENERATION_PASS")


if __name__ == "__main__":
    main()
