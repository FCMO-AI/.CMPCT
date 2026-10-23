"""Independent revision-24 rename-target scientific court.

Prediction (recorded before hosted execution): append_rename checks only the
literal target and pathlib parent, so five unsafe/canonical-colliding target
spellings commit a footer and subsequently make the archive unreadable.
This is an evidence court, NOT a fix or a relaxed validator. It is based on
PR #247 exactly and does not edit transactions.py or inherited tests.

Future corrected behavior intentionally FAILS this reproduction suite; a
product regression suite should invert these expectations and demand a
byte-identical fail-closed rejection instead.
"""
from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from cmpct.builder import Builder
from cmpct.reader import CMPCT
from cmpct.transactions import append_rename
from cmpct.validation import preflight_archive


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class RenameTargetScientificCourt(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="cmpct-rename-target-court-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.src = self.root / "source"
        (self.src / "dir").mkdir(parents=True)
        (self.src / "empty").mkdir()
        (self.src / "dir" / "child.txt").write_bytes(b"child" * 81)
        (self.src / "root.txt").write_bytes(b"root" * 117)
        self.archive = self.root / "test.cmpct"
        Builder(self.src, workers=1, reproducible=True).build(self.archive)
        preflight_archive(self.archive)
        with CMPCT(self.archive) as rd:
            rd.verify()
            self.assertEqual(rd.read("root.txt"), b"root" * 117)
        self.initial_sha = digest(self.archive)
        self.initial_bytes = self.archive.read_bytes()

    def assert_bad_rename_commits_unreadable(self, bad_target: str):
        self.assertIsNone(append_rename(self.archive, "root.txt", bad_target))
        self.assertNotEqual(digest(self.archive), self.initial_sha)
        with self.assertRaises((OSError, ValueError)):
            preflight_archive(self.archive)
        with self.assertRaises((OSError, ValueError)):
            with CMPCT(self.archive) as rd:
                rd.verify()

    def test_absolute_target_commits_unreadable_archive(self):
        self.assert_bad_rename_commits_unreadable("/absolute-name")

    def test_dot_component_commits_unreadable_archive(self):
        self.assert_bad_rename_commits_unreadable("./dotted")

    def test_trailing_separator_commits_unreadable_archive(self):
        self.assert_bad_rename_commits_unreadable("trailing/")

    def test_double_separator_under_explicit_parent_commits_unreadable_archive(self):
        self.assert_bad_rename_commits_unreadable("dir//double")

    def test_backslash_alias_collision_commits_unreadable_archive(self):
        # A separate live entry already owns the same canonical key.
        self.assert_bad_rename_commits_unreadable("dir\\child.txt")

    def test_empty_directory_rename_into_own_descendant_reports_false_success(self):
        # POSIX cannot relocate a directory underneath itself; the one-row
        # generation removes the parent and manufactures an orphaned child.
        before = self.archive.read_bytes()
        with self.assertRaises(OSError):
            (self.src / "empty").rename(self.src / "empty" / "child")
        self.assertIsNone(append_rename(self.archive, "empty", "empty/child"))
        self.assertNotEqual(self.archive.read_bytes(), before)
        with CMPCT(self.archive) as reader:
            names = {r[0] for r in reader.index["files"]}
            self.assertNotIn("empty", names)
            self.assertIn("empty/child", names)

    def test_valid_rename_preserves_exact_bytes(self):
        self.assertIsNone(append_rename(self.archive, "root.txt", "dir/renamed.txt"))
        preflight_archive(self.archive)
        with CMPCT(self.archive) as rd:
            rd.verify()
            self.assertEqual(rd.read("dir/renamed.txt"), b"root" * 117)
            self.assertEqual(rd.read("dir/child.txt"), b"child" * 81)
            rd.extractall(self.root / "extract", metadata=True)
        self.assertEqual((self.root / "extract" / "dir" / "renamed.txt").read_bytes(), b"root" * 117)

    def test_missing_parent_is_already_fail_closed(self):
        with self.assertRaises(FileNotFoundError):
            append_rename(self.archive, "root.txt", "missing/renamed.txt")
        self.assertEqual(self.archive.read_bytes(), self.initial_bytes)
        preflight_archive(self.archive)


if __name__ == "__main__":
    unittest.main()
