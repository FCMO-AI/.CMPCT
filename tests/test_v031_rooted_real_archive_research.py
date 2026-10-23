"""Source-exact scientific court for experimental POSIX capability-root extraction.

All writes, including adversarial "outside" fixtures, remain under pytest temp roots.
A PASS for the moved-open-directory case establishes a *negative* result for lexical
containment, not a security success.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import stat

import pytest

from cmpct.builder import Builder
from cmpct.reader import CMPCT
from cmpct._rooted_extract_research import extract_rooted_research


pytestmark = pytest.mark.skipif(
    os.name != "posix" or not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "symlink"),
    reason="POSIX no-follow directory handles required")


def _make_archive(tmp_path: Path, files: dict[str, bytes], *, symlinks=None, hardlinks=None):
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
    archive = tmp_path / "source.cmpct"
    Builder(src, workers=1, reproducible=True).build(archive)
    return archive


def test_real_archive_clean_bytes_symlink_and_hardlink(tmp_path):
    items = {"nested/alpha.txt": b"ALPHA" * 1024,
             "nested/beta.bin": bytes(range(256)) * 4096,
             "owners/original.txt": b"OWNED DATA"}
    arc = _make_archive(tmp_path, items,
                        symlinks={"direct.lnk": "owners/original.txt"},
                        hardlinks={"owners/alias.txt": "owners/original.txt"})
    dest = tmp_path / "dest"
    with CMPCT(arc) as reader:
        assert reader.verify() >= 5
        extract_rooted_research(reader, dest)
    for rel, data in items.items():
        assert (dest / rel).read_bytes() == data
        assert hashlib.sha256((dest / rel).read_bytes()).digest() == hashlib.sha256(data).digest()
    assert (dest / "direct.lnk").is_symlink()
    assert os.readlink(dest / "direct.lnk") == "owners/original.txt"
    owner, alias = dest / "owners/original.txt", dest / "owners/alias.txt"
    assert owner.stat().st_ino == alias.stat().st_ino
    assert owner.read_bytes() == alias.read_bytes() == b"OWNED DATA"


def test_inherited_symlink_parent_refused_before_outside_write(tmp_path):
    arc = _make_archive(tmp_path, {"nested/member.bin": b"PAYLOAD"})
    outside = tmp_path / "outside"
    outside.mkdir()
    victim = outside / "member.bin"
    victim.write_bytes(b"INVARIANT")
    before = victim.stat().st_ino
    dest = tmp_path / "dest"
    dest.mkdir()
    (dest / "nested").symlink_to(outside, target_is_directory=True)
    with CMPCT(arc) as reader:
        with pytest.raises((OSError, IOError)):
            extract_rooted_research(reader, dest)
    assert victim.read_bytes() == b"INVARIANT"
    assert victim.stat().st_ino == before


def test_post_initial_scan_parent_pivot_refused(tmp_path):
    arc = _make_archive(tmp_path, {"nested/member.bin": b"PAYLOAD"})
    outside = tmp_path / "outside"
    outside.mkdir()
    victim = outside / "member.bin"
    victim.write_bytes(b"INVARIANT")
    dest = tmp_path / "dest"
    dest.mkdir()
    seen = []
    def swap(_):
        original = dest / "nested"
        os.rename(original, dest / "displaced")
        original.symlink_to(outside, target_is_directory=True)
        seen.append(True)
    with CMPCT(arc) as reader:
        with pytest.raises((OSError, IOError)):
            extract_rooted_research(reader, dest, before_member=swap)
    assert seen == [True]
    assert victim.read_bytes() == b"INVARIANT"
    assert not (dest / "displaced/member.bin").exists()


def test_atomic_leaf_replaces_link_not_external_target(tmp_path):
    arc = _make_archive(tmp_path, {"member.bin": b"NEW"})
    outside = tmp_path / "outside.bin"
    outside.write_bytes(b"DO NOT MODIFY")
    ino = outside.stat().st_ino
    dest = tmp_path / "dest"
    dest.mkdir()
    (dest / "member.bin").symlink_to(outside)
    with CMPCT(arc) as reader:
        extract_rooted_research(reader, dest)
    assert outside.read_bytes() == b"DO NOT MODIFY"
    assert outside.stat().st_ino == ino
    assert not (dest / "member.bin").is_symlink()
    assert (dest / "member.bin").read_bytes() == b"NEW"


def test_failed_sha_does_not_publish_or_leave_temporary_files(tmp_path, monkeypatch):
    arc = _make_archive(tmp_path, {"member.bin": b"GOOD"})
    dest = tmp_path / "dest"
    dest.mkdir()
    (dest / "member.bin").write_bytes(b"EXISTING")
    with CMPCT(arc) as reader:
        monkeypatch.setattr(reader, "file_sha256", lambda _name: b"\xff" * 32)
        with pytest.raises(IOError, match="SHA"):
            extract_rooted_research(reader, dest)
    assert (dest / "member.bin").read_bytes() == b"EXISTING"
    assert sorted(p.name for p in dest.iterdir()) == ["member.bin"]


def test_member_budget_fails_before_creating_destination(tmp_path):
    arc = _make_archive(tmp_path, {"member.bin": b"X" * 100})
    dest = tmp_path / "dest"
    with CMPCT(arc) as reader:
        with pytest.raises(IOError, match="budget"):
            extract_rooted_research(reader, dest, max_member_bytes=64)
    assert not dest.exists()


def test_moved_open_directory_inode_breaks_lexical_containment_negative(tmp_path):
    """NEGATIVE: fd pinning prevents symlink redirection but not rename of pinned inode."""
    arc = _make_archive(tmp_path, {"nested/member.bin": b"PAYLOAD"})
    outside = tmp_path / "outside"
    outside.mkdir()
    victim = outside / "member.bin"
    victim.write_bytes(b"INVARIANT")
    dest = tmp_path / "dest"
    dest.mkdir()
    escaped = tmp_path / "escaped"
    def move_after_open(_):
        os.rename(dest / "nested", escaped)
        (dest / "nested").symlink_to(outside, target_is_directory=True)
    with CMPCT(arc) as reader:
        # The Reader eventually refuses metadata traversal through the replacement symlink,
        # but that failure occurs AFTER the fd-rooted staging and publication below. A late
        # IOError does not establish "no writes outside the original lexical root".
        with pytest.raises(OSError):
            extract_rooted_research(reader, dest, after_parent_open=move_after_open)
    assert victim.read_bytes() == b"INVARIANT"
    assert (escaped / "member.bin").read_bytes() == b"PAYLOAD"
    assert (dest / "nested").is_symlink()
    # This is precisely why a rooted fd is NOT an absolute pathname sandbox.
    assert not (dest / "nested/member.bin").read_bytes() == b"PAYLOAD"


def test_reject_unsafe_archive_symlink_target_before_materializing_it(tmp_path):
    arc = _make_archive(tmp_path, {"safe.txt": b"SAFE"},
                        symlinks={"unsafe.lnk": "../outside.bin"})
    dest = tmp_path / "dest"
    with CMPCT(arc) as reader:
        with pytest.raises(IOError, match="unsafe archived symlink"):
            extract_rooted_research(reader, dest)
    assert not (dest / "unsafe.lnk").exists()


def test_existing_hardlink_leaf_cannot_truncate_external_inode(tmp_path):
    """Distinct from symlink leaf: O_NOFOLLOW alone cannot protect an external hardlink."""
    arc = _make_archive(tmp_path, {"member.bin": b"NEW CONTENT"})
    outside = tmp_path / "outside.bin"
    outside.write_bytes(b"EXTERNAL-HARDLINK-SENTINEL")
    ino = outside.stat().st_ino
    dest = tmp_path / "dest"
    dest.mkdir()
    os.link(outside, dest / "member.bin")
    assert (dest / "member.bin").stat().st_ino == ino
    with CMPCT(arc) as reader:
        extract_rooted_research(reader, dest)
    assert outside.read_bytes() == b"EXTERNAL-HARDLINK-SENTINEL"
    assert outside.stat().st_ino == ino
    assert (dest / "member.bin").read_bytes() == b"NEW CONTENT"
    assert (dest / "member.bin").stat().st_ino != ino


def test_max_name_component_uses_short_private_staging(tmp_path):
    """NAME_MAX belongs to the archived leaf, not to a prefixed staging name."""
    name = "n" * 255
    arc = _make_archive(tmp_path, {name: b"FULL-LENGTH-POSIX-COMPONENT"})
    dest = tmp_path / "dest"
    with CMPCT(arc) as reader:
        extract_rooted_research(reader, dest)
    assert (dest / name).read_bytes() == b"FULL-LENGTH-POSIX-COMPONENT"
    assert len(os.fsencode(name)) == 255
    assert sorted(x.name for x in dest.iterdir()) == [name]
