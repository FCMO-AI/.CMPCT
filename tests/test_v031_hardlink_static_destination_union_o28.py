"""O28 cross-owner product court: authenticated hardlink owners and prewrite destination pivot safety.

The shipped Builder/Reader and genuine r24 archive, not mocked format metadata, must
exercise both independent owner changes in one runtime. This is *static* prewrite
protection, not a proof against concurrent destination swaps or mutable source input.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from cmpct.builder import Builder
from cmpct.reader import CMPCT
from cmpct.validation import preflight_archive


@pytest.mark.skipif(os.name != "posix" or not hasattr(os, "link") or not hasattr(os, "symlink"),
                    reason="POSIX hardlink and symlink inode semantics required")
def test_o28_multiple_authenticated_aliases_with_late_destination_pivot(tmp_path: Path):
    src = tmp_path / "src"
    (src / "z-last").mkdir(parents=True)
    (src / "a-first.txt").write_bytes(b"EARLY-MUST-NOT-PUBLISH")
    physical = src / "owner.data"
    physical.write_bytes(b"ONE-PHYSICAL-OWNER" * 16)
    os.link(physical, src / "alias-one.data")
    os.link(physical, src / "alias-two.data")
    (src / "z-last" / "late.bin").write_bytes(b"OUTER-MUST-NOT-CHANGE")

    archive = tmp_path / "signed-r24.cmpct"
    Builder(src, workers=1, reproducible=True).build(archive)
    assert preflight_archive(archive)["files"] >= 5

    outside = tmp_path / "outside"
    outside.mkdir()
    sentinel = outside / "late.bin"
    sentinel.write_bytes(b"EXTERNAL-SENTINEL")
    prior_inode = sentinel.stat().st_ino
    dest = tmp_path / "dest"
    dest.mkdir()
    pivot = dest / "z-last"
    pivot.symlink_to(outside, target_is_directory=True)

    with CMPCT(archive) as reader:
        # O25 iteratively authenticates owner topology at ordinary open;
        # O27 independently checks *destination* trust before any publication.
        for name in ("owner.data", "alias-one.data", "alias-two.data"):
            assert reader.read(name) == b"ONE-PHYSICAL-OWNER" * 16
            assert reader.file_sha256(name) == reader.file_sha256("owner.data")
        assert len(reader._hardlink_owners) == 2
        with pytest.raises(OSError, match="pre-existing destination symlink"):
            reader.extractall(dest, safe_symlinks=True)
        for name in ("a-first.txt", "owner.data", "alias-one.data", "alias-two.data"):
            assert not (dest / name).exists()
        assert sentinel.read_bytes() == b"EXTERNAL-SENTINEL"
        assert sentinel.stat().st_ino == prior_inode

        pivot.unlink()
        reader.extractall(dest, safe_symlinks=True)
        assert (dest / "a-first.txt").read_bytes() == b"EARLY-MUST-NOT-PUBLISH"
        for name in ("owner.data", "alias-one.data", "alias-two.data"):
            assert (dest / name).read_bytes() == b"ONE-PHYSICAL-OWNER" * 16
        ids = {(dest / name).stat().st_ino for name in
               ("owner.data", "alias-one.data", "alias-two.data")}
        assert len(ids) == 1
        assert (dest / "z-last" / "late.bin").read_bytes() == b"OUTER-MUST-NOT-CHANGE"
