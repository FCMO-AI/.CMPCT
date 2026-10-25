"""O69: opt-in truthful xattr application without changing portable default semantics."""
from __future__ import annotations

import errno
import os
import sys
from pathlib import Path

import pytest

from cmpct.core import Builder, CMPCT


KEY = "user.cmpct_o69"
VALUE = b"\x00\xff\x01signed-xattr"


def _signed_xattr_archive(tmp_path: Path, monkeypatch) -> Path:
    """Construct a real r24 archive with an authenticated fsmeta xattr on every host.

    The source-side API is injected only during Builder construction: the Reader
    under test consumes the actual serialized, hashed archive, not a fake index.
    """
    src = tmp_path / "source"
    src.mkdir()
    (src / "member.bin").write_bytes(b"recovered payload\x00\x01")
    archive = tmp_path / "signed-xattr.cmpct"

    def enumerate_attrs(path, *, follow_symlinks=False):
        assert follow_symlinks is False
        return [KEY] if os.fspath(path).endswith("member.bin") else []

    def read_attr(path, name, *, follow_symlinks=False):
        assert follow_symlinks is False
        assert os.fspath(path).endswith("member.bin")
        assert name == KEY
        return VALUE

    with monkeypatch.context() as patch:
        patch.setattr(os, "listxattr", enumerate_attrs, raising=False)
        patch.setattr(os, "getxattr", read_attr, raising=False)
        Builder(src, workers=1).build(archive)

    with CMPCT(archive) as reader:
        assert reader.verify() == 1
        assert reader.fsmeta["xattrs"]
        assert reader.read("member.bin") == (src / "member.bin").read_bytes()
    return archive


def test_default_remains_best_effort_on_failed_setxattr(tmp_path, monkeypatch):
    archive = _signed_xattr_archive(tmp_path, monkeypatch)

    def fail(*args, **kwargs):
        raise OSError(errno.EPERM, "intentionally denied")

    with CMPCT(archive) as reader, monkeypatch.context() as patch:
        patch.setattr(os, "setxattr", fail, raising=False)
        dest = tmp_path / "best-effort"
        reader.extractall(dest)
        assert (dest / "member.bin").read_bytes() == b"recovered payload\x00\x01"


def test_opt_in_surfaces_xattr_failure_without_claiming_atomic_rollback(tmp_path, monkeypatch):
    archive = _signed_xattr_archive(tmp_path, monkeypatch)

    def fail(*args, **kwargs):
        raise OSError(errno.ENOTSUP, "destination cannot store xattrs")

    with CMPCT(archive) as reader, monkeypatch.context() as patch:
        patch.setattr(os, "setxattr", fail, raising=False)
        dest = tmp_path / "strict"
        with pytest.raises(IOError, match=r"xattr restoration failed.*member.bin.*cmpct_o69") as error:
            reader.extractall(dest, require_xattrs=True)
        assert isinstance(error.value.__cause__, OSError)
        # A post-write xattr error is not a claim of transactional extraction.
        assert (dest / "member.bin").read_bytes() == b"recovered payload\x00\x01"


def test_opt_in_applies_exact_authenticated_xattr_value(tmp_path, monkeypatch):
    archive = _signed_xattr_archive(tmp_path, monkeypatch)
    calls = []

    def record(path, name, value, *, follow_symlinks=False):
        calls.append((Path(path).name, name, value, follow_symlinks))

    with CMPCT(archive) as reader, monkeypatch.context() as patch:
        patch.setattr(os, "setxattr", record, raising=False)
        dest = tmp_path / "restored"
        reader.extractall(dest, require_xattrs=True)
        assert (dest / "member.bin").read_bytes() == b"recovered payload\x00\x01"
    assert calls == [("member.bin", KEY, VALUE, False)]


def test_missing_host_api_is_rejected_before_destination_creation(tmp_path, monkeypatch):
    archive = _signed_xattr_archive(tmp_path, monkeypatch)
    dest = tmp_path / "must-remain-absent"

    with CMPCT(archive) as reader, monkeypatch.context() as patch:
        patch.delattr(os, "setxattr", raising=False)
        with pytest.raises(IOError, match="unsupported by destination host"):
            reader.extractall(dest, require_xattrs=True)
    assert not dest.exists()


def test_contradictory_opt_in_is_rejected_before_destination_creation(tmp_path, monkeypatch):
    archive = _signed_xattr_archive(tmp_path, monkeypatch)
    dest = tmp_path / "must-also-remain-absent"

    with CMPCT(archive) as reader:
        with pytest.raises(ValueError, match="requires metadata=True"):
            reader.extractall(dest, metadata=False, require_xattrs=True)
    assert not dest.exists()


def test_empty_xattr_archive_requires_no_host_support(tmp_path, monkeypatch):
    src = tmp_path / "empty-metadata-src"
    src.mkdir()
    (src / "plain.bin").write_bytes(b"nothing to restore")
    archive = tmp_path / "no-xattrs.cmpct"
    Builder(src, reproducible=True, workers=1).build(archive)

    with CMPCT(archive) as reader, monkeypatch.context() as patch:
        assert not reader.fsmeta.get("xattrs")
        patch.delattr(os, "setxattr", raising=False)
        dest = tmp_path / "no-xattrs-dest"
        reader.extractall(dest, require_xattrs=True)
        assert (dest / "plain.bin").read_bytes() == b"nothing to restore"


@pytest.mark.skipif(sys.platform != "linux", reason="real Linux user-xattr roundtrip only")
def test_linux_real_xattr_roundtrip_when_supported(tmp_path):
    if not all(hasattr(os, n) for n in ("setxattr", "getxattr", "listxattr")):
        pytest.skip("host lacks xattr API")
    src = tmp_path / "real-source"
    src.mkdir()
    member = src / "data.bin"
    member.write_bytes(b"live filesystem metadata")
    try:
        os.setxattr(member, KEY, VALUE, follow_symlinks=False)
    except OSError as exc:
        if exc.errno in (errno.ENOTSUP, getattr(errno, "EOPNOTSUPP", errno.ENOTSUP), errno.EPERM):
            pytest.skip("runner does not permit user namespace xattrs")
        raise

    archive = tmp_path / "real.cmpct"
    Builder(src, workers=1).build(archive)
    with CMPCT(archive) as reader:
        assert reader.verify() == 1
        dest = tmp_path / "real-dest"
        reader.extractall(dest, require_xattrs=True)
    assert (dest / "data.bin").read_bytes() == member.read_bytes()
    assert os.getxattr(dest / "data.bin", KEY, follow_symlinks=False) == VALUE
