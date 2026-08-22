from __future__ import annotations

import os
from pathlib import Path

import msgpack
import pytest

from experiments import entropygraph_v030_fs_compact as CFS2
from experiments import entropygraph_v030_fs_implicit as IFS
from experiments import entropygraph_v030_product_fs as FS


def _capture(root: Path):
    return FS.capture_filesystem_manifest(
        root,
        max_path_bytes=4096,
        max_profile_files=1024,
        max_profile_logical_bytes=64 * 1024 * 1024,
        max_entries=4096,
    )


def test_implicit_manifest_preserves_semantics_and_removes_regular_paths(tmp_path: Path):
    root = tmp_path / "source"
    root.mkdir()
    (root / "assets").mkdir()
    owner = root / "assets" / "very-long-regular-owner-name.bin"
    owner.write_bytes(b"alpha" * 8192)
    alias = root / "assets" / "alias.bin"
    os.link(owner, alias)
    note = root / "a-second-long-regular-document-name.txt"
    note.write_text("hello\n" * 200, encoding="utf-8")
    (root / "z-link").symlink_to(note.name)

    raw_v1, regular_sources, _ = _capture(root)
    raw_v2 = CFS2.encode_v1(raw_v1, max_path_bytes=4096, max_entries=4096)
    raw_v3 = IFS.encode_v1(raw_v1, max_path_bytes=4096, max_entries=4096)
    assert IFS.semantics_equal(raw_v1, raw_v3, max_path_bytes=4096, max_entries=4096)
    assert len(raw_v3) < len(raw_v2)

    payload = msgpack.unpackb(raw_v3, raw=False)
    assert payload[0] == IFS.IMPLICIT_VERSION
    # Regular paths are intentionally absent from the filesystem wire form. They remain authenticated by the
    # federated content graph and are supplied to decoding only through its verified identity map.
    for source, rel in regular_sources:
        assert rel.encode() not in raw_v3

    profile = tmp_path / "profile"
    profile.mkdir()
    for source, rel in regular_sources:
        target = profile / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        os.link(source, target)
    manifest = profile / FS.FILESYSTEM_MANIFEST
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_bytes(raw_v3)

    identities = IFS.identities_from_profile(profile, raw_v3, max_path_bytes=4096, max_entries=4096)
    expanded = IFS.decode_to_v1(
        raw_v3,
        regular_identities=identities,
        max_path_bytes=4096,
        max_entries=4096,
    )
    original = FS.decode_manifest(raw_v1, max_path_bytes=4096, max_entries=4096)
    assert expanded["manifest"] == original["manifest"]


def test_implicit_manifest_rejects_regular_count_or_explicit_path_collision(tmp_path: Path):
    root = tmp_path / "source"
    root.mkdir()
    (root / "a.bin").write_bytes(b"A" * 4096)
    raw_v1, regular_sources, _ = _capture(root)
    raw_v3 = IFS.encode_v1(raw_v1, max_path_bytes=4096, max_entries=4096)

    profile = tmp_path / "profile"
    profile.mkdir()
    for source, rel in regular_sources:
        target = profile / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        os.link(source, target)
    internal = profile / FS.FILESYSTEM_MANIFEST
    internal.parent.mkdir(parents=True, exist_ok=True)
    internal.write_bytes(raw_v3)
    (profile / "unexpected.bin").write_bytes(b"evil")
    with pytest.raises(RuntimeError, match="regular-count mismatch"):
        IFS.identities_from_profile(profile, raw_v3, max_path_bytes=4096, max_entries=4096)


def test_implicit_manifest_rejects_invalid_hardlink_graph_index(tmp_path: Path):
    root = tmp_path / "source"
    root.mkdir()
    owner = root / "a.bin"
    owner.write_bytes(b"A" * 4096)
    os.link(owner, root / "b.bin")
    raw_v1, _, _ = _capture(root)
    raw_v3 = IFS.encode_v1(raw_v1, max_path_bytes=4096, max_entries=4096)
    payload = msgpack.unpackb(raw_v3, raw=False)
    hardlink_rows = [row for row in payload[3] if row[2] == 3]
    assert len(hardlink_rows) == 1
    hardlink_rows[0][4] = len(payload[2])
    bad = msgpack.packb(payload, use_bin_type=True)
    with pytest.raises(RuntimeError, match="hardlink target"):
        IFS.decode_to_v1(
            bad,
            regular_identities={"a.bin": (4096, b"0" * 32)},
            max_path_bytes=4096,
            max_entries=4096,
        )
