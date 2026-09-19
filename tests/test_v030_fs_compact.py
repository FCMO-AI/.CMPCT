from __future__ import annotations

import os
from pathlib import Path

import msgpack
import pytest

from experiments import entropygraph_v030_fs_compact as CFS
from experiments import entropygraph_v030_product_fs as FS


def _capture(root: Path):
    return FS.capture_filesystem_manifest(
        root,
        max_path_bytes=4096,
        max_profile_files=1024,
        max_profile_logical_bytes=64 * 1024 * 1024,
        max_entries=4096,
    )


def test_compact_manifest_preserves_exact_semantics_and_removes_regular_identity_duplication(tmp_path: Path):
    root = tmp_path / "source"
    root.mkdir()
    (root / "dir").mkdir()
    owner = root / "dir" / "a.bin"
    owner.write_bytes(b"alpha" * 8192)
    alias = root / "dir" / "b.bin"
    os.link(owner, alias)
    (root / "notes.txt").write_text("hello\n" * 100, encoding="utf-8")
    link = root / "z-link"
    link.symlink_to("notes.txt")

    raw_v1, regular_sources, _ = _capture(root)
    raw_v2 = CFS.encode_v1(raw_v1, max_path_bytes=4096, max_entries=4096)
    assert CFS.semantics_equal(raw_v1, raw_v2, max_path_bytes=4096, max_entries=4096)
    assert len(raw_v2) < len(raw_v1)

    # The compact wire form deliberately carries no 32-byte regular-file digests. Their sole authenticated owner
    # is the federated content graph; the control plane must not silently reacquire a duplicate identity copy.
    v1 = FS.decode_manifest(raw_v1, max_path_bytes=4096, max_entries=4096)
    for _path, (_size, digest) in v1["regular"].items():
        assert digest not in raw_v2

    profile = tmp_path / "profile"
    profile.mkdir()
    for source, rel in regular_sources:
        target = profile / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        os.link(source, target)
    manifest_path = profile / FS.FILESYSTEM_MANIFEST
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_bytes(raw_v2)

    identities = CFS.identities_from_profile(
        profile,
        raw_v2,
        max_path_bytes=4096,
        max_entries=4096,
    )
    expanded = CFS.decode_to_v1(
        raw_v2,
        regular_identities=identities,
        max_path_bytes=4096,
        max_entries=4096,
    )
    assert expanded["manifest"] == v1["manifest"]


def test_compact_manifest_rejects_graph_path_mismatch(tmp_path: Path):
    root = tmp_path / "source"
    root.mkdir()
    (root / "a.bin").write_bytes(b"A" * 4096)
    raw_v1, regular_sources, _ = _capture(root)
    raw_v2 = CFS.encode_v1(raw_v1, max_path_bytes=4096, max_entries=4096)

    profile = tmp_path / "profile"
    profile.mkdir()
    for source, rel in regular_sources:
        target = profile / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        os.link(source, target)
    internal = profile / FS.FILESYSTEM_MANIFEST
    internal.parent.mkdir(parents=True, exist_ok=True)
    internal.write_bytes(raw_v2)
    (profile / "unexpected.bin").write_bytes(b"evil")

    with pytest.raises(RuntimeError, match="path mismatch"):
        CFS.identities_from_profile(profile, raw_v2, max_path_bytes=4096, max_entries=4096)


def test_compact_manifest_rejects_noncanonical_path_delta(tmp_path: Path):
    root = tmp_path / "source"
    root.mkdir()
    (root / "a").write_bytes(b"a")
    (root / "b").write_bytes(b"b")
    raw_v1, _, _ = _capture(root)
    raw_v2 = CFS.encode_v1(raw_v1, max_path_bytes=4096, max_entries=4096)
    payload = msgpack.unpackb(raw_v2, raw=False)
    # Force the second row to reconstruct the first path again.
    payload[2][1][0] = 0
    payload[2][1][1] = payload[2][0][1]
    bad = msgpack.packb(payload, use_bin_type=True)
    with pytest.raises(RuntimeError, match="sorted/unique"):
        CFS.regular_paths(bad, max_path_bytes=4096, max_entries=4096)
