"""Independent v0.31 genuine-archive court for OPTIONAL shared-leaf atomic publication.

The default static rejection tests in test_v031_destination_hardlink_leaf_alias.py
are immutable controls. This opt-in *does not* establish race-safe containment:
concurrent ancestor swaps still require directory-capability ownership.
"""
from __future__ import annotations

import hashlib
import os
import stat
import zipfile
from pathlib import Path

import pytest

from cmpct.builder import Builder
from cmpct.codec import S_BLOB, S_CDC, S_PACK, S_SPARSE, S_VZIP
from cmpct.reader import CMPCT

pytestmark = pytest.mark.skipif(
    os.name != "posix" or not hasattr(os, "link") or not hasattr(os, "fchmod"),
    reason="requires POSIX hardlinks and descriptor-mode preservation",
)


def _archive(tmp_path: Path, kind: str) -> tuple[Path, str, int]:
    src = tmp_path / "src"
    src.mkdir()
    rel = ("nested/z-last.bin" if kind == "nested_blob" else
           "z-last.zip" if kind in ("pack", "vzip") else "z-last.bin")
    target = src / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    if kind in ("blob", "nested_blob"):
        target.write_bytes(b"actual-CMPCT-BLOB-" * 4096)
        want = S_BLOB
    elif kind == "sparse":
        with target.open("wb") as f:
            f.write(b"A" * 4096)
            f.seek(16 * 1024 * 1024 - 4096)
            f.write(b"B" * 4096)
        want = S_SPARSE
    elif kind == "pack":
        for i in range(8):
            member = target if i == 7 else src / f"zip-{i:02d}.zip"
            with zipfile.ZipFile(member, "w", compression=zipfile.ZIP_DEFLATED) as z:
                z.writestr("member.txt", bytes([i]) * 1536)
        want = S_PACK
    elif kind == "vzip":
        with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_STORED) as z:
            z.writestr("payload.dat", b"VZIP" * 128)
        want = S_VZIP
    elif kind == "cdc":
        target.write_bytes(os.urandom(2 * 1024 * 1024))
        want = S_CDC
    elif kind == "name_max":
        target.unlink(missing_ok=True)
        rel = "m" * 255
        target = src / rel
        target.write_bytes(b"max-name-blob" * 128)
        want = S_BLOB
    else:
        raise ValueError(kind)
    (src / "a-first.bin").write_bytes(b"early-member-must-be-exact")
    dst = tmp_path / "synthetic.cmpct"
    Builder(src, workers=1, reproducible=True).build(dst)
    return dst, rel, want


def _shared_destination(tmp_path: Path, rel: str, external=True):
    dest = tmp_path / "dest"
    dest.mkdir()
    leaf = dest / rel
    leaf.parent.mkdir(parents=True, exist_ok=True)
    old = b"OLD-SHARED-INODE-PRESERVE-CONTENTS"
    if external:
        other = tmp_path / "outside" / "victim.bin"
        other.parent.mkdir()
        other.write_bytes(old)
        os.link(other, leaf)
    else:
        leaf.write_bytes(old)
        other = dest / "inside-sibling"
        os.link(leaf, other)
    stat_before = other.stat()
    baseline = (stat_before.st_dev, stat_before.st_ino,
                stat_before.st_size, stat.S_IMODE(stat_before.st_mode),
                hashlib.sha256(other.read_bytes()).digest())
    return dest, leaf, other, baseline


def _assert_untouched(other: Path, baseline) -> None:
    s = other.stat()
    assert (s.st_dev, s.st_ino, s.st_size, stat.S_IMODE(s.st_mode),
            hashlib.sha256(other.read_bytes()).digest()) == baseline


@pytest.mark.parametrize("kind", ["blob", "nested_blob", "sparse", "pack", "vzip", "name_max"])
def test_real_reader_atomic_optin_separates_outside_hardlink_without_corruption(
    tmp_path: Path, kind: str,
) -> None:
    archive, rel, expected = _archive(tmp_path, kind)
    dest, leaf, other, baseline = _shared_destination(tmp_path, rel)
    with CMPCT(archive) as reader:
        assert reader.by[rel][6][0] == expected, "wrong Builder admission invalidates court"
        reader.extractall(dest, safe_symlinks=True, atomic_shared_leaf=True)
        expected_bytes = reader.read(rel)
        assert leaf.read_bytes() == expected_bytes
        assert hashlib.sha256(leaf.read_bytes()).digest() == hashlib.sha256(expected_bytes).digest()
        assert (dest / "a-first.bin").read_bytes() == b"early-member-must-be-exact"
        if kind == "sparse":
            assert leaf.stat().st_size == 16 * 1024 * 1024
            assert leaf.stat().st_blocks * 512 < leaf.stat().st_size // 2, (
                "atomic fallback must preserve sparse holes, not materialize zeros"
            )
    _assert_untouched(other, baseline)
    assert leaf.stat().st_ino != baseline[1], "new inode publication is the mechanism"
    assert not list(leaf.parent.glob(".cmpct-part-*"))


def test_benign_in_root_sibling_is_independent_after_optin(tmp_path: Path) -> None:
    archive, rel, expected = _archive(tmp_path, "blob")
    dest, leaf, sibling, baseline = _shared_destination(tmp_path, rel, external=False)
    with CMPCT(archive) as reader:
        assert reader.by[rel][6][0] == expected
        reader.extractall(dest, safe_symlinks=True, atomic_shared_leaf=True)
        assert leaf.read_bytes() == reader.read(rel)
    _assert_untouched(sibling, baseline)
    assert leaf.stat().st_ino != sibling.stat().st_ino
    assert sibling.read_bytes() != leaf.read_bytes()


