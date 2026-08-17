from __future__ import annotations

from pathlib import Path

from experiments import entropygraph_v030_prefixgraph as pg
from experiments import entropygraph_v030_release_admission as admission


def _fixture(root: Path) -> None:
    root.mkdir(parents=True)
    base = (b'{"id":1,"values":[' + b"1234567890," * 120 + b"]}\n") * 20
    for index in range(4):
        (root / f"v{index}.json").write_bytes(base.replace(b'"id":1', f'"id":{index + 1}'.encode(), 1))


def test_metadata_only_locality_matches_prefixgraph_contract(tmp_path: Path) -> None:
    source = tmp_path / "source"
    _fixture(source)
    archive = tmp_path / "prefix.cmpct"
    stats = pg.build(source, archive)
    assert stats["prefix_records"] > 0

    locality = admission.prefixgraph_locality(archive)
    assert locality["passed"] is True
    assert locality["max_member_read_amplification"] <= 8.0
    assert locality["prefix_records"] == stats["prefix_records"]
    assert locality["accounting_source"] == "authenticated-metadata-only"
    assert locality["payload_bytes_materialized_for_locality"] == 0


def test_encoder_total_logical_ceiling_rejects_before_prefixgraph_build(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "source"
    source.mkdir()
    # Avoid allocating hundreds of MiB in the test: patch the release-only policy ceiling downward while
    # preserving the exact same branch of admission logic.
    monkeypatch.setattr(admission, "MAX_PREFIXGRAPH_TOTAL_LOGICAL_BYTES", 10)
    (source / "a.bin").write_bytes(b"a" * 6)
    (source / "b.bin").write_bytes(b"b" * 6)
    eligible, reason = admission.prefixgraph_eligibility(source, pg.treehash(source))
    assert eligible is False
    assert reason == "encoder-total-logical-ceiling"


def test_authoritative_tree_identity_remains_exact(tmp_path: Path) -> None:
    source = tmp_path / "source"
    _fixture(source)
    expected = pg.treehash(source)
    eligible, reason = admission.prefixgraph_eligibility(source, expected)
    assert eligible is True
    assert reason is None
    eligible, reason = admission.prefixgraph_eligibility(source, "0" * 64)
    assert eligible is False
    assert reason == "tree-identity-contract-mismatch"
