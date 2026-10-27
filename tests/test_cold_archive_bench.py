"""Exercise the independent hash oracle and pipeline failure accounting."""
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest


def load(name):
    path = Path(__file__).resolve().parents[1] / "benchmarks" / (name + ".py")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


bench = load("cold_archive_bench")
corpus = load("cold_tree_corpus")


class ColdArchiveBenchTests(unittest.TestCase):
    def test_trusted_links_never_authorize_link_parent_pivots(self):
        bench.check_no_link_parents({"link": ["l", "/outside"], "member": ["f", 0, "hash"]})
        with self.assertRaisesRegex(ValueError, "parent"):
            bench.check_no_link_parents({"link": ["l", "/outside"], "link/member": ["f", 0, "hash"]})

    @unittest.skipUnless(Path("/usr/bin/time").is_file(), "Linux benchmark requires GNU time")
    def test_upstream_failure_cannot_look_like_pipeline_success(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(RuntimeError, r"\[7, 0\]"):
                bench.timed_pipeline([
                    [sys.executable, "-c", "raise SystemExit(7)"],
                    [sys.executable, "-c", "import sys; sys.stdin.buffer.read()"],
                ], Path(td), "failed-upstream")

    def test_manifest_detects_mutation_missing_extra_and_link_target(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            p = root / "member"
            p.write_bytes(b"before")
            link = root / "link"
            link.symlink_to("member")
            before = bench.manifest(root)
            p.write_bytes(b"after!")  # Same length, different digest.
            self.assertNotEqual(before, bench.manifest(root))
            p.write_bytes(b"before")
            link.unlink()
            link.symlink_to("other")
            self.assertNotEqual(before, bench.manifest(root))
            link.unlink()
            link.symlink_to("member")
            (root / "extra").write_bytes(b"")
            self.assertNotEqual(before, bench.manifest(root))
            (root / "extra").unlink()
            p.unlink()
            self.assertNotEqual(before, bench.manifest(root))

    def test_work_inside_source_is_refused_before_writing(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            with self.assertRaisesRegex(ValueError, "disjoint"):
                bench.measure(root, root / "work", ["zstd"])
            self.assertFalse((root / "work").exists())

    def test_public_generator_is_seeded_and_preserves_losing_controls(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            a = corpus.generate(root / "a", files=16, stages=2)
            b = corpus.generate(root / "b", files=16, stages=2)
            self.assertEqual(bench.manifest(a), bench.manifest(b))
            self.assertEqual((a / "snapshot-00/object-00001.dat").read_bytes(),
                             (a / "snapshot-01/object-00001.dat").read_bytes())
            self.assertNotEqual((a / "snapshot-00/object-00000.dat").read_bytes(),
                                (a / "snapshot-01/object-00000.dat").read_bytes())

    def test_scaled_analogue_reuses_content_across_names_and_keeps_edits(self):
        with tempfile.TemporaryDirectory() as td:
            root = corpus.generate(Path(td) / "tree", files=24, copies_per_object=2,
                                   files_per_dir=4, event_multiplier=8, block_bytes=1024, links_per_stage=8)
            a = root / "snapshot-00/group-00000"
            self.assertEqual((a / "object-00000.dat").read_bytes(), (a / "object-00001.dat").read_bytes())
            self.assertNotEqual((a / "object-00000.dat").read_bytes(),
                                (root / "snapshot-01/group-00000/object-00000.dat").read_bytes())
            self.assertEqual(sum(r[0] == "f" for r in bench.manifest(root).values()), 4 * (24 + 14))
            rows = bench.manifest(root)
            self.assertEqual(sum(r[0] == "l" for r in rows.values()), 32)
            bench.check_no_link_parents(rows)


if __name__ == "__main__":
    unittest.main()