def test_metadata_disabled_preserves_preexisting_leaf_mode(tmp_path: Path) -> None:
    archive, rel, _ = _archive(tmp_path, "blob")
    dest, leaf, other, baseline = _shared_destination(tmp_path, rel)
    os.chmod(leaf, 0o640)
    old_mode = stat.S_IMODE(other.stat().st_mode)
    with CMPCT(archive) as reader:
        reader.extractall(dest, metadata=False, atomic_shared_leaf=True)
        assert leaf.read_bytes() == reader.read(rel)
    assert stat.S_IMODE(leaf.stat().st_mode) == old_mode
    assert stat.S_IMODE(other.stat().st_mode) == old_mode


def test_decode_failure_preserves_both_old_aliases_and_cleans_staging(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    archive, rel, _ = _archive(tmp_path, "blob")
    dest, leaf, other, baseline = _shared_destination(tmp_path, rel)
    with CMPCT(archive) as reader:
        def fail_read(_):
            raise IOError("synthetic decoder refusal BEFORE publication")
        monkeypatch.setattr(reader, "read", fail_read)
        with pytest.raises(OSError, match="synthetic decoder refusal"):
            reader.extractall(dest, atomic_shared_leaf=True)
    _assert_untouched(other, baseline)
    assert leaf.stat().st_ino == baseline[1]
    assert leaf.read_bytes() == other.read_bytes()
    assert not list(leaf.parent.glob(".cmpct-part-*"))


def test_replace_failure_preserves_both_old_aliases_and_cleans_staging(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    archive, rel, _ = _archive(tmp_path, "blob")
    dest, leaf, other, baseline = _shared_destination(tmp_path, rel)
    real_replace = os.replace
    def fail_publication(src, dst, *args, **kwargs):
        if Path(src).name.startswith(".cmpct-part-"):
            raise OSError("synthetic publication refusal")
        return real_replace(src, dst, *args, **kwargs)
    monkeypatch.setattr(os, "replace", fail_publication)
    with CMPCT(archive) as reader:
        with pytest.raises(OSError, match="synthetic publication refusal"):
            reader.extractall(dest, atomic_shared_leaf=True)
    _assert_untouched(other, baseline)
    assert leaf.stat().st_ino == baseline[1]
    assert not list(leaf.parent.glob(".cmpct-part-*"))


def test_optin_does_not_bypass_preexisting_ancestor_symlink_guard(tmp_path: Path) -> None:
    archive, rel, _ = _archive(tmp_path, "nested_blob")
    outside = tmp_path / "outside"
    outside.mkdir()
    victim = outside / "z-last.bin"
    victim.write_bytes(b"must-not-change")
    dest = tmp_path / "dest"
    dest.mkdir()
    (dest / "nested").symlink_to(outside, target_is_directory=True)
    with CMPCT(archive) as reader:
        with pytest.raises(OSError, match="pre-existing destination symlink"):
            reader.extractall(dest, atomic_shared_leaf=True)
    assert victim.read_bytes() == b"must-not-change"
    assert not (dest / "a-first.bin").exists()


def test_cdc_existing_atomic_path_still_works_without_optin(tmp_path: Path) -> None:
    archive, rel, expected = _archive(tmp_path, "cdc")
    dest, leaf, other, baseline = _shared_destination(tmp_path, rel)
    with CMPCT(archive) as reader:
        assert reader.by[rel][6][0] == expected
        reader.extractall(dest, atomic_shared_leaf=True)
        assert leaf.read_bytes() == reader.read(rel)
    _assert_untouched(other, baseline)


def test_two_distinct_archive_members_preexisting_as_one_inroot_inode(
    tmp_path: Path,
) -> None:
    """The first atomic replace lowers nlink for the next shared leaf.

    This is a causal same-archive multi-entry ownership test, not an outside-
    alias fixture. A preflight-only count cannot be assumed stable throughout
    the archive extraction even without a concurrent actor.
    """
    source = tmp_path / "src"
    source.mkdir()
    (source / "a.bin").write_bytes(b"archive-A-" * 8192)
    (source / "b.bin").write_bytes(b"archive-B-" * 8192)
    archive = tmp_path / "double.cmpct"
    Builder(source, workers=1, reproducible=True).build(archive)
    dest = tmp_path / "dest"
    dest.mkdir()
    a_leaf, b_leaf = dest / "a.bin", dest / "b.bin"
    a_leaf.write_bytes(b"BENIGN-SHARED-OLD-INODE")
    os.link(a_leaf, b_leaf)
    assert a_leaf.stat().st_nlink == b_leaf.stat().st_nlink == 2
    with CMPCT(archive) as reader:
        assert reader.by["a.bin"][6][0] == S_BLOB
        assert reader.by["b.bin"][6][0] == S_BLOB
        reader.extractall(dest, atomic_shared_leaf=True)
        assert a_leaf.read_bytes() == reader.read("a.bin")
        assert b_leaf.read_bytes() == reader.read("b.bin")
    assert a_leaf.stat().st_ino != b_leaf.stat().st_ino
    assert not list(dest.glob(".cmpct-part-*"))
