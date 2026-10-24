"""Source-exact r24 structural preflight court for authenticated impossible trees.

A genuine Builder produces physical member bytes; only index file rows are
changed and both index copies plus their SHA commitments are reauthenticated.
The same assertions must run unchanged before and after the implementation.
"""
from __future__ import annotations

from pathlib import Path

import msgpack
import pytest

from cmpct.builder import Builder
from cmpct.codec import (
    FMAGIC, FTR, HDR, K_DIR, K_HARDLINK, MAGIC, sha, zc, zd,
)
from cmpct.reader import CMPCT
from cmpct.validation import ValidationError, preflight_archive


def _source(tmp_path: Path) -> Path:
    root = tmp_path / "input"
    root.mkdir()
    (root / "parent.bin").write_bytes(b"PHYSICAL-OWNER")
    (root / "child.bin").write_bytes(b"PHYSICAL-CHILD")
    archive = tmp_path / "original.cmpct"
    Builder(root, workers=1, reproducible=True).build(archive)
    return archive


def _resign(source: Path, target: Path, mutate) -> bytes:
    """Modify only logical rows, re-sign both copies, preserve physical bytes."""
    original = source.read_bytes()
    magic, version, flags, compressed_size, raw_size, data_size, commitment = HDR.unpack_from(original)
    assert magic == MAGIC and version == 24
    plain = zd(original[HDR.size:HDR.size + compressed_size], raw_size)
    assert sha(plain) == commitment
    index = msgpack.unpackb(plain, raw=False)
    mutate(index)
    new_plain = msgpack.packb(index, use_bin_type=True)
    new_compressed = zc(new_plain, 12)
    new_commitment = sha(new_plain)
    physical = original[HDR.size + compressed_size:HDR.size + compressed_size + data_size]
    assert len(physical) == data_size
    target.write_bytes(
        HDR.pack(MAGIC, version, flags, len(new_compressed), len(new_plain), data_size, new_commitment)
        + new_compressed + physical + new_compressed
        + FTR.pack(FMAGIC, 0, 1, 0, 0, len(new_compressed), len(new_plain), 0, new_commitment)
    )
    wire = target.read_bytes()
    assert wire[HDR.size + len(new_compressed):HDR.size + len(new_compressed) + data_size] == physical
    assert wire[HDR.size:HDR.size + len(new_compressed)] == wire[-FTR.size - len(new_compressed):-FTR.size]
    assert HDR.unpack_from(wire)[-1] == new_commitment
    return physical


@pytest.mark.parametrize("shape,child,reverse", [
    ("regular", "parent.bin/child.bin", False),
    ("regular", "parent.bin/child.bin", True),
    ("regular", "parent.bin/sub/child.bin", False),
    ("hardlink", "z_alias.bin/child.bin", False),
    ("hardlink", "z_alias.bin/sub/child.bin", True),
])
def test_strict_preflight_refuses_authenticated_impossible_tree_before_extract(
    tmp_path: Path, shape: str, child: str, reverse: bool,
) -> None:
    original = _source(tmp_path)
    hostile = tmp_path / "hostile.cmpct"

    def mutate(index):
        owner = next(row for row in index["files"] if row[0] == "parent.bin")
        for row in index["files"]:
            if row[0] == "child.bin":
                row[0] = child
        if shape == "hardlink":
            index["files"].append([
                "z_alias.bin", K_HARDLINK, owner[2], owner[3], owner[4],
                None, ["parent.bin"],
            ])
        index["files"].sort(key=lambda row: row[0], reverse=reverse)

    _resign(original, hostile, mutate)

    # Real Reader can still read independently valid bytes, even though the
    # signed logical tree is not one coherent filesystem hierarchy.
    with CMPCT(hostile) as reader:
        assert reader.read("parent.bin") == b"PHYSICAL-OWNER"
        assert reader.read(child) == b"PHYSICAL-CHILD"
        if shape == "hardlink":
            assert reader.read("z_alias.bin") == b"PHYSICAL-OWNER"
        out = tmp_path / "out"
        with pytest.raises(OSError, match="non-directory archive ancestor"):
            reader.extractall(out, metadata=False)
        assert out.is_dir() and list(out.iterdir()) == []

    # This is the primary claim. Before the candidate change the strict
    # validator accepts the same authenticated impossible hierarchy.
    with pytest.raises(ValidationError, match="non-directory archive ancestor"):
        preflight_archive(hostile)


def test_valid_explicit_and_implicit_directories_remain_preflightable(tmp_path: Path) -> None:
    root = tmp_path / "tree"
    (root / "dir" / "sub").mkdir(parents=True)
    (root / "dir" / "sub" / "payload.bin").write_bytes(b"EXACT-CONTENT")
    original = tmp_path / "original.cmpct"
    Builder(root, workers=1, reproducible=True).build(original)
    assert preflight_archive(original)["files"] >= 1

    implicit = tmp_path / "implicit.cmpct"
    _resign(
        original, implicit,
        lambda index: index.__setitem__(
            "files", [row for row in index["files"] if row[1] != K_DIR],
        ),
    )
    assert preflight_archive(implicit)["files"] == 1
    with CMPCT(implicit) as reader:
        out = tmp_path / "out"
        reader.extractall(out, metadata=False)
    assert (out / "dir" / "sub" / "payload.bin").read_bytes() == b"EXACT-CONTENT"


def test_valid_hardlink_owner_alias_remains_preflightable(tmp_path: Path) -> None:
    original = _source(tmp_path)
    valid = tmp_path / "valid_alias.cmpct"

    def mutate(index):
        owner = next(row for row in index["files"] if row[0] == "parent.bin")
        index["files"].append([
            "z_alias.bin", K_HARDLINK, owner[2], owner[3], owner[4],
            None, ["parent.bin"],
        ])
        index["files"].sort(key=lambda row: row[0])

    _resign(original, valid, mutate)
    assert preflight_archive(valid)["files"] == 3
    with CMPCT(valid) as reader:
        assert reader.read("z_alias.bin") == b"PHYSICAL-OWNER"
