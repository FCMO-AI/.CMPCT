from __future__ import annotations

from pathlib import Path

import pytest

from experiments import entropygraph_v025 as V25
from experiments import entropygraph_v030_federated_candidate as CAND
from experiments import entropygraph_v030_release_product as PRODUCT


def _tree(root: Path) -> None:
    (root / "docs").mkdir(parents=True)
    (root / "docs" / "report.txt").write_bytes((b"federated-candidate\n" * 4096) + b"end")
    (root / "data.bin").write_bytes(bytes(range(256)) * 256)


def test_candidate_has_separate_identity_and_roundtrips_canonical_tree(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    _tree(source)
    archive = tmp_path / "candidate.cmpct"
    stats = CAND.build(source, archive)
    assert archive.read_bytes()[:8] == CAND.MAGIC
    assert CAND.MAGIC != V25.MAG
    assert stats["profile"] == "federated-eg01"
    assert stats["format_revision"] == 25
    assert stats["verified"]["ok"] is True
    restored = tmp_path / "restored"
    CAND.extract(archive, restored)
    assert PRODUCT.treehash(restored) == PRODUCT.treehash(source)


def test_candidate_engine_restores_historical_globals_on_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source = tmp_path / "source"
    source.mkdir()
    _tree(source)
    archive = tmp_path / "candidate.cmpct"
    before = (V25.ROOT, V25.OUT, V25.MAG, V25.TAIL, V25.zc)

    def explode():
        raise RuntimeError("intentional candidate build failure")

    monkeypatch.setattr(V25, "build", explode)
    with pytest.raises(RuntimeError, match="intentional candidate build failure"):
        CAND.build(source, archive)
    after = (V25.ROOT, V25.OUT, V25.MAG, V25.TAIL, V25.zc)
    assert after == before


def test_shipping_selector_does_not_claim_candidate_identity(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    _tree(source)
    archive = tmp_path / "candidate.cmpct"
    CAND.build(source, archive)
    # The candidate is deliberately pre-promotion: ordinary product authority must not silently accept it.
    with pytest.raises(Exception):
        PRODUCT.strong_verify(archive)
