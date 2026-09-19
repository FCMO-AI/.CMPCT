"""Product-scope regression for v0.30 full-extraction semantic-SHA folding.

The only surface allowed to defer nested record/node/file semantic SHA is the caller-owned
verified staging extraction, whose mandatory terminal tree hash decides acceptance before
publication. Every ordinary/diagnostic/selective reader surface remains strict.
"""
from pathlib import Path

import pytest

from benchmarks import v030_ml_semantic_fold_hostile as hostile
from benchmarks import v030_release_performance as PERF
from experiments import entropygraph_v030_release_product as PRODUCT
from experiments import entropygraph_v030_verified_restore as VR

POLICY = VR.C.POLICY
R = POLICY.R


def test_record_logical_sha_deferral_is_verified_staging_only(tmp_path: Path) -> None:
    src = PERF._build_corpora(tmp_path / "corpora")[("neutral_hostile_v1", "09_ml_artifacts")]
    archive = tmp_path / "ml.cmpct"
    PRODUCT.build(src, archive)
    expected_tree = PRODUCT.treehash(src)

    bad = tmp_path / "record-logical-sha-only.cmpct"
    hostile._rewrite_header(
        archive,
        bad,
        lambda codec, usize, csize, crc, digest: (
            codec,
            usize,
            csize,
            crc,
            bytes([digest[0] ^ 1]) + digest[1:],
        ),
    )

    # The promotion owner may fold this redundant nested proof because the complete
    # reconstructed tree is still authenticated before the staging tree can publish.
    staging = tmp_path / "verified-staging"
    result = POLICY.extract_verified_into_staging(bad, staging)
    assert result["ok"] is True
    assert result["tree_sha256"] == expected_tree
    assert PRODUCT.treehash(staging) == expected_tree

    # Every other reader surface stays strict by default. A future refactor that infers
    # deferral from target_root (rather than the explicit policy) must fail here.
    ordinary = tmp_path / "ordinary"
    with pytest.raises(RuntimeError):
        R.extract(bad, ordinary)
    assert not ordinary.exists()

    verified = PRODUCT.strong_verify(bad)
    assert verified["ok"] is False

    member = next(row["path"] for row in PRODUCT.list_members(archive) if row.get("kind") == "file")
    with pytest.raises(Exception):
        PRODUCT.read_member(bad, member)
