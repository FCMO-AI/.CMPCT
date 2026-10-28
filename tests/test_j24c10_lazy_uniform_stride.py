"""J24C10: bounded optional uniform S_CHUNKS geometry, strictly after admission.

Genuine first-party signed r24 fixture for Reader behavior; independent deterministic
predicate/fallback and hostile checks. Tests do not weaken inherited validators.
"""
from __future__ import annotations

import os
import random
import tempfile
import unittest
from pathlib import Path

import cmpct._chunk_admission as admission
from cmpct.reader import CMPCT
from test_o215_fixed_chunk_admission import _make_archive

REQUIRED = os.environ.get("CMPCT_J24C10_EXPECT_NATIVE", "0") == "1"


def _blob_row(length):
    return [0, length, length, 0, 0]


def _strict_uniform(refs, blobs, size):
    if (type(refs) is not list or type(blobs) is not list or
            type(size) is not int or size <= 0 or not refs):
        return 0
    stride = 0
    total = 0
    for j, idx in enumerate(refs):
        if type(idx) is not int or not 0 <= idx < len(blobs):
            return 0
        row = blobs[idx]
        if type(row) is not list or len(row) != 5 or type(row[1]) is not int:
            return 0
        ln = row[1]
        if ln <= 0:
            return 0
        total += ln
        if j == 0:
            stride = ln
        elif j != len(refs)-1 and ln != stride:
            return 0
        elif j == len(refs)-1 and ln > stride:
            return 0
    return stride if total == size else 0


