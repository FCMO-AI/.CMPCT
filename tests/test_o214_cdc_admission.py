"""O214: independent root-v24 CDC same-effective-index admission court.

Product regression, not a benchmark/release certificate. Physical RAW blob records,
CRC, whole logical SHA, index digest, head and tail are built without Builder.
The CDC descriptor length is the controlled variable; no Reader monkeypatching.
"""
from __future__ import annotations

import base64
import binascii
import json
import hashlib
import os
from pathlib import Path
import tempfile
import unittest

import msgpack

from cmpct.codec import (
    MAGIC, VERSION, FMAGIC, BMAGIC, HDR, BHDR, FTR,
    CODEC_RAW, K_FILE, S_CDC, zc, sha,
)
from cmpct.reader import CMPCT
from cmpct.validation import ValidationError, preflight_archive

PATH = "cdc.bin"
MTIME_NS = 946684800000000000


def _index(entries, logical: bytes, blob_rows):
    return {
        "v": VERSION,
        "files": [[PATH, K_FILE, 0o644, MTIME_NS, len(logical),
                   sha(logical), [S_CDC, entries]]],
        "blobs": blob_rows,
        "recipes": [],
        "dict_blob": None,
        "fsmeta": {},
    }


def _encoded_index(index):
    raw = msgpack.packb(index, use_bin_type=True)
    compressed = zc(raw, 12)
    return compressed, raw, sha(raw)


def _r24(entries, logical: bytes, *, blobs=(b"ABCD",), latest_entries=None):
    """Build a real two-index+footer revision-24 archive.

    The archive-level digest authenticates each supplied index, including any
    intentionally contradictory descriptor. This is not a trusted signature.
    """
    records = bytearray()
    blob_rows = []
    for payload in blobs:
        off = len(records)
        blob_rows.append([off, len(payload), len(payload), CODEC_RAW, 0])
        records.extend(
            BHDR.pack(BMAGIC, CODEC_RAW, 0, 0,
                      len(payload), len(payload), 0,
                      binascii.crc32(payload) & 0xffffffff, sha(payload))
        )
        records.extend(payload)

    def footer(compressed, raw, digest):
        return FTR.pack(FMAGIC, 0, 1, 0, 0,
                        len(compressed), len(raw), 0, digest)

    initial_index = _index(entries, logical, blob_rows)
    compressed, raw, digest = _encoded_index(initial_index)
    archive = (
        HDR.pack(MAGIC, VERSION, 0, len(compressed),
                 len(raw), len(records), digest)
        + compressed + bytes(records) + compressed
        + footer(compressed, raw, digest)
    )
    if latest_entries is not None:
        latest_index = _index(latest_entries, logical, blob_rows)
        comp2, raw2, digest2 = _encoded_index(latest_index)
        archive += comp2 + footer(comp2, raw2, digest2)
    return archive


