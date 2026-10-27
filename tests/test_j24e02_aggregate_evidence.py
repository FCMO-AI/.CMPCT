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
    if kind in ("zip-string-nan", "zip-string-inf", "zip-zero-time",
                "zip-string-time", "zip-bool-bytes", "zip-negative-bytes",
                "cmpct-string-time"):
        record = _report()
        row = record["corpora"]["independent"]
        if kind == "zip-string-nan":
            row["library"]["zip"]["create_s_median"] = "nan"
        elif kind == "zip-string-inf":
            row["library"]["zip"]["extract_s_median"] = "inf"
        elif kind == "zip-zero-time":
            row["library"]["zip"]["create_s_median"] = 0
        elif kind == "zip-string-time":
            row["cli"]["zip"]["create_s_median"] = "0.1"
        elif kind == "zip-bool-bytes":
            row["library"]["zip"]["bytes"] = True
        elif kind == "zip-negative-bytes":
            row["cli"]["zip"]["bytes"] = -1
        else:
            row["library"]["cmpct"]["create_s_median"] = "0.1"
        return _dump(record)
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
                    "nonfinite" if kind in ("zip-NaN", "zip-Infinity", "zip--Infinity", "zip-overflow") else "duplicate JSON object key",
                    fixed_run.stderr, kind + ": " + fixed_run.stderr,
                )

    def test_typed_metric_laundering_above_json_parser(self):
        good = _dump(_report())
        for kind in ("zip-string-nan", "zip-string-inf", "zip-zero-time",
                     "zip-string-time", "zip-bool-bytes", "zip-negative-bytes",
                     "cmpct-string-time"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as td:
                d = Path(td)
                base_run, base = _aggregate(CANDIDATE_AGG, good, good, d, "base")
                self.assertEqual(base_run.returncode, 0, base_run.stderr)
                hostile = _hostile(kind)
                original_run, old_path = _aggregate(ORIGINAL_AGG, hostile, hostile, d, "original")
                self.assertEqual(original_run.returncode, 0, kind + ": " + original_run.stderr)
                old_verdict = _command(CHECKER, "--base", base, "--candidate", old_path)
                self.assertEqual(old_verdict.returncode, 0, kind + ": " + old_verdict.stderr + old_verdict.stdout)
                fixed_run, output = _aggregate(CANDIDATE_AGG, hostile, hostile, d, "fixed")
                self.assertNotEqual(fixed_run.returncode, 0, kind)
                self.assertFalse(output.exists(), kind)
                self.assertIn("ValueError", fixed_run.stderr, kind)
                self.assertIn("expected", fixed_run.stderr, kind + ": " + fixed_run.stderr)

    def test_eight_corpus_ABBA_statistics_and_real_row_red_are_unchanged(self):
        # This is a held-out realistic report *shape*, not a claim that the
        # official frozen corpus was generated or timed during this test.
        names = ("tiny", "source", "media", "binary", "dedup_links",
                 "sparse", "nested", "combined")
        base = _report()
        base["repetitions"] = 7
        base["corpora"] = {name: _row() for name in names}
        rows = []
        for offset in (-0.002, 0.002, 0.0, 0.0):
            row = copy.deepcopy(base)
            for j, name in enumerate(names):
                row["corpora"][name]["logical_bytes"] += j * 97
                for layer in ("library", "cli"):
                    for fmt in ("cmpct", "zip"):
                        row["corpora"][name][layer][fmt]["create_s_median"] += offset
                        row["corpora"][name][layer][fmt]["extract_s_median"] += offset / 2
            rows.append(row)

        def aggregate_many(script, records, dest, prefix):
            output = dest / f"{prefix}-aggregate.json"
            files = []
            for i, value in enumerate(records):
                f = dest / f"{prefix}-{i}.json"
                f.write_text(_dump(value), encoding="utf-8")
                files.append(f)
            run = _command(script, "--out", output, *files)
            self.assertEqual(run.returncode, 0, run.stderr)
            return output

        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            old = aggregate_many(ORIGINAL_AGG, rows, d, "old")
            new = aggregate_many(CANDIDATE_AGG, rows, d, "new")
            self.assertEqual(old.read_bytes(), new.read_bytes())
            loaded = json.loads(new.read_text(encoding="utf-8"))
            self.assertEqual(loaded["aggregate_runs"], 4)
            self.assertEqual(loaded["source_repetitions_per_run"], [7] * 4)
            self.assertEqual(set(loaded["corpora"]), set(names))
            self.assertEqual(
                loaded["corpora"]["tiny"]["library"]["cmpct"]["create_s_median"], 0.1,
            )
            aa = _command(CHECKER, "--base", new, "--candidate", old)
            self.assertEqual(aa.returncode, 0, aa.stderr + aa.stdout)

            bad_rows = copy.deepcopy(rows)
            for record in bad_rows:
                record["corpora"]["sparse"]["library"]["cmpct"]["create_s_median"] += 0.007
            bad = aggregate_many(CANDIDATE_AGG, bad_rows, d, "real-red")
            verdict = _command(CHECKER, "--base", new, "--candidate", bad)
            self.assertEqual(verdict.returncode, 1, verdict.stderr + verdict.stdout)
            self.assertIn("sparse/library/create_s_median", verdict.stdout)



if __name__ == "__main__":
    unittest.main()
