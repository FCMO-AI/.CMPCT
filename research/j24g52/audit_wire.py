"""J24G52 physically independent revision-24 wire referee (never imports cmpct)."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import struct
import sys

import msgpack
import zstandard as zstd

HDR = struct.Struct("<8sHHQQQ32s")
FTR = struct.Struct("<8sBBBBQQQ32s")
BHDR = struct.Struct("<4sBBHQQII32s")


def sha(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def inspect(archive: bytes) -> dict:
    assert len(archive) >= HDR.size + FTR.size
    magic, version, flags, compressed, uncompressed, body_span, digest = HDR.unpack_from(archive)
    assert (magic, version, flags) == (b"CMPCT24\x00", 24, 0)
    assert compressed > 0 and uncompressed > 0
    index_start = HDR.size
    body_start = index_start + compressed
    body_end = body_start + body_span
    tail_end = body_end + compressed
    assert tail_end + FTR.size == len(archive)
    encoded = archive[index_start:body_start]
    assert archive[body_end:tail_end] == encoded
    index_raw = zstd.ZstdDecompressor().decompress(encoded, max_output_size=uncompressed + 1)
    assert len(index_raw) == uncompressed and sha(index_raw) == digest
    footer = FTR.unpack_from(archive, tail_end)
    assert footer == (b"CMPTF24\x00", 0, 1, 0, 0, compressed, uncompressed, 0, digest)
    index = msgpack.unpackb(index_raw, raw=False)
    assert index["v"] == 24
    by = {row[0]: (ordinal, row) for ordinal, row in enumerate(index["files"])}
    assert len(by) == len(index["files"]) == 4
    assert set(by) == {"a-owner.bin", "z-alias.bin", "b-copy.bin", "c-copy.bin"}
    assert by["a-owner.bin"][1][1] == 0
    assert by["z-alias.bin"][1][1] == 3
    assert by["z-alias.bin"][1][6] == ["a-owner.bin"]
    assert by["b-copy.bin"][1][1] == by["c-copy.bin"][1][1] == 0
    for i, record in enumerate(index["blobs"]):
        off, usize, csize, codec, meta_len = record
        at = body_start + off
        header = BHDR.unpack_from(archive, at)
        assert header[0] == b"CMA4"
        assert (header[1], header[4], header[5], header[6]) == (codec, usize, csize, meta_len)
        assert at + BHDR.size + meta_len + csize <= body_end
    attrs = {}
    for ordinal, records in index["fsmeta"]["xattrs"]:
        assert 0 <= ordinal < len(index["files"])
        for key, value in records:
            assert isinstance(key, str) and isinstance(value, bytes)
            attrs[(index["files"][ordinal][0], key)] = value
    assert len(attrs) == 4
    (owner_key, owner_value), = [(key, value) for (name, key), value in attrs.items()
                                 if name == "a-owner.bin"]
    (alias_key, alias_value), = [(key, value) for (name, key), value in attrs.items()
                                 if name == "z-alias.bin"]
    assert owner_key == alias_key
    assert attrs[("b-copy.bin", owner_key)] != attrs[("c-copy.bin", owner_key)]
    return {
        "archive_sha256": sha(archive).hex(),
        "index_sha256": sha(index_raw).hex(),
        "body_sha256": sha(archive[body_start:body_end]).hex(),
        "bytes": len(archive),
        "body_bytes": body_span,
        "explicit_hardlink_xattr_conflict": owner_value != alias_value,
        "different_content_inodes_allowed": True,
    }


def main(root: Path) -> None:
    good = inspect((root / "compatible.cmpct").read_bytes())
    bad = inspect((root / "contradictory.cmpct").read_bytes())
    assert not good["explicit_hardlink_xattr_conflict"]
    assert bad["explicit_hardlink_xattr_conflict"]
    assert good["body_sha256"] == bad["body_sha256"]

    # Prove the referee actually detects several physical corruption classes.
    original = (root / "compatible.cmpct").read_bytes()
    fields = HDR.unpack_from(original)
    tail_pos = HDR.size + fields[3] + fields[5]
    mutations = {
        "primary": HDR.size,
        "tail": tail_pos,
        "footer": len(original) - FTR.size,
        "physical_blob": HDR.size + fields[3],
    }
    refused = {}
    for label, pos in mutations.items():
        damaged = bytearray(original)
        damaged[pos] ^= 1
        try:
            inspect(bytes(damaged))
        except (AssertionError, ValueError, zstd.ZstdError, msgpack.UnpackException, struct.error):
            refused[label] = True
        else:
            refused[label] = False
    assert all(refused.values()), refused
    result = {
        "audit": "J24G52 independent wire referee",
        "compatible": good, "contradictory": bad,
        "mutations_rejected": refused,
        "decision": "SIGNED_EXPLICIT_HARDLINK_CONFLICT_DISTINGUISHED",
        "scope": "wire integrity/metadata only; OS inode restoration is separate installed-product evidence",
    }
    (root / "independent-referee.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
