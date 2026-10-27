"""J24E04: same-semantics ABBA admission on authentic scripts, not a surrogate evaluator."""
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
AGGREGATOR = ROOT / "tools" / "aggregate_parity_runs.py"
CHECKER = ROOT / "tools" / "check_performance_regression.py"
HISTORICAL_AGG = os.getenv("J24E04_ORIGINAL_AGGREGATOR")
HISTORICAL_CHECKER = os.getenv("J24E04_ORIGINAL_CHECKER")


def fixture():
    metric = {"bytes": 1000, "create_s_median": 0.1, "extract_s_median": 0.07}
    return {
        "schema": "cmpct-zip-parity-v1",
        "repetitions": 7,
        "timing_statistic": "median",
        "cache_semantics": "warm ordinary cache",
        "integrity_semantics": {"cmpct": "SHA/CRC", "zip": "CRC"},
        "filesystem_semantic_mismatch": "ZIP dereferences symlinks",
        "corpus_semantics": "one immutable test tree",
        "corpora": {"synthetic": {"logical_bytes": 1000,
                                    "library": {"cmpct": copy.deepcopy(metric), "zip": copy.deepcopy(metric)},
                                    "cli": {"cmpct": copy.deepcopy(metric), "zip": copy.deepcopy(metric)}}},
    }


FIELDS = {
    "timing_statistic": "minimum not median",
    "cache_semantics": "cold cache rather than warm",
    "integrity_semantics": {"cmpct": "no verification", "zip": "CRC"},
    "filesystem_semantic_mismatch": "ZIP faithfully preserves hardlinks",
    "corpus_semantics": "another corpus with same reported length",
}


def script_run(script, records, aggregate):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        paths = []
        for i, record in enumerate(records):
            p = root / f"record-{i}.json"
            p.write_text(json.dumps(record, allow_nan=False), encoding="utf-8")
            paths.append(p)
        if aggregate:
            cmd = [sys.executable, str(script), "--out", str(root / "aggregate.json"), *(str(p) for p in paths)]
        else:
            cmd = [sys.executable, str(script), "--base", str(paths[0]), "--candidate", str(paths[1])]
        result = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=15)
        output = (root / "aggregate.json")
        return result, (json.loads(output.read_text()) if output.is_file() else None)


