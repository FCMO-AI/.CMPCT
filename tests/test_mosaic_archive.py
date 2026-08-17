from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
ENGINE_PATH = ROOT / "experiments" / "entropygraph_v029_mosaic_strict.py"
CORPUS_PATH = ROOT / "benchmarks" / "mosaic_hostile_corpus_v1.py"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


ENGINE = _load(ENGINE_PATH, "cmpct_mosaic_archive_test_engine")
CORPUS = _load(CORPUS_PATH, "cmpct_mosaic_archive_test_corpus")


def _workload(tmp_path: Path) -> Path:
    suite = tmp_path / "suite"
    CORPUS.two_parent_branch_merge(suite)
    return suite / "01_two_parent_branch_merge"


def test_strict_full_artifact_reconstructs_and_uses_mosaic(tmp_path: Path):
    source = _workload(tmp_path)
    archive = tmp_path / "mosaic.cmpct"
    stats = ENGINE.build_graph(source, archive)

    # Footnote: this bypasses the outer v0.28 fallback on purpose.  Conformance tests need to exercise
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


def test_primary_metadata_damage_recovers_from_authenticated_tail(tmp_path: Path):
    source = _workload(tmp_path)
    archive = tmp_path / "recover.cmpct"
    stats = ENGINE.build_graph(source, archive)
    assert stats["mosaic_nodes"] >= 1

    raw = bytearray(archive.read_bytes())
    _, meta_comp_size, *_ = ENGINE.HDR.unpack(raw[: ENGINE.HDR.size])
    assert meta_comp_size > 4
    # Damage only the primary compressed metadata.  Header sizes remain intact so the reader can locate
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

    # Footnote: metadata recovery is not payload forgiveness.  A corrupt Merkle-authenticated physical
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
