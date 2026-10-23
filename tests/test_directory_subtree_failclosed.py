"""Source-exact regression: revision-24 nonempty directory mutation must fail closed.

Issue #244 / scientific evidence PR #243; compose on the hardlink-owner guard PR #241.
"""
from __future__ import annotations

import hashlib
import os
import stat
import tempfile
import unittest
from pathlib import Path

from cmpct.builder import Builder
from cmpct.reader import CMPCT
from cmpct.transactions import append_delete, append_rename
from cmpct.validation import preflight_archive

EPOCH = 315532800


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree_manifest(root: Path) -> dict:
    rows = {}
    for path in sorted(root.rglob("*")):
        st = os.lstat(path)
        rel = path.relative_to(root).as_posix()
        row = (stat.S_IMODE(st.st_mode), st.st_mtime_ns)
        if stat.S_ISDIR(st.st_mode):
            rows[rel] = ("directory", *row)
        elif stat.S_ISREG(st.st_mode):
            rows[rel] = ("file", *row, st.st_size, digest(path))
        elif stat.S_ISLNK(st.st_mode):
            rows[rel] = ("symlink", *row, os.readlink(path))
        else:
            raise AssertionError("unexpected special test node")
    return rows


class DirectorySubtreeMutationFailClosed(unittest.TestCase):
    def setUp(self):
        self._temp = tempfile.TemporaryDirectory(prefix="cmpct-directory-subtree-")
        self.addCleanup(self._temp.cleanup)
        root = Path(self._temp.name)
        self.src = root / "source"
        (self.src / "dir" / "sub").mkdir(parents=True)
        (self.src / "dir2").mkdir()
        (self.src / "empty").mkdir()
        (self.src / "dir" / "child.txt").write_bytes(b"child-a" * 100)
        (self.src / "dir" / "sub" / "nested.bin").write_bytes(b"nested-b" * 129)
        (self.src / "dir2" / "unrelated.bin").write_bytes(b"other" * 32)
        (self.src / "plain.txt").write_bytes(b"plain" * 20)
        for p in sorted(self.src.rglob("*")):
            if p.is_file():
                p.chmod(0o640)
                os.utime(p, (EPOCH, EPOCH))
        for p in sorted((p for p in self.src.rglob("*") if p.is_dir()), reverse=True):
            p.chmod(0o750)
            os.utime(p, (EPOCH, EPOCH))
        os.utime(self.src, (EPOCH, EPOCH))
        self.archive = root / "test.cmpct"
        Builder(self.src, workers=1, reproducible=False).build(self.archive)
        preflight_archive(self.archive)
        self.original_hash = digest(self.archive)
        self.original_size = self.archive.stat().st_size
        self.expected = tree_manifest(self.src)

    def assert_source_preserved(self):
        self.assertEqual(digest(self.archive), self.original_hash)
        self.assertEqual(self.archive.stat().st_size, self.original_size)
        preflight_archive(self.archive)
        with CMPCT(self.archive) as reader:
            reader.verify()
            dest = Path(self._temp.name) / "restored"
            reader.extractall(dest, metadata=True)
        self.assertEqual(tree_manifest(dest), self.expected)

    def test_nonempty_directory_rename_refused_before_append(self):
        with self.assertRaisesRegex(OSError, "nonempty directory"):
            append_rename(self.archive, "dir", "moved")
        self.assert_source_preserved()

    def test_nonempty_directory_delete_refused_before_append(self):
        with self.assertRaisesRegex(OSError, "nonempty directory"):
            append_delete(self.archive, "dir")
        self.assert_source_preserved()

    def test_nested_nonempty_directory_rename_refused(self):
        with self.assertRaisesRegex(OSError, "nonempty directory"):
            append_rename(self.archive, "dir/sub", "elsewhere")
        self.assert_source_preserved()

    def test_empty_directory_rename_keeps_unrelated_similar_prefix(self):
        # dir2/ descendants must not count as descendants of empty/ or dir/.
        append_rename(self.archive, "empty", "new_empty")
        with CMPCT(self.archive) as reader:
            reader.verify()
            dest = Path(self._temp.name) / "renamed"
            reader.extractall(dest, metadata=True)
        original = dict(self.expected)
        original["new_empty"] = original.pop("empty")
        self.assertEqual(tree_manifest(dest), original)

    def test_empty_directory_delete_keeps_other_members(self):
        append_delete(self.archive, "empty")
        with CMPCT(self.archive) as reader:
            reader.verify()
            dest = Path(self._temp.name) / "deleted"
            reader.extractall(dest, metadata=True)
        original = dict(self.expected)
        original.pop("empty")
        self.assertEqual(tree_manifest(dest), original)

    def test_regular_file_rename_remains_supported(self):
        append_rename(self.archive, "plain.txt", "renamed.txt")
        with CMPCT(self.archive) as reader:
            reader.verify()
            dest = Path(self._temp.name) / "renamed-file"
            reader.extractall(dest, metadata=True)
        original = dict(self.expected)
        original["renamed.txt"] = original.pop("plain.txt")
        self.assertEqual(tree_manifest(dest), original)

    def test_regular_file_delete_remains_supported(self):
        append_delete(self.archive, "plain.txt")
        with CMPCT(self.archive) as reader:
            reader.verify()
            dest = Path(self._temp.name) / "deleted-file"
            reader.extractall(dest, metadata=True)
        original = dict(self.expected)
        original.pop("plain.txt")
        self.assertEqual(tree_manifest(dest), original)


if __name__ == "__main__":
    unittest.main()