class CDCAdmissionContract(unittest.TestCase):
    def setUp(self):
        self._temporary = tempfile.TemporaryDirectory(prefix="cmpct-o214-")
        self.addCleanup(self._temporary.cleanup)
        self.root = Path(self._temporary.name)

    def _write(self, filename, wire):
        path = self.root / filename
        path.write_bytes(wire)
        return path

    def _valid(self, label, entries, logical, blobs=(b"ABCD",),
               latest_entries=None, extract=True):
        data = _r24(entries, logical, blobs=blobs, latest_entries=latest_entries)
        path = self._write(label + ".cmpct", data)
        original_sha = hashlib.sha256(data).digest()
        self.assertEqual(preflight_archive(path, verify_blob_headers=True)["files"], 1)
        with CMPCT(path) as reader:
            self.assertEqual(reader.verify(), 1)
            self.assertEqual(reader.read(PATH), logical)
            self.assertEqual(reader.file_sha256(PATH), sha(logical))
            for start in range(len(logical) + 1):
                for length in range(len(logical) - start + 1):
                    self.assertEqual(reader.read_range(PATH, start, length),
                                     logical[start:start + length],
                                     msg=(label, start, length))
            # Windows extraction is independently red on the inherited
            # unguarded os.fchmod primitive (J24W02/#536); admission and
            # read semantics remain compulsory on Windows.
            if extract and os.name != "nt":
                out = self.root / ("extracted-" + label)
                reader.extractall(out, metadata=False)
                self.assertEqual((out / PATH).read_bytes(), logical)
        self.assertEqual(hashlib.sha256(path.read_bytes()).digest(), original_sha)

    def _invalid(self, label, entries, logical=b"ABCD", *,
                 blobs=(b"ABCD",), latest_entries=None):
        wire = _r24(entries, logical, blobs=blobs, latest_entries=latest_entries)
        path = self._write(label + ".cmpct", wire)
        original_digest = hashlib.sha256(wire).digest()
        with self.assertRaises(ValidationError, msg="strict preflight " + label):
            preflight_archive(path, verify_blob_headers=True)
        with self.assertRaises(ValidationError, msg="Reader admission " + label):
            CMPCT(path)
        self.assertEqual(hashlib.sha256(path.read_bytes()).digest(),
                         original_digest, "Reader modified source " + label)

    def test_single_blob_all_ranges_and_posix_extraction(self):
        self._valid("single", [[4, 0]], b"ABCD")

    def test_distinct_blob_boundary_and_repeated_physical_ownership(self):
        self._valid("two-distinct", [[4, 0], [4, 1]],
                    b"ABCDEFGH", blobs=(b"ABCD", b"EFGH"))
        self._valid("two-references", [[4, 0], [4, 0]], b"ABCDABCD")

    def test_immutable_mixed_codec_cdc_conformance_vector(self):
        """Independent archived r24 CDC wire bytes: raw Deflate, Zstd and RAW.

        This file predates O214; do NOT rebuild its bytes from today's Builder.
        It is a stronger control against overly strict candidate admission.
        """
        root = Path(os.environ.get("GITHUB_WORKSPACE", Path(__file__).resolve().parents[1]))
        fixture = root / "tests" / "conformance" / "v24-chunk-maps.json"
        self.assertTrue(fixture.is_file(), "missing frozen conformance vector")
        suite = json.loads(fixture.read_text(encoding="utf-8"))
        vec = next(v for v in suite["vectors"] if v["storage_kind"] == S_CDC)
        wire = base64.b64decode(vec["archive_base64"], validate=True)
        self.assertEqual(hashlib.sha256(wire).hexdigest(), vec["archive_sha256"])
        self.assertEqual(len(wire), vec["archive_bytes"])
        path = self._write("frozen-mixed-codec.cmpct", wire)
        self.assertEqual(preflight_archive(path, verify_blob_headers=True)["files"], 1)
        with CMPCT(path) as reader:
            self.assertEqual(reader.verify(), 1)
            logical = reader.read(vec["name"])
            self.assertEqual(len(logical), vec["logical_size"])
            self.assertEqual(hashlib.sha256(logical).hexdigest(), vec["logical_sha256"])
            rng = vec["range"]
            self.assertEqual(reader.read_range(vec["name"], rng["offset"], rng["length"]).hex(),
                             rng["hex"])
            for start, length in ((0, 1), (1, 3),
                                  (vec["logical_size"] - 17, 17)):
                self.assertEqual(reader.read_range(vec["name"], start, length),
                                 logical[start:start + length])
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), vec["archive_sha256"])

    def test_later_authenticated_valid_generation_is_effective(self):
        # An earlier malformed checkpoint must not contaminate a later
        # correctly committed index if the Reader resolves the latter.
        self._valid("latest-valid", [[1, 0]], b"ABCD",
                    latest_entries=[[4, 0]])

    def test_latest_authenticated_bad_generation_rejected(self):
        # Conversely, a valid initial checkpoint does not grant validity
        # to a newer authenticated, structurally inconsistent CDC descriptor.
        self._invalid("latest-invalid", [[4, 0]],
                      latest_entries=[[2, 0]])

    def test_underdeclared_and_overdeclared_lengths(self):
        for length in (1, 2, 5):
            with self.subTest(length=length):
                self._invalid("length-" + str(length), [[length, 0]])

    def test_zero_negative_bool_string_and_reference_types(self):
        for label, length in (
            ("zero", 0), ("negative", -1), ("bool", True), ("text", "4")
        ):
            with self.subTest(label=label):
                self._invalid(label, [[length, 0]])

    def test_bad_reference_missing_or_negative(self):
        for label, idx in (("unmapped", 1000), ("negative-id", -1)):
            with self.subTest(label=label):
                self._invalid(label, [[4, idx]])

    def test_bad_multi_chunk_sum_and_repeated_refs(self):
        self._invalid("short-second", [[4, 0], [2, 1]], b"ABCDEFGH",
                      blobs=(b"ABCD", b"EFGH"))
        self._invalid("short-repeat", [[4, 0], [2, 0]], b"ABCDABCD")
        self._invalid("size-mismatch", [[4, 0]], b"ABCDEFGH",
                      blobs=(b"ABCD", b"EFGH"))

    def test_bad_empty_descriptor_or_entry(self):
        self._invalid("empty-cdc-list", [], b"ABCD")
        self._invalid("bad-cdc-entry", [[4]], b"ABCD")


if __name__ == "__main__":
    unittest.main(verbosity=2)
