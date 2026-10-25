"""O84 cross-owner source-fidelity and output-ownership interaction controls.

Inherited O80 and O81 owner suites run unmodified alongside this file.
These controls use real installed revision-24 Builder and Reader APIs.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest
from cmpct.builder import Builder
from cmpct.reader import CMPCT


def _root(tmp_path: Path):
    root = tmp_path / "source"
    root.mkdir()
    payload = b"o84-root-regular-link-xattr" * 181
    (root / "payload.bin").write_bytes(payload)
    os.link(root / "payload.bin", root / "member-hardlink.bin")
    if os.name != "nt":
        (root / "member-symlink").symlink_to("payload.bin")
    key = "user.cmpct_o84"
    value = b"\x00o84-metadata\xff"
    xattr = False
    if hasattr(os, "setxattr") and hasattr(os, "getxattr"):
        try:
            os.setxattr(root / "payload.bin", key, value, follow_symlinks=False)
            xattr = os.getxattr(root / "payload.bin", key, follow_symlinks=False) == value
        except (OSError, NotImplementedError, TypeError):
            pass
    return root, payload, key, value, xattr


def test_mixed_source_rejects_external_output_alias_then_reconstructs(tmp_path: Path):
    root, payload, key, value, has_xattr = _root(tmp_path)
    output = tmp_path / "external-output.cmpct"
    os.link(root / "payload.bin", output)
    before = output.read_bytes()
    with pytest.raises(ValueError, match="hardlink to source"):
        Builder(root, workers=1).build(output)
    assert output.read_bytes() == before == payload
    assert (root / "payload.bin").read_bytes() == payload
    assert (root / "member-hardlink.bin").read_bytes() == payload

    output.unlink()
    Builder(root, workers=1).build(output)
    with CMPCT(output) as archive:
        assert archive.verify() >= 1
        dest = tmp_path / "restored"
        # This is a Builder/source-ownership court, not the independently owned
        # Reader metadata-portability repair (O69). On Windows the unchanged
        # Reader raises NotImplementedError for utime(follow_symlinks=False).
        # Retain real byte/hardlink extraction with metadata=False on Windows;
        # Linux/macOS continue exercising physical xattr restoration.
        archive.extractall(dest, metadata=(os.name != 'nt'))
    assert (dest / "payload.bin").read_bytes() == payload
    assert (dest / "member-hardlink.bin").read_bytes() == payload
    assert (os.stat(dest / "payload.bin").st_dev, os.stat(dest / "payload.bin").st_ino) == (
        os.stat(dest / "member-hardlink.bin").st_dev, os.stat(dest / "member-hardlink.bin").st_ino
    )
    if os.name != "nt":
        assert os.readlink(dest / "member-symlink") == "payload.bin"
    if has_xattr:
        assert os.getxattr(dest / "payload.bin", key, follow_symlinks=False) == value


def test_in_tree_output_rejected_before_source_inventory(tmp_path: Path, monkeypatch):
    root, payload, _, _, _ = _root(tmp_path)
    out = root / "subdir" / "fresh.cmpct"
    out.parent.mkdir()
    called = []
    original_scandir = os.scandir

    def watch_scandir(path):
        called.append(os.fspath(path))
        return original_scandir(path)

    monkeypatch.setattr(os, "scandir", watch_scandir)
    with pytest.raises(ValueError, match="outside the source root"):
        Builder(root, workers=1).build(out)
    assert not called, "preflight must not scan an in-tree destination"
    assert not out.exists()
    assert (root / "payload.bin").read_bytes() == payload
