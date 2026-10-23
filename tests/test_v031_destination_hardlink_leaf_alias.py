"""Prospectively registered POSIX static pre-existing destination hardlink court.

Synthetic files only. This court does not prove race-resistant extraction:
an adversarial concurrent swap requires fd-rooted operations and atomic
publication for *all* writes and metadata operations.
"""
from __future__ import annotations

import hashlib
import os
import zipfile
from pathlib import Path

import pytest

from cmpct.builder import Builder
from cmpct.codec import S_BLOB, S_CDC, S_PACK, S_SPARSE
from cmpct.reader import CMPCT


pytestmark = pytest.mark.skipif(
    os.name != "posix" or not hasattr(os, "link"),
    reason="POSIX hardlink identity required",
)


def _make_archive(tmp_path: Path, *, kind: str) -> tuple[Path, str, int]:
    src = tmp_path / "source"
    src.mkdir()
    rel = "z-last.zip" if kind == "pack" else "z-last.bin"
    member = src / rel
    if kind == "blob":
        member.write_bytes(b"CMPCT-ARCHIVE-BYTES-" * 4096)
        expected = S_BLOB
    elif kind == "sparse":
        with member.open("wb") as f:
            f.write(b"A" * 4096)
            f.seek(16 * 1024 * 1024 - 4096)
            f.write(b"B" * 4096)
        expected = S_SPARSE
    elif kind == "cdc":
        # Content-defined-chunk admission is size-driven and independent of
        # the filename or fixture identity; >4*CHUNK is required.
        member.write_bytes(os.urandom(2 * 1024 * 1024))
        expected = S_CDC
    elif kind == "pack":
        # Eight genuine ZIP files trigger the Builder's ordinary generic
        # multi-ZIP PACK admission (not an index mutation or fabricated row).
        for i in range(8):
            p = member if i == 7 else src / f"zip-{i:02d}.zip"
            with zipfile.ZipFile(p, "w", compression=zipfile.ZIP_DEFLATED) as z:
                z.writestr("content.txt", bytes([i]) * 1536)
        expected = S_PACK
    else:
        raise ValueError(kind)
    (src / "a-first.bin").write_bytes(b"FIRST-SHOULD-NOT-BE-TOUCHED")
    archive = tmp_path / "src.cmpct"
    Builder(src, workers=1, reproducible=True).build(archive)
    return archive, rel, expected


def _outside_alias(tmp_path: Path, rel: str) -> tuple[Path, Path, Path, tuple[int, int, bytes]]:
    outside = tmp_path / "outside"
    outside.mkdir()
    victim = outside / "sentinel.bin"
    victim.write_bytes(b"OUTSIDE-VICTIM-MUST-REMAIN-EXACT")
    s = victim.stat()
    initial = (s.st_ino, s.st_size, hashlib.sha256(victim.read_bytes()).digest())
    dest = tmp_path / "dest"
    dest.mkdir()
    os.link(victim, dest / rel)
    assert victim.stat().st_nlink == 2
    return victim, dest, dest / rel, initial


def _assert_outside_unchanged(victim: Path, initial: tuple[int, int, bytes]) -> None:
    s = victim.stat()
    assert (s.st_ino, s.st_size, hashlib.sha256(victim.read_bytes()).digest()) == initial


@pytest.mark.parametrize("kind", ["blob", "sparse", "pack"])
def test_safe_extract_fails_before_partial_publication_on_preexisting_hardlink_leaf(
    tmp_path: Path, kind: str
) -> None:
    archive, rel, expected_storage = _make_archive(tmp_path, kind=kind)
    victim, dest, alias, initial = _outside_alias(tmp_path, rel)
    with CMPCT(archive) as reader:
        assert reader.by[rel][6][0] == expected_storage, "test must exercise a direct-truncate storage kind"
        assert reader.verify() == sum(row[1] != 1 for row in reader.files)
        with pytest.raises(OSError, match="pre-existing destination hardlink alias"):
            reader.extractall(dest, safe_symlinks=True)
    _assert_outside_unchanged(victim, initial)
    assert alias.stat().st_ino == initial[0]
    assert not (dest / "a-first.bin").exists(), "the preflight must reject before the first archive write"


def test_safe_cdc_atomic_replacement_preserves_preexisting_hardlink_outside(
    tmp_path: Path,
) -> None:
    archive, rel, expected_storage = _make_archive(tmp_path, kind="cdc")
    victim, dest, alias, initial = _outside_alias(tmp_path, rel)
    with CMPCT(archive) as reader:
        assert reader.by[rel][6][0] == expected_storage
        assert reader.verify() == 2
        reader.extractall(dest, safe_symlinks=True)
        assert alias.read_bytes() == reader.read(rel)
    _assert_outside_unchanged(victim, initial)
    assert alias.stat().st_ino != initial[0], "the atomic file publisher must install a new inode"


def test_safe_existing_single_link_leaf_remains_reusable(tmp_path: Path) -> None:
    archive, rel, expected_storage = _make_archive(tmp_path, kind="blob")
    dest = tmp_path / "dest"
    dest.mkdir()
    reused = dest / rel
    reused.write_bytes(b"OLD-CONTENT")
    assert reused.stat().st_nlink == 1
    with CMPCT(archive) as reader:
        assert reader.by[rel][6][0] == expected_storage
        reader.extractall(dest, safe_symlinks=True)
        assert reused.read_bytes() == reader.read(rel)


def test_explicit_unsafe_optout_keeps_legacy_hardlink_overwrite(tmp_path: Path) -> None:
    archive, rel, expected_storage = _make_archive(tmp_path, kind="blob")
    victim, dest, alias, initial = _outside_alias(tmp_path, rel)
    with CMPCT(archive) as reader:
        assert reader.by[rel][6][0] == expected_storage
        reader.extractall(dest, safe_symlinks=False)
        assert victim.read_bytes() == reader.read(rel)
    assert alias.stat().st_ino == initial[0]
    assert victim.stat().st_size != initial[1]
