from __future__ import annotations

from pathlib import Path

import pytest

from benchmarks import resemblance_hostile_corpus_v1 as CORPUS
from experiments import entropygraph_v030_zipfactor_compact_v3 as V3
from experiments import entropygraph_v030_zipfactor_recovery_product_candidate as PRODUCT
from experiments import entropygraph_v030_zipfactor_recovery_reader_candidate as READER


def _source(tmp_path: Path) -> Path:
    corpus = tmp_path / "corpus"
    CORPUS.build(corpus)
    return corpus / "04_deflate_family"


def _flip(raw: bytes, index: int) -> bytes:
    out = bytearray(raw)
    out[index] ^= 0x5A
    return bytes(out)


def test_selective_reader_decodes_only_direct_metadata_and_target_group(tmp_path: Path) -> None:
    source = _source(tmp_path)
    archive = tmp_path / "candidate.cmpct"
    READER.build(source, archive, level=3, group_size=7)

    expected = {
        path.relative_to(source).as_posix(): path.read_bytes()
        for path in source.rglob("*")
        if path.is_file() and not path.is_symlink()
    }
    assert {row["path"] for row in READER.list_members(archive) if row["kind"] == "file"} == set(expected)
    for rel, want in expected.items():
        got, stats = READER.read_member_with_stats(archive, rel)
        assert got == want
        assert stats["full_archive_verify_before_read"] is False
        assert stats["direct_metadata_decode_passes"] == 1
        assert stats["payload_group_decode_passes"] == 1
        assert stats["candidate_tempfile_round_trips"] == 0
        assert stats["decoded_context_amplification"] <= 8.0
        assert stats["decoded_context_bytes"] <= 8 * 1024 * 1024


def test_v3_parser_has_exact_path_and_resident_byte_semantics(tmp_path: Path) -> None:
    source = _source(tmp_path)
    archive = tmp_path / "candidate.cmpct"
    READER.build(source, archive, level=3, group_size=7)
    _recovered_from, candidate = READER._select_v3_candidate(archive.read_bytes())
    resident = V3._open(candidate)
    candidate_path = tmp_path / "candidate-v3.cmpct"
    candidate_path.write_bytes(candidate)
    on_disk = V3._open(candidate_path)

    assert resident[0] == on_disk[0]
    assert resident[1] == on_disk[1]
    assert resident[2] == on_disk[2]
    assert resident[3] == on_disk[3]


def test_selective_reader_uses_authenticated_tail_without_full_verify(tmp_path: Path) -> None:
    source = _source(tmp_path)
    archive = tmp_path / "candidate.cmpct"
    READER.build(source, archive, level=3, group_size=7)
    raw = archive.read_bytes()
    primary_len = PRODUCT._control_len_from_primary(raw)
    _, tail_start, _ = PRODUCT._tail_layout(raw)
    rel = sorted(
        path.relative_to(source).as_posix()
        for path in source.rglob("*")
        if path.is_file() and not path.is_symlink()
    )[0]

    primary_bad = tmp_path / "primary-bad.cmpct"
    primary_bad.write_bytes(_flip(raw, len(PRODUCT.MAGIC) + min(7, primary_len - 1)))
    got, stats = READER.read_member_with_stats(primary_bad, rel)
    assert got == (source / rel).read_bytes()
    assert stats["recovered_from"] == "tail"
    assert stats["full_archive_verify_before_read"] is False
    assert stats["candidate_tempfile_round_trips"] == 0

    both_bad = tmp_path / "both-bad.cmpct"
    both_bad.write_bytes(_flip(primary_bad.read_bytes(), tail_start + min(7, primary_len - 1)))
    with pytest.raises(RuntimeError):
        READER.read_member(both_bad, rel)


def test_selective_reader_remains_unpromoted() -> None:
    assert READER.PROMOTION_STATE == "canonical-selective-reader-candidate-only"
    assert READER.SELECTOR_ENABLED is False
    assert READER.RELEASE_CREDIT is False