class LazyStrideProof(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="j24c10-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        original = admission._uniform_stride
        self.addCleanup(lambda: setattr(admission, "_uniform_stride", original))

    def _signed(self, refs, logical):
        path = self.root / "signed.cmpct"
        path.write_bytes(_make_archive(refs, logical))
        return path

    def test_optional_binary_is_real_or_absent(self):
        self.assertEqual(callable(admission._uniform_stride), REQUIRED)
        blobs = [_blob_row(4), _blob_row(2)]
        if REQUIRED:
            self.assertEqual(admission._uniform_stride([0, 0, 1], blobs, 10), 4)
            self.assertEqual(admission._uniform_stride([0, 1, 0], blobs, 10), 0)
            self.assertEqual(admission._uniform_stride([0, True], blobs, 8), 0)
            self.assertEqual(admission._uniform_stride([0, 2**100], blobs, 8), 0)
            self.assertEqual(admission._uniform_stride([0, 0], blobs, 7), 0)
        else:
            self.assertIsNone(admission._uniform_stride)

    def test_genuine_signed_reader_late_ranges_and_zero_boundary(self):
        count = 256
        logical = b"ABCD" * count
        path = self._signed([0] * count, logical)
        with CMPCT(path) as rd:
            self.assertEqual(rd.read_range("fixed.bin", 0, 9), logical[:9])
            self.assertNotIn("fixed.bin", rd._chunk_stride_cache)
            for at, length in [(len(logical)//2, 13), (len(logical)-17, 17),
                               (len(logical)-1, 1), (len(logical), 0),
                               (0, 12), (37, 55)]:
                self.assertEqual(rd.read_range("fixed.bin", at, length),
                                 logical[at:at+length])
            self.assertEqual(rd._chunk_stride_cache["fixed.bin"], 4 if REQUIRED else 0)
            self.assertEqual(rd.read("fixed.bin"), logical)
            self.assertEqual(rd.verify(), 1)

    def test_invalid_ranges_keep_original_contract(self):
        path = self._signed([0]*64, b"ABCD"*64)
        with CMPCT(path) as rd:
            for offset, ln in [(-1, 2), (255, 2), (4, -1), (257, 0)]:
                with self.assertRaises(ValueError):
                    rd.read_range("fixed.bin", offset, ln)
            self.assertEqual(rd.read_range("fixed.bin", 256, 0), b"")

    def test_disabled_failed_and_false_witness_are_identical(self):
        path = self._signed([0]*256, b"ABCD"*256)
        outcomes = []
        native = admission._uniform_stride
        for scanner in (None, lambda *_: 0,
                        lambda *_: (_ for _ in ()).throw(RuntimeError("native failure")),
                        native):
            admission._uniform_stride = scanner
            with CMPCT(path) as rd:
                outcomes.append(tuple(rd.read_range("fixed.bin", p, n)
                                      for p, n in ((512, 13), (1002, 22), (0, 12))))
                self.assertEqual(rd._chunk_stride_cache.get("fixed.bin"), 4 if scanner is native and REQUIRED else 0)
        self.assertTrue(all(o == outcomes[0] for o in outcomes))

    def test_bogus_positive_witness_arithmetic_is_rejected(self):
        blobs = [_blob_row(4), _blob_row(7)]
        admission._uniform_stride = lambda *args: 4
        self.assertEqual(admission.native_uniform_stride([1, [0, 1]], blobs, 11), 0)
        self.assertEqual(admission.native_uniform_stride([1, [0, True]], blobs, 8), 0)
        self.assertEqual(admission.native_uniform_stride([1, [0, 0]], blobs, 8), 4)
        self.assertEqual(admission.native_uniform_stride([1, [0, 0]], blobs, 9), 0)

    def test_multiowner_equal_lengths_and_short_tail(self):
        blobs = [_blob_row(4) for _ in range(256)] + [_blob_row(2)]
        refs = list(range(256))*2 + [256]
        size = 512*4+2
        if REQUIRED:
            self.assertEqual(admission.native_uniform_stride([1, refs], blobs, size), 4)
            self.assertEqual(admission.native_uniform_stride([1, refs[:-1]+[0]], blobs, size), 0)

    def test_signed_256_distinct_physical_owners_equal_stride(self):
        blobs = tuple(bytes([i]) * 4 for i in range(256))
        refs = list(range(256)) * 4
        logical = b"".join(blobs[i] for i in refs)
        path = self.root / "multiowner.cmpct"
        path.write_bytes(_make_archive(refs, logical, blobs=blobs))
        with CMPCT(path) as rd:
            for at, length in ((0, 8), (len(logical)//2+3, 25),
                               (len(logical)-23, 23), (len(logical), 0)):
                self.assertEqual(rd.read_range("fixed.bin", at, length),
                                 logical[at:at+length])
            self.assertEqual(rd._chunk_stride_cache.get("fixed.bin"),
                             4 if REQUIRED else 0)
            self.assertEqual(rd.verify(), 1)

    def test_signed_smaller_final_chunk_and_ragged_fallback(self):
        for name, refs, blobs in (
            ("short-tail", [0]*63+[1], (b"ABCD", b"XY")),
            ("ragged", [0,1,2]*64, (b"ABCD", b"F", b"XYZ"))):
            logical=b"".join(blobs[i] for i in refs)
            path=self.root / (name+".cmpct")
            path.write_bytes(_make_archive(refs, logical, blobs=blobs))
            with CMPCT(path) as rd:
                for at, length in ((12, 8), (len(logical)//2, 11),
                                   (len(logical)-17, 17), (len(logical), 0)):
                    self.assertEqual(rd.read_range("fixed.bin", at, length),
                                     logical[at:at+length], name)
                expected=4 if name=="short-tail" and REQUIRED else 0
                self.assertEqual(rd._chunk_stride_cache.get("fixed.bin"), expected)
                self.assertEqual(rd.verify(), 1)

    def test_late_witness_does_not_bypass_corrupt_physical_blob_header(self):
        # Signing the index does not authenticate hostile physical BHDR control
        # flags. A shortcut in range location must never become a codec bypass.
        from cmpct.codec import BHDR, HDR
        path = self._signed([0]*256, b"ABCD"*256)
        wire = bytearray(path.read_bytes())
        record_start = HDR.size + HDR.unpack_from(wire, 0)[3]
        head = list(BHDR.unpack_from(wire, record_start))
        self.assertEqual(head[2], 0)
        head[2] = 1
        wire[record_start:record_start + BHDR.size] = BHDR.pack(*head)
        path.write_bytes(wire)

        current = admission._uniform_stride
        outcomes = []
        for witness in (None, current):
            admission._uniform_stride = witness
            with CMPCT(path) as rd:
                with self.assertRaises(IOError) as error:
                    rd.read_range("fixed.bin", 1020, 4)
                outcomes.append((type(error.exception).__name__, str(error.exception)))
        self.assertEqual(outcomes[0], outcomes[1])

    def test_structured_positive_and_single_interior_mutation_differential(self):
        if not REQUIRED:
            self.skipTest("native witness absent on Python 3.10")
        rng = random.Random(241001)
        for case in range(1200):
            stride = rng.randrange(2, 65)
            tail = rng.randrange(1, stride + 1)
            n = rng.randrange(3, 130)
            blobs = [_blob_row(stride) for _ in range(6)]
            blobs.append(_blob_row(tail))
            blobs.append(_blob_row(stride - 1))
            refs = [rng.randrange(6) for _ in range(n - 1)] + [6]
            size = stride * (n - 1) + tail
            self.assertEqual(_strict_uniform(refs, blobs, size), stride)
            self.assertEqual(admission.native_uniform_stride([1, refs], blobs, size),
                             stride, ("positive", case))
            # A single different interior physical length can leave the
            # signed total valid when its declared size is updated. It must
            # NOT acquire the original stride or be mislocated arithmetically.
            wrong = list(refs)
            wrong[rng.randrange(1, n - 1)] = 7
            altered_size = size - 1
            self.assertEqual(_strict_uniform(wrong, blobs, altered_size), 0)
            self.assertEqual(admission.native_uniform_stride([1, wrong], blobs, altered_size),
                             0, ("mutant", case))

    def test_new_reader_never_inherits_witness_across_path_replacement(self):
        path=self.root / "replaced.cmpct"
        original=b"ABCD"*64
        path.write_bytes(_make_archive([0]*64, original))
        with CMPCT(path) as rd:
            self.assertEqual(rd.read_range("fixed.bin", len(original)-16, 16),
                             original[-16:])
            self.assertEqual(rd._chunk_stride_cache.get("fixed.bin"), 4 if REQUIRED else 0)
        blobs=(b"ABCD", b"F", b"XY")
        refs=[0,1,2]*64
        changed=b"".join(blobs[i] for i in refs)
        # Replace archive pathname only after the previous Reader closes.
        # A global/pathname cache would incorrectly carry a uniform proof.
        path.write_bytes(_make_archive(refs, changed, blobs=blobs))
        with CMPCT(path) as rd:
            self.assertEqual(rd.read_range("fixed.bin", len(changed)-13, 13),
                             changed[-13:])
            self.assertEqual(rd._chunk_stride_cache.get("fixed.bin"), 0)

    def test_deterministic_hostile_differential_no_false_positives(self):
        if not REQUIRED:
            self.skipTest("no native extension; strict Python is the only route")
        rng = random.Random(2410)
        blobs = [_blob_row(4), _blob_row(4), _blob_row(2), _blob_row(7)]
        pool = [0, 1, 2, 3, 4, -1, True, 2**80, 0.0, None, [0]]
        for i in range(1200):
            refs = [rng.choice(pool) for _ in range(rng.randrange(1, 15))]
            size = rng.choice([0, 2, 4, 7, 8, 14, 24, 60, 2**90, True])
            expected = _strict_uniform(refs, blobs, size)
            actual = admission.native_uniform_stride([1, refs], blobs, size)
            self.assertEqual(actual, expected, (i, refs, size))


if __name__ == "__main__":
    unittest.main()
