from __future__ import annotations

from pathlib import Path

import pytest

from cmpct.codec import FTR, HDR
from cmpct.core import Builder, CMPCT, append_update
from cmpct.validation import ParserLimits, ResourceLimitError, ValidationError, preflight_archive


def _small_archive(tmp_path: Path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "alpha.txt").write_text("alpha\n" * 100)
    (src / "beta.bin").write_bytes(bytes(range(256)) * 32)
    archive = tmp_path / "sample.cmpct"
    Builder(src).build(archive)
    return src, archive


def test_preflight_accepts_reference_archive(tmp_path: Path):
    src, archive = _small_archive(tmp_path)

    summary = preflight_archive(archive)

    assert summary["version"] == 24
    assert summary["files"] == 2
    assert summary["blobs"] >= 2
    assert summary["archive_bytes"] == archive.stat().st_size


def test_preflight_accepts_canonical_directory_hash_sentinel(tmp_path: Path):
    src = tmp_path / "src"
    nested = src / "nested"
    nested.mkdir(parents=True)
    (nested / "child.txt").write_text("child")
    archive = tmp_path / "directory.cmpct"
    Builder(src).build(archive)

    summary = preflight_archive(archive)

    assert summary["version"] == 24
    assert summary["files"] == 2  # one directory row + one file row in the revision-24 index


def test_footer_resource_limit_is_checked_before_decode(tmp_path: Path):
    _, archive = _small_archive(tmp_path)
    data = bytearray(archive.read_bytes())
    footer_pos = len(data) - FTR.size
    fields = list(FTR.unpack_from(data, footer_pos))
    fields[6] = 512 * 1024 * 1024  # uncompressed generation bytes
    data[footer_pos : footer_pos + FTR.size] = FTR.pack(*fields)
    archive.write_bytes(data)

    with pytest.raises(ResourceLimitError, match="generation payload exceeds limit"):
        preflight_archive(
            archive,
            ParserLimits(max_generation_bytes=8 * 1024 * 1024),
        )


def test_primary_index_resource_limit_is_checked_before_decode(tmp_path: Path):
    _, archive = _small_archive(tmp_path)
    data = bytearray(archive.read_bytes())
    fields = list(HDR.unpack_from(data, 0))
    fields[4] = 512 * 1024 * 1024  # declared uncompressed primary-index bytes
    data[: HDR.size] = HDR.pack(*fields)
    archive.write_bytes(data)

    with pytest.raises(ResourceLimitError, match="primary index exceeds limit"):
        preflight_archive(
            archive,
            ParserLimits(max_index_bytes=8 * 1024 * 1024),
        )


def test_blob_physical_header_mismatch_is_detected_without_decoding(tmp_path: Path):
    _, archive = _small_archive(tmp_path)
    with CMPCT(archive) as ar:
        first_blob_pos = ar.record_base + ar.blobs[0][0]

    data = bytearray(archive.read_bytes())
    data[first_blob_pos] ^= 0x01  # corrupt the first byte of the self-describing blob magic
    archive.write_bytes(data)

    with pytest.raises(ValidationError, match="blob 0 magic mismatch"):
        preflight_archive(archive)


def test_corrupt_latest_generation_falls_back_to_previous_commit(tmp_path: Path):
    src, archive = _small_archive(tmp_path)
    replacement = tmp_path / "replacement.txt"
    replacement.write_text("replacement\n" * 100)
    append_update(archive, "alpha.txt", replacement)

    with CMPCT(archive) as ar:
        latest_footer = ar.latest_footer_pos
        assert ar.read("alpha.txt") == replacement.read_bytes()

    data = bytearray(archive.read_bytes())
    data[latest_footer - 1] ^= 0x01  # invalidate newest generation payload/hash, not the old footer
    archive.write_bytes(data)

    summary = preflight_archive(archive)
    assert summary["latest_footer"] < latest_footer
    with CMPCT(archive) as ar:
        assert ar.read("alpha.txt") == (src / "alpha.txt").read_bytes()


def test_blob_limit_can_be_lowered_without_touching_archive_bytes(tmp_path: Path):
    _, archive = _small_archive(tmp_path)

    with pytest.raises(ResourceLimitError, match="blob 0 size exceeds parser limit|blob 1 size exceeds parser limit"):
        preflight_archive(
            archive,
            ParserLimits(max_blob_bytes=64),
        )


def test_truncated_archive_is_rejected_as_structure_not_struct_error(tmp_path: Path):
    archive = tmp_path / "truncated.cmpct"
    archive.write_bytes(b"CMPCT24\x00")

    with pytest.raises(ValidationError, match="smaller than the revision-24 header"):
        preflight_archive(archive)
