"""J24G01 pure, network-free PR topology safety tests.

The fixture models live GitHub PR metadata but never supplies merge permission
or asserts path overlap implies an actual git merge conflict.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "pr_integration_topology.py"
spec = importlib.util.spec_from_file_location("pr_integration_topology", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


def pr(n, head, base, paths, *, base_repo="FCMO-AI/.CMPCT"):
    return {
        "number": n, "head_ref": head, "head_sha": f"{n:040x}",
        "head_repo": "FCMO-AI/.CMPCT",
        "base_ref": base, "base_sha": f"{n + 1000:040x}",
        "base_repo": base_repo,
        "files": list(paths), "url": f"https://github.com/FCMO-AI/.CMPCT/pull/{n}",
        "draft": True, "state": "open",
    }


class TopologyTests(unittest.TestCase):
    def test_stack_is_not_independent_collision(self):
        original = pr(608, "cdc-bounds", "main", ["native/cmpct_cdc.c"])
        child = pr(614, "cdc-portable", "cdc-bounds", ["native/cmpct_cdc.c"])
        evidence = module.analyze([child, original])
        self.assertEqual(evidence["known_stacks"], [{"parent": 608, "child": 614}])
        self.assertEqual(evidence["shared_mutation_surfaces"][0]["relation"],
                         "known_stacked_shared_code")
        self.assertNotIn("mergeable", evidence)

    def test_parallel_shared_path_is_only_risk_signal(self):
        p = pr(609, "raw-geometry", "main", ["src/cmpct/reader.py"])
        q = pr(613, "sparse-verify", "main", ["src/cmpct/reader.py"])
        evidence = module.analyze([p, q])
        self.assertEqual(evidence["shared_mutation_surfaces"][0]["relation"],
                         "parallel_shared_code_surface")
        self.assertIn("does not establish", evidence["shared_mutation_surfaces"][0]["note"])

    def test_unseen_parent_cannot_be_declared_parallel(self):
        p = pr(569, "composed-reader", "unseen-parent-branch", ["src/cmpct/reader.py"])
        q = pr(609, "raw-geometry", "main", ["src/cmpct/reader.py"])
        evidence = module.analyze([p, q])
        self.assertEqual(evidence["shared_mutation_surfaces"][0]["relation"],
                         "shared_code_ancestry_incomplete")
        self.assertEqual(evidence["external_bases_not_in_sample"][0]["number"], 569)

    def test_docs_only_overlap_not_code_conflict(self):
        p = pr(574, "discovery-reconcile", "main", ["docs/discovery/STATE.json"])
        q = pr(575, "discovery-other", "main", ["docs/discovery/STATE.json"])
        evidence = module.analyze([p, q])
        self.assertEqual(evidence["shared_mutation_surfaces"], [])

    def test_cycle_fails_even_without_shared_files(self):
        a = pr(21, "left", "right", ["src/a.py"])
        b = pr(22, "right", "left", ["src/b.py"])
        with self.assertRaisesRegex(ValueError, "cycle"):
            module.analyze([a, b])

    def test_duplicate_pr_and_ambiguous_branches_fail_closed(self):
        p = pr(22, "same", "main", ["src/a.py"])
        with self.assertRaisesRegex(ValueError, "duplicate PR"):
            module.analyze([p, p])
        q = pr(23, "same", "main", ["src/b.py"])
        with self.assertRaisesRegex(ValueError, "ambiguous head"):
            module.analyze([p, q])

    def test_output_has_exact_head_without_claiming_ci_green(self):
        evidence = module.analyze([pr(123, "feature", "main", ["native/a.c"])])
        self.assertEqual(evidence["heads"][0]["head"], f"{123:040x}")
        self.assertNotIn("ci_status", evidence)
        self.assertNotIn("release_ready", evidence)
        self.assertIn("no merge", evidence["scope"])

    def test_offline_cli_fixture_does_not_require_network(self):
        import json
        with tempfile.TemporaryDirectory() as td:
            fixture = Path(td) / "fixture.json"
            out = Path(td) / "report.json"
            fixture.write_text(json.dumps([pr(12, "feature", "main", ["src/a.py"])]))
            rc = module.main(["--repo", "FCMO-AI/.CMPCT", "--input", str(fixture),
                              "--output", str(out)])
            self.assertEqual(rc, 0)
            result = json.loads(out.read_text())
            self.assertEqual(result["data_source"], "offline fixture")
            self.assertEqual(result["pr_count"], 1)
            self.assertEqual(result["heads"][0]["number"], 12)


if __name__ == "__main__":
    unittest.main()
