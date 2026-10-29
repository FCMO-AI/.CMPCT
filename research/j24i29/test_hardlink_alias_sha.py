#!/usr/bin/env python3
"""J24I29 — independent fixed-wire hardlink alias SHA custody court.

Scientific NEGATIVE is a successful result when the actual installed Reader
accepts an internally contradictory *present alias-row* digest. Do not merge
this test as a permanent product assertion without a normative format decision.
"""
from __future__ import annotations

import base64
import binascii
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
import zlib

import msgpack

from cmpct.codec import (
    BHDR, BMAGIC, CODEC_RAW, CODEC_ZSTD, CODEC_DEFLATE, FMAGIC, FTR,
    HDR, K_HARDLINK, MAGIC, S_BLOB, VERSION, sha, zc, zd,
)
from cmpct.reader import CMPCT
from cmpct.validation import preflight_archive

ROOT = Path(__file__).resolve().parents[2]
GOLDEN = ROOT / "tests" / "conformance" / "v24-direct-codecs.json"
CASES = []


def physical_and_index(archive: bytes):
    """Parse both exact authoritative indexes and physical RAW/ZSTD/Deflate blob.

    This referee uses struct/messagepack/zlib/direct codec, not CMPCT.Reader
    or Builder; source and re-signed variants share identical physical bytes.
    """
    m, v, flags, cs, us, span, digest = HDR.unpack_from(archive, 0)
    assert (m, v, flags) == (MAGIC, VERSION, 0)
    index_start = HDR.size
    compressed = archive[index_start:index_start + cs]
    wire = zd(compressed, us)
    assert len(wire) == us and sha(wire) == digest
    index = msgpack.unpackb(wire, raw=False)
    physical = archive[index_start + cs:index_start + cs + span]
    assert len(physical) == span
    footer_at = len(archive) - FTR.size
    fmagic, kind, codec, ff, reserved, tail_cs, tail_us, parent, tail_digest = FTR.unpack_from(
        archive, footer_at
    )
    assert (fmagic, kind, codec, ff, reserved, parent) == (FMAGIC, 0, 1, 0, 0, 0)
    assert tail_cs == cs and tail_us == us and tail_digest == digest
    assert archive[footer_at - tail_cs:footer_at] == compressed
    assert len(index["blobs"]) == 1
    off, size, comp_size, blob_codec, meta_len = index["blobs"][0]
    p = off
    bhmagic, physical_codec, bf, br, rus, rcs, rml, crc, phash = BHDR.unpack_from(physical, p)
    assert (bhmagic, physical_codec, bf, br) == (BMAGIC, blob_codec, 0, 0)
    assert (rus, rcs, rml) == (size, comp_size, meta_len)
    p += BHDR.size + meta_len
    data = physical[p:p + comp_size]
    assert len(data) == comp_size and p + comp_size == len(physical)
    if blob_codec == CODEC_RAW:
        raw = data
    elif blob_codec == CODEC_ZSTD:
        raw = zd(data, size)
    elif blob_codec == CODEC_DEFLATE:
        raw = zlib.decompress(data, -15)
    else:
        raise AssertionError("outside fixed direct-codec vector")
    assert len(raw) == size
    assert (binascii.crc32(raw) & 0xffffffff) == crc
    assert hashlib.sha256(raw).digest() == phash
    return index, physical, raw


def add_hardlink_alias(original: bytes, alias: str, digest):
    """Only append one logical alias row and recompute both unkeyed index copies."""
    index, physical, raw = physical_and_index(original)
    assert len(index["files"]) == 1
    owner = index["files"][0]
    assert owner[6][0] == S_BLOB and owner[4] == len(raw)
    index["files"].append([alias, K_HARDLINK, owner[2], owner[3], owner[4], digest, [owner[0]]])
    index["files"].sort(key=lambda row: row[0])
    encoded_index = msgpack.packb(index, use_bin_type=True)
    compressed = zc(encoded_index, 12)
    digest_index = sha(encoded_index)
    header = HDR.pack(MAGIC, VERSION, 0, len(compressed), len(encoded_index),
                      len(physical), digest_index)
    footer = FTR.pack(FMAGIC, 0, 1, 0, 0, len(compressed), len(encoded_index), 0, digest_index)
    changed = header + compressed + physical + compressed + footer
    after, preserved_physical, preserved_raw = physical_and_index(changed)
    assert preserved_physical == physical and preserved_raw == raw
    assert next(r for r in after["files"] if r[0] == alias)[5] == digest
    return changed


