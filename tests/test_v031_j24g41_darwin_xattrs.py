"""J24G41 source-exact physical Darwin xattrs and O72 inheritance.

Research/provisional product court: a green native bridge test is not evidence
of atomic whole-tree snapshots, ACL fidelity or release readiness.
"""
from __future__ import annotations

import errno
import hashlib
import os
from pathlib import Path
import subprocess
import sys

import pytest

from cmpct import _xattrs
from cmpct.builder import Builder
from cmpct.reader import CMPCT

KEY_MAC = "com.fcmo.cmpct.j24g41"
KEY_LINUX = "user.cmpct_j24g41"
VALUE = b"J24G41 native xattr\x00\xff\x01"


def _native_mac_write(path: Path, key: str, value: bytes):
    assert sys.platform == "darwin"
    subprocess.run(
        ["/usr/bin/xattr", "-wx", key, value.hex(), os.fspath(path)],
        capture_output=True, text=True, check=True,
    )


def _native_mac_read(path: Path, key: str) -> bytes:
    result = subprocess.run(
        ["/usr/bin/xattr", "-px", key, os.fspath(path)],
        capture_output=True, text=True, check=True,
    )
    return bytes.fromhex("".join(result.stdout.split()))


def test_provider_capability_matches_native_platform():
    assert _xattrs.can_list() == (hasattr(os, "listxattr") or sys.platform == "darwin")
    assert _xattrs.can_set() == (hasattr(os, "setxattr") or sys.platform == "darwin")


@pytest.mark.skipif(sys.platform not in ("darwin", "linux"), reason="physical POSIX fixture")
def test_native_xattr_roundtrip_through_authentic_r24_archive(tmp_path):
    source = tmp_path / "src"
    source.mkdir()
    payload = b"J24G41 exact payload\x00" * 113
    leaf = source / "member.bin"
    leaf.write_bytes(payload)
    original_sha = hashlib.sha256(payload).hexdigest()
    key = KEY_MAC if sys.platform == "darwin" else KEY_LINUX

    # The independent OS writer/getter establish a *real* source xattr. A skipped
    # or failed fixture is not permitted to masquerade as CMPCT correctness.
    if sys.platform == "darwin":
        _native_mac_write(leaf, key, VALUE)
        assert _native_mac_read(leaf, key) == VALUE
    else:
        os.setxattr(leaf, key, VALUE, follow_symlinks=False)
        assert os.getxattr(leaf, key, follow_symlinks=False) == VALUE

    assert key in _xattrs.listxattr(leaf, follow_symlinks=False)
    assert _xattrs.getxattr(leaf, key, follow_symlinks=False) == VALUE

    archive = tmp_path / "native.cmpct"
    Builder(source, workers=1, reproducible=False).build(archive)
    with CMPCT(archive) as reader:
        assert reader.verify() == 1
        assert reader.read("member.bin") == payload
        rows = [(i, dict(attrs)) for i, attrs in reader.fsmeta["xattrs"]]
        assert len(rows) == 1
        assert rows[0][0] == 0
        assert rows[0][1][key] == VALUE
        destination = tmp_path / "dest"
        reader.extractall(destination, require_xattrs=True)

    restored = destination / "member.bin"
    assert hashlib.sha256(restored.read_bytes()).hexdigest() == original_sha
    if sys.platform == "darwin":
        assert _native_mac_read(restored, key) == VALUE
    else:
        assert os.getxattr(restored, key, follow_symlinks=False) == VALUE
    assert hashlib.sha256(leaf.read_bytes()).hexdigest() == original_sha


@pytest.mark.skipif(sys.platform != "darwin", reason="Darwin NOFOLLOW ABI")
def test_darwin_nofollow_does_not_inherit_target_xattr(tmp_path):
    leaf = tmp_path / "physical"
    leaf.write_bytes(b"target")
    link = tmp_path / "link"
    link.symlink_to(leaf)
    _native_mac_write(leaf, KEY_MAC, VALUE)
    assert _native_mac_read(leaf, KEY_MAC) == VALUE
    assert KEY_MAC in _xattrs.listxattr(link, follow_symlinks=True)
    # A symlink may have its own xattrs, but must not borrow the target's.
    assert KEY_MAC not in _xattrs.listxattr(link, follow_symlinks=False)


def test_bounded_native_two_pass_never_silently_truncates():
    with pytest.raises(OSError) as too_large:
        _xattrs._bounded_copy("path", lambda: 1025, lambda _b, _s: 0, 1024)
    assert too_large.value.errno == errno.E2BIG

    invocations = []
    def racing_read(_buf, _size):
        invocations.append(1)
        raise OSError(errno.ERANGE, "attribute changed")
    with pytest.raises(OSError) as changed:
        _xattrs._bounded_copy("path", lambda: 3, racing_read, 100)
    assert changed.value.errno == errno.ERANGE
    assert len(invocations) == 3

    with pytest.raises(OSError) as invalid_length:
        _xattrs._bounded_copy("path", lambda: 1, lambda _b, _s: 2, 100)
    assert invalid_length.value.errno == errno.EIO


def test_native_name_is_lossless_or_rejected():
    assert _xattrs._name_bytes(KEY_MAC) == KEY_MAC.encode()
    with pytest.raises(UnicodeDecodeError):
        _xattrs._name_bytes(b"invalid-\xff")
    with pytest.raises(ValueError):
        _xattrs._name_bytes("bad\x00name")


def test_missing_darwin_provider_symbol_is_fail_closed_not_no_xattr(monkeypatch):
    # An ABI-loading failure is NOT ENOSYS from the user's filesystem.
    # O65 historically accepts ENOSYS as unsupported xattr enumeration,
    # so accidentally returning ENOSYS here would silently erase metadata.
    class MissingNativeSymbols:
        pass

    with monkeypatch.context() as patch:
        patch.setattr(_xattrs, "_DARWIN", True)
        patch.setattr(_xattrs.ctypes, "CDLL", lambda *_a, **_kw: MissingNativeSymbols())
        _xattrs._darwin_api.cache_clear()
        try:
            with pytest.raises(OSError) as err:
                _xattrs._darwin_api()
            assert err.value.errno == errno.EIO
        finally:
            _xattrs._darwin_api.cache_clear()
