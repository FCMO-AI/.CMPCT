"""J24C13: fused ABI3 exact index proof produces range hints without weakening admission.

These archives are serialized independently of Builder by the inherited O215
physical-header and signed-index oracle. Distinguish optional-native evidence
from strict Python 3.10 fallback (both must return identical logical bytes).
"""
from __future__ import annotations

import bisect
import os
import random
from pathlib import Path
import tempfile
import unittest

import cmpct._chunk_admission as admission
from cmpct.codec import K_FILE, S_CHUNKS
from cmpct.reader import CMPCT
from cmpct.validation import ValidationError, _validate_storage
from test_o215_fixed_chunk_admission import _make_archive

EXPECTED_NATIVE = os.environ.get("CMPCT_J24C13_EXPECT_NATIVE", "0") == "1"


class FusedNativeCheckpointCourt(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="cmpct-j24c13-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.prior_index = admission._scan_refs_index
        self.prior_basic = admission._scan_refs
        self.addCleanup(lambda: setattr(admission, "_scan_refs_index", self.prior_index))
        self.addCleanup(lambda: setattr(admission, "_scan_refs", self.prior_basic))

    def _path(self, label, refs, data):
        logical = b"".join(data[i] for i in refs)
        p = self.root / (label + ".cmpct")
        p.write_bytes(_make_archive(refs, logical, blobs=tuple(data)))
        return p, logical

    def _check(self, name, refs, blobs):
        p, expected = self._path(name, refs, blobs)
        rng = random.Random(2413 + len(refs))
        with CMPCT(p) as rd:
            self.assertEqual(rd.read("fixed.bin"), expected)
            self.assertEqual(rd.verify(), 1)
            marks = rd._chunk_range_marks.get("fixed.bin")
            should_index = EXPECTED_NATIVE and len(refs) >= 512
            self.assertEqual(marks is not None, should_index)
            if marks is not None:
                self.assertEqual(len(marks), (len(refs) + 255) // 256)
                cursor = 0
                for i, idx in enumerate(refs):
                    if i % 256 == 0:
                        self.assertEqual(marks[i // 256], cursor)
                    cursor += len(blobs[idx])
                self.assertEqual(cursor, len(expected))
                self.assertEqual(marks[0], 0)
                self.assertEqual(list(marks), sorted(marks))
            cases = [(0, 0), (0, min(5, len(expected))),
                     (len(expected), 0)]
            for k in range(400):
                start = rng.randrange(len(expected) + 1)
                length = rng.randrange(min(33, len(expected) - start) + 1)
                cases.append((start, length))
            # Independently reconstruct the oracle from original immutable
            # payloads rather than using CMPCT.read() as the expected result.
            for start, length in cases:
                self.assertEqual(rd.read_range("fixed.bin", start, length),
                                 expected[start:start + length], (name, start, length))
            self.assertEqual(rd._chunk_range_marks.get("fixed.bin"), marks)

    def test_signed_fixed_512_references(self):
        self._check("fixed512", [0] * 512, [b"A"])

    def test_signed_heterogeneous_with_empty_blob_and_reused_owners(self):
        refs = [(i * 13) % 4 for i in range(4096)]
        self._check("hetero4096", refs, [b"A", b"", b"BC", b"DEFG"])

    def test_dense_65536_references(self):
        refs = [(i * 31) % 2 for i in range(65536)]
        self._check("dense65536", refs, [b"X", b"YZ"])

    def test_short_native_preserves_original_scan_contract(self):
        blobs = [[0, 4, 4, 0, 0]]
        refs = [0, 0]
        touched = []
        base = self.prior_basic
        if EXPECTED_NATIVE:
            self.assertTrue(callable(base))
            def spy(*args):
                touched.append(args)
                return base(*args)
            admission._scan_refs = spy
        self.assertIs(admission.native_chunk_proof([S_CHUNKS, refs], blobs, 8),
                      EXPECTED_NATIVE)
        self.assertEqual(bool(touched), EXPECTED_NATIVE)

    def test_index_helper_rejects_adversarial_metadata_without_false_accept(self):
        blobs = [[0, 1, 1, 0, 0]]
        refsets = [
            [0] * 511 + [True], [0] * 511 + [-1],
            [0] * 511 + [8], [0] * 511 + [2 ** 100],
            [0] * 511 + [[0]], [0] * 512,
        ]
        for i, refs in enumerate(refsets):
            size = len(refs) + (1 if i == 5 else 0)
            with self.subTest(i=i):
                with self.assertRaises((ValidationError, ValueError, TypeError, OverflowError, IndexError)):
                    _validate_storage("bad", K_FILE, size,
                                      [S_CHUNKS, refs], blobs, [])
                proof = admission.native_chunk_proof([S_CHUNKS, refs], blobs, size)
                self.assertIs(proof, False)

    def test_1000_held_out_native_original_equivalence(self):
        # Independent structural comparator: the older stable-ABI full scan
        # remains the hard safety acceptance set. A new checkpoint proof must
        # never accept something the original scanner rejects, including
        # malformed refs around the 512/513 admission boundary.
        rng = random.Random(241313)
        blobs = [[0, 1, 1, 0, 0], [0, 7, 7, 0, 0], [0, 0, 0, 0, 0]]
        pool = [0, 1, 2, True, -1, 5, 2 ** 80, "0", 0.0, [0]]
        for i in range(1000):
            n = rng.choice([0, 1, 511, 512, 513, 1024, 4096])
            good = (i % 4 == 0)
            refs = ([rng.randrange(3) for _ in range(n)] if good
                    else [rng.choice(pool) for _ in range(n)])
            if good:
                declared = sum(blobs[r][1] for r in refs)
                if i % 8 == 0:
                    declared += 1
            else:
                declared = rng.choice([0, 1, 512, 4096, True, 2 ** 80])
            original = admission.native_chunk_ok([S_CHUNKS, refs], blobs, declared)
            fused = admission.native_chunk_proof([S_CHUNKS, refs], blobs, declared)
            self.assertEqual(original, bool(fused), (i, n))
            if type(fused) is tuple:
                self.assertGreaterEqual(n, 512)
                prefix = 0
                for j, ref in enumerate(refs):
                    if j % 256 == 0:
                        self.assertEqual(fused[j // 256], prefix)
                    prefix += blobs[ref][1]
                self.assertEqual(prefix, declared)

    def test_malformed_optional_checkpoint_tuple_fails_closed(self):
        p, expected = self._path("malformed-hint", [0] * 1024, [b"ABC"])
        # Native code is treated as an optimization, not the sole safety gate.
        # A malformed tuple cannot bypass the inherited native/strict validator
        # or become a range map, even when its parent full index is valid.
        malicious = (
            (), (0,), (0, -1, 700, 1000), (0, 0, True, 0),
            (0, 0, 3000, 9999999),
        )
        for hint in malicious:
            with self.subTest(hint=hint):
                admission._scan_refs_index = lambda *a, h=hint: h
                with CMPCT(p) as rd:
                    self.assertFalse(rd._chunk_range_marks)
                    self.assertEqual(rd.read_range("fixed.bin", 2231, 19),
                                     expected[2231:2250])
                    self.assertEqual(rd.verify(), 1)

    def test_simulated_native_failure_preserves_strict_fallback_and_no_index(self):
        p, data = self._path("native-fail", [0] * 1024, [b"ABC"])
        admission._scan_refs_index = lambda *args: (_ for _ in ()).throw(RuntimeError("fault"))
        admission._scan_refs = None
        with CMPCT(p) as rd:
            self.assertFalse(rd._chunk_range_marks)
            self.assertEqual(rd.read_range("fixed.bin", 19, 37), data[19:56])
            self.assertEqual(rd.verify(), 1)

    def test_absent_extension_preserves_python_310_path(self):
        if EXPECTED_NATIVE:
            self.skipTest("native installed; negative simulated in previous test")
        self.assertIsNone(self.prior_index)
        self.assertIsNone(self.prior_basic)
        p, expected = self._path("no-extension", [0] * 1024, [b"ABC"])
        with CMPCT(p) as rd:
            self.assertFalse(rd._chunk_range_marks)
            self.assertEqual(rd.read_range("fixed.bin", 99, 13), expected[99:112])


if __name__ == "__main__":
    unittest.main()
