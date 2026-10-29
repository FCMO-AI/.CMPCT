#!/usr/bin/env python3
"""J24I27: fixed, Builder-independent r24 direct-member optional SHA court.

The *original* golden archive bytes under tests/conformance are never changed.
Derived signed-index variants only probe the strong verification contract.
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
    BHDR, BMAGIC, CODEC_RAW, CODEC_ZSTD, CODEC_DEFLATE,
    FMAGIC, FTR, HDR, MAGIC, S_BLOB, VERSION, sha, zc, zd,
)
from cmpct.builder import Builder
from cmpct.codec import K_SYMLINK
from cmpct.reader import CMPCT
from cmpct.validation import preflight_archive

ROOT = Path(__file__).resolve().parents[2]
GOLDEN = ROOT / "tests" / "conformance" / "v24-direct-codecs.json"


def source_parts(archive: bytes):
    """Independently account for head index, original physical span, and tail."""
    magic, ver, flags, cs, us, span, index_sha = HDR.unpack_from(archive)
    assert (magic, ver, flags) == (MAGIC, VERSION, 0)
    original_index_compressed = archive[HDR.size:HDR.size + cs]
    index_wire = zd(original_index_compressed, us)
    assert hashlib.sha256(index_wire).digest() == index_sha
    idx = msgpack.unpackb(index_wire, raw=False)
    assert len(idx["files"]) == 1 and len(idx["blobs"]) == 1
    assert idx["files"][0][6][0] == S_BLOB
    physical = archive[HDR.size + cs:HDR.size + cs + span]
    assert len(physical) == span
    tail_offset = HDR.size + cs + span
    tail_comp = archive[tail_offset:len(archive) - FTR.size]
    fmagic, kind, fcodec, fflags, fres, tail_cs, tail_us, parent, digest = FTR.unpack_from(
        archive, len(archive) - FTR.size
    )
    assert (fmagic, kind, fcodec, fflags, fres, parent) == (FMAGIC, 0, 1, 0, 0, 0)
    assert tail_cs == len(tail_comp) and tail_us == len(index_wire)
    assert zd(tail_comp, tail_us) == index_wire and digest == index_sha

    off, us_b, cs_b, codec_b, meta_b = idx["blobs"][0]
    m, c, flags, reserved, logical_len, physical_len, metalen, crc, digest = BHDR.unpack_from(
        physical, off
    )
    assert (m, c, flags, reserved) == (BMAGIC, codec_b, 0, 0)
    assert (logical_len, physical_len, metalen) == (us_b, cs_b, meta_b)
    payload_at = off + BHDR.size + metalen
    encoded = physical[payload_at:payload_at + cs_b]
    assert len(encoded) == cs_b
    if codec_b == CODEC_RAW:
        raw = encoded
    elif codec_b == CODEC_ZSTD:
        raw = zd(encoded, us_b)
    elif codec_b == CODEC_DEFLATE:
        raw = zlib.decompress(encoded, -15)
    else:
        raise AssertionError("unexpected frozen direct codec")
    assert len(raw) == us_b
    assert binascii.crc32(raw) & 0xffffffff == crc
    assert hashlib.sha256(raw).digest() == digest
    return idx, physical, raw


def with_row_hash(archive: bytes, present_hash):
    """Re-sign *both* indexes without altering one physical-record byte."""
    idx, physical, raw = source_parts(archive)
    idx["files"][0][5] = present_hash
    index_wire = msgpack.packb(idx, use_bin_type=True)
    encoded = zc(index_wire, 3)
    header = HDR.pack(MAGIC, VERSION, 0, len(encoded), len(index_wire),
                      len(physical), sha(index_wire))
    footer = FTR.pack(FMAGIC, 0, 1, 0, 0, len(encoded), len(index_wire),
                      0, sha(index_wire))
    rebuilt = header + encoded + physical + encoded + footer
    rebuilt_idx, rebuilt_physical, rebuilt_raw = source_parts(rebuilt)
    assert rebuilt_idx["files"][0][5] == present_hash
    assert rebuilt_physical == physical and rebuilt_raw == raw
    return rebuilt


class PresentRowDirectSHA(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture = json.loads(GOLDEN.read_text())
        assert fixture["format_revision"] == 24
        cls.vectors = fixture["vectors"]
        assert {v["codec"] for v in cls.vectors} == {CODEC_RAW, CODEC_ZSTD, CODEC_DEFLATE}

    def _run_archive(self, archive, vec, expected_failure=False):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "probe.cmpct"
            path.write_bytes(archive)
            meta = preflight_archive(path)
            self.assertEqual(meta["files"], 1)
            self.assertEqual(meta["blobs"], 1)
            with CMPCT(path) as reader:
                raw = reader.read(vec["name"])
                self.assertEqual(hashlib.sha256(raw).hexdigest(), vec["logical_sha256"])
                self.assertEqual(
                    reader.read_range(vec["name"], vec["range"]["offset"], vec["range"]["length"]),
                    bytes.fromhex(vec["range"]["hex"]),
                )
                if expected_failure:
                    with self.assertRaisesRegex(IOError, "SHA-256.*verification failure"):
                        reader.verify()
                else:
                    self.assertEqual(reader.verify(), 1)

    def test_frozen_builder_independent_originals_and_absent_digests(self):
        for vec in self.vectors:
            with self.subTest(codec=vec["codec"]):
                original = base64.b64decode(vec["archive_base64"])
                self.assertEqual(len(original), vec["archive_bytes"])
                self.assertEqual(hashlib.sha256(original).hexdigest(), vec["archive_sha256"])
                original_index, _, raw = source_parts(original)
                self.assertIsNone(original_index["files"][0][5])
                self.assertEqual(hashlib.sha256(raw).hexdigest(), vec["logical_sha256"])
                self._run_archive(original, vec)

    def test_optional_none_empty_and_correct_present_sha(self):
        for vec in self.vectors:
            original = base64.b64decode(vec["archive_base64"])
            correct = bytes.fromhex(vec["logical_sha256"])
            for label, digest in [("none", None), ("empty", b""), ("correct", correct)]:
                with self.subTest(codec=vec["codec"], case=label):
                    self._run_archive(with_row_hash(original, digest), vec)

    def test_conflicting_present_sha_rejected_without_rewriting_physical_record(self):
        for vec in self.vectors:
            with self.subTest(codec=vec["codec"]):
                original = base64.b64decode(vec["archive_base64"])
                wrong = hashlib.sha256(b"J24I27 deliberate foreign logical digest").digest()
                self.assertNotEqual(wrong.hex(), vec["logical_sha256"])
                changed = with_row_hash(original, wrong)
                _, original_physical, _ = source_parts(original)
                _, changed_physical, _ = source_parts(changed)
                self.assertEqual(original_physical, changed_physical)
                self._run_archive(changed, vec, expected_failure=True)

    def test_genuine_symlink_preserves_present_sha_on_strong_verify(self):
        """Secondary *Builder-produced* topology regression, never a golden oracle."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "tree"
            root.mkdir()
            target = "relative-target.txt"
            try:
                os.symlink(target, root / "link")
            except (OSError, NotImplementedError):
                self.skipTest("host cannot construct a genuine symlink")
            archive = Path(td) / "symlink.cmpct"
            Builder(root, workers=1, reproducible=True).build(archive)
            original = archive.read_bytes()
            idx, physical, raw = source_parts(original)
            self.assertEqual(idx["files"][0][1], K_SYMLINK)
            self.assertEqual(raw, target.encode())
            vec = {
                "name": "link",
                "logical_sha256": hashlib.sha256(raw).hexdigest(),
                "range": {"offset": 1, "length": 5, "hex": raw[1:6].hex()},
            }
            self._run_archive(original, vec)
            correct = hashlib.sha256(raw).digest()
            self._run_archive(with_row_hash(original, correct), vec)
            self._run_archive(with_row_hash(original, b""), vec)
            wrong = hashlib.sha256(b"wrong-symlink-literal").digest()
            self.assertNotEqual(correct, wrong)
            mutated = with_row_hash(original, wrong)
            self.assertEqual(source_parts(mutated)[1], physical)
            self._run_archive(mutated, vec, expected_failure=True)

    def test_physical_header_sha_remains_an_independent_required_check(self):
        for vec in self.vectors:
            with self.subTest(codec=vec["codec"]):
                original = base64.b64decode(vec["archive_base64"])
                changed = bytearray(with_row_hash(original, bytes.fromhex(vec["logical_sha256"])))
                _, _, original_raw = source_parts(bytes(changed))
                _, _, _, compressed_index, _, _, _ = HDR.unpack_from(changed)
                # BHDR's trailing 32-byte digest names its physical owner's exact bytes.
                digest_offset = HDR.size + compressed_index + BHDR.size - 32
                altered = hashlib.sha256(b"J24I27 wrong physical SHA").digest()
                self.assertNotEqual(altered, hashlib.sha256(original_raw).digest())
                changed[digest_offset:digest_offset + 32] = altered
                self._run_archive(bytes(changed), vec, expected_failure=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
