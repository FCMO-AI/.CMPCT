#!/usr/bin/env python3
"""J24P01 independent physical-wire and receipt auditor; imports no CMPCT product.

It does not trust the first-party PASS bit: reinterprets source-frozen r24 wire,
validates both index copies, decompresses by independently installed zstandard,
derives every PACK slice, and rejects deliberate falsified evidence.
"""
from __future__ import annotations

import base64
import binascii
import copy
import hashlib
import json
import os
from pathlib import Path
import struct

import msgpack
import zstandard

HDR = struct.Struct("<8sHHQQQ32s")
BHDR = struct.Struct("<4sBBHQQII32s")
FTR = struct.Struct("<8sBBBBQQQ32s")


def sha(x: bytes) -> bytes:
    return hashlib.sha256(x).digest()


def check(receipt: dict, manifest: dict, manifest_bytes: bytes) -> None:
    assert receipt["schema"] == "j24p01-pack-crosshost-v1"
    assert receipt["status"] == "PASS"
    assert receipt["head"] == os.environ["CMPCT_EVIDENCE_HEAD"]
    assert receipt["manifest_sha256"] == sha(manifest_bytes).hex()
    assert "site-packages" in receipt["installed"].lower() or "dist-packages" in receipt["installed"].lower(), receipt["installed"]
    assert len(receipt["source_hashes"]) == 2
    assert set(receipt["source_hashes"]) == {"reader.py", "codec.py"}
    assert manifest["schema"] == "cmpct-v24-independent-pack-golden-v1"
    assert len(manifest["vectors"]) == 2
    reported = {x["name"]: x for x in receipt["vectors"]}
    assert set(reported) == {x["name"] for x in manifest["vectors"]}
    dctx = zstandard.ZstdDecompressor()
    for v in manifest["vectors"]:
        obs = reported[v["name"]]
        data = base64.b64decode(v["archive_base64"], validate=True)
        assert len(data) == v["archive_bytes"] == obs["archive_bytes"]
        assert sha(data).hex() == v["archive_sha256"] == obs["archive_sha256"]
        magic, ver, flags, ci, ui, physical_span, digest = HDR.unpack_from(data)
        assert (magic, ver) == (b"CMPCT24\0", 24)
        assert flags == 0
        comp_index = data[HDR.size:HDR.size+ci]
        decoded_index = dctx.decompress(comp_index, max_output_size=ui)
        assert sha(decoded_index) == digest
        index = msgpack.unpackb(decoded_index, raw=False)
        assert index["v"] == 24
        assert len(index["blobs"]) == 1
        assert len(index["files"]) == len(v["files"])
        tail_comp = data[HDR.size+ci+physical_span:-FTR.size]
        assert tail_comp == comp_index
        tail = FTR.unpack_from(data, len(data)-FTR.size)
        assert tail == (b"CMPTF24\0", 0, 1, 0, 0, ci, ui, 0, digest)
        physical_start = HDR.size + ci
        head = BHDR.unpack_from(data, physical_start)
        blob_magic, codec, blob_flags, reserve, logical_size, compressed_size, meta_len, crc, digest_physical = head
        assert blob_magic == b"CMA4"
        assert blob_flags == 0 and reserve == 0 and meta_len == 0
        assert codec == v["physical_codec"] == obs["physical_codec"]
        assert logical_size == v["packed_blob_uncompressed_bytes"]
        assert compressed_size == v["packed_blob_compressed_bytes"]
        physical_bytes = data[physical_start+BHDR.size:physical_start+BHDR.size+compressed_size]
        assert physical_start+BHDR.size+compressed_size == physical_start+physical_span
        original_pack = physical_bytes if codec == 0 else dctx.decompress(
            physical_bytes, max_output_size=logical_size
        )
        assert len(original_pack) == logical_size
        assert binascii.crc32(original_pack) & 0xffffffff == crc
        assert sha(original_pack) == digest_physical
        assert sha(original_pack).hex() == v["packed_blob_sha256"]
        found = {}
        for row in index["files"]:
            name, kind, mode, mtime, declared, _hash, storage = row
            assert kind == 0
            assert name in v["files"]
            assert storage[0:2] == [4, 0]
            offset, length = storage[2:]
            assert offset >= 0 and length == declared
            assert offset + length <= len(original_pack)
            reconstructed = original_pack[offset:offset+length]
            want = bytes.fromhex(v["files"][name]["hex"])
            assert reconstructed == want
            assert len(reconstructed) == v["files"][name]["size"]
            assert sha(reconstructed).hex() == v["files"][name]["sha256"]
            assert obs["members"][name] == sha(reconstructed).hex()
            found[name] = (offset, length, reconstructed)
        assert set(found) == set(v["files"])
        assert found["alpha-copy.txt"][:2] == found["alpha.txt"][:2]
        for probe in v["ranges"]:
            p = found[probe["name"]][2][probe["offset"]:probe["offset"]+probe["length"]]
            assert p == bytes.fromhex(probe["hex"])
        assert obs["ranges"] == len(v["ranges"])
        for key in ["preflight", "full_reads", "selective_reads", "verify", "extraction",
                    "physical_corruption_rejected", "authenticated_bad_index_rejected"]:
            assert obs[key] is True, (v["name"], key)


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    receipt = json.loads(Path(os.environ.get("CMPCT_J24P01_EVIDENCE", "pack-crosshost-evidence")).joinpath("result.json").read_text())
    manifest_path = root / "tests" / "conformance" / "v24-pack.json"
    raw = manifest_path.read_bytes()
    manifest = json.loads(raw)
    check(receipt, manifest, raw)
    falsified = copy.deepcopy(receipt)
    falsified["vectors"][0]["archive_sha256"] = "00" * 32
    try:
        check(falsified, manifest, raw)
    except AssertionError:
        pass
    else:
        raise AssertionError("independent referee accepted fabricated archive digest")
    evidence = Path(os.environ.get("CMPCT_J24P01_EVIDENCE", "pack-crosshost-evidence"))
    (evidence / "referee.json").write_text(json.dumps({
        "schema": "j24p01-independent-physical-referee-v1", "status": "PASS",
        "head": receipt["head"], "source": "original immutable Builder-independent #307 wires",
        "vectors": len(manifest["vectors"]), "members": sum(len(v["files"]) for v in manifest["vectors"]),
        "forged_receipts_rejected": 1,
    }, indent=2, sort_keys=True) + "\n")
    print("PASS: independent physical RAW/Zstd PACK decode, 8 members, two indexes each, forged receipt rejected")
