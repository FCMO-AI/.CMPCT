"""Fixed wire S_PACK conformance: no archive in this module comes from Builder.

The static golden bytes and expected member digests were created independently
from revision-24 framing, not generated through the CMPCT encoder under test.
"""
from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path

import pytest

from cmpct.codec import BHDR, CODEC_RAW, CODEC_ZSTD, HDR, S_PACK
from cmpct.reader import CMPCT
from cmpct.validation import preflight_archive

VECTORS = Path(__file__).parent / "conformance" / "v24-pack.json"


@pytest.fixture(scope="module")
def golden():
    manifest = json.loads(VECTORS.read_text(encoding="utf-8"))
    assert manifest["schema"] == "cmpct-v24-independent-pack-golden-v1"
    assert manifest["format_revision"] == 24
    assert {v["physical_codec"] for v in manifest["vectors"]} == {CODEC_RAW, CODEC_ZSTD}
    return manifest["vectors"]


@pytest.mark.parametrize("index", [0, 1])
def test_independently_frozen_pack_complete_and_selective_reads(tmp_path, golden, index):
    vec = golden[index]
    wire = base64.b64decode(vec["archive_base64"], validate=True)
    assert len(wire) == vec["archive_bytes"]
    assert hashlib.sha256(wire).hexdigest() == vec["archive_sha256"]
    assert wire.startswith(b"CMPCT24\0")
    path = tmp_path / f"{vec['name']}.cmpct"
    path.write_bytes(wire)

    preflight = preflight_archive(path)
    assert preflight["version"] == 24
    assert preflight["files"] == len(vec["files"])
    assert preflight["blobs"] == 1
    with CMPCT(path) as reader:
        assert set(reader.by) == set(vec["files"])
        assert len(reader.blobs) == 1
        blob_idx = 0
        assert reader.blobs[blob_idx][3] == vec["physical_codec"]
        offset = reader.record_base + reader.blobs[blob_idx][0]
        physical = BHDR.unpack_from(wire, offset)
        assert physical[0] == b"CMA4"
        assert physical[1] == vec["physical_codec"]
        assert physical[4] == vec["packed_blob_uncompressed_bytes"]
        assert physical[5] == vec["packed_blob_compressed_bytes"]
        assert physical[-1].hex() == vec["packed_blob_sha256"]

        for name, expected in vec["files"].items():
            row = reader.by[name]
            assert row[6][0] == S_PACK and row[6][1] == 0
            raw = bytes.fromhex(expected["hex"])
            assert len(raw) == expected["size"]
            assert hashlib.sha256(raw).hexdigest() == expected["sha256"]
            assert reader.read(name) == raw
            assert reader.read_range(name, 0, len(raw)) == raw
            assert reader.read_range(name, len(raw), 0) == b""
        for probe in vec["ranges"]:
            want = bytes.fromhex(probe["hex"])
            assert len(want) == probe["length"]
            assert reader.read_range(probe["name"], probe["offset"], probe["length"]) == want
        assert reader.read("alpha-copy.txt") == reader.read("alpha.txt")
        assert reader.by["alpha-copy.txt"][6] == reader.by["alpha.txt"][6]
        assert reader.verify() == len(vec["files"])

        with pytest.raises(ValueError):
            reader.read_range("omega.bin", vec["files"]["omega.bin"]["size"] - 1, 2)

        dest = tmp_path / f"{vec['name']}-extract"
        reader.extractall(dest, metadata=False)
        for name, expected in vec["files"].items():
            assert (dest / name).read_bytes() == bytes.fromhex(expected["hex"])


@pytest.mark.parametrize("index", [0, 1])
def test_pack_corrupt_physical_data_is_rejected(tmp_path, golden, index):
    vec = golden[index]
    raw = bytearray(base64.b64decode(vec["archive_base64"], validate=True))
    path = tmp_path / "corrupt-pack.cmpct"
    path.write_bytes(raw)
    with CMPCT(path) as reader:
        record = reader.record_base + reader.blobs[0][0]
        payload_start = record + BHDR.size + reader.blobs[0][4]
    # Corrupt physical bytes without modifying the authenticated index or BHDR
    # checksum. Some codecs fail to decompress, others fail CRC after decoding.
    raw[payload_start + 4] ^= 0x40
    path.write_bytes(raw)
    with CMPCT(path) as reader:
        with pytest.raises((IOError, OSError, ValueError, RuntimeError)):
            reader.read("alpha.txt")
