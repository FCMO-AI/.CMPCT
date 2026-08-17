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


def _v1_two_parent(tmp_path: Path) -> Path:
    suite = tmp_path / "suite"
    CORPUS.two_parent_branch_merge(suite)
    return suite / "01_two_parent_branch_merge"


def _stress(tmp_path: Path, builder, name: str) -> Path:
    suite = tmp_path / name
    builder(suite)
    return suite / name


def test_placement_archive_reconstructs_and_uses_mosaic(tmp_path: Path):
    source = _v1_two_parent(tmp_path)
    archive = tmp_path / "placement.cmpct"
    stats = ENGINE.build_graph(source, archive)
    assert archive.read_bytes()[:8] == ENGINE.MAG
    assert stats["mosaic_nodes"] >= 1
    assert stats["max_mosaic_read_amplification"] <= ENGINE.MAX_READ_AMP
    assert ENGINE.strong_verify(archive)["tree_sha256"] == ENGINE.BASE.treehash(source)

    restored = tmp_path / "restored"
    ENGINE.extract(archive, restored)
    assert ENGINE.BASE.treehash(restored) == ENGINE.BASE.treehash(source)


def test_shifted_reordered_stays_in_better_solid_representation(tmp_path: Path):
    source = _stress(tmp_path, STRESS.shifted_reordered_merge, "02_shifted_reordered_merge")
    archive = tmp_path / "shifted.cmpct"
    stats = ENGINE.build_graph(source, archive)

    # The focused diagnostic proved both external mosaic and same-pack preconditioning lose here. The
    # Placement Compiler must still discover/evaluate the target, but it must not manufacture a win.
    assert stats["mosaic_auditions"] >= 1
    assert stats["pack_local_mosaic_nodes"] == 0
    assert stats["copack_mosaic_nodes"] == 0
    assert ENGINE.strong_verify(archive)["ok"] is True


def test_source_like_uses_pack_local_semantic_recipe(tmp_path: Path):
    source = _stress(tmp_path, STRESS.source_like_merge, "04_source_like_merge")
    archive = tmp_path / "source-like.cmpct"
    stats = ENGINE.build_graph(source, archive)

    # Oracle diagnosis measured +128 B after charging descriptor overhead only when the recipe replaces
    # the raw target *inside the already-required solid pack*. Attempt #4 must exercise that embodiment.
    assert stats["pack_local_trials"] >= 1
    assert stats["pack_local_mosaic_nodes"] >= 1
    assert stats["max_mosaic_read_amplification"] <= ENGINE.MAX_READ_AMP
    assert ENGINE.strong_verify(archive)["ok"] is True

    stream, meta, *_ = ENGINE._open(archive)
    stream.close()
    assert any(desc[0] == "pack_mosaic" for desc in meta["nodes"])


def test_root_diversity_can_copack_required_direct_bases(tmp_path: Path):
    source = _stress(tmp_path, STRESS.root_diversity_pressure, "09_root_diversity_pressure")
    archive = tmp_path / "diversity.cmpct"
    stats = ENGINE.build_graph(source, archive)

    # The oracle found ~62.8 KiB marginal headroom but the best four roots spanned two generic packs.
    # A dedicated base co-pack is allowed only inside the existing 2 MiB / 8x locality contract.
    assert stats["copack_trials"] >= 1
    assert stats["copack_mosaic_nodes"] >= 1
    assert stats["max_mosaic_read_amplification"] <= ENGINE.MAX_READ_AMP
    assert ENGINE.strong_verify(archive)["ok"] is True


def test_small_target_relative_floor_can_upgrade_single_delta(tmp_path: Path):
    source = _stress(tmp_path, STRESS.small_metadata_control, "10_small_metadata_control")
    archive = tmp_path / "small.cmpct"
    stats = ENGINE.build_graph(source, archive)

    # The 2 KiB target already has a valid inherited single delta. The missing second root copied only
    # ~540 B, so a 4 KiB absolute mosaic contribution floor made it impossible to nominate. Attempt #4
    # uses the preregistered target-relative floor and still requires a complete measured record win.
    assert stats["small_mosaic_upgrades"] >= 1
    assert stats["mosaic_upgrade_nodes"] >= 1
    assert stats["max_mosaic_read_amplification"] <= ENGINE.MAX_READ_AMP
    assert ENGINE.strong_verify(archive)["ok"] is True


def test_false_neighbor_and_incompressible_controls_do_not_create_mosaic(tmp_path: Path):
    false_source = _stress(tmp_path, STRESS.false_neighbors_control, "07_false_neighbors_control")
    incompressible_source = _stress(tmp_path, STRESS.incompressible_control, "08_incompressible_control")
    false_archive = tmp_path / "false.cmpct"
    random_archive = tmp_path / "random.cmpct"
    false_stats = ENGINE.build_graph(false_source, false_archive)
    random_stats = ENGINE.build_graph(incompressible_source, random_archive)
    assert false_stats["mosaic_nodes"] == 0
    assert random_stats["mosaic_nodes"] == 0
    assert ENGINE.strong_verify(false_archive)["ok"] is True
    assert ENGINE.strong_verify(random_archive)["ok"] is True


def test_all_mosaic_dependencies_remain_direct(tmp_path: Path):
    source = _v1_two_parent(tmp_path)
    archive = tmp_path / "flat.cmpct"
    ENGINE.build_graph(source, archive)
    stream, meta, *_ = ENGINE._open(archive)
    stream.close()
    nodes = meta["nodes"]
    for desc in nodes:
        if desc[0] == "mosaic":
            base_ids = desc[1]
        elif desc[0] == "pack_mosaic":
            base_ids = desc[4]
        else:
            continue
        assert 2 <= len(base_ids) <= 4
        assert all(nodes[base_id][0] == "direct" for base_id in base_ids)


def test_primary_metadata_damage_recovers_from_authenticated_tail(tmp_path: Path):
    source = _v1_two_parent(tmp_path)
    archive = tmp_path / "recover.cmpct"
    ENGINE.build_graph(source, archive)
    raw = bytearray(archive.read_bytes())
    _, meta_comp_size, *_ = ENGINE.HDR.unpack(raw[: ENGINE.HDR.size])
    assert meta_comp_size > 4
    raw[ENGINE.HDR.size + 3] ^= 0x5A
    archive.write_bytes(raw)
    assert ENGINE.strong_verify(archive)["ok"] is True


def test_physical_leaf_corruption_fails_closed(tmp_path: Path):
    source = _v1_two_parent(tmp_path)
    archive = tmp_path / "corrupt.cmpct"
    ENGINE.build_graph(source, archive)
    stream, meta, record_start, offsets, _ = ENGINE._open(archive)
    stream.close()
    assert offsets
    raw = bytearray(archive.read_bytes())
    first_header = record_start + offsets[0]
    _, _, csize, _, _ = ENGINE.PH.unpack(raw[first_header : first_header + ENGINE.PH.size])
    assert csize > 0
    raw[first_header + ENGINE.PH.size] ^= 0x01
    archive.write_bytes(raw)
    with pytest.raises(RuntimeError):
        ENGINE.strong_verify(archive)


def test_outer_portfolio_never_exceeds_v028_artifact(tmp_path: Path):
    source = _v1_two_parent(tmp_path)
    archive = tmp_path / "portfolio.cmpct"
    result = ENGINE.build(source, archive)
    assert result["archive_bytes"] <= result["v028_bytes"]
    assert result["selected"] in {"mosaic", "v028-fallback"}
    assert ENGINE.strong_verify(archive)["ok"] is True
