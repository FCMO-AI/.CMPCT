"""J24I04 independent receipt referee self-test, with synthetic A/A red and green.

Not a CMPCT product, performance or authentic-receipt test: only validates
the untrusted-observation auditor's logic before expensive hosted work.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from research.j24i04_independent_receipt_referee import (
    evaluate, mutation_court, NAMES, ORDER, SOURCE,
)


class RefereeSelfCourt(unittest.TestCase):
    def fixture(self, root: Path, *, false_red: bool) -> None:
        archive = b"CMPCT-not-a-product-fixture"
        archive_digest = hashlib.sha256(archive).hexdigest()
        identity = {
            f"{name}/{layer}": [len(archive), archive_digest]
            for name in NAMES for layer in ("library", "cli")
        }

        def payload(label: str) -> dict:
            candidate = label.startswith("candidate")
            corpora = {}
            for name in NAMES:
                layers = {}
                for layer in ("library", "cli"):
                    formats = {}
                    for fmt in ("cmpct", "zip"):
                        value = (0.11 if (false_red and candidate and name == "binary"
                                 and layer == "library" and fmt == "cmpct") else 0.1)
                        formats[fmt] = {"bytes": len(archive),
                                        "create_s_median": value,
                                        "extract_s_median": 0.1}
                    layers[layer] = formats
                corpora[name] = layers
            return {"schema": "cmpct-zip-parity-v1", "repetitions": 7, "corpora": corpora}

        for label, _ in ORDER:
            (root / f"{label}.json").write_text(json.dumps(payload(label)))
        for label in ("base-a", "candidate-a"):
            (root / f"{label}-binary-library.cmpct").write_bytes(archive)
        for label, sample in (("base", "base-a"), ("candidate", "candidate-a")):
            (root / f"{label}.json").write_text(json.dumps(payload(sample)))

        def engine(side: str) -> dict:
            path = str(root / f"engine-{side}")
            return {"source_commit": SOURCE, "engine_root": path,
                    "python_source_sha256": {
                        f"f{i}.py": f"{i:064x}" for i in range(5)
                    },
                    "native_sha256": "a" * 64, "native_bytes": 999,
                    "native_name": "cmpct_core.abi3.so",
                    "imported_paths": {
                        "package": path + "/src/cmpct/__init__.py",
                        "native": path + "/src/cmpct/cmpct_core.abi3.so",
                    }}

        before = {"files": 1, "tree_sha256": "b" * 64, "logical_bytes": 1}
        record = {
            "schema": "cmpct-v031-j24i04-full-matrix-aa-v1",
            "expected_engine_sha": SOURCE, "repetitions_per_sweep": 7,
            "order": [list(x) for x in ORDER],
            "corpus_before": before, "corpus_after": dict(before),
            "engine_a": engine("A"), "engine_b": engine("B"),
            "sweeps": [
                {"label": label, "side": side, "engine_sha": SOURCE,
                 "engine_root": str(root / f"engine-{side}"),
                 "return_code": 0, "archive_sha256": dict(identity)}
                for label, side in ORDER
            ],
            "decision": "AA_FALSE_RED_REPRODUCED" if false_red else "AA_FULL_NEUTRAL",
            "diagnostic_gate_return_code": 1 if false_red else 0,
        }
        (root / "j24i04-record.json").write_text(json.dumps(record))

    def test_neutral_result_and_seven_forgery_rejections(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.fixture(root, false_red=False)
            out = evaluate(root)
            self.assertEqual(out["scientific_decision"], "AA_FULL_NEUTRAL")
            self.assertEqual(out["comparison_cells_checked"], 64)
            self.assertEqual(len(out["false_red_cells"]), 0)
            self.assertEqual(len(mutation_court(root)), 7)

    def test_material_false_red_result(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.fixture(root, false_red=True)
            out = evaluate(root)
            self.assertEqual(out["scientific_decision"], "AA_FALSE_RED_REPRODUCED")
            self.assertEqual(len(out["false_red_cells"]), 1)
            x = out["false_red_cells"][0]
            self.assertEqual((x["name"], x["layer"], x["format"], x["metric"]),
                             ("binary", "library", "cmpct", "create_s_median"))
            self.assertAlmostEqual(x["delta_ms"], 10.0)
            self.assertEqual(len(mutation_court(root)), 7)


if __name__ == "__main__":
    unittest.main()
