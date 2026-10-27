"""J24E03: independently exercise the actual inherited and composed release comparators.

This is not an alternative comparator implementation: it runs the original
#328 and current CLI scripts as separate child processes on identical text.
The historical source is provided explicitly by source-bound CI, not guessed.
"""
from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "tools" / "check_performance_regression.py"
ORIGINAL = Path(os.environ.get("J24E03_ORIGINAL_CHECKER", ""))


def record():
    metric = {"bytes": 1000, "create_s_median": 0.100, "extract_s_median": 0.070}
    return {"schema": "cmpct-zip-parity-v1", "corpora": {
        "fixture": {"logical_bytes": 1000,
                    "library": {"cmpct": copy.deepcopy(metric), "zip": copy.deepcopy(metric)},
                    "cli": {"cmpct": copy.deepcopy(metric), "zip": copy.deepcopy(metric)}}}}


def dump(data):
    return json.dumps(data, separators=(",", ":"), allow_nan=False)


def run_checker(script, before, after, *flags):
    with tempfile.TemporaryDirectory() as folder:
        a, b = Path(folder) / "a.json", Path(folder) / "b.json"
        a.write_text(before, encoding="utf-8")
        b.write_text(after, encoding="utf-8")
        return subprocess.run([sys.executable, str(script), "--base", str(a),
                               "--candidate", str(b), *flags],
                              text=True, capture_output=True, timeout=10, check=False)


def ambiguous_records():
    good = dump(record())
    data = record()
    slow = copy.deepcopy(data["corpora"]["fixture"])
    slow["library"]["cmpct"]["create_s_median"] = 0.107
    row_good = dump(data["corpora"]["fixture"])
    row_slow = dump(slow)
    leaf = '"create_s_median":0.1'
    assert leaf in good
    corpus_row = '"fixture":' + row_good
    assert corpus_row in good
    candidates = {
        "duplicate-root-schema": good.replace('"schema":', '"schema":"cmpct-zip-parity-v1","schema":', 1),
        "duplicate-leaf-time": good.replace(leaf, '"create_s_median":0.107,' + leaf, 1),
        "duplicate-corpus-row": good.replace(corpus_row, '"fixture":' + row_slow + ',' + corpus_row, 1),
        "duplicate-logical-size": good.replace('"logical_bytes":1000',
                                                '"logical_bytes":999,"logical_bytes":1000', 1),
        "duplicate-library": good.replace('"library":', '"library":{},"library":', 1),
    }
    return good, candidates


class GenuineTwoBoundaryComposition(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not ORIGINAL.is_file():
            if os.environ.get("J24E03_ORIGINAL_CHECKER"):
                raise RuntimeError("frozen source comparator path configured but missing")
            raise unittest.SkipTest("requires source-bound historical comparator from exact parent #328")
        if not CHECKER.is_file():
            raise RuntimeError("current release comparator missing")

    def test_original_valid_aa_and_actual_regression_identical(self):
        good = dump(record())
        for script in (ORIGINAL, CHECKER):
            same = run_checker(script, good, good)
            self.assertEqual(same.returncode, 0, same.stdout + same.stderr)
            self.assertIn("Result: **PASS**", same.stdout)
            bad = record()
            bad["corpora"]["fixture"]["library"]["cmpct"]["create_s_median"] = 0.107
            slow = run_checker(script, good, dump(bad))
            self.assertEqual(slow.returncode, 1, slow.stdout + slow.stderr)
            self.assertIn("Result: **FAIL**", slow.stdout)
            larger = record()
            larger["corpora"]["fixture"]["library"]["cmpct"]["bytes"] += 1
            size = run_checker(script, good, dump(larger))
            self.assertEqual(size.returncode, 1, size.stdout + size.stderr)

    def test_original_false_green_becomes_fail_closed(self):
        good, hostile = ambiguous_records()
        for kind, candidate in hostile.items():
            with self.subTest(kind=kind):
                old = run_checker(ORIGINAL, good, candidate)
                new = run_checker(CHECKER, good, candidate)
                self.assertEqual(old.returncode, 0, kind + ": " + old.stdout + old.stderr)
                self.assertIn("Result: **PASS**", old.stdout)
                self.assertNotEqual(new.returncode, 0, kind)
                self.assertIn("duplicate JSON object key", new.stderr, kind + ": " + new.stderr)
                self.assertNotIn("Result: **PASS**", new.stdout)

    def test_inherited_numeric_policy_cannot_be_relaxed(self):
        good = dump(record())
        for arg in ("--timing-relative=nan", "--timing-absolute-ms=inf",
                    "--max-time-regression=0.051", "--max-size-regression=-0.01"):
            with self.subTest(arg=arg):
                original = run_checker(ORIGINAL, good, good, arg)
                combined = run_checker(CHECKER, good, good, arg)
                self.assertEqual(original.returncode, 2, original.stderr)
                self.assertEqual(combined.returncode, original.returncode, combined.stderr)
                self.assertNotIn("Result: **PASS**", combined.stdout)


if __name__ == "__main__":
    unittest.main()