class FixedWireHardlinkAliasSHA(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        gold = json.loads(GOLDEN.read_text(encoding="utf-8"))
        assert gold["schema"] == "cmpct-v24-golden-direct-codecs-v1"
        assert gold["format_revision"] == 24
        assert {r["codec"] for r in gold["vectors"]} == {
            CODEC_RAW, CODEC_ZSTD, CODEC_DEFLATE
        }
        cls.vectors = gold["vectors"]

    def test_direct_owner_and_alias_sha_semantics(self):
        for vec in self.vectors:
            with self.subTest(codec=vec["codec"]):
                original = base64.b64decode(vec["archive_base64"], validate=True)
                assert len(original) == vec["archive_bytes"]
                assert hashlib.sha256(original).hexdigest() == vec["archive_sha256"]
                idx, physical, raw = physical_and_index(original)
                assert idx["files"][0][0] == vec["name"]
                assert hashlib.sha256(raw).hexdigest() == vec["logical_sha256"]
                alias = "z-j24i29-alias-" + str(vec["codec"]) + ".bin"
                foreign = sha(b"J24I29 deliberately contradictory hardlink alias SHA")
                assert foreign != sha(raw)
                with tempfile.TemporaryDirectory(prefix="j24i29-") as td:
                    source = Path(td) / "original.cmpct"
                    source.write_bytes(original)
                    with CMPCT(source) as ar:
                        assert ar.verify() == 1
                    for label, row_sha in (
                        ("none", None),
                        ("empty", b""),
                        ("matching", sha(raw)),
                        ("contradictory", foreign),
                    ):
                        archive = add_hardlink_alias(original, alias, row_sha)
                        out = Path(td) / (label + ".cmpct")
                        out.write_bytes(archive)
                        pre = preflight_archive(out)
                        assert pre["version"] == 24 and pre["files"] == 2
                        with CMPCT(out) as ar:
                            assert ar.read(alias) == raw
                            offset = min(3, len(raw))
                            length = min(17, len(raw) - offset)
                            assert ar.read_range(alias, offset, length) == raw[offset:offset + length]
                            verified = ar.verify()
                        # Deliberately preserve the predicted product-negative:
                        # the CURRENT candidate accepts an incorrect present
                        # alias digest. This is not a future normative assertion.
                        self.assertEqual(verified, 2, (vec["codec"], label))
                        CASES.append({
                            "codec": int(vec["codec"]),
                            "case": label,
                            "original_archive_sha256": vec["archive_sha256"],
                            "result_archive_sha256": hashlib.sha256(archive).hexdigest(),
                            "physical_blob_sha256": hashlib.sha256(physical).hexdigest(),
                            "logical_owner_sha256": hashlib.sha256(raw).hexdigest(),
                            "alias_row_sha256": None if row_sha is None else bytes(row_sha).hex(),
                            "preflight_files": pre["files"],
                            "verify_count": verified,
                            "present_alias_contradiction_accepted": bool(label == "contradictory"),
                        })

if __name__ == "__main__":
    try:
        unittest.main(verbosity=2, exit=False)
    finally:
        dest = os.environ.get("J24I29_RESULTS")
        if dest:
            Path(dest).write_text(json.dumps({
                "schema": "cmpct-j24i29-wire-alias-sha-v1",
                "classification": "research-only / does not authorize release",
                "cases": CASES,
            }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
