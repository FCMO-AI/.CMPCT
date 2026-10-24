"""Hostile, independent filesystem-semantics evidence (Issue #312)."""

from __future__ import annotations

import importlib.util
import hashlib
import ast
import random
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("v031_fs_oracle", ROOT / "tools" / "v031_fs_semantics_oracle.py")
assert SPEC and SPEC.loader
ORACLE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ORACLE)
sha = ORACLE.semantic_tree_digest_v1


class SemanticTreeDigestCourt(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.left = Path(self.tmp.name) / "a"
        self.right = Path(self.tmp.name) / "b"
        self.left.mkdir()
        self.right.mkdir()

    def symlink(self, root: Path, link: str, target: str, *, is_dir: bool = False) -> None:
        try:
            (root / link).symlink_to(target, target_is_directory=is_dir)
        except (OSError, NotImplementedError) as exc:
            self.skipTest(f"symbolic links unavailable: {exc}")

    def hardlink(self, src: Path, dst: Path) -> None:
        try:
            os.link(src, dst)
        except (OSError, NotImplementedError) as exc:
            self.skipTest(f"hardlinks unavailable: {exc}")

    def test_identical_trees_have_identical_hashes(self):
        for root in (self.left, self.right):
            (root / "dir").mkdir()
            (root / "dir" / "file.bin").write_bytes(b"abc\x00\xff")
            (root / "empty").mkdir()
        self.assertEqual(sha(self.left), sha(self.right))

    def test_file_symlink_vs_identical_regular_bytes(self):
        for root in (self.left, self.right):
            (root / "target.txt").write_bytes(b"ABC")
        self.symlink(self.left, "alias", "target.txt")
        (self.right / "alias").write_bytes(b"ABC")
        self.assertNotEqual(sha(self.left), sha(self.right))

    def test_directory_symlink_vs_real_directory(self):
        for root in (self.left, self.right):
            (root / "adir").mkdir()
        self.symlink(self.left, "dirlink", "adir", is_dir=True)
        (self.right / "dirlink").mkdir()
        self.assertNotEqual(sha(self.left), sha(self.right))

    def test_hardlink_group_vs_independent_copy(self):
        for root in (self.left, self.right):
            (root / "original").write_bytes(b"payload")
        self.hardlink(self.left / "original", self.left / "alias")
        (self.right / "alias").write_bytes(b"payload")
        self.assertEqual((self.left / "original").stat().st_ino,
                         (self.left / "alias").stat().st_ino)
        self.assertNotEqual((self.right / "original").stat().st_ino,
                            (self.right / "alias").stat().st_ino)
        self.assertNotEqual(sha(self.left), sha(self.right))

    def test_equivalent_hardlink_groups_across_different_inodes(self):
        for root in (self.left, self.right):
            (root / "original").write_bytes(b"payload")
            self.hardlink(root / "original", root / "alias")
        self.assertEqual(sha(self.left), sha(self.right))

    def test_equal_link_counts_with_different_partition_membership(self):
        # Every path has byte-identical payload, and each tree has two
        # two-member hardlink groups; only the equivalence classes differ.
        for p in ("a", "c"):
            (self.left / p).write_bytes(b"same")
        self.hardlink(self.left / "a", self.left / "b")
        self.hardlink(self.left / "c", self.left / "d")
        for p in ("a", "b"):
            (self.right / p).write_bytes(b"same")
        self.hardlink(self.right / "a", self.right / "c")
        self.hardlink(self.right / "b", self.right / "d")
        self.assertNotEqual(sha(self.left), sha(self.right))

    def test_nested_hardlink_equivalence_is_path_order_independent(self):
        for root in (self.left, self.right):
            (root / "nested").mkdir()
            (root / "z.bin").write_bytes(b"long shared payload")
            self.hardlink(root / "z.bin", root / "nested" / "alias.bin")
        self.assertEqual(sha(self.left), sha(self.right))
        (self.right / "nested" / "alias.bin").unlink()
        (self.right / "nested" / "alias.bin").write_bytes(b"long shared payload")
        self.assertNotEqual(sha(self.left), sha(self.right))

    def test_symlinks_outside_tree_are_not_followed(self):
        external = Path(self.tmp.name) / "outside.txt"
        external.write_bytes(b"private")
        self.symlink(self.left, "external", str(external))
        self.symlink(self.right, "external", str(external))
        first = sha(self.left)
        external.write_bytes(b"changed")
        self.assertEqual(first, sha(self.left))
        self.assertEqual(sha(self.left), sha(self.right))

    def test_dangling_symlink_target_is_committed(self):
        self.symlink(self.left, "alias", "nothing-here")
        self.symlink(self.right, "alias", "different-missing-target")
        self.assertNotEqual(sha(self.left), sha(self.right))

    def test_directory_symlink_cycle_is_not_walked(self):
        for root in (self.left, self.right):
            (root / "a").mkdir()
            self.symlink(root, "a/back", "..", is_dir=True)
        self.assertEqual(sha(self.left), sha(self.right))

    def test_different_contents_and_names_change_hash(self):
        (self.left / "alpha").write_bytes(b"ABC")
        (self.right / "alpha").write_bytes(b"ABD")
        self.assertNotEqual(sha(self.left), sha(self.right))
        (self.right / "alpha").unlink()
        (self.right / "beta").write_bytes(b"ABC")
        self.assertNotEqual(sha(self.left), sha(self.right))

    def test_path_component_structure_is_not_flattened(self):
        (self.left / "a").mkdir()
        (self.left / "a" / "b").write_bytes(b"same")
        (self.right / "a").write_bytes(b"same")
        (self.right / "b").mkdir()
        self.assertNotEqual(sha(self.left), sha(self.right))

    def test_limits_fail_closed(self):
        (self.left / "a").mkdir()
        (self.left / "a" / "b").write_bytes(b"x")
        with self.assertRaisesRegex(ValueError, "entry budget"):
            sha(self.left, max_entries=1)
        with self.assertRaisesRegex(ValueError, "depth budget"):
            sha(self.left, max_depth=0)
        with self.assertRaisesRegex(ValueError, "byte budget"):
            sha(self.left, max_path_bytes=1)
        with self.assertRaises(ValueError):
            sha(self.left, max_entries=-1)

    def test_wide_directory_budget_rejects_before_reading_payload(self):
        # A limit checked *after* sorted(scandir(...)) is ineffective
        # against a directory containing more entries than the budget.
        for n in range(7):
            (self.left / f"entry-{n:02d}").write_bytes(b"PAYLOAD")
        from unittest.mock import patch
        with patch.object(ORACLE.os, "open",
                          side_effect=AssertionError("payload should not be opened")):
            with self.assertRaisesRegex(ValueError, "entry budget"):
                sha(self.left, max_entries=3)

    def test_path_budget_rejects_before_payload_open(self):
        (self.left / "oversized-filename.bin").write_bytes(b"PAYLOAD")
        from unittest.mock import patch
        with patch.object(ORACLE.os, "open",
                          side_effect=AssertionError("payload should not be opened")):
            with self.assertRaisesRegex(ValueError, "byte budget"):
                sha(self.left, max_path_bytes=2)

    def test_root_symlink_is_not_accepted(self):
        self.symlink(self.left, "rootlink", str(self.right), is_dir=True)
        with self.assertRaisesRegex(ValueError, "real directory"):
            sha(self.left / "rootlink")

    @unittest.skipUnless(os.name == "posix", "raw POSIX path bytes only")
    def test_non_utf8_path_name_and_symlink_target_bytes(self):
        raw = os.fsencode(self.left) + b"/raw-\xff"
        fd = os.open(raw, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        os.write(fd, b"x")
        os.close(fd)
        os.symlink(b"raw-\xff", os.fsencode(self.left) + b"/link")
        raw2 = os.fsencode(self.right) + b"/raw-\xff"
        fd = os.open(raw2, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        os.write(fd, b"x")
        os.close(fd)
        os.symlink(b"raw-\xff", os.fsencode(self.right) + b"/link")
        self.assertEqual(sha(self.left), sha(self.right))
        os.unlink(os.fsencode(self.right) + b"/link")
        os.symlink(b"raw-\xfe", os.fsencode(self.right) + b"/link")
        self.assertNotEqual(sha(self.left), sha(self.right))

    @unittest.skipUnless(hasattr(os, "mkfifo"), "FIFO unsupported")
    def test_special_entry_rejected_not_silently_skipped(self):
        os.mkfifo(self.left / "pipe")
        with self.assertRaises(ORACLE.UnsupportedFilesystemEntry):
            sha(self.left)

    def test_independent_manifest_crosscheck_on_held_out_mixtures(self):
        """A differently routed manifest checks types/contents/equivalence.

        This comparator uses pathlib walk + lstat, not the oracle's scandir
        traversal or serialization. It covers stable trees only.
        """
        def manifest(root):
            entries = []
            for p in sorted(root.rglob("*"), key=lambda x: os.fsencode(x.relative_to(root).as_posix())):
                relative = os.fsencode(p.relative_to(root).as_posix())
                mode = p.lstat().st_mode
                if p.is_symlink():
                    entries.append((relative, "L", os.fsencode(os.readlink(p))))
                elif p.is_dir():
                    entries.append((relative, "D", b""))
                elif p.is_file():
                    st = p.stat()
                    entries.append((relative, "F", hashlib.sha256(p.read_bytes()).digest(),
                                    (st.st_dev, st.st_ino)))
                else:
                    raise AssertionError("unsupported in held-out manifest")
            identity = {}
            normalized = []
            for entry in entries:
                if entry[1] == "F":
                    key = entry[3]
                    if key not in identity:
                        identity[key] = len(identity)
                    normalized.append(entry[:3] + (identity[key],))
                else:
                    normalized.append(entry)
            return tuple(normalized)

        rng = random.Random(312266)
        for case in range(90):
            for root in (self.left, self.right):
                for node in root.iterdir():
                    if node.is_dir() and not node.is_symlink():
                        import shutil
                        shutil.rmtree(node)
                    else:
                        node.unlink()
            # Generate ONCE for both roots. Otherwise any changed name/link
            # trivially compares two unrelated byte corpora instead of isolating
            # the single structural difference under test.
            common_payloads = [rng.randbytes(rng.randrange(0, 60))
                               for _ in range(rng.randrange(1, 8))]
            for root in (self.left, self.right):
                (root / "nested").mkdir()
                for n, payload in enumerate(common_payloads):
                    (root / "nested" / f"data{n}").write_bytes(payload)
                (root / "root").write_bytes(b"same bytes")
            if case % 3 == 0:
                self.hardlink(self.left / "root", self.left / "extra")
                (self.right / "extra").write_bytes(b"same bytes")
            elif case % 3 == 1:
                self.symlink(self.left, "extra", "root")
                (self.right / "extra").write_bytes(b"same bytes")
            else:
                for root in (self.left, self.right):
                    self.symlink(root, "extra", "root")
            self.assertEqual(sha(self.left) == sha(self.right),
                             manifest(self.left) == manifest(self.right),
                             f"independent manifest mismatch on case {case}")

    def test_original_source_helper_false_equivalence_is_distinguished(self):
        """Execute the repository's *actual* legacy function body via AST.

        Don't require the legacy defect to persist: once owners fix it this
        court must continue to validate the stronger oracle.
        """
        source = ROOT / "src" / "cmpct" / "transactions.py"
        if not source.exists():
            self.skipTest("source checkout missing")
        module = ast.parse(source.read_text(encoding="utf-8"))
        funcs = [node for node in module.body
                 if isinstance(node, ast.FunctionDef) and node.name == "tree_digest"]
        self.assertEqual(len(funcs), 1)
        stand_alone = ast.Module(body=funcs, type_ignores=[])
        ast.fix_missing_locations(stand_alone)
        import struct
        scope = {"Path": Path, "hashlib": hashlib, "struct": struct, "os": os}
        exec(compile(stand_alone, str(source), "exec"), scope)
        legacy = scope["tree_digest"]
        for root in (self.left, self.right):
            (root / "target").write_bytes(b"ABC")
        self.symlink(self.left, "alias", "target")
        (self.right / "alias").write_bytes(b"ABC")
        self.assertNotEqual(sha(self.left), sha(self.right))
        # The legacy helper has a known false equality on current sources;
        # when repaired, don't make the improved behavior a test failure.
        self.assertIsInstance(legacy(self.left) == legacy(self.right), bool)

    def test_real_r24_archive_preserves_typed_tree_and_hardlink_partition(self):
        # Unlike a digest-only comparison, this exercises the *real* Builder
        # and Reader on a held-out mixed tree. In standalone stdlib-only courts
        # the installed package is intentionally unavailable; general CMPCT
        # CI must exercise this test against its actual package installation.
        try:
            from cmpct.core import Builder, CMPCT
        except ModuleNotFoundError as exc:
            if exc.name in ("cmpct", "cmpct.core"):
                self.skipTest("real installed CMPCT package unavailable in stdlib-only court")
            raise
        (self.left / "nested").mkdir()
        (self.left / "nested" / "data.bin").write_bytes(b"real r24 exact test" * 256)
        self.hardlink(self.left / "nested" / "data.bin", self.left / "a-hard.bin")
        self.symlink(self.left, "file-link", "nested/data.bin")
        self.symlink(self.left, "directory-link", "nested", is_dir=True)
        expected = sha(self.left)
        archive = Path(self.tmp.name) / "authentic.cmpct"
        Builder(self.left, workers=1).build(archive)
        with CMPCT(archive) as reader:
            self.assertTrue(reader.verify())
            reader.extractall(self.right, metadata=False)
        self.assertEqual(sha(self.right), expected)
        self.assertTrue((self.right / "file-link").is_symlink())
        self.assertTrue((self.right / "directory-link").is_symlink())
        self.assertEqual(os.readlink(self.right / "file-link"), "nested/data.bin")
        self.assertEqual(os.readlink(self.right / "directory-link"), "nested")
        owner = (self.right / "nested" / "data.bin").stat()
        alias = (self.right / "a-hard.bin").stat()
        self.assertEqual((owner.st_dev, owner.st_ino), (alias.st_dev, alias.st_ino))

    def test_large_file_hash_is_chunked(self):
        for root in (self.left, self.right):
            with (root / "data").open("wb") as f:
                f.write(b"z" * ((1 << 20) + 117))
        self.assertEqual(sha(self.left), sha(self.right))
        with (self.right / "data").open("r+b") as f:
            f.seek((1 << 20) + 1)
            f.write(b"q")
        self.assertNotEqual(sha(self.left), sha(self.right))


if __name__ == "__main__":
    unittest.main()
