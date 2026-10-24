"""O27 cross-owner composition: static destination protection + O10R Reader semantics.

Real revision-24 Builder/Reader, no mocks, no alternate parser. Does not
demonstrate race-safe destination capability, source lifetime, or atomic tree commit.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from cmpct.builder import Builder
from cmpct.reader import CMPCT


@pytest.mark.skipif(os.name != "posix" or not hasattr(os, "symlink"),
                    reason="POSIX inode/link semantics required")
def test_signed_link_hardlink_and_late_static_pivot_prewrite(tmp_path: Path):
    src = tmp_path / "input"
    (src / "z-last").mkdir(parents=True)
    (src / "a-first.bin").write_bytes(b"EARLY-MEMBER")
    (src / "owner.bin").write_bytes(b"HARDLINK-OWNER")
    os.link(src / "owner.bin", src / "alias.bin")
    (src / "member.lnk").symlink_to("owner.bin")
    (src / "z-last" / "member.bin").write_bytes(b"LATE-MEMBER")

    archive = tmp_path / "real-r24.cmpct"
    Builder(src, workers=1, reproducible=True).build(archive)

    outside = tmp_path / "outside"
    outside.mkdir()
    sentinel = outside / "member.bin"
    sentinel.write_bytes(b"OUTSIDE-UNCHANGED")
    outside_ino = sentinel.stat().st_ino

    dest = tmp_path / "dest"
    dest.mkdir()
    pivot = dest / "z-last"
    pivot.symlink_to(outside, target_is_directory=True)

    with CMPCT(archive) as reader:
        assert reader.read("a-first.bin") == b"EARLY-MEMBER"
        assert reader.verify() >= 4

        # The malicious destination entry sorts after ordinary early members.
        # Static preflight must reject before ANY of them materialize.
        with pytest.raises(OSError, match="pre-existing destination symlink"):
            reader.extractall(dest, safe_symlinks=True)
        assert not (dest / "a-first.bin").exists()
        assert not (dest / "owner.bin").exists()
        assert not (dest / "alias.bin").exists()
        assert not (dest / "member.lnk").exists()
        assert sentinel.read_bytes() == b"OUTSIDE-UNCHANGED"
        assert sentinel.stat().st_ino == outside_ino

        # Identical Reader/bytes must then reconstruct legitimately when
        # destination ownership is no longer adversarial.
        pivot.unlink()
        reader.extractall(dest, safe_symlinks=True)
        assert (dest / "a-first.bin").read_bytes() == b"EARLY-MEMBER"
        assert (dest / "z-last" / "member.bin").read_bytes() == b"LATE-MEMBER"
        assert (dest / "owner.bin").read_bytes() == b"HARDLINK-OWNER"
        assert (dest / "alias.bin").read_bytes() == b"HARDLINK-OWNER"
        assert (dest / "owner.bin").stat().st_ino == (dest / "alias.bin").stat().st_ino
        assert (dest / "member.lnk").is_symlink()
        assert os.readlink(dest / "member.lnk") == "owner.bin"
        assert (dest / "member.lnk").read_bytes() == b"HARDLINK-OWNER"
