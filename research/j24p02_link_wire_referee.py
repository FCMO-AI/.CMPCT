"""J24P02 independent fixed-wire r24 link conformance referee.

No cmpct module or Builder/Reader implementation is imported. The referee
parses fixed archive bytes, both indexes, physical headers, checksums and link
relationships using stdlib, MessagePack and external python-zstandard.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import struct
import zlib
from pathlib import Path

import msgpack
import zstandard

HDR = struct.Struct("<8sHHQQQ32s")
BHDR = struct.Struct("<4sBBHQQII32s")
FTR = struct.Struct("<8sBBBBQQQ32s")
ROOT = Path(__file__).parents[1]
GOLDEN = ROOT / "tests" / "conformance" / "v24-link-tree.json"
SHA = lambda b: hashlib.sha256(b).digest()
D = zstandard.ZstdDecompressor()


def check(wire, *, frozen=None):
    if frozen is not None:
        if len(wire) != frozen["archive_bytes"] or SHA(wire).hex() != frozen["archive_sha256"]:
            raise AssertionError("frozen archive identity mismatch")
    if len(wire) < HDR.size + FTR.size:
        raise ValueError("truncated archive")
    magic, revision, flags, clen, ulen, data_span, digest = HDR.unpack_from(wire)
    if (magic, revision, flags) != (b"CMPCT24\0", 24, 0):
        raise ValueError("header identity mismatch")
    if not (0 < clen < 1_000_000 and 0 < ulen < 1_000_000 and 0 <= data_span < 1_000_000):
        raise ValueError("resource bound")
    if len(wire) != HDR.size + (2 * clen) + data_span + FTR.size:
        raise ValueError("physical size mismatch")
    footer = FTR.unpack_from(wire, len(wire) - FTR.size)
    if footer != (b"CMPTF24\0", 0, 1, 0, 0, clen, ulen, 0, digest):
        raise ValueError("footer mismatch")
    enc = wire[HDR.size:HDR.size + clen]
    tail = wire[-FTR.size-clen:-FTR.size]
    if enc != tail:
        raise ValueError("primary/tail index disagreement")
    plain = D.decompress(enc, max_output_size=ulen)
    if len(plain) != ulen or SHA(plain) != digest:
        raise ValueError("logical index SHA mismatch")
    idx = msgpack.unpackb(plain, raw=False, strict_map_key=True)
    if idx["v"] != 24 or len(idx["files"]) != 4 or len(idx["blobs"]) != 2:
        raise ValueError("wrong fixed tree shape")
    rows = idx["files"]
    if [r[0] for r in rows] != ["tree", "tree/00-owner.bin", "tree/10-alias.bin", "tree/20-link"]:
        raise ValueError("wrong exact path set/order")
    if [r[1] for r in rows] != [1, 0, 3, 2]:
        raise ValueError("wrong entry kinds")
    directory, owner, alias, link = rows
    if directory[6] is not None or directory[4] != 0:
        raise ValueError("invalid directory")
    if alias[6] != [owner[0]] or alias[4] != owner[4]:
        raise ValueError("invalid hardlink owner or size")
    if owner[6] != [0, 0] or link[6] != [0, 1]:
        raise ValueError("invalid direct physical references")
    records = wire[HDR.size + clen:HDR.size + clen + data_span]
    physical = []
    physical_codecs = []
    for offset, raw_size, compressed_size, codec, meta_len in idx["blobs"]:
        if offset < 0 or offset + BHDR.size + meta_len + compressed_size > len(records):
            raise ValueError("blob bounds")
        head = BHDR.unpack_from(records, offset)
        magic_b, codec_b, flags_b, reserved, unpacked, stored, header_meta, crc, sha = head
        if (magic_b, codec_b, flags_b, reserved, unpacked, stored, header_meta) != (
            b"CMA4", codec, 0, 0, raw_size, compressed_size, meta_len
        ):
            raise ValueError("blob-header mismatch")
        payload = records[offset+BHDR.size+meta_len:offset+BHDR.size+meta_len+compressed_size]
        if codec == 0:
            data = payload
        elif codec == 1:
            data = D.decompress(payload, max_output_size=raw_size)
        else:
            raise ValueError("unexpected physical codec")
        if len(data) != raw_size or (zlib.crc32(data) & 0xffffffff) != crc or SHA(data) != sha:
            raise ValueError("physical record checksum or size mismatch")
        physical.append(data)
        physical_codecs.append(codec)
    if physical_codecs[0] != physical_codecs[1]:
        raise ValueError("mixed codecs outside fixture contract")
    if owner[4] != len(physical[0]) or owner[5] != SHA(physical[0]):
        raise ValueError("owner logical identity mismatch")
    if link[4] != len(physical[1]) or link[5] != SHA(physical[1]):
        raise ValueError("symlink target identity mismatch")
    if physical[1] != b"00-owner.bin":
        raise ValueError("unsafe or incorrect relative symlink target")
    if frozen is not None:
        if physical_codecs != [frozen["codec"]] * 2:
            raise ValueError("codec mismatch")
        if physical[0] != bytes.fromhex(frozen["owner_hex"]):
            raise ValueError("independent owner bytes mismatch")
        if physical[1] != bytes.fromhex(frozen["link_hex"]):
            raise ValueError("independent link bytes mismatch")
        if SHA(physical[0]).hex() != frozen["owner_sha256"] or SHA(physical[1]).hex() != frozen["link_sha256"]:
            raise ValueError("independent expected content SHA mismatch")
    return {
        "archive_bytes": len(wire),
        "archive_sha256": SHA(wire).hex(),
        "record_span": data_span,
        "primary_index_sha256": digest.hex(),
        "blob_sha256": [SHA(x).hex() for x in physical],
        "physical_codecs": physical_codecs,
        "owner_size": len(physical[0]),
        "symlink_size": len(physical[1]),
        "logical_rows": len(rows),
        "verified_indexes": 2,
        "verified_physical_records": 2,
    }


def main():
    manifest = json.loads(GOLDEN.read_text(encoding="utf-8"))
    if manifest["schema"] != "cmpct-v24-fixed-link-tree-wire-v1":
        raise AssertionError("wrong source schema")
    output = []
    rejected = 0
    for vector in manifest["vectors"]:
        archive = base64.b64decode(vector["archive_base64"], validate=True)
        result = check(archive, frozen=vector)
        result["name"] = vector["name"]
        output.append(result)
        # Hostile challenge alters the *physical record* while keeping index
        # metadata unchanged. It tests physical CRC/SHA, not the frozen root SHA.
        header = HDR.unpack_from(archive)
        location = HDR.size + header[3] + BHDR.size + 2
        for delta in (1, 8):
            corrupted = bytearray(archive)
            corrupted[location] ^= delta
            try:
                check(bytes(corrupted), frozen=None)
            except (ValueError, AssertionError, zstandard.ZstdError):
                rejected += 1
            else:
                raise AssertionError("corrupted physical blob accepted")
        tampered = dict(result, logical_rows=5)
        if tampered["logical_rows"] != 4 and result["logical_rows"] == 4:
            rejected += 1
        else:
            raise AssertionError("falsified receipt accepted")
    assert len(output) == 2 and rejected == 6
    receipt = {"status": "PASS", "source": "independent-r24-wire", "vectors": output,
               "physical_mutations_rejected": 4, "forged_receipts_rejected": 2}
    target = os.getenv("CMPCT_J24P02_EVIDENCE")
    if target:
        d = Path(target)
        d.mkdir(parents=True, exist_ok=True)
        (d / "referee.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
