"""Revision-24 PACK integrity regression: exact independent physical oracle.

Explicit verification must authenticate the *one* durable SHA-256 owner of
micro-packed slices (the physical blob), while normal reads retain CRC fast-path.
"""
from __future__ import annotations

import sys
from pathlib import Path

from cmpct import reader as reader_mod
from cmpct.reader import CMPCT

BENCHMARKS = Path(__file__).resolve().parents[1] / "benchmarks"
sys.path.insert(0, str(BENCHMARKS))
from v031_pack_physical_sha_court import archive_bytes, run  # noqa: E402


def test_crc_repaired_pack_is_rejected_but_control_files_preserved():
    result = run("reject")
    assert result["status"] == "PASS"
    assert result["pack_control"]["verify"] == "ACCEPT"
    assert result["pack_crc_repaired"]["verify"] == "REJECT"
    assert result["direct_crc_repaired"]["verify"] == "REJECT"


def test_shared_pack_is_strongly_hashed_only_once_per_verify(tmp_path, monkeypatch):
    left = b"a" * 64
    right = b"b" * 64
    pack = left + right
    archive = tmp_path / "pack.cmpct"
    archive.write_bytes(archive_bytes(pack, pack, packed=True))
    original_sha = reader_mod.sha
    seen = []

    def counted_sha(data):
        if data == pack:
            seen.append(1)
        return original_sha(data)

    monkeypatch.setattr(reader_mod, "sha", counted_sha)
    with CMPCT(archive) as reader:
        assert reader.verify() == 2
        assert reader.read("alpha.md") == left
        assert reader.read("beta.md") == right
    assert len(seen) == 1, "one SHA-256 per shared physical pack, not per slice"


def test_builder_zstd_pack_header_sha_change_is_rejected(tmp_path):
    """The same custody invariant holds for ordinary Builder-emitted Zstd packs."""
    import pytest
    from cmpct.builder import Builder
    from cmpct.codec import BHDR, CODEC_ZSTD, S_PACK
    from cmpct.validation import preflight_archive

    source = tmp_path / "source"
    source.mkdir()
    for i in range(8):
        (source / f"section-{i}.md").write_bytes(
            (f"section {i}: " + "shared explanatory text " * 20 + "\\n").encode() * 15
        )
    archive = tmp_path / "builder-pack.cmpct"
    Builder(source, workers=1, reproducible=True).build(archive)
    with CMPCT(archive) as reader:
        owners = [r for r in reader.files if r[6] and r[6][0] == S_PACK]
        assert len(owners) >= 2, "fixture must select actual Builder PACK storage"
        blob_idx = owners[0][6][1]
        assert reader.blobs[blob_idx][3] == CODEC_ZSTD, "fixture must exercise compressed PACK"
        pos = reader.record_base + reader.blobs[blob_idx][0]
        member = owners[0][0]
        original = reader.read(member)
        assert reader.verify() >= 8
    image = bytearray(archive.read_bytes())
    image[pos + BHDR.size - 1] ^= 1  # Alter only stored SHA, not data/CRC/index.
    archive.write_bytes(image)
    assert preflight_archive(archive)["files"] == 8
    with CMPCT(archive) as reader:
        assert reader.read(member) == original  # Intentional ordinary-read CRC contract.
        with pytest.raises(IOError, match="physical PACK SHA-256 verification failure"):
            reader.verify()
