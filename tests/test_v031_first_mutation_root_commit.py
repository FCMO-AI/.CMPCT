"""Builder-independent first-mutation recovery contract for revision-24 primary-only archives.
The builder constructs the ordinary source archive, then its redundant footer/checkpoint
copy is removed. The authenticated primary index and indexed physical blobs remain unchanged.
"""
from __future__ import annotations
import tempfile
import unittest
from pathlib import Path
from cmpct.builder import Builder
from cmpct.reader import CMPCT
from cmpct.codec import FTR
from cmpct.validation import preflight_archive
from cmpct.transactions import append_delete, append_rename, append_update

class FirstMutationRootCommit(unittest.TestCase):
    def make_archive(self, root):
        src = root / "source"
        src.mkdir()
        (src / "alpha.txt").write_bytes(b"old-content")
        archive = root / "test.cmpct"
        Builder(src, reproducible=True).build(archive)
        raw = archive.read_bytes()
        magic, kind, codec, flags, reserved, cs, us, parent, digest = FTR.unpack(raw[-FTR.size:])
        self.assertEqual(kind, 0)
        self.assertEqual(parent, 0)
        self.assertGreater(len(raw) - FTR.size - cs, 0)
        archive.write_bytes(raw[:len(raw) - FTR.size - cs])
        preflight_archive(archive)
        with CMPCT(archive) as ar:
            self.assertEqual(ar.latest_footer_pos, 0)
            self.assertEqual(ar.read("alpha.txt"), b"old-content")
        return archive

    def test_first_delete(self):
        with tempfile.TemporaryDirectory() as td:
            ar = self.make_archive(Path(td))
            append_delete(ar, "alpha.txt")
            preflight_archive(ar)
            with CMPCT(ar) as reader:
                self.assertNotIn("alpha.txt", reader.by)

    def test_first_rename(self):
        with tempfile.TemporaryDirectory() as td:
            ar = self.make_archive(Path(td))
            append_rename(ar, "alpha.txt", "beta.txt")
            preflight_archive(ar)
            with CMPCT(ar) as reader:
                self.assertNotIn("alpha.txt", reader.by)
                self.assertEqual(reader.read("beta.txt"), b"old-content")

    def test_first_update(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            ar = self.make_archive(root)
            replacement = root / "replacement.txt"
            replacement.write_bytes(b"new-content")
            append_update(ar, "alpha.txt", replacement)
            preflight_archive(ar)
            with CMPCT(ar) as reader:
                self.assertEqual(reader.read("alpha.txt"), b"new-content")

if __name__ == "__main__":
    unittest.main()