class SemanticCustody(unittest.TestCase):
    def test_legitimate_repeated_aggregation_retains_original_arithmetic(self):
        a = fixture()
        b = copy.deepcopy(a)
        b["corpora"]["synthetic"]["library"]["cmpct"]["create_s_median"] = 0.12
        result, output = script_run(AGGREGATOR, [a, b], True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertAlmostEqual(output["corpora"]["synthetic"]["library"]["cmpct"]["create_s_median"], 0.11)
        self.assertEqual(output["source_repetitions_per_run"], [7, 7])
        self.assertEqual(output["cache_semantics"], a["cache_semantics"])

    def test_legitimate_comparator_and_true_regressions(self):
        a = fixture()
        ok, _ = script_run(CHECKER, [a, a], False)
        self.assertEqual(ok.returncode, 0, ok.stdout + ok.stderr)
        self.assertIn("Result: **PASS**", ok.stdout)
        slower = copy.deepcopy(a)
        slower["corpora"]["synthetic"]["library"]["cmpct"]["create_s_median"] = 0.107
        red, _ = script_run(CHECKER, [a, slower], False)
        self.assertEqual(red.returncode, 1, red.stdout + red.stderr)
        self.assertIn("Result: **FAIL**", red.stdout)
        larger = copy.deepcopy(a)
        larger["corpora"]["synthetic"]["library"]["cmpct"]["bytes"] += 1
        red_bytes, _ = script_run(CHECKER, [a, larger], False)
        self.assertEqual(red_bytes.returncode, 1, red_bytes.stdout + red_bytes.stderr)

    def test_semantics_conflict_rejected_at_both_boundaries(self):
        a = fixture()
        for field, replacement in FIELDS.items():
            with self.subTest(field=field):
                b = copy.deepcopy(a)
                b[field] = replacement
                agg, output = script_run(AGGREGATOR, [a, b], True)
                self.assertNotEqual(agg.returncode, 0, field)
                self.assertIsNone(output)
                self.assertIn("ABBA/" + field, agg.stderr)
                comp, _ = script_run(CHECKER, [a, b], False)
                self.assertEqual(comp.returncode, 1, field + comp.stdout + comp.stderr)
                self.assertIn("Result: **FAIL**", comp.stdout)
                self.assertIn("benchmark semantics changed for " + field, comp.stdout)

    def test_type_preserving_json_identity_not_python_equality(self):
        # Python equates False and 0 even inside dictionaries; authenticated
        # comparison metadata must not silently interpret them as equivalent.
        a = fixture()
        scenarios = []
        left = copy.deepcopy(a)
        right = copy.deepcopy(a)
        left["cache_semantics"] = False
        right["cache_semantics"] = 0
        scenarios.append((left, right, "cache_semantics"))
        left = copy.deepcopy(a)
        right = copy.deepcopy(a)
        left["integrity_semantics"]["cmpct"] = False
        right["integrity_semantics"]["cmpct"] = 0
        scenarios.append((left, right, "integrity_semantics"))
        left = copy.deepcopy(a)
        right = copy.deepcopy(a)
        left.pop("corpus_semantics")
        right["corpus_semantics"] = None
        scenarios.append((left, right, "corpus_semantics"))
        for left, right, field in scenarios:
            with self.subTest(field=field):
                agg, result = script_run(AGGREGATOR, [left, right], True)
                self.assertNotEqual(agg.returncode, 0, agg.stdout + agg.stderr)
                self.assertIsNone(result)
                self.assertIn("ABBA/" + field, agg.stderr)
                checker, _ = script_run(CHECKER, [left, right], False)
                self.assertEqual(checker.returncode, 1, checker.stdout + checker.stderr)
                self.assertIn("benchmark semantics changed for " + field, checker.stdout)

    def test_equivalent_nested_mapping_key_order_is_preserved(self):
        a = fixture()
        b = copy.deepcopy(a)
        b["integrity_semantics"] = {
            "zip": a["integrity_semantics"]["zip"],
            "cmpct": a["integrity_semantics"]["cmpct"],
        }
        agg, result = script_run(AGGREGATOR, [a, b], True)
        self.assertEqual(agg.returncode, 0, agg.stderr)
        self.assertEqual(result["integrity_semantics"], a["integrity_semantics"])
        checker, _ = script_run(CHECKER, [a, b], False)
        self.assertEqual(checker.returncode, 0, checker.stdout + checker.stderr)

    @unittest.skipUnless(HISTORICAL_AGG and HISTORICAL_CHECKER, "source-bound historical scripts needed")
    def test_exact_parent_false_acceptance_exposed(self):
        self.assertTrue(Path(HISTORICAL_AGG).is_file(), "configured original aggregator absent")
        self.assertTrue(Path(HISTORICAL_CHECKER).is_file(), "configured original comparator absent")
        a = fixture()
        for field, replacement in FIELDS.items():
            with self.subTest(field=field):
                b = copy.deepcopy(a)
                b[field] = replacement
                original_agg, out = script_run(Path(HISTORICAL_AGG), [a, b], True)
                self.assertEqual(original_agg.returncode, 0, field + original_agg.stderr)
                self.assertEqual(out[field], a[field], "original copies first metadata, masking second")
                original_comp, _ = script_run(Path(HISTORICAL_CHECKER), [a, b], False)
                self.assertEqual(original_comp.returncode, 0, field + original_comp.stderr)
                self.assertIn("Result: **PASS**", original_comp.stdout)


if __name__ == "__main__":
    unittest.main()
