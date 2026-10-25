"""O80: end-to-end mixed physical source fidelity across independent Builder guards.

The three owners' unchanged suites remain the primary regression reference.
This synthetic mixed-root case checks fail-closed admission before publication,
then authentic r24 reconstruction after the unrepresentable alias is removed.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from cmpct.builder import Builder
from cmpct.reader import CMPCT


@pytest.mark.skipif(os.name == "nt", reason="POSIX hardlinks to symlink inodes")
def test_xattr_regular_hardlink_and_selected_symlink_alias_interaction(tmp_path: Path):
    root = tmp_path / "source"
    root.mkdir()
    data = b"mixed-O80-source-identity" * 77
    owner = root / "owner.bin"
    owner.write_bytes(data)
    os.link(owner, root / "alias.bin")
    first = root / "alpha.link"
    second = root / "omega.link"
    os.symlink("owner.bin", first)
    try:
        os.link(first, second, follow_symlinks=False)
    except (OSError, ValueError, NotImplementedError) as exc:
        pytest.skip(f"host cannot hardlink symlink inode: {exc}")
    assert (os.lstat(first).st_dev, os.lstat(first).st_ino) == (
        os.lstat(second).st_dev, os.lstat(second).st_ino
    )

    # Positive metadata control when host can actually represent this xattr.
    key = "user.cmpct_o80"
    value = b"mixed-guard-metadata\x00\xff"
    xattr_supported = False
    if hasattr(os, "setxattr") and hasattr(os, "getxattr"):
        try:
            os.setxattr(owner, key, value, follow_symlinks=False)
            xattr_supported = os.getxattr(owner, key, follow_symlinks=False) == value
        except OSError:
            pass

    archive = tmp_path / "existing.cmpct"
    sentinel = b"PREEXISTING_ARCHIVE_MUST_SURVIVE"
    archive.write_bytes(sentinel)
    with pytest.raises(OSError, match="hardlinked symlink"):
        Builder(root, workers=1).build(archive)
    assert archive.read_bytes() == sentinel

    second.unlink()
    Builder(root, workers=1).build(archive)
    with CMPCT(archive) as reader:
        assert reader.verify() >= 1
        dest = tmp_path / "restored"
        reader.extractall(dest)
    assert (dest / "owner.bin").read_bytes() == data
    assert (dest / "alias.bin").read_bytes() == data
    assert (os.stat(dest / "owner.bin").st_dev, os.stat(dest / "owner.bin").st_ino) == (
        os.stat(dest / "alias.bin").st_dev, os.stat(dest / "alias.bin").st_ino
    )
    assert os.readlink(dest / "alpha.link") == "owner.bin"
    if xattr_supported:
        assert os.getxattr(dest / "owner.bin", key, follow_symlinks=False) == value
