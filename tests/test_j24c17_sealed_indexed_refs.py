"""J24C17 — exercise sealed reference custody against the signed J24C16 defect.

Product-Reader test, not a proof against arbitrary hostile Python code. An
installed native wheel must execute the proof path; source-only fallback uses
the inherited strict validator with unchanged mutable source structures.
"""
from __future__ import annotations

import os
from pathlib import Path
import random
import tempfile
import unittest

import cmpct.reader as reader_module
from cmpct.codec import S_CHUNKS
from cmpct.reader import CMPCT
from test_o215_fixed_chunk_admission import _make_archive


REQUIRE_NATIVE = os.environ.get("CMPCT_J24C17_EXPECT_NATIVE", "0") == "1"


class SealedIndexedRefsCourt(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="cmpct-j24c17-")
        self.addCleanup(self.tmp.cleanup)

    def _path(self, label, refs, owners):
        expected = b"".join(owners[i] for i in refs)
        path = Path(self.tmp.name) / (label + ".cmpct")
        path.write_bytes(_make_archive(refs, expected, blobs=tuple(owners)))
        return path, expected

    def _require_native_if_declared(self, rd):
        indexed = "fixed.bin" in rd._chunk_range_sealed
        if REQUIRE_NATIVE:
            self.assertTrue(indexed, "installed ABI3 proof was not exercised")
        return indexed

    def test_j24c16_authenticated_swap_cannot_return_silent_wrong_byte(self):
        # The exact hostile reference geometry from installed J24C16 #672.
        original = [1] + [0] * 255 + [2] + [0] * 255
        owners = [b"A", b"BB", b""]
        path, expected = self._path("j24c16", original, owners)
        self.assertEqual(len(original), 512)
        self.assertEqual(len(expected), 512)
        self.assertEqual(expected[257:258], b"A")
        with CMPCT(path) as rd:
            self.assertEqual(rd.read("fixed.bin"), expected)
            self.assertEqual(rd.verify(), 1)
            if not self._require_native_if_declared(rd):
                return
            self.assertEqual(rd._chunk_range_marks["fixed.bin"], (0, 257))
            self.assertEqual(rd.read_range("fixed.bin", 257, 1), b"A")
            row = rd.by["fixed.bin"]
            storage = row[6]
            refs = storage[1]
            self.assertIs(type(refs), tuple)
            with self.assertRaises(TypeError):
                refs[0] = 2
            # The public storage outer list remains assignable for compatibility,
            # but rebinding it must not reuse the authenticated cached proof.
            swapped = list(refs)
            swapped[0], swapped[256] = swapped[256], swapped[0]
            self.assertEqual(sum(len(owners[i]) for i in swapped), len(expected))
            storage[1] = swapped
            with self.assertRaisesRegex(IOError, "descriptor changed"):
                rd.read_range("fixed.bin", 257, 1)
            storage[1] = refs
            self.assertEqual(rd.read_range("fixed.bin", 257, 1), b"A")
            row[6] = [S_CHUNKS, swapped]
            with self.assertRaisesRegex(IOError, "descriptor changed"):
                rd.read_range("fixed.bin", 257, 1)
            row[6] = storage
            row[4] += 1
            with self.assertRaisesRegex(IOError, "descriptor changed"):
                rd.read_range("fixed.bin", 257, 1)
            row[4] -= 1
            row[0] = "changed.bin"
            with self.assertRaisesRegex(IOError, "descriptor changed"):
                rd.read_range("fixed.bin", 257, 1)
            row[0] = "fixed.bin"
            # Public diagnostic hint mutations cannot affect indexed reads.
            rd._chunk_range_marks["fixed.bin"] = (0, 0)
            self.assertEqual(rd.read_range("fixed.bin", 257, 1), b"A")
            self.assertEqual(rd.verify(), 1)

    def test_heterogeneous_empty_and_nonempty_owner_ranges(self):
        owners = [b"A", b"", b"BC", b"DEF"]
        refs = [(i * 37 + 11) % 4 for i in range(4096)]
        path, expected = self._path("heterogeneous", refs, owners)
        rng = random.Random(2417)
        with CMPCT(path) as rd:
            if not self._require_native_if_declared(rd):
                self.assertEqual(rd.read("fixed.bin"), expected)
                return
            self.assertIs(type(rd.by["fixed.bin"][6][1]), tuple)
            self.assertEqual(rd.read("fixed.bin"), expected)
            self.assertEqual(rd.verify(), 1)
            for _ in range(500):
                start = rng.randrange(len(expected) + 1)
                length = rng.randrange(min(59, len(expected) - start) + 1)
                self.assertEqual(
                    rd.read_range("fixed.bin", start, length),
                    expected[start:start + length],
                    (start, length),
                )

    def test_budget_denial_retains_the_original_linear_fallback(self):
        path, expected = self._path("budget", [0] * 1024, [b"ABC"])
        old = reader_module._MAX_CHUNK_RANGE_HINTS
        reader_module._MAX_CHUNK_RANGE_HINTS = 1
        self.addCleanup(
            lambda: setattr(reader_module, "_MAX_CHUNK_RANGE_HINTS", old)
        )
        with CMPCT(path) as rd:
            self.assertEqual(rd._chunk_range_sealed, {})
            self.assertEqual(rd._chunk_range_hint_count, 0)
            self.assertIs(type(rd.by["fixed.bin"][6][1]), list)
            self.assertEqual(rd.read_range("fixed.bin", 2033, 19), expected[2033:2052])
            self.assertEqual(rd.verify(), 1)

    def test_missing_native_preserves_original_python_strict_fallback(self):
        path, expected = self._path("missing-native", [0] * 1024, [b"ABC"])
        prior = reader_module.native_chunk_proof
        reader_module.native_chunk_proof = lambda *args: False
        self.addCleanup(lambda: setattr(reader_module, "native_chunk_proof", prior))
        with CMPCT(path) as rd:
            self.assertFalse(rd._chunk_range_sealed)
            self.assertIs(type(rd.by["fixed.bin"][6][1]), list)
            self.assertEqual(rd.read_range("fixed.bin", 1999, 17), expected[1999:2016])
            self.assertEqual(rd.verify(), 1)


if __name__ == "__main__":
    unittest.main()
