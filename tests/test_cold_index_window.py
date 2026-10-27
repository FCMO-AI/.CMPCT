"""Research gate: exact payload preservation, complete-byte fallback and hostile framing."""
import importlib.util
from pathlib import Path
import subprocess
import shutil
import tempfile
import unittest
from unittest.mock import patch

from cmpct.builder import Builder
from cmpct.codec import HDR
from cmpct.reader import CMPCT


spec = importlib.util.spec_from_file_location(
    "cold_index_window", Path(__file__).resolve().parents[1] / "experiments/cold_index_window.py")
experiment = importlib.util.module_from_spec(spec)
spec.loader.exec_module(experiment)


class ColdIndexWindowTests(unittest.TestCase):
    def fixture(self, root):
        source = root / "tree"
        source.mkdir()
        for stage in range(4):
            dest = source / f"stage-{stage}"
            dest.mkdir()
            for i in range(64):
                (dest / f"member-{i:04d}.txt").write_bytes(f"content-{i}\n".encode() * 30)
        archive = root / "base.cmpct"
        Builder(source, workers=1, reproducible=True).build(archive)
        return archive

    @unittest.skipUnless(shutil.which("zstd"), "research index audition requires optional zstd CLI")
    def test_rewrite_keeps_payload_and_every_logical_byte(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            base = self.fixture(root)
            output = root / "candidate.cmpct"
            result = experiment.recompress(base, output)
            self.assertTrue(result["selected"], "repeated-metadata fixture must exercise the winning rewrite")
            self.assertLess(output.stat().st_size, base.stat().st_size)
            self.assertEqual(result["payload_bytes_changed"], 0)
            def regions(path):
                b = path.read_bytes()
                header = HDR.unpack(b[:HDR.size])
                cs, us, span = header[3:6]
                index = subprocess.run(["zstd", "-q", "-d", "--long=31", "-c"],
                                       input=b[HDR.size:HDR.size + cs],
                                       stdout=subprocess.PIPE, check=True).stdout
                self.assertEqual(len(index), us)
                return index, b[HDR.size + cs:HDR.size + cs + span]
            # Independent mature codec checks raw metadata; compare the entire physical data span.
            self.assertEqual(regions(base), regions(output))
            with CMPCT(base) as old, CMPCT(output) as new:
                self.assertEqual(set(old.by), set(new.by))
                for name, row in old.by.items():
                    if row[1] == 0:
                        self.assertEqual(old.read(name), new.read(name))

    def test_losing_audition_is_exact_original_artifact(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            base = self.fixture(root)
            output = root / "candidate.cmpct"
            with patch.object(experiment.subprocess, "run", return_value=type(
                    "Result", (), {"stdout": b"unprofitable" * base.stat().st_size})()):
                result = experiment.recompress(base, output)
            self.assertFalse(result["selected"])
            self.assertEqual(base.read_bytes(), output.read_bytes())

    def test_trailing_bytes_are_not_silently_dropped(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            base = self.fixture(root)
            with base.open("ab") as f:
                f.write(b"uncommitted")
            with self.assertRaises((ValueError, IOError)):
                experiment.recompress(base, root / "output")

    def test_existing_output_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            base = self.fixture(root)
            output = root / "candidate.cmpct"
            output.write_bytes(b"keep")
            with self.assertRaisesRegex(ValueError, "must not exist"):
                experiment.recompress(base, output)
            self.assertEqual(output.read_bytes(), b"keep")

    def test_recovered_tail_does_not_authorize_rewriting_bad_primary(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            base = self.fixture(root)
            data = bytearray(base.read_bytes())
            data[HDR.size - 1] ^= 1  # Valid compressed index, invalid primary identity.
            base.write_bytes(data)
            output = root / "candidate.cmpct"
            with self.assertRaisesRegex(ValueError, "primary index identity"):
                experiment.recompress(base, output)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
