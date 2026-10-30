"""Real Git DAG controls for ZIP parity admission; independent of release benchmark."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "parity_scope", ROOT / "tools" / "classify_zip_parity_scope.py"
)
assert SPEC and SPEC.loader
import sys
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class GitScopeCourt(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name)
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.name", "CI Scope Court")
        self.git("config", "user.email", "scope@example.invalid")
        self.commit("README.md", "baseline\n")
        self.base = self.head()
        self.git("checkout", "-q", "-b", "candidate")

    def git(self, *args):
        return subprocess.check_output(
            ["git", *args], cwd=self.repo, stderr=subprocess.PIPE,
        ).decode().strip()

    def head(self):
        return self.git("rev-parse", "HEAD")

    def commit(self, relative, content):
        p = self.repo / relative
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        self.git("add", "-A")
        self.git("commit", "-q", "-m", f"fixture: {relative}")
        return self.head()

    def decision(self, event="pull_request", base=None):
        return MODULE.classify(
            event, self.head(), self.base if base is None else base, cwd=self.repo,
        )

    def test_two_commit_product_then_workflow_still_runs(self):
        self.commit("src/cmpct/reader.py", "product edit\n")
        product_head = self.head()
        self.commit(".github/workflows/unrelated.yml", "name: docs workflow\n")
        self.assertTrue(self.decision().run)
        self.assertEqual(self.decision().basis, "pr-merge-base")
        self.assertNotEqual(product_head, self.head())
        # Exact historical bug: only the last commit is examined here.
        last_only = self.git("diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD")
        self.assertNotIn("src/cmpct/reader.py", last_only)

    def test_docs_only_and_reverted_product_delta_skip(self):
        self.commit("README.md", "documentation only\n")
        self.assertFalse(self.decision().run)
        self.commit("native/cmpct-core/src/lib.rs", "temporary change\n")
        self.assertTrue(self.decision().run)
        (self.repo / "native/cmpct-core/src/lib.rs").unlink()
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "restore exact original base tree")
        self.assertFalse(self.decision().run)

    def test_moving_base_does_not_count_base_only_source_edits(self):
        self.commit("README.md", "candidate documentation\n")
        self.git("checkout", "-q", "main")
        moved_base = self.commit("src/cmpct/reader.py", "only base changed\n")
        self.git("checkout", "-q", "candidate")
        decision = self.decision(base=moved_base)
        self.assertFalse(decision.run)
        self.assertEqual(decision.basis, "pr-merge-base")

    def test_relevant_rename_deletion_and_weird_paths(self):
        self.commit("src/cmpct/a.py", "same payload\n")
        self.assertTrue(self.decision().run)
        self.git("mv", "src/cmpct/a.py", "README-moved.md")
        self.git("commit", "-q", "-m", "rename source to docs")
        # src/a.py no longer exists in the candidate; moving from base only
        # counts if the source exists in the base. Construct that baseline next.
        self.git("checkout", "-q", "main")
        baseline_source = self.commit("src/cmpct/will_move.py", "content\n")
        self.git("checkout", "-q", "candidate")
        self.git("merge", "-q", "--no-edit", "main")
        self.git("mv", "src/cmpct/will_move.py", "doc-moved.txt")
        self.git("commit", "-q", "-m", "rename baseline source to docs")
        changed = MODULE._git(
            "diff", "--no-renames", "--name-only", "-z",
            baseline_source, self.head(), cwd=self.repo,
        )
        self.assertIn(b"src/cmpct/will_move.py", changed.split(b"\0"))
        self.assertTrue(self.decision(base=baseline_source).run)
        self.commit("tests/strange\nfile.py", "test bytes\n")
        self.assertTrue(self.decision(base=baseline_source).run)

    def test_single_newline_containing_test_path_is_not_misparsed(self):
        self.commit("tests/odd\\nname.py", "standalone test change\\n")
        result = self.decision()
        self.assertTrue(result.run)
        self.assertEqual(result.affected, (b"tests/odd\\nname.py",))

    def test_source_deleted_into_docs_requires_performance(self):
        self.git("checkout", "-q", "main")
        source_base = self.commit("src/cmpct/source_to_move.py", "original\\n")
        self.git("checkout", "-q", "candidate")
        self.git("merge", "-q", "--no-edit", "main")
        self.git("mv", "src/cmpct/source_to_move.py", "renamed-doc.txt")
        self.git("commit", "-q", "-m", "source renamed outside watched path")
        result = self.decision(base=source_base)
        self.assertTrue(result.run)
        self.assertIn(b"src/cmpct/source_to_move.py", result.affected)

    def test_push_before_after_range_and_manual(self):
        prior = self.head()
        docs_head = self.commit("notes.txt", "notes\n")
        self.assertFalse(self.decision(event="push", base=prior).run)
        self.commit("src/cmpct/reader.py", "material\n")
        self.assertTrue(self.decision(event="push", base=docs_head).run)
        self.assertTrue(self.decision(event="workflow_dispatch", base="").run)

    def test_missing_history_and_unknown_events_fail_closed(self):
        self.commit("README.md", "docs\n")
        self.assertTrue(self.decision(base=MODULE.ZERO_SHA).run)
        self.assertTrue(self.decision(base="f" * 40).run)
        self.assertTrue(self.decision(event="schedule").run)

    def test_exact_head_mismatch_rejected_not_skipped(self):
        with self.assertRaisesRegex(ValueError, "checkout HEAD mismatch"):
            MODULE.classify("pull_request", "0" * 40, self.base, cwd=self.repo)

    def test_fetched_but_unrelated_histories_fail_closed(self):
        self.commit("README.md", "candidate docs\\n")
        # A live Git object can exist without any common ancestry. Merely
        # checking cat-file on the event base is insufficient for PR custody.
        self.git("checkout", "-q", "--orphan", "foreign")
        self.git("rm", "-q", "-rf", ".")
        foreign = self.commit("unrelated.txt", "independent history\\n")
        self.git("checkout", "-q", "candidate")
        result = self.decision(base=foreign)
        self.assertTrue(result.run)
        self.assertEqual(result.basis, "history-unavailable-fail-closed")

    def test_criss_cross_incomparable_merge_bases_run_conservatively(self):
        # Two independent merge commits incorporating each other's earlier
        # changes, but not each other's merge commits, have two merge-bases.
        # Selecting just one can classify source changes as absent.
        self.git("checkout", "-q", "-b", "left")
        left = self.commit("src/cmpct/left.py", "source\\n")
        self.git("checkout", "-q", "-b", "right", self.base)
        right = self.commit("README.md", "right docs\\n")
        self.git("checkout", "-q", "left")
        self.git("merge", "-q", "--no-ff", "--no-edit", right)
        left_merge = self.head()
        self.git("checkout", "-q", "right")
        self.git("merge", "-q", "--no-ff", "--no-edit", left)
        right_merge = self.head()
        self.assertEqual(len(self.git(
            "merge-base", "--all", left_merge, right_merge,
        ).splitlines()), 2)
        result = MODULE.classify(
            "pull_request", right_merge, left_merge, cwd=self.repo,
        )
        self.assertTrue(result.run)
        self.assertEqual(result.basis, "ambiguous-merge-base-fail-closed")

    def test_workflow_topology_with_pr_diff_marker(self):
        spec = importlib.util.spec_from_file_location(
            "ci_topology", ROOT / "tools" / "check_ci_topology.py"
        )
        assert spec and spec.loader
        checker = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(checker)
        workflow = ROOT / ".github" / "workflows" / "zip-parity.yml"
        self.assertEqual(checker.validate(workflow), [])
        with tempfile.TemporaryDirectory() as tmp:
            broken = Path(tmp) / "zip-parity.yml"
            contents = workflow.read_text()
            # A marker and commented-out call must not trick the text-level
            # topology ratchet into approving an unenforced release gate.
            broken.write_text(contents.replace(
                "          python tools/classify_zip_parity_scope.py",
                "          # python tools/classify_zip_parity_scope.py",
            ))
            errors = checker.validate(broken)
            self.assertTrue(any("classifier" in error for error in errors))
            broken.write_text(contents.replace(
                "          fetch-depth: 0", "          fetch-depth: 2",
            ))
            errors = checker.validate(broken)
            self.assertTrue(any("fetch-depth" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
