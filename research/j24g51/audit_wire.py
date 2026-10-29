"""Independent signed-wire referee for J24G51; imports no CMPCT modules.

It authenticates index, footer, immutable physical body, and the distinct
inode-metadata requirements; it never claims an actual OS extraction result.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import struct
import sys

import msgpack
import zstandard as zstd

HDR = struct.Struct("<8sHHQQQ32s")
# Use the public revision-24 footer tuple layout from FORMAT / fixed test vectors.
# The footer is decoded independently and the primary/tail payload bytes must agree.
FTR = struct.Struct("<8sBBBBQQQ32s")
MAGIC = b"CMPCT24\0"
FMAGIC = b"CMPTF24\0"


def sha(v: bytes) -> bytes:
    return hashlib.sha256(v).digest()


def load(path: Path):
    archive = path.read_bytes()
    magic, version, flags, compressed_size, raw_size, span, expected = HDR.unpack_from(archive)
    assert magic == MAGIC and version == 24 and flags == 0
    encoded = archive[HDR.size:HDR.size + compressed_size]
    decoded = zstd.ZstdDecompressor().decompress(encoded, max_output_size=raw_size + 1)
    assert len(decoded) == raw_size and sha(decoded) == expected
    body_end = HDR.size + compressed_size + span
    assert archive[body_end:body_end + compressed_size] == encoded
    footer = FTR.unpack_from(archive, body_end + compressed_size)
    assert footer[0] == FMAGIC and footer[1] == 0 and footer[2] == 1
    assert footer[5] == compressed_size and footer[6] == raw_size
    assert footer[7] == 0 and footer[8] == expected
    assert body_end + compressed_size + FTR.size == len(archive)
    index = msgpack.unpackb(decoded, raw=False)
    assert index["v"] == 24
    by = {row[0]: (i, row) for i, row in enumerate(index["files"])}
    assert len(by) == len(index["files"]) == 4
    assert by["z-alias.bin"][1][6] == ["a-owner.bin"]
    assert by["a-owner.bin"][1][1] == by["b-copy.bin"][1][1] == by["c-copy.bin"][1][1]
    xattrs = {
        index["files"][ordinal][0]: dict(items)
        for ordinal, items in index["fsmeta"]["xattrs"]
    }
    assert set(xattrs) == set(by)
    return {
        "archive_bytes": len(archive),
        "archive_sha256": sha(archive).hex(),
        "index_sha256": sha(decoded).hex(),
        "body_sha256": sha(archive[HDR.size + compressed_size:body_end]).hex(),
        "physical_body_bytes": span,
        "owner_alias_equal": xattrs["a-owner.bin"] == xattrs["z-alias.bin"],
        "regular_pair_distinct": xattrs["b-copy.bin"] != xattrs["c-copy.bin"],
        "indexed_paths": list(by),
    }


def main():
    root = Path(sys.argv[1])
    compatible = load(root / "compatible.cmpct")
    contradictory = load(root / "contradictory.cmpct")
    assert compatible["owner_alias_equal"]
    assert not contradictory["owner_alias_equal"]
    assert compatible["regular_pair_distinct"] and contradictory["regular_pair_distinct"]
    assert compatible["body_sha256"] == contradictory["body_sha256"]
    assert compatible["physical_body_bytes"] == contradictory["physical_body_bytes"]
    assert compatible["archive_sha256"] != contradictory["archive_sha256"]
    data = {
        "independent_referee": "J24G51",
        "compatible": compatible,
        "contradictory": contradictory,
        "decision": "AUTHENTICATED_INDEX_CONTRADICTS_SHARED_INODE_METADATA",
        "scope": "wire only; physical restored inode and host xattrs are first-party hosted test evidence",
    }
    (root / "independent-referee.json").write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    print(json.dumps(data, sort_keys=True))


if __name__ == "__main__":
    main()
