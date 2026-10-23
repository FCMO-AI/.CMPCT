"""POSIX symlink targets are raw filesystem bytes, not necessarily valid UTF-8."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path

import pytest

from cmpct.core import Builder, CMPCT


@pytest.mark.skipif(os.name != "posix", reason="raw non-UTF-8 symlinks are POSIX-only")
@pytest.mark.parametrize(
    "target",
    [
        b"relative-\xff\xfe",
        b"nested/\x80\xe2\x82",
        b"./\x01\x7f\xf0\xff",
        b"./" + bytes(range(1, 256)),
    ],
    ids=["invalid-high-bytes", "truncated-utf8", "control-bytes", "all-nonzero-octets"],
)
def test_non_utf8_symlink_target_round_trips_exact_bytes(tmp_path: Path, target: bytes) -> None:
    root = tmp_path / "source"
    root.mkdir()
    # The link need not resolve. Its physically stored target bytes are the source of truth.
    link = root / "link"
    os.symlink(target, os.fsencode(link))
    assert os.readlink(os.fsencode(link)) == target

    archive = tmp_path / "archive.cmpct"
    Builder(root, workers=1, reproducible=True).build(archive)

    with CMPCT(archive) as reader:
        assert reader.verify() == 1  # one symlink is included, not a resolved referent
        assert reader.read("link") == target
        destination = tmp_path / "out"
        reader.extractall(destination, metadata=False)
    assert os.readlink(os.fsencode(destination / "link")) == target
    assert hashlib.sha256(os.readlink(os.fsencode(destination / "link"))).digest() == hashlib.sha256(target).digest()


@pytest.mark.skipif(os.name != "posix", reason="raw non-UTF-8 symlinks are POSIX-only")
@pytest.mark.parametrize("target", [b"simple-target", "caf\u00e9/\u65e5\u672c".encode("utf-8")])
def test_valid_utf8_symlink_encoding_matches_existing_behavior(tmp_path: Path, target: bytes) -> None:
    root = tmp_path / "source"
    root.mkdir()
    link = root / "link"
    os.symlink(target, os.fsencode(link))
    # Normal text targets retain the exact historical encoder bytes.
    assert os.fsencode(os.readlink(link)) == os.readlink(link).encode("utf-8") == target
    archive = tmp_path / "archive.cmpct"
    Builder(root, workers=1, reproducible=True).build(archive)
    with CMPCT(archive) as reader:
        assert reader.verify() == 1
        assert reader.read("link") == target


@pytest.mark.skipif(os.name != "posix", reason="raw non-UTF-8 symlinks are POSIX-only")
@pytest.mark.parametrize("target", [b"/tmp/\xff-absolute", b"../\xff-traversal"])
def test_raw_unsafe_symlink_remains_rejected_on_extract(tmp_path: Path, target: bytes) -> None:
    root = tmp_path / "source"
    root.mkdir()
    os.symlink(target, os.fsencode(root / "link"))
    archive = tmp_path / "archive.cmpct"
    Builder(root, workers=1, reproducible=True).build(archive)
    with CMPCT(archive) as reader:
        assert reader.verify() == 1
        assert reader.read("link") == target
        with pytest.raises((IOError, ValueError)):
            reader.extractall(tmp_path / "out", metadata=False)
    assert not (tmp_path / "out" / "link").is_symlink()
