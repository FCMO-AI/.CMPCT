from __future__ import annotations

import os
from pathlib import Path

import msgpack
import pytest

from experiments import entropygraph_v030_fs_implicit as IFS3
from experiments import entropygraph_v030_fs_implicit_v4 as IFS4
from experiments import entropygraph_v030_product_fs as FS


def _capture(root: Path):
    return FS.capture_filesystem_manifest(
        root,
        max_path_bytes=4096,
        max_profile_files=1024,
        max_profile_logical_bytes=64 * 1024 * 1024,
        max_entries=4096,
    )


def test_implicit_v4_preserves_semantics_and_compacts_repeated_metadata(tmp_path: Path):
    root = tmp_path / "source"
    root.mkdir()
    (root / "assets").mkdir()
    for index in range(24):
        path = root / "assets" / f"artifact-{index:02d}.bin"
        path.write_bytes((f"row-{index}\n".encode()) * 128)
        os.chmod(path, 0o644)
        os.utime(path, ns=(1_700_000_000_000_000_000 + index * 1_000_000,)*2)
    os.chmod(root / "assets", 0o755)
    os.utime(root / "assets", ns=(1_700_000_000_000_000_000,)*2)

    raw_v1, regular_sources, _ = _capture(root)
    raw_v3 = IFS3.encode_v1(raw_v1, max_path_bytes=4096, max_entries=4096)
    raw_v4 = IFS4.encode_v1(raw_v1, max_path_bytes=4096, max_entries=4096)
    assert IFS4.semantics_equal(raw_v1, raw_v4, max_path_bytes=4096, max_entries=4096)
    assert len(raw_v4) < len(raw_v3)

    payload = msgpack.unpackb(raw_v4, raw=False)
    assert payload[0] == IFS4.IMPLICIT_V4_VERSION
    default = payload[1]
    regular_overrides = payload[2]
    assert len(default) == 5
    assert len(regular_overrides) == len(regular_sources)
    # Numeric metadata that differs from the default is represented as a delta, not a repeated absolute stat tuple.
    assert all(isinstance(row, list) and row and isinstance(row[0], int) for row in regular_overrides)

    profile = tmp_path / "profile"
    profile.mkdir()
    for source, rel in regular_sources:
        target = profile / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        os.link(source, target)
    internal_path = f"{FS.INTERNAL_ROOT}/f4"
    internal = profile / internal_path
    internal.parent.mkdir(parents=True, exist_ok=True)
    internal.write_bytes(raw_v4)
    identities = IFS4.identities_from_profile(
        profile,
        raw_v4,
        max_path_bytes=4096,
        max_entries=4096,
        internal_path=internal_path,
    )
    expanded = IFS4.decode_to_v1(
        raw_v4,
        regular_identities=identities,
        max_path_bytes=4096,
        max_entries=4096,
    )
    original = FS.decode_manifest(raw_v1, max_path_bytes=4096, max_entries=4096)
    assert expanded["manifest"] == original["manifest"]


def test_implicit_v4_preserves_hardlink_symlink_and_signed_mtime(tmp_path: Path):
    root = tmp_path / "source"
    root.mkdir()
    owner = root / "owner.bin"
    owner.write_bytes(b"owner" * 1024)
    os.link(owner, root / "owner-alias.bin")
    (root / "link").symlink_to("owner.bin")
    os.utime(owner, ns=(-1_000_000_000, -1_000_000_000))

    raw_v1, _, _ = _capture(root)
    raw_v4 = IFS4.encode_v1(raw_v1, max_path_bytes=4096, max_entries=4096)
    original = FS.decode_manifest(raw_v1, max_path_bytes=4096, max_entries=4096)
    identities = {path: identity for path, identity in original["regular"].items()}
    expanded = IFS4.decode_to_v1(
        raw_v4,
        regular_identities=identities,
        max_path_bytes=4096,
        max_entries=4096,
    )
    assert expanded["manifest"] == original["manifest"]
    assert expanded["hardlinks"]


def test_implicit_v4_rejects_malformed_override_and_hardlink_index(tmp_path: Path):
    root = tmp_path / "source"
    root.mkdir()
    owner = root / "a.bin"
    owner.write_bytes(b"A" * 4096)
    os.link(owner, root / "b.bin")
    raw_v1, _, _ = _capture(root)
    raw_v4 = IFS4.encode_v1(raw_v1, max_path_bytes=4096, max_entries=4096)
    payload = msgpack.unpackb(raw_v4, raw=False)

    broken_override = msgpack.unpackb(raw_v4, raw=False)
    broken_override[2][0] = [0x80]
    with pytest.raises(RuntimeError, match="override mask"):
        IFS4.decode_to_v1(
            msgpack.packb(broken_override, use_bin_type=True),
            regular_identities={"a.bin": (4096, b"0" * 32)},
            max_path_bytes=4096,
            max_entries=4096,
        )

    hardlinks = [row for row in payload[3] if row[2] == 3]
    assert len(hardlinks) == 1
    hardlinks[0][4] = len(payload[2])
    with pytest.raises(RuntimeError, match="hardlink target"):
        IFS4.decode_to_v1(
            msgpack.packb(payload, use_bin_type=True),
            regular_identities={"a.bin": (4096, b"0" * 32)},
            max_path_bytes=4096,
            max_entries=4096,
        )
