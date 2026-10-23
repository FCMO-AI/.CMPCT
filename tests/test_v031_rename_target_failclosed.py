"""Product regression: append_rename destination must not publish invalid namespace.

Scientific red baseline: PR #249 @ 2d2e8348e1ae, genuine Builder/Writer/
Reader court run 39942895945 (five mutated unreadable generations).
This suite intentionally INVERTS that reproduction: invalid destinations
must fail before any byte append, and valid operations remain exact.
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


class RenameTargetFailClosed(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="cmpct-rename-target-fix-")
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.src = root / "src"
        (self.src / "dir").mkdir(parents=True)
        (self.src / "dir" / "child.txt").write_bytes(b"child" * 81)
        (self.src / "root.txt").write_bytes(b"root" * 117)
        self.archive = root / "archive.cmpct"
        Builder(self.src, workers=1, reproducible=True).build(self.archive)
        preflight_archive(self.archive)
        self.pristine = self.archive.read_bytes()
        self.pristine_digest = hashlib.sha256(self.pristine).hexdigest()
        self.root = root

    def assert_no_write(self, dest, expected_error):
        with self.assertRaises(expected_error, msg=repr(dest)):
            append_rename(self.archive, "root.txt", dest)
        self.assertEqual(self.archive.read_bytes(), self.pristine, dest)
        self.assertEqual(hashlib.sha256(self.archive.read_bytes()).hexdigest(),
                         self.pristine_digest, dest)
        preflight_archive(self.archive)
        with CMPCT(self.archive) as reader:
            reader.verify()
            self.assertEqual(reader.read("root.txt"), b"root" * 117)
            self.assertEqual(reader.read("dir/child.txt"), b"child" * 81)

    def test_absolute_target_rejected_before_append(self):
        self.assert_no_write("/absolute-name", ValueError)

    def test_dot_component_rejected_before_append(self):
        self.assert_no_write("./dotted", ValueError)

    def test_double_separator_rejected_before_append(self):
        self.assert_no_write("dir//double", ValueError)

    def test_trailing_separator_rejected_before_append(self):
        self.assert_no_write("trailing/", ValueError)

    def test_backslash_canonical_alias_rejected_before_append(self):
        self.assert_no_write("dir\\child.txt", ValueError)

    def test_dotdot_component_rejected_before_append(self):
        self.assert_no_write("dir/../move.txt", ValueError)

    def test_nul_rejected_before_append(self):
        self.assert_no_write("mal" + chr(0) + "formed", ValueError)

    def test_exact_existing_destination_rejected_before_append(self):
        self.assert_no_write("dir/child.txt", FileExistsError)

    def test_missing_destination_parent_rejected_before_append(self):
        self.assert_no_write("missing/new.txt", FileNotFoundError)

    def test_parent_regular_file_rejected_before_append(self):
        self.assert_no_write("dir/child.txt/new.txt", FileNotFoundError)

    def test_root_destination_is_valid(self):
        append_rename(self.archive, "root.txt", "root-renamed.txt")
        preflight_archive(self.archive)
        with CMPCT(self.archive) as reader:
            reader.verify()
            self.assertEqual(reader.read("root-renamed.txt"), b"root" * 117)
            self.assertEqual(reader.read("dir/child.txt"), b"child" * 81)

    def test_existing_directory_destination_is_valid_and_extracts(self):
        append_rename(self.archive, "root.txt", "dir/moved.txt")
        preflight_archive(self.archive)
        with CMPCT(self.archive) as reader:
            reader.verify()
            self.assertEqual(reader.read("dir/moved.txt"), b"root" * 117)
            dest = self.root / "restored"
            reader.extractall(dest, metadata=True)
        self.assertEqual((dest / "dir" / "moved.txt").read_bytes(), b"root" * 117)
        self.assertEqual((dest / "dir" / "child.txt").read_bytes(), b"child" * 81)


    def test_checkpoint_boundary_rejection_and_valid_recovery(self):
        # 63 safe transactions make the next mutation the full-checkpoint
        # transition. An invalid target must not publish any footer there.
        source = "root.txt"
        for i in range(63):
            next_name = f"temporary_{i}.txt"
            append_rename(self.archive, source, next_name)
            source = next_name
        preflight_archive(self.archive)
        with CMPCT(self.archive) as reader:
            self.assertEqual(reader.delta_depth, 63)
            self.assertEqual(reader.read(source), b"root" * 117)
            reader.verify()
        before = self.archive.read_bytes()
        with self.assertRaises(ValueError):
            append_rename(self.archive, source, "./invalid-checkpoint")
        self.assertEqual(self.archive.read_bytes(), before)
        preflight_archive(self.archive)
        with CMPCT(self.archive) as reader:
            reader.verify()
            self.assertEqual(reader.read(source), b"root" * 117)
        # The supported valid action must still publish a correct checkpoint.
        append_rename(self.archive, source, "dir/checkpoint.txt")
        preflight_archive(self.archive)
        with CMPCT(self.archive) as reader:
            reader.verify()
            self.assertEqual(reader.read("dir/checkpoint.txt"), b"root" * 117)
            self.assertEqual(reader.read("dir/child.txt"), b"child" * 81)
            self.assertEqual(reader.delta_depth, 0)


if __name__ == "__main__":
    unittest.main()
