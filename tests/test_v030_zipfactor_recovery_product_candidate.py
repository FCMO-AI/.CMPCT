from __future__ import annotations

from pathlib import Path

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


def test_product_candidate_exact_semantics_and_recovery(tmp_path: Path) -> None:
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

    raw = archive.read_bytes()
    primary_len = ZF._control_len_from_primary(raw)
    _, tail_start, _ = ZF._tail_layout(raw)

    primary_bad = tmp_path / "primary-bad.cmpct"
    primary_bad.write_bytes(_flip(raw, 8 + 7))
    recovered = ZF.verify_and_identities(primary_bad)
    assert recovered["ok"] is True
    assert recovered["recovered_from"] == "tail"
    assert recovered["identities"] == identities

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


def test_product_candidate_is_not_selector_promoted() -> None:
    assert ZF.PROMOTION_STATE == "canonical-semantics-candidate-only"
    assert ZF.SELECTOR_ENABLED is False
    assert ZF.PUBLIC_READER_COMPLETE is False
    assert ZF.RELEASE_CREDIT is False
