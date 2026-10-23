"""Hardlink owner mutations fail before a footer can publish dangling aliases."""
from __future__ import annotations

import hashlib
import os
import tempfile
import unittest
from pathlib import Path

from cmpct.builder import Builder
from cmpct.codec import FTR
from cmpct.reader import CMPCT
from cmpct.transactions import append_delete, append_rename
from cmpct.validation import preflight_archive


class HardlinkOwnerGuard(unittest.TestCase):
    def make_archive(self, root: Path, *, aliases: int = 1, primary_only: bool = False) -> Path:
        src = root / "input"
        src.mkdir()
        owner = src / "a.txt"
        owner.write_bytes(b"logical-owner" * 31)
        for i in range(aliases):
            os.link(owner, src / ("hard.txt" if i == 0 else f"hard{i}.txt"))
        (src / "independent.txt").write_bytes(b"unrelated")
        archive = root / "source.cmpct"
        Builder(src, reproducible=True).build(archive)
        if primary_only:
            # Remove only the redundant checkpoint; authenticated primary data remains.
            data = archive.read_bytes()
            _, kind, _, _, _, compressed, _, prev, _ = FTR.unpack(data[-FTR.size:])
            self.assertEqual((kind, prev), (0, 0))
            archive.write_bytes(data[:-FTR.size-compressed])
        preflight_archive(archive)
        with CMPCT(archive) as ar:
            self.assertEqual(ar.read("hard.txt"), ar.read("a.txt"))
        return archive

    def assert_rejected_without_mutation(self, archive: Path, operation):
        before = archive.read_bytes()
        digest = hashlib.sha256(before).digest()
        with self.assertRaisesRegex(ValueError, "hardlink owner"):
            operation()
        self.assertEqual(archive.read_bytes(), before)
        self.assertEqual(hashlib.sha256(archive.read_bytes()).digest(), digest)
        preflight_archive(archive)
        with CMPCT(archive) as reader:
            self.assertEqual(reader.read("a.txt"), b"logical-owner" * 31)
            self.assertEqual(reader.read("hard.txt"), reader.read("a.txt"))

    def test_delete_owner_is_rejected_atomically(self):
        with tempfile.TemporaryDirectory() as td:
            ar = self.make_archive(Path(td))
            self.assert_rejected_without_mutation(ar, lambda: append_delete(ar, "a.txt"))

    def test_rename_owner_is_rejected_atomically(self):
        with tempfile.TemporaryDirectory() as td:
            ar = self.make_archive(Path(td))
            self.assert_rejected_without_mutation(ar, lambda: append_rename(ar, "a.txt", "renamed.txt"))

    def test_three_aliases_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            ar = self.make_archive(Path(td), aliases=3)
            self.assert_rejected_without_mutation(ar, lambda: append_delete(ar, "a.txt"))
            self.assert_rejected_without_mutation(ar, lambda: append_rename(ar, "a.txt", "renamed.txt"))

    def test_primary_only_recovery_input_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            ar = self.make_archive(Path(td), primary_only=True)
            self.assert_rejected_without_mutation(ar, lambda: append_delete(ar, "a.txt"))
            self.assert_rejected_without_mutation(ar, lambda: append_rename(ar, "a.txt", "renamed.txt"))

    def test_rename_alias_preserves_inode_relationship(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            ar = self.make_archive(root)
            append_rename(ar, "hard.txt", "alias-renamed.txt")
            preflight_archive(ar)
            with CMPCT(ar) as reader:
                self.assertEqual(reader.read("alias-renamed.txt"), reader.read("a.txt"))
                reader.extractall(root / "extract")
            self.assertEqual((root / "extract/a.txt").stat().st_ino,
                             (root / "extract/alias-renamed.txt").stat().st_ino)

    def test_delete_alias_is_valid(self):
        with tempfile.TemporaryDirectory() as td:
            ar = self.make_archive(Path(td))
            append_delete(ar, "hard.txt")
            preflight_archive(ar)
            with CMPCT(ar) as reader:
                self.assertNotIn("hard.txt", reader.by)
                self.assertEqual(reader.read("a.txt"), b"logical-owner" * 31)

    def test_after_rejected_owner_removing_alias_unblocks_rename(self):
        with tempfile.TemporaryDirectory() as td:
            ar = self.make_archive(Path(td))
            self.assert_rejected_without_mutation(ar, lambda: append_delete(ar, "a.txt"))
            append_delete(ar, "hard.txt")
            append_rename(ar, "a.txt", "renamed.txt")
            preflight_archive(ar)
            with CMPCT(ar) as reader:
                self.assertEqual(reader.read("renamed.txt"), b"logical-owner" * 31)

    def test_unrelated_member_operations_remain_valid(self):
        with tempfile.TemporaryDirectory() as td:
            ar = self.make_archive(Path(td))
            append_rename(ar, "independent.txt", "moved.txt")
            preflight_archive(ar)
            append_delete(ar, "moved.txt")
            preflight_archive(ar)
            with CMPCT(ar) as reader:
                self.assertNotIn("moved.txt", reader.by)
                self.assertEqual(reader.read("hard.txt"), b"logical-owner" * 31)


if __name__ == "__main__":
    unittest.main()
