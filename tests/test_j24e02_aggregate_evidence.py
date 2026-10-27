"""J24E02: source-exact two-stage raw ABBA evidence ingestion court.

The original aggregator, changed aggregator and unchanged strict comparator are
executed as separate Python processes on identical serialized UTF-8 reports.
No second implementation of CMPCT's aggregator/comparator is used here.
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
CANDIDATE_AGG = ROOT / "tools" / "aggregate_parity_runs.py"
CHECKER = ROOT / "tools" / "check_performance_regression.py"
ORIGINAL_AGG = Path(os.environ.get("J24E02_ORIGINAL_AGGREGATOR", ""))


def _row():
    metric = {"bytes": 1000, "create_s_median": 0.1, "extract_s_median": 0.07}
    return {
        "logical_bytes": 1000,
        "library": {"cmpct": copy.deepcopy(metric), "zip": copy.deepcopy(metric)},
        "cli": {"cmpct": copy.deepcopy(metric), "zip": copy.deepcopy(metric)},
    }


def _report(row=None):
    return {"schema": "cmpct-zip-parity-v1", "repetitions": 3,
            "corpora": {"independent": row if row is not None else _row()}}


def _dump(data):
    return json.dumps(data, separators=(",", ":"), allow_nan=False)


def _hostile(kind):
    good = _dump(_report())
    if kind == "nested-cmpct-timing":
        needle = '"create_s_median":0.1'
        assert needle in good
        return good.replace(needle, '"create_s_median":0.107,' + needle, 1)
    if kind == "whole-corpus-map":
        bad = _row()
        bad["library"]["cmpct"]["create_s_median"] = 0.107
        bad_map = _dump({"independent": bad})
        return good.replace('"corpora":', '"corpora":' + bad_map + ',"corpora":', 1)
    if kind == "zip-bytes":
        needle = '"zip":{"bytes":1000'
        assert needle in good
        return good.replace(needle, '"zip":{"bytes":1001,"bytes":1000', 1)
    if kind in {"zip-NaN", "zip-Infinity", "zip--Infinity", "zip-overflow"}:
        # These affect *only* ZIP measurements. The strict CMPCT comparator
        # validates CMPCT but cannot detect invalid normalized ZIP evidence.
        needle = '"zip":{"bytes":1000,"create_s_median":0.1'
        assert needle in good
        token = {"zip-NaN": "NaN", "zip-Infinity": "Infinity",
                 "zip--Infinity": "-Infinity", "zip-overflow": "1e309"}[kind]
        return good.replace(needle, '"zip":{"bytes":1000,"create_s_median":' + token, 1)
    raise AssertionError(kind)


def _command(script, *args):
    return subprocess.run([sys.executable, str(script), *map(str, args)],
                          text=True, capture_output=True, check=False, timeout=15)


def _aggregate(script, first, second, directory, prefix):
    p1, p2, output = [directory / f"{prefix}-{name}.json"
                      for name in ("one", "two", "out")]
    p1.write_text(first, encoding="utf-8")
    p2.write_text(second, encoding="utf-8")
    run = _command(script, "--out", output, p1, p2)
    return run, output


class AggregateEvidenceCourt(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not ORIGINAL_AGG.is_file():
            raise RuntimeError("J24E02_ORIGINAL_AGGREGATOR must identify frozen parent source")
        for path in (CANDIDATE_AGG, CHECKER):
            if not path.is_file():
                raise RuntimeError(f"required authentic source missing: {path}")

    def test_same_input_AA_and_real_regression_keep_policy(self):
        good = _dump(_report())
        real = _report()
        real["corpora"]["independent"]["library"]["cmpct"]["create_s_median"] = 0.107
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            parent, base = _aggregate(ORIGINAL_AGG, good, good, d, "base-original")
            new, newbase = _aggregate(CANDIDATE_AGG, good, good, d, "base-new")
            self.assertEqual(parent.returncode, 0, parent.stderr)
            self.assertEqual(new.returncode, 0, new.stderr)
            self.assertEqual(base.read_bytes(), newbase.read_bytes())
            aa = _command(CHECKER, "--base", base, "--candidate", newbase)
            self.assertEqual(aa.returncode, 0, aa.stderr + aa.stdout)
            self.assertIn("Result: **PASS**", aa.stdout)
            red, redpath = _aggregate(CANDIDATE_AGG, _dump(real), _dump(real), d, "real-red")
            self.assertEqual(red.returncode, 0, red.stderr)
            verdict = _command(CHECKER, "--base", newbase, "--candidate", redpath)
            self.assertEqual(verdict.returncode, 1, verdict.stderr + verdict.stdout)
            self.assertIn("Result: **FAIL**", verdict.stdout)

    def test_raw_ambiguous_evidence_cannot_be_laundered(self):
        good = _dump(_report())
        for kind in ("nested-cmpct-timing", "whole-corpus-map", "zip-bytes",
                     "zip-NaN", "zip-Infinity", "zip--Infinity", "zip-overflow"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as td:
                d = Path(td)
                hostile = _hostile(kind)
                base_run, base = _aggregate(CANDIDATE_AGG, good, good, d, "base")
                self.assertEqual(base_run.returncode, 0, base_run.stderr)
                # Two hostile repeat outputs are deliberate: no misleading
                # "one bad sample, one good sample" median assumption.
                old_run, old_path = _aggregate(ORIGINAL_AGG, hostile, hostile, d, "old")
                self.assertEqual(old_run.returncode, 0, kind + ": " + old_run.stderr)
                old_gate = _command(CHECKER, "--base", base, "--candidate", old_path)
                self.assertEqual(old_gate.returncode, 0, kind + ": " + old_gate.stderr + old_gate.stdout)
                self.assertIn("Result: **PASS**", old_gate.stdout)
                fixed_run, fixed_path = _aggregate(CANDIDATE_AGG, hostile, hostile, d, "fixed")
                self.assertNotEqual(fixed_run.returncode, 0, kind)
                self.assertFalse(fixed_path.exists(), kind)
                self.assertIn("ValueError", fixed_run.stderr, kind)
                self.assertIn(
                    "duplicate JSON object key" if not kind.startswith("zip-") else "nonfinite",
                    fixed_run.stderr, kind + ": " + fixed_run.stderr,
                )


if __name__ == "__main__":
    unittest.main()
