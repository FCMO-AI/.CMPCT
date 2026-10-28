"""Source-independent frozen revision-24 link-tree conformance, not a Builder roundtrip.

The archive byte strings were assembled with struct/MessagePack/system libzstd,
SHA-frozen in the manifest, then committed before any Reader test ran.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import stat
from pathlib import Path

import msgpack
import pytest
import zstandard as zstd

from cmpct.codec import FTR, FMAGIC, HDR, MAGIC, K_DIR, K_FILE, K_HARDLINK, K_SYMLINK
from cmpct.reader import CMPCT
from cmpct.validation import preflight_archive

VECTORS = Path(__file__).parent / "conformance" / "v24-link-tree.json"
OWNER = "tree/00-owner.bin"
ALIAS = "tree/10-alias.bin"
SYMLINK = "tree/20-link"
DIRECTORY = "tree"


def _vectors():
    d = json.loads(VECTORS.read_text(encoding="utf-8"))
    assert d["schema"] == "cmpct-v24-fixed-link-tree-wire-v1"
    assert d["revision"] == 24
    assert len(d["vectors"]) == 2
    assert {v["codec"] for v in d["vectors"]} == {0, 1}
    return d["vectors"]


def _source(v):
    archive = base64.b64decode(v["archive_base64"], validate=True)
    assert len(archive) == v["archive_bytes"]
    assert hashlib.sha256(archive).hexdigest() == v["archive_sha256"]
    assert archive.startswith(b"CMPCT24\0")
    return archive


@pytest.mark.parametrize("case", [0, 1])
def test_authentic_frozen_link_tree_reader_and_preflight(tmp_path, case):
    v = _vectors()[case]
    path = tmp_path / "independent.cmpct"
    path.write_bytes(_source(v))
    owner = bytes.fromhex(v["owner_hex"])
    link = bytes.fromhex(v["link_hex"])
    assert hashlib.sha256(owner).hexdigest() == v["owner_sha256"]
    assert hashlib.sha256(link).hexdigest() == v["link_sha256"]
    assert link == b"00-owner.bin"
    proof = preflight_archive(path)
    assert proof["version"] == 24
    assert proof["files"] == 4
    assert proof["blobs"] == 2
    with CMPCT(path) as reader:
        assert len(reader.blobs) == 2
        assert set(reader.by) == {DIRECTORY, OWNER, ALIAS, SYMLINK}
        assert [reader.by[p][1] for p in (DIRECTORY, OWNER, ALIAS, SYMLINK)] == [
            K_DIR, K_FILE, K_HARDLINK, K_SYMLINK,
        ]
        assert reader.by[ALIAS][6] == [OWNER]
        assert reader.by[OWNER][6] == [0, 0]
        assert reader.by[SYMLINK][6] == [0, 1]
        assert reader.blobs[0][3] == reader.blobs[1][3] == v["codec"]
        with pytest.raises(IsADirectoryError):
            reader.read(DIRECTORY)
        for name, raw in ((OWNER, owner), (ALIAS, owner), (SYMLINK, link)):
            assert reader.read(name) == raw
            assert reader.read_range(name, 0, len(raw)) == raw
            assert reader.read_range(name, 3, 7) == raw[3:10]
            assert reader.read_range(name, len(raw), 0) == b""
            with pytest.raises(ValueError):
                reader.read_range(name, len(raw) - 1, 2)
        assert reader.verify() == 3


@pytest.mark.parametrize("case", [0, 1])
def test_authentic_fixed_link_tree_filesystem_identity(tmp_path, case):
    v = _vectors()[case]
    path = tmp_path / "independent.cmpct"
    path.write_bytes(_source(v))
    destination = tmp_path / "output"
    with CMPCT(path) as reader:
        try:
            reader.extractall(destination, metadata=False, max_bytes=2 * len(bytes.fromhex(v["owner_hex"])) + len(bytes.fromhex(v["link_hex"])))
        except OSError as exc:
            # On some Windows runners OS symlink privilege is unavailable. This
            # skip covers only filesystem materialization, never Reader/preflight.
            if os.name == "nt" and getattr(exc, "winerror", None) == 1314:
                pytest.skip("Windows host lacks symlink creation privilege")
            raise
    owner = destination / OWNER
    alias = destination / ALIAS
    symlink = destination / SYMLINK
    assert owner.read_bytes() == alias.read_bytes() == bytes.fromhex(v["owner_hex"])
    assert stat.S_ISREG(os.lstat(owner).st_mode)
    assert stat.S_ISREG(os.lstat(alias).st_mode)
    assert os.path.samefile(owner, alias), "Hardlink must be an inode alias, not a byte-identical copy"
    assert symlink.is_symlink()
    assert os.readlink(symlink) == "00-owner.bin"
    assert symlink.read_bytes() == owner.read_bytes()
    assert stat.S_ISDIR(os.lstat(destination / DIRECTORY).st_mode)


def _mutated_original(v, mutation):
    wire = _source(v)
    magic, rev, flags, csize, usize, span, _digest = HDR.unpack_from(wire)
    raw = zstd.ZstdDecompressor().decompress(wire[HDR.size:HDR.size+csize], max_output_size=usize)
    data = msgpack.unpackb(raw, raw=False)
    rows = {r[0]:r for r in data["files"]}
    if mutation == "missing-hardlink-owner":
        rows[ALIAS][6][0] = "tree/absent.bin"
    elif mutation == "symlink-out-of-range-blob":
        rows[SYMLINK][6][1] = len(data["blobs"])
    else:
        raise AssertionError(mutation)
    changed = msgpack.packb(data, use_bin_type=True)
    encoded = zstd.ZstdCompressor(level=12).compress(changed)
    digest = hashlib.sha256(changed).digest()
    record = wire[HDR.size+csize:HDR.size+csize+span]
    assert len(record) == span
    result = (HDR.pack(MAGIC, rev, flags, len(encoded), len(changed), span, digest)
              + encoded + record + encoded
              + FTR.pack(FMAGIC, 0, 1, 0, 0, len(encoded), len(changed), 0, digest))
    assert result != wire
    assert record == result[HDR.size+len(encoded):HDR.size+len(encoded)+span]
    assert hashlib.sha256(result).digest() != hashlib.sha256(wire).digest()
    return result


@pytest.mark.parametrize("case", [0, 1])
@pytest.mark.parametrize("mutation", ["missing-hardlink-owner", "symlink-out-of-range-blob"])
def test_signed_wire_structural_mutants_fail_strict_admission(tmp_path, case, mutation):
    v = _vectors()[case]
    path = tmp_path / "mutated.cmpct"
    path.write_bytes(_mutated_original(v, mutation))
    # Both indexes are rehashed. The missing reference is structural invalidity,
    # not a failed SHA calculation or a forged digital signature.
    with pytest.raises((IOError, ValueError)):
        preflight_archive(path)
