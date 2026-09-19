"""Product-scope regression for v0.30 full-extraction semantic-SHA folding."""
from copy import deepcopy
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


def _flip32(value: bytes) -> bytes:
    return bytes([value[0] ^ 1]) + value[1:]


def test_record_scope_payload_auth_and_rollback(tmp_path: Path) -> None:
    src = PERF._build_corpora(tmp_path / "corpora")[("neutral_hostile_v1", "09_ml_artifacts")]
    archive = tmp_path / "ml.cmpct"
    PRODUCT.build(src, archive)
    assert PRODUCT.strong_verify(archive)["ok"] is True
    expected_graph_tree = _graph_tree(archive)

    bad = tmp_path / "record-logical-sha-only.cmpct"
    hostile._rewrite_header(archive, bad, lambda c, u, s, r, h: (c, u, s, r, _flip32(h)))
    staging = tmp_path / "verified-staging"
    result = POLICY.extract_verified_into_staging(bad, staging)
    assert result["ok"] is True
    assert result["tree_sha256"] == expected_graph_tree

    ordinary = tmp_path / "ordinary"
    with pytest.raises(RuntimeError):
        R.extract(bad, ordinary)
    assert not ordinary.exists()
    assert PRODUCT.strong_verify(bad)["ok"] is False
    member = next(row["path"] for row in PRODUCT.list_members(archive) if row.get("kind") == "file")
    with pytest.raises(Exception):
        PRODUCT.read_member(bad, member)

    bad_payload = tmp_path / "bad-payload.cmpct"
    hostile._mutate_payload(archive, bad_payload)
    rollback = hostile._assert_destination_rollback(bad_payload, tmp_path / "rollback-dst")
    assert rollback["failed_closed"] is True and rollback["destination_tree_preserved"] is True
    post_crc = hostile._post_crc_fault(archive, tmp_path / "post-crc-out")
    assert post_crc["failed_closed"] is True and post_crc["fault_injected"] is True


def test_node_and_file_semantic_sha_are_deferred_only_by_verified_staging(tmp_path: Path, monkeypatch) -> None:
    src = PERF._build_corpora(tmp_path / "corpora")[("neutral_hostile_v1", "09_ml_artifacts")]
    archive = tmp_path / "ml.cmpct"
    PRODUCT.build(src, archive)
    expected_graph_tree = _graph_tree(archive)
    original_open = R._g04_open

    def exercise(label: str, mutate) -> None:
        def opened(path: Path):
            stream, meta, start, offsets, merkle, tail = original_open(path)
            copied = deepcopy(meta)
            mutate(copied)
            return stream, copied, start, offsets, merkle, tail

        with monkeypatch.context() as scoped:
            scoped.setattr(R, "_g04_open", opened)
            staging = tmp_path / f"staging-{label}"
            result = POLICY.extract_verified_into_staging(archive, staging)
            assert result["ok"] is True and result["tree_sha256"] == expected_graph_tree
            with pytest.raises(RuntimeError):
                R._stream_g04(archive, None, R.MAX_DECLARED_LOGICAL_BYTES)

    def mutate_node(meta: dict) -> None:
        referenced = None
        for rel in sorted(meta["files"]):
            desc = meta["files"][rel]
            if desc[0] != "preflate" and desc[1]:
                referenced = int(desc[1][0])
                break
        assert referenced is not None
        meta["nodes"][referenced][-1] = _flip32(meta["nodes"][referenced][-1])

    def mutate_file(meta: dict) -> None:
        rel = sorted(meta["files"])[0]
        meta["files"][rel][3] = _flip32(meta["files"][rel][3])

    exercise("node-sha", mutate_node)
    exercise("file-sha", mutate_file)
