"""O65: xattr-error admission must not turn an incomplete source into a successful r24 archive.

These deterministic failure-injection tests distinguish a listed-but-unreadable
attribute (loss) from an unsupported xattr enumeration interface (compatibility).
They do not claim to model the frequency of real filesystem errors.
"""
from __future__ import annotations

import errno
import os
from pathlib import Path

import pytest

from cmpct.builder import Builder


POSIX_XATTR = pytest.mark.skipif(
    not hasattr(os, "listxattr") or not hasattr(os, "getxattr"),
    reason="POSIX extended-attribute enumeration API unavailable",
)


def source(tmp_path: Path) -> tuple[Path, Path]:
    root = tmp_path / "tree"
    root.mkdir()
    leaf = root / "payload.bin"
    leaf.write_bytes(b"O65 deterministic xattr source\n")
    return root, leaf


def list_one(_path, *, follow_symlinks=False):
    assert follow_symlinks is False
    return ["user.cmpct_o65"]


@POSIX_XATTR
def test_listed_xattr_values_are_recorded_exactly(tmp_path, monkeypatch):
    root, _ = source(tmp_path)
    monkeypatch.setattr(os, "listxattr", list_one)

    def get_value(_path, name, *, follow_symlinks=False):
        assert name == "user.cmpct_o65"
        assert follow_symlinks is False
        return b"\x00O65\xff"

    monkeypatch.setattr(os, "getxattr", get_value)
    builder = Builder(root, workers=1)
    builder.scan()
    assert builder.meta_by_rel["payload.bin"][2] == {"user.cmpct_o65": b"\x00O65\xff"}


@POSIX_XATTR
@pytest.mark.parametrize(
    ("stage", "error"),
    [
        ("list", errno.EACCES),
        ("list", errno.EIO),
        ("get", errno.EACCES),
        ("get", getattr(errno, "ENODATA", errno.ENOENT)),
        ("get", getattr(errno, "EOPNOTSUPP", errno.ENOTSUP)),
    ],
)
def test_errors_that_could_hide_metadata_refuse_publish(tmp_path, monkeypatch, stage, error):
    root, _ = source(tmp_path)
    output = tmp_path / "already-good.cmpct"
    sentinel = b"existing independent archive must survive\n"
    output.write_bytes(sentinel)

    def forbidden_list(_path, *, follow_symlinks=False):
        if stage == "list":
            raise OSError(error, "enumeration failed")
        return list_one(_path, follow_symlinks=follow_symlinks)

    def forbidden_get(_path, _name, *, follow_symlinks=False):
        raise OSError(error, "observed value unreadable")

    monkeypatch.setattr(os, "listxattr", forbidden_list)
    monkeypatch.setattr(os, "getxattr", forbidden_get)
    with pytest.raises(OSError):
        Builder(root, workers=1).build(output)
    assert output.read_bytes() == sentinel


@POSIX_XATTR
@pytest.mark.parametrize("error", sorted({errno.ENOTSUP, getattr(errno, "EOPNOTSUPP", errno.ENOTSUP), errno.ENOSYS}))
def test_unsupported_attribute_enumeration_keeps_historical_empty_metadata(tmp_path, monkeypatch, error):
    root, _ = source(tmp_path)

    def unsupported(_path, *, follow_symlinks=False):
        raise OSError(error, "filesystem has no supported xattr interface")

    monkeypatch.setattr(os, "listxattr", unsupported)
    builder = Builder(root, workers=1)
    builder.scan()
    assert builder.meta_by_rel["payload.bin"][2] == {}


def test_reproducible_mode_explicitly_normalizes_xattrs_without_probing(tmp_path, monkeypatch):
    root, _ = source(tmp_path)
    # The reproducible-byte-build contract deliberately discards host xattrs.
    # A doomed enumeration must not be attempted in this mode.
    if hasattr(os, "listxattr"):
        def forbidden(_path, **_kwargs):
            raise AssertionError("reproducible mode must not enumerate xattrs")
        monkeypatch.setattr(os, "listxattr", forbidden)
    builder = Builder(root, workers=1, reproducible=True)
    builder.scan()
    assert builder.meta_by_rel["payload.bin"] == (0, 0, {})
