"""J24C08 installed Reader: native engagement, strict fallback, hostile signed r24.

The donor O215 Builder-independent fixture and original strict validator are unchanged.
Only the scanner's private call target is switched to prove its defensive fallback;
ordinary native engagement is exercised through unmodified CMPCT(path).
"""
from __future__ import annotations

import os
from pathlib import Path
import tempfile
import unittest

from cmpct.codec import K_FILE, S_CHUNKS
from cmpct.reader import CMPCT
from cmpct.validation import ValidationError, _validate_storage
import cmpct._chunk_admission as admission
from test_o215_fixed_chunk_admission import _make_archive


EXPECTED_NATIVE = os.environ.get("CMPCT_J24C08_EXPECT_NATIVE", "0") == "1"


class InstalledOptionalAbi3(unittest.TestCase):
    def setUp(self):
        td = tempfile.TemporaryDirectory(prefix="j24c08-installed-")
        self.addCleanup(td.cleanup)
        self.root = Path(td.name)
        self.original_scanner = admission._scan_refs
        self.addCleanup(lambda: setattr(admission, "_scan_refs", self.original_scanner))

    def _wire(self, name, refs, *, logical=b"ABCD", declared_size=None):
        data = _make_archive(refs, logical, declared_size=declared_size)
        p = self.root / (name + ".cmpct")
        p.write_bytes(data)
        return p

    def _reader_outcome(self, path):
        try:
            with CMPCT(path) as rd:
                return ("ACCEPT", rd.read_range("fixed.bin", 0, min(4, rd.files[0][4])))
        except Exception as exc:
            return ("REJECT", type(exc).__name__, str(exc))

    def test_real_wheel_exposes_exact_native_or_python310_fallback(self):
        if EXPECTED_NATIVE:
            self.assertTrue(callable(self.original_scanner),
                            "required cp311-abi3 native module missing from installed wheel")
            blobs = [[0, 4, 4, 0, 0]]
            self.assertIs(self.original_scanner([0, 0], blobs, 8), True)
            for bad, size in [([True], 4), ([-1], 4), ([2], 4),
                              ([2 ** 120], 4), ([0, 0], 7), ([[0]], 4)]:
                self.assertIs(self.original_scanner(bad, blobs, size), False)
        else:
            # A Python 3.10 build has no cp311-abi3 extension. The original
            # Python validator must continue to handle the same signed wire.
            self.assertIsNone(self.original_scanner)

    def test_native_engaged_in_unmodified_reader_constructor(self):
        calls = []
        if EXPECTED_NATIVE:
            original = self.original_scanner
            def counted(*args):
                calls.append(args)
                return original(*args)
            admission._scan_refs = counted
        path = self._wire("valid", [0, 0], logical=b"ABCDABCD")
        with CMPCT(path) as rd:
            self.assertEqual(rd.read_range("fixed.bin", 2, 5), b"CDABC")
            self.assertEqual(rd.read("fixed.bin"), b"ABCDABCD")
            self.assertEqual(rd.verify(), 1)
        self.assertEqual(bool(calls), EXPECTED_NATIVE)
        if calls:
            self.assertEqual(calls[0][0], [0, 0])
            self.assertEqual(calls[0][2], 8)

    def test_strict_fallback_has_identical_exception_type_and_message(self):
        cases = [
            ("over-size", [0], b"ABCD", 5),
            ("under-size", [0], b"ABCD", 3),
            ("wrong-bool", [True], b"ABCD", 4),
            ("wrong-negative", [-1], b"ABCD", 4),
            ("wrong-index", [5], b"ABCD", 4),
            ("wrong-huge", [2 ** 120], b"ABCD", 4),
            ("wrong-sublist", [[0]], b"ABCD", 4),
            ("wrong-tail", [0, 0, True], b"ABCD" * 3, 12),
        ]
        paths = [self._wire(label, refs, logical=logical, declared_size=size)
                 for label, refs, logical, size in cases]
        admission._scan_refs = None
        baseline = [self._reader_outcome(p) for p in paths]
        self.assertTrue(all(row[0] == "REJECT" for row in baseline))
        if self.original_scanner is not None:
            admission._scan_refs = self.original_scanner
            self.assertEqual([self._reader_outcome(p) for p in paths], baseline)
        admission._scan_refs = lambda *args: False
        self.assertEqual([self._reader_outcome(p) for p in paths], baseline)

        def scanner_failure(*args):
            raise RuntimeError("simulated recoverable native failure")
        admission._scan_refs = scanner_failure
        self.assertEqual([self._reader_outcome(p) for p in paths], baseline)

        # Positive data must still work if the native module is absent/failing.
        good = self._wire("good-fallback", [0, 0], logical=b"ABCDABCD")
        self.assertEqual(self._reader_outcome(good), ("ACCEPT", b"ABCD"))

    def test_native_helper_never_admits_other_storage_shapes(self):
        blobs = [[0, 4, 4, 0, 0]]
        self.assertFalse(admission.native_chunk_ok([3, [[4, 0]]], blobs, 4))
        self.assertFalse(admission.native_chunk_ok([S_CHUNKS], blobs, 4))
        self.assertFalse(admission.native_chunk_ok([S_CHUNKS, [0], "extra"], blobs, 4))
        self.assertFalse(admission.native_chunk_ok([S_CHUNKS, {"0": 0}], blobs, 4))
        self.assertFalse(admission.native_chunk_ok((S_CHUNKS, [0]), blobs, 4))

    def test_original_strict_validator_is_never_rewritten(self):
        blobs = [[0, 4, 4, 0, 0]]
        _validate_storage("fixed.bin", K_FILE, 4, [S_CHUNKS, [0]], blobs, [])
        with self.assertRaises(ValidationError):
            _validate_storage("fixed.bin", K_FILE, 4, [S_CHUNKS, [True]], blobs, [])


if __name__ == "__main__":
    unittest.main()
