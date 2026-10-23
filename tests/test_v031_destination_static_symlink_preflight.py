"""Real r24 Builder/Reader court for static pre-existing destination symlink pivots.

All created paths, including outside sentinels, live under pytest temporary roots.
Does not claim a race-safe directory capability solution.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path

import pytest

from cmpct.builder import Builder
from cmpct.reader import CMPCT


pytestmark = pytest.mark.skipif(os.name != "posix" or not hasattr(os, "symlink"),
                                reason="POSIX symlink semantics required")


def _archive(tmp_path: Path, files: dict[str, bytes], *, symlinks=None, hardlinks=None) -> Path:
    src = tmp_path / "src"
    src.mkdir()
    for rel, data in files.items():
        path = src / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    for rel, target in (symlinks or {}).items():
        path = src / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.symlink_to(target)
    for rel, target in (hardlinks or {}).items():
        path = src / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        os.link(src / target, path)
    archive = tmp_path / "data.cmpct"
    Builder(src, workers=1, reproducible=True).build(archive)
    return archive


@pytest.mark.parametrize("pivot", ["ancestor", "leaf"])
def test_static_preexisting_symlink_outside_cannot_receive_source_bytes(tmp_path, pivot):
    payload = b"archived-member-" + pivot.encode()
    name = "nested/member.bin" if pivot == "ancestor" else "member.bin"
    archive = _archive(tmp_path, {name: payload})
    outside = tmp_path / "outside"
    outside.mkdir()
    victim = outside / "member.bin"
    victim.write_bytes(b"OUTSIDE-CONTENT-UNCHANGED")
    before = victim.stat()
    root = tmp_path / "dest"
    root.mkdir()
    if pivot == "ancestor":
        (root / "nested").symlink_to(outside, target_is_directory=True)
    else:
        (root / "member.bin").symlink_to(victim)
    with CMPCT(archive) as reader:
        assert reader.read(name) == payload
        assert reader.verify() >= 1
        with pytest.raises(OSError, match="pre-existing destination symlink"):
            reader.extractall(root, safe_symlinks=True)
    assert victim.read_bytes() == b"OUTSIDE-CONTENT-UNCHANGED"
    assert victim.stat().st_ino == before.st_ino
    assert hashlib.sha256(victim.read_bytes()).digest() == hashlib.sha256(b"OUTSIDE-CONTENT-UNCHANGED").digest()


def test_reject_later_ancestor_before_any_earlier_member_materializes(tmp_path):
    archive = _archive(tmp_path, {"a-first.bin": b"FIRST", "z-last/member.bin": b"LAST"})
    outside = tmp_path / "outside"
    outside.mkdir()
    victim = outside / "member.bin"
    victim.write_bytes(b"KEEP")
    root = tmp_path / "dest"
    root.mkdir()
    (root / "z-last").symlink_to(outside, target_is_directory=True)
    with CMPCT(archive) as reader:
        assert reader.verify() == 2
        with pytest.raises(OSError, match="pre-existing destination symlink"):
            reader.extractall(root, safe_symlinks=True)
    assert not (root / "a-first.bin").exists()
    assert victim.read_bytes() == b"KEEP"


def test_regular_existing_files_and_directories_can_be_reused(tmp_path):
    archive = _archive(tmp_path, {"nested/member.bin": b"GOOD"})
    root = tmp_path / "dest"
    (root / "nested").mkdir(parents=True)
    (root / "nested/member.bin").write_bytes(b"OLD")
    with CMPCT(archive) as reader:
        assert reader.verify() == 1
        reader.extractall(root, safe_symlinks=True)
    assert (root / "nested/member.bin").read_bytes() == b"GOOD"


def test_preexisting_link_leaf_replaced_by_safe_archived_symlink(tmp_path):
    archive = _archive(tmp_path, {"target.bin": b"SAFE"}, symlinks={"member.lnk": "target.bin"})
    outside = tmp_path / "outside.bin"
    outside.write_bytes(b"UNTOUCHED")
    root = tmp_path / "dest"
    root.mkdir()
    (root / "member.lnk").symlink_to(outside)
    with CMPCT(archive) as reader:
        assert reader.verify() == 2
        reader.extractall(root, safe_symlinks=True)
    assert outside.read_bytes() == b"UNTOUCHED"
    assert (root / "member.lnk").is_symlink()
    assert os.readlink(root / "member.lnk") == "target.bin"
    assert (root / "member.lnk").read_bytes() == b"SAFE"


def test_hardlink_source_symlink_is_rejected_without_touching_outside(tmp_path):
    archive = _archive(tmp_path, {"owner.bin": b"OWN"}, hardlinks={"alias.bin": "owner.bin"})
    outside = tmp_path / "outside.bin"
    outside.write_bytes(b"SENTINEL")
    root = tmp_path / "dest"
    root.mkdir()
    (root / "owner.bin").symlink_to(outside)
    with CMPCT(archive) as reader:
        assert reader.verify() == 2
        with pytest.raises(OSError, match="pre-existing destination symlink"):
            reader.extractall(root, safe_symlinks=True)
    assert outside.read_bytes() == b"SENTINEL"
    assert not (root / "alias.bin").exists()


def test_symlinked_caller_selected_root_is_explicitly_trusted(tmp_path):
    archive = _archive(tmp_path, {"member.bin": b"ROOT"})
    physical = tmp_path / "physical"
    physical.mkdir()
    root = tmp_path / "selected-root"
    root.symlink_to(physical, target_is_directory=True)
    with CMPCT(archive) as reader:
        reader.extractall(root, safe_symlinks=True)
    assert (physical / "member.bin").read_bytes() == b"ROOT"


def test_unsafe_flag_preserves_explicit_opt_out_semantics(tmp_path):
    archive = _archive(tmp_path, {"member.bin": b"NEW"})
    root = tmp_path / "dest"
    root.mkdir()
    target = root / "old.bin"
    target.write_bytes(b"OLD")
    (root / "member.bin").symlink_to(target)
    with CMPCT(archive) as reader:
        reader.extractall(root, safe_symlinks=False)
    assert target.read_bytes() == b"NEW"
