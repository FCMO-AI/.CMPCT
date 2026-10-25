"""O42 source-independent hostile court for the r24 release-corpus witness."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "v031_release_corpus_semantic_witness.py"
spec = importlib.util.spec_from_file_location("o42", TOOL)
assert spec and spec.loader
o42 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(o42)


def legacy_release_hash(root: Path) -> str:
    """Original zip-parity.yml hashing loop, unchanged field order and bytes."""
    h = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root).as_posix().encode()
        st = path.lstat()
        h.update(len(rel).to_bytes(4, "little"))
        h.update(rel)
        h.update((st.st_mode & 0o177777).to_bytes(4, "little"))
        h.update(st.st_mtime_ns.to_bytes(8, "little", signed=True))
        if path.is_symlink():
            target = os.readlink(path).encode()
            h.update(b"L")
            h.update(len(target).to_bytes(4, "little"))
            h.update(target)
        elif path.is_file():
            data = path.read_bytes()
            h.update(b"F")
            h.update(len(data).to_bytes(8, "little"))
            h.update(data)
        elif path.is_dir():
            h.update(b"D")
    return h.hexdigest()


@unittest.skipUnless(os.name == "posix", "release witness is POSIX-only")
class ReleaseSemanticWitnessCourt(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.a = Path(self.temp.name) / "a"
        self.b = Path(self.temp.name) / "b"
        self.a.mkdir()
        self.b.mkdir()
        self.fixed_ns = 1767225600 * 10**9

    def freeze(self):
        for root in (self.a, self.b):
            # Freeze the same controllable metadata as the release court.
            nodes = sorted(root.rglob("*"), key=lambda p: len(p.parts), reverse=True)
            for p in nodes:
                os.utime(p, ns=(self.fixed_ns, self.fixed_ns), follow_symlinks=False)
            os.utime(root, ns=(self.fixed_ns, self.fixed_ns))

    def hash(self, root):
        return o42.semantic_release_tree_sha256(root)

    def set_user_xattr(self, path, value):
        if not hasattr(os, "setxattr"):
            self.skipTest("xattr syscalls unavailable")
        try:
            os.setxattr(path, b"user.cmpct_o42_witness", value)
        except OSError as e:
            self.skipTest(f"xattrs unsupported on fixture volume: {e}")

    def test_old_corpus_hash_misses_hardlink_partition_but_new_distinguishes(self):
        for root in (self.a, self.b):
            (root / "owner.bin").write_bytes(b"same\x00" * 500)
        os.link(self.a / "owner.bin", self.a / "alias.bin")
        shutil.copyfile(self.b / "owner.bin", self.b / "alias.bin")
        self.freeze()
        self.assertEqual(legacy_release_hash(self.a), legacy_release_hash(self.b))
        self.assertNotEqual(self.hash(self.a), self.hash(self.b))
        self.assertEqual((self.a / "owner.bin").stat().st_ino,
                         (self.a / "alias.bin").stat().st_ino)
        self.assertNotEqual((self.b / "owner.bin").stat().st_ino,
                            (self.b / "alias.bin").stat().st_ino)

    def test_old_corpus_hash_misses_extended_attributes(self):
        for root in (self.a, self.b):
            (root / "payload.bin").write_bytes(b"identity" * 333)
        self.set_user_xattr(self.a / "payload.bin", b"physical metadata")
        self.freeze()
        self.assertEqual(legacy_release_hash(self.a), legacy_release_hash(self.b))
        self.assertNotEqual(self.hash(self.a), self.hash(self.b))

    def test_different_inode_numbers_same_partition_and_metadata_equal(self):
        for root in (self.a, self.b):
            (root / "inner").mkdir()
            (root / "inner" / "owner").write_bytes(b"same")
            os.link(root / "inner" / "owner", root / "hard")
        self.freeze()
        self.assertNotEqual((self.a / "hard").stat().st_ino,
                            (self.b / "hard").stat().st_ino)
        self.assertEqual(self.hash(self.a), self.hash(self.b))

    def test_same_count_of_hardlink_groups_but_different_memberships(self):
        for root in (self.a, self.b):
            for n in "abcd":
                (root / n).write_bytes(b"same")
        for name in "bd":
            (self.a / name).unlink()
        os.link(self.a / "a", self.a / "b")
        os.link(self.a / "c", self.a / "d")
        for name in "cd":
            (self.b / name).unlink()
        os.link(self.b / "a", self.b / "c")
        os.link(self.b / "b", self.b / "d")
        self.freeze()
        self.assertEqual(legacy_release_hash(self.a), legacy_release_hash(self.b))
        self.assertNotEqual(self.hash(self.a), self.hash(self.b))

    def test_symlink_and_directory_types_and_targets(self):
        for root in (self.a, self.b):
            (root / "dir").mkdir()
            (root / "dir" / "f").write_bytes(b"contents")
        (self.a / "pointer").symlink_to("dir", target_is_directory=True)
        (self.b / "pointer").mkdir()
        self.freeze()
        self.assertNotEqual(self.hash(self.a), self.hash(self.b))
        (self.b / "pointer").rmdir()
        (self.b / "pointer").symlink_to("dir", target_is_directory=True)
        self.freeze()
        self.assertEqual(self.hash(self.a), self.hash(self.b))
        (self.b / "pointer").unlink()
        (self.b / "pointer").symlink_to("different-target", target_is_directory=True)
        self.freeze()
        self.assertNotEqual(self.hash(self.a), self.hash(self.b))

    def test_cli_adds_only_new_manifest_fields_and_detects_xattr_mutation(self):
        for root in (self.a, self.b):
            (root / "x").write_bytes(b"stable")
        self.freeze()
        manifest = Path(self.temp.name) / "corpus.json"
        original = {"tree_sha256": legacy_release_hash(self.a),
                    "files": 1, "logical_bytes": 6, "fixed_mtime_ns": self.fixed_ns}
        manifest.write_text(json.dumps(original))
        cmd = [sys.executable, str(TOOL), str(self.a)]
        subprocess.run(cmd + ["--record-json", str(manifest)], check=True,
                       capture_output=True, text=True)
        after = json.loads(manifest.read_text())
        for key, value in original.items():
            self.assertEqual(after[key], value)
        self.assertEqual(after["semantic_tree_sha256"], self.hash(self.a))
        subprocess.run(cmd + ["--check-json", str(manifest)], check=True,
                       capture_output=True, text=True)
        self.set_user_xattr(self.a / "x", b"changed after original evidence")
        changed = subprocess.run(cmd + ["--check-json", str(manifest)],
                                 capture_output=True, text=True)
        self.assertNotEqual(changed.returncode, 0)
        self.assertIn("release input semantic tree changed", changed.stderr)

    def test_unreadable_xattr_namespace_fails_closed(self):
        (self.a / "file").write_bytes(b"data")
        self.freeze()
        with patch.object(o42.os, "listxattr", side_effect=OSError("denied")):
            with self.assertRaisesRegex(OSError, "denied"):
                self.hash(self.a)

    def test_special_file_rejected(self):
        if not hasattr(os, "mkfifo"):
            self.skipTest("FIFO unsupported")
        os.mkfifo(self.a / "pipe")
        self.freeze()
        with self.assertRaisesRegex(ValueError, "unsupported release input entry kind"):
            self.hash(self.a)

    def test_resource_limits_are_fail_closed(self):
        (self.a / "d").mkdir()
        (self.a / "d" / "f").write_bytes(b"data")
        self.freeze()
        with self.assertRaisesRegex(ValueError, "entry budget"):
            o42.semantic_release_tree_sha256(self.a, max_entries=1)
        with self.assertRaisesRegex(ValueError, "depth budget"):
            o42.semantic_release_tree_sha256(self.a, max_depth=0)
        with self.assertRaises(ValueError):
            o42.semantic_release_tree_sha256(self.a, max_entries=0)

    def test_root_is_not_accepted_as_symlink(self):
        (self.a / "link").symlink_to(self.b, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "real directory"):
            self.hash(self.a / "link")


if __name__ == "__main__":
    unittest.main()
