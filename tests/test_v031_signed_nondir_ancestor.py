"""Signed-r24 tree-topology court: file ancestors must not cause partial extraction.

A real Builder produces physical bytes. Only the MessagePack logical rows change;
both indexes, header and footer receive fresh valid SHA-256 commitments.
Same immutable adversarial test runs on baseline and candidate.
"""
from __future__ import annotations

from pathlib import Path

import msgpack
import pytest

from cmpct.builder import Builder
from cmpct.codec import FMAGIC, FTR, HDR, K_DIR, K_HARDLINK, MAGIC, sha, zc, zd
from cmpct.reader import CMPCT


def _signed_reindex(original: Path, target: Path, edit) -> None:
    """Replace both authenticated r24 indexes without changing a single blob byte."""
    physical = original.read_bytes()
    magic, version, flags, cs, us, data_size, original_hash = HDR.unpack_from(physical)
    assert magic == MAGIC and version == 24
    decoded = zd(physical[HDR.size:HDR.size + cs], us)
    assert sha(decoded) == original_hash
    index = msgpack.unpackb(decoded, raw=False)
    edit(index)
    new_plain = msgpack.packb(index, use_bin_type=True)
    new_index = zc(new_plain, 12)
    new_hash = sha(new_plain)
    physical_blobs = physical[HDR.size + cs:HDR.size + cs + data_size]
    assert len(physical_blobs) == data_size
    target.write_bytes(
        HDR.pack(MAGIC, version, flags, len(new_index), len(new_plain), data_size, new_hash)
        + new_index + physical_blobs + new_index
        + FTR.pack(FMAGIC, 0, 1, 0, 0, len(new_index), len(new_plain), 0, new_hash)
    )
    # A wire-authentic fixture needs both copies consistent and physical bytes unchanged.
    produced = target.read_bytes()
    hdr = HDR.unpack_from(produced)
    assert hdr[-1] == new_hash
    assert produced[HDR.size + hdr[3]:HDR.size + hdr[3] + data_size] == physical_blobs
    assert produced[HDR.size:HDR.size + len(new_index)] == (
        produced[-FTR.size - len(new_index):-FTR.size]
    )


def _physical_source(tmp_path: Path) -> Path:
    root = tmp_path / "physical"
    root.mkdir()
    (root / "parent.bin").write_bytes(b"PARENT-EXACT-ONE")
    (root / "child.bin").write_bytes(b"CHILD-EXACT-TWO")
    archive = tmp_path / "original.cmpct"
    Builder(root, workers=1, reproducible=True).build(archive)
    return archive


@pytest.mark.parametrize("descendant", [
    "parent.bin/child.bin",
    "parent.bin/subdirectory/child.bin",
])
def test_signed_regular_parent_cannot_leave_partial_output(
    tmp_path: Path, descendant: str,
) -> None:
    base = _physical_source(tmp_path)
    hostile = tmp_path / "signed_hostile.cmpct"

    def mutate(index):
        for row in index["files"]:
            if row[0] == "child.bin":
                row[0] = descendant
        index["files"].sort(key=lambda row: row[0])

    _signed_reindex(base, hostile, mutate)
    with CMPCT(hostile) as reader:
        # The individual records are valid and exact. The defect is topology.
        assert reader.read("parent.bin") == b"PARENT-EXACT-ONE"
        assert reader.read(descendant) == b"CHILD-EXACT-TWO"
        out = tmp_path / "out"
        with pytest.raises(OSError):
            reader.extractall(out, metadata=False)
        assert out.is_dir()
        assert list(out.iterdir()) == [], (
            "a signed impossible file tree must fail before publishing any member"
        )


def test_signed_implicit_directory_parent_remains_extractable(tmp_path: Path) -> None:
    root = tmp_path / "valid_tree"
    (root / "folder" / "sub").mkdir(parents=True)
    (root / "folder" / "sub" / "payload.txt").write_bytes(b"EXACT-CHILD")
    (root / "other.bin").write_bytes(b"EXACT-ROOT")
    base = tmp_path / "base.cmpct"
    Builder(root, workers=1, reproducible=True).build(base)
    implicit = tmp_path / "implicit.cmpct"

    def remove_explicit_directories(index):
        index["files"] = [row for row in index["files"] if row[1] != K_DIR]

    _signed_reindex(base, implicit, remove_explicit_directories)
    with CMPCT(implicit) as reader:
        out = tmp_path / "out"
        reader.extractall(out, metadata=False)
        assert (out / "folder" / "sub" / "payload.txt").read_bytes() == b"EXACT-CHILD"
        assert (out / "other.bin").read_bytes() == b"EXACT-ROOT"


def test_original_builder_archive_and_directory_parent_preserved(tmp_path: Path) -> None:
    root = tmp_path / "normal"
    (root / "folder").mkdir(parents=True)
    (root / "folder" / "nested.txt").write_bytes(b"VALID-NESTED")
    (root / "folder.txt").write_bytes(b"VALID-SIBLING")
    path = tmp_path / "normal.cmpct"
    Builder(root, workers=1, reproducible=True).build(path)
    with CMPCT(path) as reader:
        out = tmp_path / "out"
        reader.extractall(out, metadata=False)
        assert (out / "folder" / "nested.txt").read_bytes() == b"VALID-NESTED"
        assert (out / "folder.txt").read_bytes() == b"VALID-SIBLING"


def test_signed_hardlink_parent_cannot_leave_partial_output(tmp_path: Path) -> None:
    # Held-out O1: an archive hardlink is a real *file*, never a directory.
    # Construct a genuine physical r24 file pair, then authenticate an added
    # logical alias alongside a physical child whose path crosses that alias.
    base = _physical_source(tmp_path)
    hostile = tmp_path / "hardlink_parent.cmpct"
    child = "alias.bin/child.bin"

    def mutate(index):
        parent = next(row for row in index["files"] if row[0] == "parent.bin")
        assert parent[1] != K_DIR
        for row in index["files"]:
            if row[0] == "child.bin":
                row[0] = child
        index["files"].append([
            "alias.bin", K_HARDLINK, parent[2], parent[3],
            parent[4], None, ["parent.bin"],
        ])
        index["files"].sort(key=lambda row: row[0])

    _signed_reindex(base, hostile, mutate)
    with CMPCT(hostile) as reader:
        assert reader.read("parent.bin") == b"PARENT-EXACT-ONE"
        assert reader.read("alias.bin") == b"PARENT-EXACT-ONE"
        assert reader.read(child) == b"CHILD-EXACT-TWO"
        out = tmp_path / "out"
        with pytest.raises(OSError, match="non-directory archive ancestor"):
            reader.extractall(out, metadata=False)
        assert out.is_dir() and list(out.iterdir()) == []


def test_signed_valid_hardlink_alias_preserves_inode_sharing(tmp_path: Path) -> None:
    base = _physical_source(tmp_path)
    signed = tmp_path / "hardlink_valid.cmpct"

    def mutate(index):
        parent = next(row for row in index["files"] if row[0] == "parent.bin")
        index["files"].append([
            "alias.bin", K_HARDLINK, parent[2], parent[3],
            parent[4], None, ["parent.bin"],
        ])
        index["files"].sort(key=lambda row: row[0])

    _signed_reindex(base, signed, mutate)
    with CMPCT(signed) as reader:
        out = tmp_path / "out"
        reader.extractall(out, metadata=False)
        assert (out / "alias.bin").read_bytes() == b"PARENT-EXACT-ONE"
        assert (out / "child.bin").read_bytes() == b"CHILD-EXACT-TWO"
        import os
        assert os.path.samefile(out / "parent.bin", out / "alias.bin")
