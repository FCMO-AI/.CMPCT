from __future__ import annotations

from pathlib import Path

from experiments import entropygraph_v030_geometry_overlay_g04_publish as duplicated
from experiments import entropygraph_v030_shared_portfolio as shared


def _multi_file_fixture(root: Path) -> None:
    root.mkdir(parents=True)
    rows = [f"{index:06d},region-{index % 4},metric-{index % 17:04d}\n" for index in range(2200)]
    body = "".join(rows).encode()
    (root / "events-a.csv").write_bytes(body)
    (root / "events-b.csv").write_bytes(body.replace(b"region-3", b"region-8"))
    (root / "events-c.csv").write_bytes(body.replace(b"metric-0016", b"metric-0099"))


def _single_file_fixture(root: Path) -> None:
    root.mkdir(parents=True)
    # One deterministic mixed stream exercises the accepted single-file portfolio law while G0-G4 still
    # receives the exact pre-fallback graph it needs. The test does not assume whether fast reject fires.
    body = bytearray()
    for index in range(9000):
        body.extend(f"{index:08d}|{index % 31:02d}|value-{index % 127:03d}\n".encode())
    (root / "single.log").write_bytes(bytes(body))


def _assert_identity(source: Path, tmp_path: Path, stem: str) -> None:
    old_archive = tmp_path / f"{stem}-duplicated.cmpct"
    new_archive = tmp_path / f"{stem}-shared.cmpct"

    old_stats = duplicated.build(source, old_archive)
    new_stats = shared.build(source, new_archive)

    assert new_archive.read_bytes() == old_archive.read_bytes()
    assert new_stats["archive_bytes"] == old_stats["archive_bytes"]
    assert new_stats["v029_bytes"] == old_stats["v029_bytes"]
    assert new_stats["selected"] == old_stats["selected"]
    assert new_stats["saving_vs_v029_bytes"] == old_stats["saving_vs_v029_bytes"]
    assert new_stats["pre_overlay_graph_bytes"] == old_stats["pre_overlay_graph_bytes"]
    assert new_stats["overlay_bytes"] == old_stats["overlay_bytes"]
    assert new_stats["attempt5_graph_build_count"] == 1
    assert new_stats["shared_analysis_mode"] == "attempt5-graph-built-once"
    assert new_stats["selection_extra_payload_write_bytes"] == 0
    assert new_stats["publication_identity_check"] == "streamed-sha256"


def test_shared_portfolio_is_byte_identical_on_multi_file_tree(tmp_path: Path) -> None:
    source = tmp_path / "multi-source"
    _multi_file_fixture(source)
    _assert_identity(source, tmp_path, "multi")


def test_shared_portfolio_is_byte_identical_on_single_file_tree(tmp_path: Path) -> None:
    source = tmp_path / "single-source"
    _single_file_fixture(source)
    _assert_identity(source, tmp_path, "single")


def test_shared_floor_preserves_strict_tie_and_fast_reject_law(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "source"
    _single_file_fixture(source)
    temp = tmp_path / "shared"
    temp.mkdir()

    # Force only the *selection law* after both independently required v0.30 candidates exist. This proves a
    # retained graph cannot sneak into the accepted-v0.29 floor merely because Geometry needed it built.
    monkeypatch.setattr(shared.V029_ACCEPTED, "_fast_reject", lambda v028, files: "forced-fast-reject")
    result = shared._build_shared_candidates(source, temp)
    assert result["floor_selected"] == "v028-fallback"
    assert result["floor_path"] == result["v028_path"]
    assert result["v029_stats"]["fast_reject_reason"] == "forced-fast-reject"
    assert result["graph_path"].is_file()

# Footnote: the identity tests deliberately compare complete archive bytes, not only selected sizes. Scheduling
# is allowed to change wall time and temporary-artifact lifetime; it is not allowed to change one stored byte.
