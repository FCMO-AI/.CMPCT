"""Product-scope regression for v0.30 full-extraction semantic-SHA folding."""
from pathlib import Path

import pytest

from benchmarks import v030_ml_semantic_fold_hostile as hostile
from benchmarks import v030_release_performance as PERF
from experiments import entropygraph_v030_release_product as PRODUCT
from experiments import entropygraph_v030_verified_restore as VR

POLICY = VR.C.POLICY
R = POLICY.R


def _graph_tree(archive: Path) -> str:
    stream, meta, _start, _offsets, _merkle, _tail = R._g04_open(archive)
    try:
        return str(meta["tree_sha256"])
    finally:
        stream.close()


def test_record_logical_sha_deferral_is_verified_staging_only(tmp_path: Path) -> None:
    src = PERF._build_corpora(tmp_path / "corpora")[("neutral_hostile_v1", "09_ml_artifacts")]
    archive = tmp_path / "ml.cmpct"
    PRODUCT.build(src, archive)
    strict_valid = PRODUCT.strong_verify(archive)
    assert strict_valid["ok"] is True
    expected_graph_tree = _graph_tree(archive)

    bad = tmp_path / "record-logical-sha-only.cmpct"
    hostile._rewrite_header(
        archive,
        bad,
        lambda codec, usize, csize, crc, digest: (
            codec, usize, csize, crc, bytes([digest[0] ^ 1]) + digest[1:]
        ),
    )

    # Only the unpublished verified-staging owner may fold the redundant nested proof.
    staging = tmp_path / "verified-staging"
    result = POLICY.extract_verified_into_staging(bad, staging)
    assert result["ok"] is True
    assert result["tree_sha256"] == expected_graph_tree

    # Every other reader surface stays strict by default.
    ordinary = tmp_path / "ordinary"
    with pytest.raises(RuntimeError):
        R.extract(bad, ordinary)
    assert not ordinary.exists()

    verified = PRODUCT.strong_verify(bad)
    assert verified["ok"] is False

    member = next(row["path"] for row in PRODUCT.list_members(archive) if row.get("kind") == "file")
    with pytest.raises(Exception):
        PRODUCT.read_member(bad, member)
