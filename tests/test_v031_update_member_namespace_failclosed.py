"""Regressions: r24 one-row put must never commit an incoherent namespace.

Companion to directory-subtree PR #245 and hardlink-owner PR #241. These
tests use the installed Builder, Reader and preflight, not a standalone index
simulation. Rejected updates must not append even an uncommitted byte.
"""
from __future__ import annotations

import hashlib
import os
import tempfile
import unittest
from pathlib import Path

from cmpct.builder import Builder
from cmpct.reader import CMPCT
from cmpct.transactions import append_update
from cmpct.validation import preflight_archive

EXPECTED = b"replacement" * 31


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class UpdateNamespaceFailClosed(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(prefix="cmpct-v031-put-namespace-")
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.source = root / "input"
        self.source.mkdir()
        (self.source / "normal.txt").write_bytes(b"original" * 81)
        (self.source / "solo.txt").write_bytes(b"solo" * 42)
        (self.source / "dir").mkdir()
        (self.source / "dir" / "child.txt").write_bytes(b"nested" * 53)
        (self.source / "empty").mkdir()
        os.symlink("normal.txt", self.source / "link")
        os.link(self.source / "normal.txt", self.source / "hard")
        self.archive = root / "archive.cmpct"
        Builder(self.source, reproducible=True).build(self.archive)
        self.payload = root / "replacement"
        self.payload.write_bytes(EXPECTED)
        preflight_archive(self.archive)
        with CMPCT(self.archive) as reader:
            # Owner path is determined by the Builder, not by this test's
            # assumption about which hardlink spelling is the physical owner.
            self.owner = next(row[0] for row in reader.index["files"]
                              if row[1] == 0 and row[0] in ("hard", "normal.txt"))
            self.alias = "normal.txt" if self.owner == "hard" else "hard"

    def assert_no_write(self, member: str, error: type[Exception]) -> None:
        before = self.archive.read_bytes()
        initial_sha = digest(self.archive)
        with self.assertRaises(error, msg=repr(member)):
            append_update(self.archive, member, self.payload)
        self.assertEqual(self.archive.read_bytes(), before, member)
        self.assertEqual(digest(self.archive), initial_sha, member)
        preflight_archive(self.archive)
        with CMPCT(self.archive) as reader:
            reader.verify()

    def assert_good_put(self, member: str) -> None:
        before = digest(self.archive)
        result = append_update(self.archive, member, self.payload)
        self.assertIn("generation_bytes", result)
        self.assertNotEqual(digest(self.archive), before)
        preflight_archive(self.archive)
        with CMPCT(self.archive) as reader:
            reader.verify()
            self.assertEqual(reader.read(member), EXPECTED)

    def test_existing_ordinary_file_update(self) -> None:
        self.assert_good_put("solo.txt")

    def test_create_at_root(self) -> None:
        self.assert_good_put("newfile.txt")

    def test_create_under_explicit_directory(self) -> None:
        self.assert_good_put("dir/newfile.txt")

    def test_missing_parent_cannot_synthesize_directory(self) -> None:
        self.assert_no_write("ghost/new.bin", FileNotFoundError)

    def test_regular_file_cannot_be_parent(self) -> None:
        self.assert_no_write("solo.txt/new.bin", FileNotFoundError)

    def test_symlink_cannot_be_parent(self) -> None:
        self.assert_no_write("link/new.bin", FileNotFoundError)

    def test_hardlink_cannot_be_parent(self) -> None:
        self.assert_no_write("hard/new.bin", FileNotFoundError)

    def test_nonempty_directory_cannot_be_replaced_with_file(self) -> None:
        self.assert_no_write("dir", OSError)

    def test_empty_directory_cannot_be_replaced_with_file(self) -> None:
        self.assert_no_write("empty", OSError)

    def test_symlink_cannot_be_replaced_with_file(self) -> None:
        self.assert_no_write("link", OSError)

    def test_hardlink_alias_cannot_be_replaced_with_file(self) -> None:
        self.assert_no_write(self.alias, OSError)

    def test_hardlink_owner_update_requires_atomic_alias_metadata(self) -> None:
        self.assert_no_write(self.owner, ValueError)

    def test_absolute_member_rejected_before_any_write(self) -> None:
        self.assert_no_write("/tmp/cmpct-invalid", ValueError)

    def test_parent_traversal_rejected_before_any_write(self) -> None:
        self.assert_no_write("../escape", ValueError)

    def test_dot_component_rejected_before_any_write(self) -> None:
        self.assert_no_write("dir/./new.bin", ValueError)

    def test_backslash_alias_of_existing_file_rejected(self) -> None:
        self.assert_no_write("dir\\child.txt", ValueError)

    def test_backslash_new_spelling_rejected(self) -> None:
        self.assert_no_write("dir\\newfile.txt", ValueError)

    def test_nul_path_rejected_before_any_write(self) -> None:
        self.assert_no_write("nul" + chr(0) + "value", ValueError)


if __name__ == "__main__":
    unittest.main()
