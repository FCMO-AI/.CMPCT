from __future__ import annotations

from pathlib import Path

import pytest

from benchmarks import resemblance_hostile_corpus_v1 as CORPUS
from experiments import entropygraph_v030_zipfactor_recovery_product_candidate as ZF


def _source(tmp_path: Path) -> Path:
    corpus = tmp_path / "corpus"
    CORPUS.build(corpus)
    return corpus / "04_deflate_family"


def _flip(raw: bytes, index: int) -> bytes:
    out = bytearray(raw)
    out[index] ^= 0x5A
    return bytes(out)


def _regular_bytes(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file() and not path.is_symlink()
    }


def test_product_candidate_exact_semantics_recovery_random_access_and_extract(tmp_path: Path) -> None:
    source = _source(tmp_path)
    archive = tmp_path / "candidate.cmpct"
    stats = ZF.build(source, archive, level=3, group_size=7)

    assert archive.read_bytes()[:8] == ZF.MAGIC
    assert stats["format_profile"] == ZF.PROFILE
    assert stats["payload_body_copies"] == 1
    assert stats["control_copies"] == 2
    assert stats["direct_v3_in_memory"] is True
    assert stats["path_identity_used_for_admission"] is False
    assert stats["max_member_read_amplification"] <= 8.0
    assert stats["max_decode_unit_bytes"] <= 8 * 1024 * 1024

    clean = ZF.verify_and_identities(archive)
    assert clean["ok"] is True
    assert clean["recovered_from"] == "primary"
    identities = clean["identities"]

    expected_files = _regular_bytes(source)
    listed = ZF.list_members(archive)
    listed_files = {row["path"] for row in listed if row["kind"] == "file"}
    assert listed_files == set(expected_files)
    for rel, expected in expected_files.items():
        got, read_stats = ZF.read_member_with_stats(archive, rel)
        assert got == expected
        assert read_stats["recovered_from"] == "primary"
        assert read_stats["decoded_context_amplification"] <= 8.0
        assert read_stats["decoded_context_bytes"] <= 8 * 1024 * 1024

    extracted = tmp_path / "extracted"
    ZF.extract(archive, extracted, max_output_bytes=sum(map(len, expected_files.values())))
    assert _regular_bytes(extracted) == expected_files

    raw = archive.read_bytes()
    primary_len = ZF._control_len_from_primary(raw)
    _, tail_start, _ = ZF._tail_layout(raw)

    primary_bad = tmp_path / "primary-bad.cmpct"
    primary_bad.write_bytes(_flip(raw, 8 + 7))
    recovered = ZF.verify_and_identities(primary_bad)
    assert recovered["ok"] is True
    assert recovered["recovered_from"] == "tail"
    assert recovered["identities"] == identities
    sample_rel = sorted(expected_files)[0]
    sample, sample_stats = ZF.read_member_with_stats(primary_bad, sample_rel)
    assert sample == expected_files[sample_rel]
    assert sample_stats["recovered_from"] == "tail"
    recovered_extract = tmp_path / "recovered-extract"
    ZF.extract(primary_bad, recovered_extract)
    assert _regular_bytes(recovered_extract) == expected_files

    tail_bad = tmp_path / "tail-bad.cmpct"
    tail_bad.write_bytes(_flip(raw, tail_start + min(7, primary_len - 1)))
    tail_recovered = ZF.verify_and_identities(tail_bad)
    assert tail_recovered["ok"] is True
    assert tail_recovered["recovered_from"] == "primary"
    assert tail_recovered["identities"] == identities

    both_bad = tmp_path / "both-bad.cmpct"
    both_bad.write_bytes(_flip(primary_bad.read_bytes(), tail_start + min(7, primary_len - 1)))
    rejected = ZF.strong_verify(both_bad)
    assert rejected["ok"] is False
    corrupt_dst = tmp_path / "corrupt-dst"
    with pytest.raises(RuntimeError):
        ZF.extract(both_bad, corrupt_dst)
    assert not corrupt_dst.exists()


def test_product_candidate_v3_semantics_never_require_temp_publication(tmp_path: Path, monkeypatch) -> None:
    source = _source(tmp_path)
    archive = tmp_path / "candidate.cmpct"
    ZF.build(source, archive, level=3, group_size=7)
    expected = _regular_bytes(source)
    sample_rel = sorted(expected)[0]

    def forbidden_tempdir(*_args, **_kwargs):
        raise AssertionError("reconstructed V3 semantics must remain resident in memory")

    # Extraction staging uses mkdtemp intentionally for transactional publication; TemporaryDirectory was only the
    # obsolete V3 publish+reread bridge. Any future reintroduction of that bridge fails this ratchet immediately.
    monkeypatch.setattr(ZF.tempfile, "TemporaryDirectory", forbidden_tempdir)
    verified = ZF.verify_and_identities(archive)
    assert verified["ok"] is True
    assert ZF.read_member(archive, sample_rel) == expected[sample_rel]
    dst = tmp_path / "extracted-resident-v3"
    ZF.extract(archive, dst)
    assert _regular_bytes(dst) == expected


def test_product_candidate_budget_fails_before_publication(tmp_path: Path) -> None:
    source = _source(tmp_path)
    archive = tmp_path / "candidate.cmpct"
    ZF.build(source, archive, level=3, group_size=7)
    dst = tmp_path / "budget-dst"
    with pytest.raises(RuntimeError, match="caller output budget"):
        ZF.extract(archive, dst, max_output_bytes=0)
    assert not dst.exists()


def test_product_candidate_is_not_selector_promoted() -> None:
    assert ZF.PROMOTION_STATE == "canonical-reader-candidate-only"
    assert ZF.SELECTOR_ENABLED is False
    assert ZF.PUBLIC_RANDOM_ACCESS_COMPLETE is True
    assert ZF.PUBLIC_EXTRACT_COMPLETE is True
    assert ZF.RELEASE_CREDIT is False
