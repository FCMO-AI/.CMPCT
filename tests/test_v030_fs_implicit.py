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


def _explicit_paths(payload: list) -> list[str]:
    """Reconstruct only filesystem-owned explicit path declarations.

    Symlink *targets* are semantic payload and may legitimately equal a regular path.
    The ownership invariant is that regular paths are absent from the explicit-path
    declarations themselves, not that their UTF-8 bytes can never appear anywhere
    in the MessagePack stream.
    """
    previous = ""
    paths: list[str] = []
    for row in payload[3]:
        prefix, suffix = row[0], row[1]
        rel = previous[:prefix] + suffix
        paths.append(rel)
        previous = rel
    return paths


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
    # Regular paths are intentionally absent from the filesystem-owned path declarations. They remain
    # authenticated by the federated content graph and are supplied to decoding only through its verified
    # identity map. A symlink target may legitimately contain the same path text, so raw-byte absence would
    # overstate the ownership rule and reject valid semantics.
    explicit_paths = set(_explicit_paths(payload))
    regular_paths = {rel for _source, rel in regular_sources}
    assert regular_paths.isdisjoint(explicit_paths)
    assert len(payload[2]) == len(regular_paths)
    assert all(isinstance(index, int) and not isinstance(index, bool) for index in payload[2])

    # The fixture deliberately exercises the aliasing case that made raw-stream substring testing invalid:
    # the symlink target names a regular file, but that name is semantic link payload rather than a second
    # filesystem-owned regular-path declaration.
    symlink_rows = [row for row in payload[3] if row[2] == 2]
    assert len(symlink_rows) == 1
    assert symlink_rows[0][4] == note.name
    assert symlink_rows[0][4] in regular_paths

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
