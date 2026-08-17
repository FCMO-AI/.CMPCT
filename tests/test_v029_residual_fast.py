from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
ENGINE_PATH = ROOT / "experiments" / "entropygraph_v029_residual_fast.py"


def _load():
    spec = importlib.util.spec_from_file_location("cmpct_v029_residual_fast_test", ENGINE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_single_file_inherited_fallback_skips_expensive_graph(monkeypatch, tmp_path: Path):
    engine = _load()
    source = tmp_path / "source"; source.mkdir(); (source / "only.bin").write_bytes(b"x" * 4096)
    out = tmp_path / "out.cmpct"
    calls = {"graph": 0}

    def fake_v028(root: Path, archive: Path):
        archive.write_bytes(b"baseline-v025")
        return {"selected": "entropygraph-v025-fallback", "portfolio_create_s": 0.01}

    def forbidden_graph(root: Path, archive: Path):
        calls["graph"] += 1
        raise AssertionError("single-file inherited fallback must not audition the multi-root graph")

    monkeypatch.setattr(engine.V028, "build", fake_v028)
    monkeypatch.setattr(engine.BASE, "_build_graph", forbidden_graph)
    result = engine.build(source, out)

    assert calls["graph"] == 0
    assert out.read_bytes() == b"baseline-v025"
    assert result["selected"] == "v028-fallback"
    assert result["fast_reject_reason"] == "single-file-and-v028-inherited-fallback"
    assert result["mosaic"]["mosaic_nodes"] == 0


def test_fast_reject_does_not_apply_to_multi_file_tree(monkeypatch, tmp_path: Path):
    engine = _load()
    source = tmp_path / "source"; source.mkdir()
    (source / "root.bin").write_bytes(b"a" * 4096)
    (source / "target.bin").write_bytes(b"b" * 4096)
    out = tmp_path / "out.cmpct"
    calls = {"graph": 0}

    def fake_v028(root: Path, archive: Path):
        archive.write_bytes(b"baseline-is-longer")
        return {"selected": "entropygraph-v025-fallback", "portfolio_create_s": 0.01}

    def fake_graph(root: Path, archive: Path):
        calls["graph"] += 1
        archive.write_bytes(b"candidate")
        return {
            "mosaic_nodes": 1,
            "residual_pack_records": 0,
            "residual_packed_delta_nodes": 0,
            "max_mosaic_read_amplification": 2.0,
            "max_additional_recipe_read_amplification": 0.0,
        }

    monkeypatch.setattr(engine.V028, "build", fake_v028)
    monkeypatch.setattr(engine.BASE, "_build_graph", fake_graph)
    result = engine.build(source, out)

    assert calls["graph"] == 1
    assert out.read_bytes() == b"candidate"
    assert result["selected"] == "mosaic"
    assert result["fast_reject_reason"] is None


def test_single_file_graph_winner_is_not_fast_rejected(monkeypatch, tmp_path: Path):
    engine = _load()
    source = tmp_path / "source"; source.mkdir(); (source / "only.bin").write_bytes(b"x" * 4096)
    out = tmp_path / "out.cmpct"
    calls = {"graph": 0}

    def fake_v028(root: Path, archive: Path):
        archive.write_bytes(b"baseline-graph-winner")
        return {"selected": "resemblance", "portfolio_create_s": 0.01}

    def fake_graph(root: Path, archive: Path):
        calls["graph"] += 1
        archive.write_bytes(b"research")
        return {
            "mosaic_nodes": 0,
            "residual_pack_records": 1,
            "residual_packed_delta_nodes": 2,
            "max_mosaic_read_amplification": 0.0,
            "max_additional_recipe_read_amplification": 0.1,
        }

    monkeypatch.setattr(engine.V028, "build", fake_v028)
    monkeypatch.setattr(engine.BASE, "_build_graph", fake_graph)
    result = engine.build(source, out)

    assert calls["graph"] == 1
    assert result["fast_reject_reason"] is None

# Footnote: these tests isolate scheduling from compression. They prove the reject cannot silently grow
# to multi-file trees or to single-file cases where v0.28's own resemblance graph already earned bytes.
