"""J24E05: authentic revision-24 wire transfer of the J24E01 research-only effect proof.

The two link archives and VZIP archive are Builder-independent, SHA-frozen
existing CMPCT conformance vectors, not newly generated favorable fixtures.
No model, Reader, Builder, admission or release behavior is modified here.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import stat
import tempfile
import time
import unittest
from pathlib import Path

import msgpack
import zstandard

from cmpct.codec import FTR, FMAGIC, HDR, MAGIC, K_DIR
from cmpct.reader import CMPCT
from cmpct.validation import preflight_archive
from research.j24e01_extract_effects_model import UnprovedEffect, planned_logical_bytes

ROOT = Path(__file__).resolve().parents[1]
LINK_MANIFEST = ROOT / "research" / "data" / "j24e05_v24_link_tree.json"
VZIP_MANIFEST = ROOT / "tests" / "conformance" / "v24-virtual-zip.json"

OWNER = "tree/00-owner.bin"
ALIAS = "tree/10-alias.bin"
SYMLINK = "tree/20-link"

LINK_EXPECTED = {
    "links-raw": (934, "1d1e102349095151312cc3efa49a8da7848453d1a322c95a537e3d0307c0e03c"),
    "links-zstd": (952, "afaea969c1cd1bf185c730adfd1d1d31e36449dbc2c1f3a5f45b1ac5d7a96b1f"),
}
VZIP_EXPECTED = (642, "bed3a5d3bf3987f4c123e782effe9cc21a5d7253a9b2eca8a9af7b2522f4d839")
SHA = lambda raw: hashlib.sha256(raw).hexdigest()


def link_vectors():
    d = json.loads(LINK_MANIFEST.read_text(encoding="utf-8"))
    if d["schema"] != "cmpct-v24-fixed-link-tree-wire-v1":
        raise AssertionError("donor schema changed")
    if len(d["vectors"]) != 2:
        raise AssertionError("donor vector count changed")
    return d["vectors"]


def decode_link(v):
    size, digest = LINK_EXPECTED[v["name"]]
    wire = base64.b64decode(v["archive_base64"], validate=True)
    assert len(wire) == size == v["archive_bytes"]
    assert SHA(wire) == digest == v["archive_sha256"]
    return wire


def reauthenticate_row_length(wire, entry, new_size):
    """Change exactly one index row and both unkeyed SHA indexes; retain physical records.

    The result is not a digitally signed archive. This is a hostile but
    SHA-consistent on-disk semantic contradiction, not a crypto attack.
    """
    magic, rev, flags, csize, usize, span, digest = HDR.unpack_from(wire)
    assert magic == MAGIC and rev == 24
    raw_index = zstandard.ZstdDecompressor().decompress(
        wire[HDR.size:HDR.size + csize], max_output_size=usize
    )
    assert hashlib.sha256(raw_index).digest() == digest
    index = msgpack.unpackb(raw_index, raw=False)
    by_name = {row[0]: row for row in index["files"]}
    assert entry in by_name and by_name[entry][4] > new_size >= 0
    by_name[entry][4] = new_size
    encoded_index_bytes = msgpack.packb(index, use_bin_type=True)
    compressed = zstandard.ZstdCompressor(level=12).compress(encoded_index_bytes)
    index_sha = hashlib.sha256(encoded_index_bytes).digest()
    record = wire[HDR.size + csize:HDR.size + csize + span]
    assert len(record) == span
    assert wire[-FTR.size:].startswith(FMAGIC)
    out = (
        HDR.pack(MAGIC, rev, flags, len(compressed), len(encoded_index_bytes), span, index_sha)
        + compressed
        + record
        + compressed
        + FTR.pack(FMAGIC, 0, 1, 0, 0, len(compressed), len(encoded_index_bytes), 0, index_sha)
    )
    assert out != wire
    assert out[HDR.size + len(compressed):HDR.size + len(compressed) + span] == record
    return out


class AuthenticWireEffectsCourt(unittest.TestCase):
    def test_two_builder_independent_link_trees_admit_exact_budget(self):
        for v in link_vectors():
            with self.subTest(codec=v["name"]), tempfile.TemporaryDirectory() as root:
                root = Path(root)
                archive = root / "source.cmpct"
                archive.write_bytes(decode_link(v))
                proof = preflight_archive(archive)
                self.assertEqual(proof["files"], 4)
                owner = bytes.fromhex(v["owner_hex"])
                target = bytes.fromhex(v["link_hex"])
                self.assertEqual(len(owner), 100)
                self.assertEqual(len(target), 12)
                # Independent oracle from immutable original logical payloads.
                want = 2 * len(owner) + len(target)
                self.assertEqual(want, 212)
                with CMPCT(archive) as reader:
                    self.assertEqual(sum(row[4] for row in reader.files if row[1] != K_DIR), want)
                    t0 = time.perf_counter()
                    self.assertEqual(planned_logical_bytes(reader.index), want)
                    print("J24E05_PROOF", v["name"], "bytes", want,
                          "wall_ms", round((time.perf_counter() - t0) * 1000, 4), flush=True)
                    self.assertEqual(reader.read(OWNER), owner)
                    self.assertEqual(reader.read(ALIAS), owner)
                    self.assertEqual(reader.read(SYMLINK), target)
                    self.assertEqual(reader.verify(), 3)
                    output = root / "legitimate"
                    try:
                        reader.extractall(output, metadata=False, max_bytes=want)
                    except OSError as exc:
                        if os.name == "nt" and getattr(exc, "winerror", None) == 1314:
                            print("J24E05_PHYSICAL_LIMITED Windows symlink privilege", flush=True)
                            continue
                        raise
                self.assertEqual((output / OWNER).read_bytes(), owner)
                self.assertEqual((output / ALIAS).read_bytes(), owner)
                self.assertTrue(os.path.samefile(output / OWNER, output / ALIAS))
                self.assertEqual(os.readlink(output / SYMLINK), target.decode())
                self.assertTrue(stat.S_ISLNK(os.lstat(output / SYMLINK).st_mode))

    def test_reauthenticated_alias_and_symlink_understatements_rejected_prewrite(self):
        for v in link_vectors():
            original = decode_link(v)
            for member, declared_total in ((SYMLINK, 200), (ALIAS, 112)):
                with self.subTest(codec=v["name"], mutated=member), tempfile.TemporaryDirectory() as root:
                    root = Path(root)
                    archive = root / "resigned.cmpct"
                    archive.write_bytes(reauthenticate_row_length(original, member, 0))
                    proof = preflight_archive(archive)
                    self.assertEqual(proof["files"], 4)
                    with CMPCT(archive) as reader:
                        self.assertEqual(reader.verify(), 3)
                        self.assertEqual(len(reader.read(OWNER)), 100)
                        self.assertEqual(len(reader.read(ALIAS)), 100)
                        self.assertEqual(len(reader.read(SYMLINK)), 12)
                        weak = sum(row[4] for row in reader.files if row[1] != K_DIR)
                        self.assertEqual(weak, declared_total)
                        self.assertLess(weak, 212)
                        untouched = root / "must-not-exist"
                        self.assertFalse(untouched.exists())
                        with self.assertRaises(UnprovedEffect):
                            planned_logical_bytes(reader.index)
                        self.assertFalse(untouched.exists())
                        print("J24E05_SIGNED_NEGATIVE", v["name"], member,
                              "declared", weak, "actual", 212,
                              "model_refused_before_mutation", True, flush=True)

    def test_independent_valid_vzip_remains_uncertifiable_by_metadata(self):
        spec = json.loads(VZIP_MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(spec["schema"], "cmpct-v24-golden-virtual-zip-v1")
        v = spec["vector"]
        wire = base64.b64decode(v["archive_base64"], validate=True)
        self.assertEqual((len(wire), SHA(wire)), VZIP_EXPECTED)
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "valid.cmpct"
            path.write_bytes(wire)
            self.assertEqual(preflight_archive(path)["files"], 1)
            with CMPCT(path) as reader:
                reconstructed = reader.read(v["name"])
                self.assertEqual(len(reconstructed), 128)
                self.assertEqual(SHA(reconstructed), v["logical_sha256"])
                self.assertEqual(reader.verify(), 1)
                self.assertEqual(sum(row[4] for row in reader.files), 128)
                with self.assertRaisesRegex(UnprovedEffect, "virtual stream length unproven"):
                    planned_logical_bytes(reader.index)
                print("J24E05_VZIP valid_real_archive", True,
                      "declared", 128, "model_uncertifiable", True, flush=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
