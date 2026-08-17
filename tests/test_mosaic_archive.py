from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
ENGINE_PATH = ROOT / "experiments" / "entropygraph_v029_mosaic_strict.py"
CORPUS_PATH = ROOT / "benchmarks" / "mosaic_hostile_corpus_v1.py"
STRESS_PATH = ROOT / "benchmarks" / "mosaic_stress_corpus_v2.py"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


ENGINE = _load(ENGINE_PATH, "cmpct_mosaic_archive_test_engine")
CORPUS = _load(CORPUS_PATH, "cmpct_mosaic_archive_test_corpus")
STRESS = _load(STRESS_PATH, "cmpct_mosaic_archive_test_stress")


def _workload(tmp_path: Path) -> Path:
    suite = tmp_path / "suite"
    CORPUS.two_parent_branch_merge(suite)
    return suite / "01_two_parent_branch_merge"


def test_strict_full_artifact_reconstructs_and_uses_mosaic(tmp_path: Path):
    source = _workload(tmp_path)
    archive = tmp_path / "mosaic.cmpct"
    stats = ENGINE.build_graph(source, archive)

    # Footnote: this bypasses the outer v0.28 fallback on purpose. Conformance tests need to exercise
    # the new grammar even when a future portfolio policy would choose an inherited artifact instead.
    assert archive.read_bytes()[:8] == ENGINE.MAG
    assert stats["mosaic_nodes"] >= 1
    assert stats["max_mosaic_read_amplification"] <= ENGINE.MAX_READ_AMP
    verified = ENGINE.strong_verify(archive)
    assert verified["ok"] is True
    assert verified["tree_sha256"] == ENGINE.BASE.treehash(source)

    restored = tmp_path / "restored"
    ENGINE.extract(archive, restored)
    assert ENGINE.BASE.treehash(restored) == ENGINE.BASE.treehash(source)


def test_pack_marginal_gate_rejects_a_paper_leaf_win(tmp_path: Path):
    suite = tmp_path / "stress"
    STRESS.shifted_reordered_merge(suite)
    source = suite / "02_shifted_reordered_merge"
    archive = tmp_path / "pack-marginal.cmpct"
    stats = ENGINE.build_graph(source, archive)

    # Attempt #2 discovered this target and estimated ~246 KiB of mosaic record savings against
    # standalone direct storage, yet the complete graph became ~1.9 KiB larger because v0.28's solid
    # root pack had already captured the same redundancy. Attempt #3 must still discover/tournament the
    # target, but it must not remove the direct leaf unless *physical pack marginal bytes* pay for the
    # complete mosaic record.
    assert stats["leaf_pack_tournaments"] >= 1
    assert stats["leaf_pack_rejections"] >= 1
    assert stats["mosaic_leaf_nodes"] == 0
    assert ENGINE.strong_verify(archive)["ok"] is True


def test_jointly_useful_partial_root_survives_one_root_loss(tmp_path: Path):
    suite = tmp_path / "source-like"
    STRESS.source_like_merge(suite)
    source = suite / "04_source_like_merge"
    archive = tmp_path / "partial-root.cmpct"
    stats = ENGINE.build_graph(source, archive)

    # This is the actual preserved v2 counterexample: root 0's one-root target costs 5,818 B, while
    # root 1 costs 5,888 B versus 5,878 B direct—10 B worse despite copying ~195 KiB. Together they
    # produce an 805 B primitive mosaic. Attempt #2 discarded root 1 because saving<=0 and therefore
    # never auditioned the complete mosaic. Attempt #3 must retain that exact-copy contribution.
    assert stats["partial_roots_retained"] >= 1
    assert stats["leaf_candidates"] >= 1
    assert stats["leaf_pack_tournaments"] >= 1
    assert stats["max_mosaic_read_amplification"] <= ENGINE.MAX_READ_AMP
    assert ENGINE.strong_verify(archive)["ok"] is True


def test_all_mosaic_dependencies_remain_direct(tmp_path: Path):
    source = _workload(tmp_path)
    archive = tmp_path / "flat.cmpct"
    ENGINE.build_graph(source, archive)
    stream, meta, *_ = ENGINE.BASE._open_mosaic(archive)
    stream.close()
    nodes = meta["nodes"]
    for desc in nodes:
        if desc[0] != "mosaic":
            continue
        base_ids = desc[1]
        assert 2 <= len(base_ids) <= 4
        assert all(nodes[base_id][0] == "direct" for base_id in base_ids)


def test_primary_metadata_damage_recovers_from_authenticated_tail(tmp_path: Path):
    source = _workload(tmp_path)
    archive = tmp_path / "recover.cmpct"
    stats = ENGINE.build_graph(source, archive)
    assert stats["mosaic_nodes"] >= 1

    raw = bytearray(archive.read_bytes())
    _, meta_comp_size, *_ = ENGINE.HDR.unpack(raw[: ENGINE.HDR.size])
    assert meta_comp_size > 4
    # Damage only the primary compressed metadata. Header sizes remain intact so the reader can locate
    # physical records after authenticating the redundant tail metadata copy.
    raw[ENGINE.HDR.size + 3] ^= 0x5A
    archive.write_bytes(raw)
    assert ENGINE.strong_verify(archive)["ok"] is True


def test_physical_leaf_corruption_fails_closed(tmp_path: Path):
    source = _workload(tmp_path)
    archive = tmp_path / "corrupt.cmpct"
    ENGINE.build_graph(source, archive)

    stream, meta, record_start, offsets, _ = ENGINE.BASE._open_mosaic(archive)
    stream.close()
    assert offsets
    raw = bytearray(archive.read_bytes())
    first_header = record_start + offsets[0]
    _, _, csize, _, _ = ENGINE.PH.unpack(raw[first_header : first_header + ENGINE.PH.size])
    assert csize > 0
    raw[first_header + ENGINE.PH.size] ^= 0x01
    archive.write_bytes(raw)

    # Footnote: metadata recovery is not payload forgiveness. A corrupt Merkle-authenticated physical
    # leaf must fail even though a healthy tail metadata copy still exists.
    with pytest.raises(RuntimeError):
        ENGINE.strong_verify(archive)


def test_outer_portfolio_never_exceeds_v028_artifact(tmp_path: Path):
    source = _workload(tmp_path)
    archive = tmp_path / "portfolio.cmpct"
    result = ENGINE.build(source, archive)
    assert result["archive_bytes"] <= result["v028_bytes"]
    assert result["selected"] in {"mosaic", "v028-fallback"}
    assert ENGINE.strong_verify(archive)["ok"] is True
