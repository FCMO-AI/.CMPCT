"""O72: one archive-level court for O65 capture and O69 strict restoration.

Source/Reader are actual installed CMPCT; the injected API is used only to force
specific filesystem error branches. The Linux native test is separately typed.
This is intentionally not a transactional-publication or OS-wide ACL guarantee.
"""
from __future__ import annotations

import errno
import os
import sys
from pathlib import Path

import pytest

from cmpct.core import Builder, CMPCT


KEY = "user.cmpct_o72"
VALUE = b"\x00\xffO72\x80\x01"


def source(tmp_path: Path) -> tuple[Path, bytes]:
    root = tmp_path / "source"
    root.mkdir()
    payload = b"O72 actual authenticated revision-24 archive\x00\xff"
    (root / "member.txt").write_bytes(payload)
    return root, payload


def archive_with_observed_xattr(tmp_path: Path, monkeypatch) -> tuple[Path, bytes]:
    root, payload = source(tmp_path)
    archive = tmp_path / "observed.cmpct"

    def list_attrs(path, *, follow_symlinks=False):
        assert follow_symlinks is False
        return [KEY] if os.fspath(path).endswith("member.txt") else []

    def get_attr(path, name, *, follow_symlinks=False):
        assert os.fspath(path).endswith("member.txt")
        assert follow_symlinks is False
        assert name == KEY
        return VALUE

    with monkeypatch.context() as patch:
        patch.setattr(os, "listxattr", list_attrs, raising=False)
        patch.setattr(os, "getxattr", get_attr, raising=False)
        Builder(root, workers=1).build(archive)

    with CMPCT(archive) as reader:
        assert reader.verify() == 1
        assert reader.fsmeta.get("xattrs")
        assert reader.read("member.txt") == payload
    return archive, payload


def test_captured_binary_xattr_reaches_strict_restore_in_same_real_archive(tmp_path, monkeypatch):
    archive, payload = archive_with_observed_xattr(tmp_path, monkeypatch)
    restored = []

    def set_attrs(path, key, value, *, follow_symlinks=False):
        restored.append((Path(path).name, key, value, follow_symlinks))

    with CMPCT(archive) as reader, monkeypatch.context() as patch:
        patch.setattr(os, "setxattr", set_attrs, raising=False)
        target = tmp_path / "strict-output"
        reader.extractall(target, require_xattrs=True)
    assert (target / "member.txt").read_bytes() == payload
    assert restored == [("member.txt", KEY, VALUE, False)]


def test_observed_but_unreadable_late_source_attribute_preserves_existing_archive(tmp_path, monkeypatch):
    root, _ = source(tmp_path)
    (root / "z-last.txt").write_bytes(b"second file triggers denied attribute")
    output = tmp_path / "already-published.cmpct"
    sentinel = b"preexisting archive bytes must not be overwritten"
    output.write_bytes(sentinel)

    def list_attrs(path, *, follow_symlinks=False):
        assert follow_symlinks is False
        return [KEY] if os.fspath(path).endswith(".txt") else []

    def get_attr(path, key, *, follow_symlinks=False):
        assert follow_symlinks is False and key == KEY
        if os.fspath(path).endswith("z-last.txt"):
            raise OSError(errno.EACCES, "late observed xattr unreadable")
        return VALUE

    with monkeypatch.context() as patch:
        patch.setattr(os, "listxattr", list_attrs, raising=False)
        patch.setattr(os, "getxattr", get_attr, raising=False)
        with pytest.raises(OSError, match="cannot read xattr"):
            Builder(root, workers=1).build(output)
    assert output.read_bytes() == sentinel


def test_unsupported_source_enumeration_preserves_portable_empty_xattr_archive(tmp_path, monkeypatch):
    root, payload = source(tmp_path)
    out = tmp_path / "unsupported.cmpct"

    def unsupported(*args, **kwargs):
        raise OSError(errno.ENOTSUP, "enumerator unsupported")

    def must_not_get(*args, **kwargs):
        raise AssertionError("cannot get a key that was never observed")

    with monkeypatch.context() as patch:
        patch.setattr(os, "listxattr", unsupported, raising=False)
        patch.setattr(os, "getxattr", must_not_get, raising=False)
        Builder(root, workers=1).build(out)

    with CMPCT(out) as reader, monkeypatch.context() as patch:
        assert not reader.fsmeta.get("xattrs")
        patch.delattr(os, "setxattr", raising=False)
        dest = tmp_path / "strict-no-attributes"
        reader.extractall(dest, require_xattrs=True)
    assert (dest / "member.txt").read_bytes() == payload


def test_destination_denial_propagates_in_strict_mode_but_not_portable_mode(tmp_path, monkeypatch):
    archive, payload = archive_with_observed_xattr(tmp_path, monkeypatch)

    def denied(*args, **kwargs):
        raise OSError(errno.EPERM, "destination denies xattr application")

    with CMPCT(archive) as reader, monkeypatch.context() as patch:
        patch.setattr(os, "setxattr", denied, raising=False)
        dest_strict = tmp_path / "denied"
        with pytest.raises(IOError, match="xattr restoration failed") as err:
            reader.extractall(dest_strict, require_xattrs=True)
        assert isinstance(err.value.__cause__, OSError)
        # Document actual late-failure semantics: not an atomic extraction transaction.
        assert (dest_strict / "member.txt").read_bytes() == payload
        dest_portable = tmp_path / "portable"
        reader.extractall(dest_portable)
    assert (dest_portable / "member.txt").read_bytes() == payload


def test_reproducible_source_disables_metadata_probing_and_archive_bytes_are_stable(tmp_path, monkeypatch):
    root, payload = source(tmp_path)
    out1 = tmp_path / "first.cmpct"
    out2 = tmp_path / "second.cmpct"

    def forbidden(*args, **kwargs):
        raise AssertionError("reproducible capture must not query host xattrs")

    with monkeypatch.context() as patch:
        patch.setattr(os, "listxattr", forbidden, raising=False)
        patch.setattr(os, "getxattr", forbidden, raising=False)
        Builder(root, workers=1, reproducible=True).build(out1)
        Builder(root, workers=1, reproducible=True).build(out2)
    assert out1.read_bytes() == out2.read_bytes()
    with CMPCT(out1) as reader:
        assert reader.verify() == 1
        assert reader.read("member.txt") == payload


@pytest.mark.skipif(sys.platform != "linux", reason="real Linux kernel user-xattr positive control")
def test_linux_kernel_xattr_capture_and_strict_readback(tmp_path):
    assert all(hasattr(os, n) for n in ("setxattr", "listxattr", "getxattr"))
    root, payload = source(tmp_path)
    leaf = root / "member.txt"
    os.setxattr(leaf, KEY, VALUE, follow_symlinks=False)
    assert os.getxattr(leaf, KEY, follow_symlinks=False) == VALUE

    out = tmp_path / "linux-kernel.cmpct"
    Builder(root, workers=1).build(out)
    with CMPCT(out) as reader:
        assert reader.verify() == 1
        dest = tmp_path / "linux-kernel-output"
        reader.extractall(dest, require_xattrs=True)
    assert (dest / "member.txt").read_bytes() == payload
    assert os.getxattr(dest / "member.txt", KEY, follow_symlinks=False) == VALUE
