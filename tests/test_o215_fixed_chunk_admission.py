"""O215: installed Reader must reject authenticated S_CHUNKS size contradictions at admission.

Builder-independent r24 HEAD, primary/tail authenticated indexes, footer and RAW blob
framing. The only controlled variable is S_CHUNKS metadata, not a monkeypatched Reader.
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

import msgpack

from cmpct.codec import (
    MAGIC, VERSION, FMAGIC, BMAGIC, HDR, BHDR, FTR,
    CODEC_RAW, K_FILE, S_CHUNKS, zc, sha,
)
from cmpct.reader import CMPCT
from cmpct.validation import ValidationError, preflight_archive

PATH = "fixed.bin"
MTIME_NS = 946684800000000000


def _make_archive(refs, logical: bytes, *, declared_size=None, blobs=(b"ABCD",),
                  latest_refs=None, latest_size=None):
    """Generate correct physical framing and authenticated metadata independently of Builder."""
    records = bytearray()
    rows = []
    for payload in blobs:
        offset = len(records)
        rows.append([offset, len(payload), len(payload), CODEC_RAW, 0])
        records.extend(BHDR.pack(BMAGIC, CODEC_RAW, 0, 0, len(payload), len(payload),
                                 0, binascii.crc32(payload) & 0xffffffff, sha(payload)))
        records.extend(payload)

    def encoded(current_refs, current_size):
        index = {
            "v": VERSION,
            "files": [[PATH, K_FILE, 0o644, MTIME_NS, current_size,
                       sha(logical), [S_CHUNKS, current_refs]]],
            "blobs": rows,
            "recipes": [],
            "dict_blob": None,
            "fsmeta": {},
        }
        raw = msgpack.packb(index, use_bin_type=True)
        return zc(raw, 12), raw, sha(raw)

    def footer(comp, raw, digest):
        return FTR.pack(FMAGIC, 0, 1, 0, 0, len(comp), len(raw), 0, digest)

    size = len(logical) if declared_size is None else declared_size
    compressed, raw, digest = encoded(refs, size)
    archive = (
        HDR.pack(MAGIC, VERSION, 0, len(compressed), len(raw), len(records), digest)
        + compressed + bytes(records) + compressed + footer(compressed, raw, digest)
    )
    if latest_refs is not None:
        later_comp, later_raw, later_hash = encoded(
            latest_refs, size if latest_size is None else latest_size
        )
        archive += later_comp + footer(later_comp, later_raw, later_hash)
    return archive


class FixedChunkAdmissionContract(unittest.TestCase):
    def setUp(self):
        self._temp = tempfile.TemporaryDirectory(prefix="cmpct-o215-")
        self.addCleanup(self._temp.cleanup)
        self.root = Path(self._temp.name)

    def _path(self, label, data):
        p = self.root / (label + ".cmpct")
        p.write_bytes(data)
        return p

    def _valid(self, label, refs, logical, *, blobs=(b"ABCD",),
               latest_refs=None, latest_size=None, extract=True):
        data = _make_archive(refs, logical, blobs=blobs,
                             latest_refs=latest_refs, latest_size=latest_size)
        p = self._path(label, data)
        identity = hashlib.sha256(data).hexdigest()
        self.assertEqual(preflight_archive(p, verify_blob_headers=True)["files"], 1)
        with CMPCT(p) as reader:
            self.assertEqual(reader.verify(), 1)
            self.assertEqual(reader.read(PATH), logical)
            for off in range(len(logical) + 1):
                for length in range(len(logical) - off + 1):
                    self.assertEqual(reader.read_range(PATH, off, length),
                                     logical[off:off + length], (label, off, length))
            if extract and os.name != "nt":
                out = self.root / ("out-" + label)
                reader.extractall(out, metadata=False)
                self.assertEqual((out / PATH).read_bytes(), logical)
        self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(), identity)

    def _invalid(self, label, refs, *, logical=b"ABCD", declared_size=5,
                 blobs=(b"ABCD",), latest_refs=None, latest_size=None):
        data = _make_archive(refs, logical, declared_size=declared_size,
                             blobs=blobs, latest_refs=latest_refs,
                             latest_size=latest_size)
        p = self._path(label, data)
        identity = hashlib.sha256(data).hexdigest()
        with self.assertRaises(ValidationError, msg="preflight " + label):
            preflight_archive(p, verify_blob_headers=True)
        # Must fail before mmap and before the public read_range can return a
        # short, wrong result for an in-bounds logical region.
        with self.assertRaises(ValidationError, msg="Reader admission " + label):
            CMPCT(p)
        self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(), identity)

    def test_single_chunk_valid_all_ranges_and_extraction(self):
        self._valid("one", [0], b"ABCD")

    def test_multiple_and_reused_physical_blobs(self):
        self._valid("distinct", [0, 1], b"ABCDEFGH",
                    blobs=(b"ABCD", b"EFGH"))
        self._valid("repeated", [0, 0], b"ABCDABCD")

    def test_empty_chunk_list_for_zero_length_file(self):
        self._valid("empty", [], b"", blobs=(), extract=False)

    def test_immutable_mixed_codec_fixed_chunk_conformance(self):
        root = Path(os.environ.get("GITHUB_WORKSPACE", Path(__file__).resolve().parents[1]))
        fixture = root / "tests/conformance/v24-chunk-maps.json"
        self.assertTrue(fixture.is_file())
        obj = json.loads(fixture.read_text(encoding="utf-8"))
        vec = next(v for v in obj["vectors"] if v["storage_kind"] == S_CHUNKS)
        wire = base64.b64decode(vec["archive_base64"], validate=True)
        self.assertEqual(hashlib.sha256(wire).hexdigest(), vec["archive_sha256"])
        p = self._path("frozen", wire)
        self.assertEqual(preflight_archive(p, verify_blob_headers=True)["files"], 1)
        with CMPCT(p) as reader:
            self.assertEqual(reader.verify(), 1)
            logical = reader.read(vec["name"])
            self.assertEqual(hashlib.sha256(logical).hexdigest(), vec["logical_sha256"])
            self.assertEqual(len(logical), vec["logical_size"])
            for off in range(len(logical) + 1):
                for length in (0, min(3, len(logical) - off)):
                    self.assertEqual(reader.read_range(vec["name"], off, length),
                                     logical[off:off + length])
        self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(), vec["archive_sha256"])

    def test_overdeclared_size_cannot_yield_short_in_bounds_range(self):
        # Parent read_range(4,1) returns b'' on a member declaring five bytes.
        # Parent read()/verify() do reject via total-length check; no claim of
        # post-verification corruption is made.
        self._invalid("overdeclared", [0], declared_size=5)

    def test_underdeclared_size_rejected_before_exposing_tree(self):
        self._invalid("underdeclared", [0], declared_size=3)

    def test_repeated_reference_size_underdeclared(self):
        self._invalid("duplicate-ref", [0, 0], logical=b"ABCDABCD", declared_size=4)

    def test_missing_reference_is_refused(self):
        self._invalid("missing-ref", [7], declared_size=4)

    def test_nonstrict_bool_reference_is_refused(self):
        self._invalid("bool-ref", [True], declared_size=4)

    def test_later_good_checkpoint_controls_effective_index(self):
        # Earlier contradictory index is superseded by a correctly committed one.
        wire = _make_archive([0], b"ABCD", declared_size=5,
                             latest_refs=[0], latest_size=4)
        p = self._path("later-good", wire)
        self.assertEqual(preflight_archive(p, verify_blob_headers=True)["files"], 1)
        with CMPCT(p) as reader:
            self.assertEqual(reader.read_range(PATH, 2, 2), b"CD")
            self.assertEqual(reader.verify(), 1)

    def test_later_bad_checkpoint_rejected(self):
        self._invalid("later-bad", [0], declared_size=4,
                      latest_refs=[0], latest_size=5)


if __name__ == "__main__":
    unittest.main()
