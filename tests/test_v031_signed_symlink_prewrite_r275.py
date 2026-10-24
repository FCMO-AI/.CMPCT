"""Hostile *signed* symlink target must fail before unrelated member publication.

Research O1 preregistered at 4c442e7ef60fd8ef68ce4819bdf473d2f029e0b9.
The source is constructed by the real r24 Builder; no forged index or mock Reader.
This check is narrower than atomic extraction or destination-TOCTOU security.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from cmpct.core import Builder, CMPCT


def _source_archive(tmp_path: Path, target: str) -> Path:
    source = tmp_path / "src"
    source.mkdir()
    (source / "a-first.bin").write_bytes(b"SIGNED-CMPCT-PREWRITE-OWNER" * 8)
    try:
        os.symlink(target, source / "z-link")
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"host cannot create symbolic link: {exc}")
    assert os.readlink(source / "z-link") == target
    archive = tmp_path / "signed.cmpct"
    Builder(source, workers=1, reproducible=True).build(archive)
    return archive


@pytest.mark.parametrize("target", ("../outside", "/absolute/outside"))
def test_unsafe_signed_symlink_target_fails_before_regular_member(tmp_path: Path, target: str) -> None:
    archive = _source_archive(tmp_path, target)
    dest = tmp_path / "restored"
    with CMPCT(archive) as reader:
        assert reader.read("a-first.bin") == b"SIGNED-CMPCT-PREWRITE-OWNER" * 8
        with pytest.raises(OSError, match="unsafe symlink target"):
            reader.extractall(dest, safe_symlinks=True)
    # A known-invalid signed symlink target must not publish an unrelated member.
    assert not (dest / "a-first.bin").exists()


def test_valid_relative_signed_symlink_still_roundtrips(tmp_path: Path) -> None:
    archive = _source_archive(tmp_path, "a-first.bin")
    dest = tmp_path / "restored"
    with CMPCT(archive) as reader:
        reader.extractall(dest, safe_symlinks=True)
    assert (dest / "a-first.bin").read_bytes() == b"SIGNED-CMPCT-PREWRITE-OWNER" * 8
    assert (dest / "z-link").is_symlink()
    assert os.readlink(dest / "z-link") == "a-first.bin"
