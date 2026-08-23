from __future__ import annotations

from pathlib import Path

import pytest

from experiments import entropygraph_v025 as V25
from experiments import entropygraph_v030_federated_embedded_fs_candidate_v7 as EG07


def _source(root: Path) -> Path:
    src = root / "source"
    src.mkdir()
    (src / "alpha.bin").write_bytes((b"alpha-beta-gamma\n" * 8192) + bytes(range(256)) * 64)
    (src / "beta.txt").write_text("fused verification keeps one reconstruction\n" * 4096, encoding="utf-8")
    return src


def test_eg07_strong_verify_reconstructs_logical_profile_once(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source = _source(tmp_path)
    archive = tmp_path / "sample.c25eg07"
    EG07.build(source, archive)

    original_extract = V25.extract
    calls = 0

    def counted_extract(destination: Path):
        nonlocal calls
        calls += 1
        return original_extract(destination)

    monkeypatch.setattr(V25, "extract", counted_extract)
    result = EG07.strong_verify(archive, expected_tree=EG07._treehash(source))

    assert result["ok"] is True
    assert result["logical_reconstruction_passes"] == 1
    assert result["inner"]["physical_pack_sha256_verified"] is True
    assert result["inner"]["tree_sha256"]
    assert result["canonical_user_tree_sha256"] == EG07._treehash(source)
    assert calls == 1


def test_eg07_fused_verify_still_rejects_corrupt_pack_payload(tmp_path: Path) -> None:
    source = _source(tmp_path)
    archive = tmp_path / "sample.c25eg07"
    EG07.build(source, archive)

    raw = bytearray(archive.read_bytes())
    magic, metadata_csize, _metadata_usize, pack_count, _digest = V25.HDR.unpack_from(raw, 0)
    assert magic == EG07.MAGIC
    assert pack_count > 0
    first_header = V25.HDR.size + int(metadata_csize)
    _codec, _usize, csize, _crc, _sha = V25.PH.unpack_from(raw, first_header)
    assert csize > 0
    payload_offset = first_header + V25.PH.size
    raw[payload_offset + int(csize) // 2] ^= 0x01
    corrupt = tmp_path / "corrupt.c25eg07"
    corrupt.write_bytes(raw)

    with pytest.raises(Exception, match=r"pack (CRC|SHA-256|size)|decompress"):
        EG07.strong_verify(corrupt, expected_tree=EG07._treehash(source))
