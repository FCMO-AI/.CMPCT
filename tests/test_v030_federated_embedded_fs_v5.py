from __future__ import annotations

import os
from pathlib import Path

import pytest

from experiments import entropygraph_v030_federated_embedded_fs_candidate_v5 as EG05


def _fixture(root: Path) -> None:
    (root / "docs").mkdir(parents=True)
    owner = root / "docs" / "owner.bin"
    owner.write_bytes((b"federated-eg05-owner\n" * 4096) + b"tail")
    (root / "plain.txt").write_text("embedded metadata control\n" * 2048, encoding="utf-8")
    try:
        os.link(owner, root / "docs" / "owner-hardlink.bin")
    except OSError:
        pytest.skip("filesystem does not support hardlinks")
    try:
        os.symlink("owner.bin", root / "docs" / "owner-link")
    except OSError:
        pytest.skip("filesystem does not support symlinks")


def test_eg05_embeds_fs_control_and_roundtrips(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    _fixture(source)
    archive = tmp_path / "candidate.cmpct"
    stats = EG05.build(source, archive)
    assert stats["profile"] == "federated-eg05-embedded-fs"
    assert stats["filesystem_control_storage"] == "authenticated-primary-tail-metadata"
    assert stats["locality"]["within_release_bounds"] is True

    control = EG05._metadata_control(archive)
    assert control
    with EG05._engine(archive):
        stream, meta, _packs = EG05.V25.open_ar()
        try:
            assert meta[EG05.EMBEDDED_FS_KEY] == control
            assert all(path != ".__cmpct_no_physical_fs_member__" for path, _desc in meta["files"])
        finally:
            stream.close()

    verified = EG05.strong_verify(archive, expected_tree=EG05._treehash(source))
    assert verified["ok"] is True
    restored = tmp_path / "restored"
    EG05.extract(archive, restored)
    assert EG05._treehash(restored) == EG05._treehash(source)
    assert (restored / "docs" / "owner-link").is_symlink()
    assert os.readlink(restored / "docs" / "owner-link") == "owner.bin"
    assert os.stat(restored / "docs" / "owner.bin").st_ino == os.stat(restored / "docs" / "owner-hardlink.bin").st_ino


def test_eg05_primary_metadata_corruption_recovers_from_tail(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    _fixture(source)
    archive = tmp_path / "candidate.cmpct"
    EG05.build(source, archive)
    raw = bytearray(archive.read_bytes())
    _magic, mcs, _mus, _packs, _hash = EG05.V25.HDR.unpack_from(raw, 0)
    assert mcs > 4
    raw[EG05.V25.HDR.size + 2] ^= 0x01
    archive.write_bytes(raw)
    verified = EG05.strong_verify(archive, expected_tree=EG05._treehash(source))
    assert verified["ok"] is True
