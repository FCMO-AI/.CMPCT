#!/usr/bin/env python3
"""J24I31 scientific negative: present PACK row digests versus strong verify.

This test is source-locked research and MUST NOT be promoted into a normative
product assertion that contradictory SHA should be accepted.
"""
from __future__ import annotations

import base64
import binascii
import copy
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest

import msgpack
import zstandard

from cmpct.codec import BHDR, BMAGIC, FTR, FMAGIC, HDR, MAGIC, VERSION, S_PACK
from cmpct.reader import CMPCT
from cmpct.validation import preflight_archive

ROOT = Path(__file__).resolve().parents[2]
GOLDEN = ROOT / "tests" / "conformance" / "v24-pack.json"
RESULTS = []
H = lambda data: hashlib.sha256(data).digest()


def physical_oracle(wire: bytes):
    """Independent MessagePack/Zstandard/struct physical/index referee."""
    magic, version, flags, cs, us, span, digest = HDR.unpack_from(wire)
    assert (magic, version, flags) == (MAGIC, VERSION, 0)
    packed_idx = wire[HDR.size:HDR.size + cs]
    raw_idx = zstandard.ZstdDecompressor().decompress(packed_idx, max_output_size=us)
    assert len(raw_idx) == us and H(raw_idx) == digest
    index = msgpack.unpackb(raw_idx, raw=False)
    payload = wire[HDR.size + cs:HDR.size + cs + span]
    assert len(payload) == span
    tail_at = len(wire) - FTR.size
    fmagic, kind, codec, flags2, reserved, fcs, fus, prev, fdigest = FTR.unpack_from(wire, tail_at)
    assert (fmagic, kind, codec, flags2, reserved, prev) == (FMAGIC, 0, 1, 0, 0, 0)
    assert (fcs, fus, fdigest) == (cs, us, digest)
    assert wire[tail_at - cs:tail_at] == packed_idx
    assert len(wire) == HDR.size + cs + span + cs + FTR.size
    assert len(index["blobs"]) == 1
    off, size, csize, codec, meta_len = index["blobs"][0]
    head = BHDR.unpack_from(payload, off)
    assert head[0] == BMAGIC and head[1] == codec
    assert head[4:7] == (size, csize, meta_len)
    start = off + BHDR.size + meta_len
    physical = payload[start:start + csize]
    assert len(physical) == csize
    assert start + csize == len(payload)
    if codec == 0:
        unpacked = physical
    elif codec == 1:
        unpacked = zstandard.ZstdDecompressor().decompress(physical, max_output_size=size)
    else:
        raise AssertionError("outside frozen RAW/Zstd PACK oracle")
    assert len(unpacked) == size and H(unpacked) == head[-1]
    assert (binascii.crc32(unpacked) & 0xffffffff) == head[-2]
    return index, payload, unpacked


def reseal_one_present_row(wire: bytes, member: str, value):
    index, physical, original_pack = physical_oracle(wire)
    changed = copy.deepcopy(index)
    matches = [row for row in changed["files"] if row[0] == member]
    assert len(matches) == 1 and matches[0][6][0] == S_PACK
    before = matches[0][5]
    matches[0][5] = value
    encoded = msgpack.packb(changed, use_bin_type=True)
    compressed = zstandard.ZstdCompressor(level=12).compress(encoded)
    digest = H(encoded)
    header = HDR.pack(MAGIC, VERSION, 0, len(compressed), len(encoded), len(physical), digest)
    footer = FTR.pack(FMAGIC, 0, 1, 0, 0, len(compressed), len(encoded), 0, digest)
    updated = header + compressed + physical + compressed + footer
    inspected, preserved, pack = physical_oracle(updated)
    assert preserved == physical and pack == original_pack
    assert inspected == changed
    # Except for exactly one target row SHA, no logical index field changes.
    restored = copy.deepcopy(inspected)
    next(row for row in restored["files"] if row[0] == member)[5] = before
    assert restored == index
    return updated, physical


class FixedPackRowDigest(unittest.TestCase):
    def test_present_row_digest_strong_verify(self):
        vectors = json.loads(GOLDEN.read_text())["vectors"]
        self.assertEqual({v["physical_codec"] for v in vectors}, {0, 1})
        for vec in vectors:
            with self.subTest(codec=vec["physical_codec"]):
                wire = base64.b64decode(vec["archive_base64"], validate=True)
                self.assertEqual(H(wire).hex(), vec["archive_sha256"])
                index, physical, pack = physical_oracle(wire)
                self.assertEqual(H(pack).hex(), vec["packed_blob_sha256"])
                target = "alpha.txt"
                actual = bytes.fromhex(vec["files"][target]["hex"])
                self.assertEqual(H(actual).hex(), vec["files"][target]["sha256"])
                self.assertEqual(len(index["files"]), 4)
                with tempfile.TemporaryDirectory(prefix="j24i31-") as td:
                    f = Path(td) / "control.cmpct"
                    f.write_bytes(wire)
                    self.assertEqual(preflight_archive(f)["files"], 4)
                    with CMPCT(f) as reader:
                        self.assertEqual(reader.verify(), 4)
                        self.assertEqual(reader.read(target), actual)
                    foreign = H(b"J24I31 contradictory-present-PACK-row-sha")
                    self.assertNotEqual(foreign, H(actual))
                    for label, row_sha in [
                        ("none", None), ("empty", b""),
                        ("matching", H(actual)), ("contradictory", foreign),
                    ]:
                        changed, kept_physical = reseal_one_present_row(wire, target, row_sha)
                        self.assertEqual(kept_physical, physical)
                        f.write_bytes(changed)
                        self.assertEqual(preflight_archive(f)["files"], 4)
                        with CMPCT(f) as reader:
                            self.assertEqual(reader.read(target), actual)
                            self.assertEqual(reader.read_range(target, 7, 17), actual[7:24])
                            # Predicted NEGATIVE: current Reader ignores a present
                            # S_PACK row digest while validating all physical bytes.
                            verdict = reader.verify()
                        self.assertEqual(verdict, 4, (vec["name"], label))
                        RESULTS.append({
                            "physical_codec": vec["physical_codec"],
                            "case": label,
                            "original_sha256": vec["archive_sha256"],
                            "mutated_sha256": H(changed).hex(),
                            "preserved_physical_sha256": H(physical).hex(),
                            "member_actual_sha256": H(actual).hex(),
                            "indexed_row_sha256": None if row_sha is None else bytes(row_sha).hex(),
                            "present_contradiction_accepted": label == "contradictory",
                            "preflight_files": 4,
                            "verify_count": verdict,
                            "classification": "negative product behavior, science-only",
                        })


if __name__ == "__main__":
    try:
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(FixedPackRowDigest)
        result = unittest.TextTestRunner(verbosity=2).run(suite)
    finally:
        out = os.environ.get("J24I31_RESULTS")
        if out:
            Path(out).write_text(json.dumps({
                "schema": "cmpct-j24i31-pack-row-digest-science-v1",
                "cases": RESULTS,
                "source": "frozen independent r24 S_PACK vectors / true installed Reader",
            }, sort_keys=True, indent=2) + "\n")
    if not result.wasSuccessful():
        raise SystemExit(1)
