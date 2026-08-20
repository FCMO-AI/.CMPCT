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
    if new_stats["selected"] == "geometry-overlay-g04":
        assert new_stats["overlay_verification_state"] == "verified-before-publication"
        assert new_stats["losing_overlay_logical_verification_skipped"] is False
    else:
        assert new_stats["overlay_verification_state"] == "deferred-until-byte-win"
        assert new_stats["losing_overlay_logical_verification_skipped"] is True


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


def test_losing_overlay_is_not_strong_verified(tmp_path: Path, monkeypatch) -> None:
    """Exact byte loss must skip a full logical decode while keeping the winning floor byte-identical."""
    source = tmp_path / "source"
    source.mkdir()
    (source / "payload.bin").write_bytes(b"payload")
    expected_tree = "ab" * 32

    def fake_shared_candidates(_root: Path, temp: Path) -> dict:
        floor = temp / "floor.cmpct"
        graph = temp / "graph.cmpct"
        floor.write_bytes(b"F" * 10)
        graph.write_bytes(b"G" * 12)
        v029_stats = {"v028_child_s": 0.0, "attempt5_child_s": 0.0}
        return {
            "v028_path": floor,
            "graph_path": graph,
            "floor_path": floor,
            "floor_selected": "v028-fallback",
            "v028_bytes": 10,
            "graph_bytes": 12,
            "floor_bytes": 10,
            "v029_stats": v029_stats,
            "graph_stats": {},
            "shared_build_s": 0.0,
        }

    def fake_overlay(_graph: Path, overlay: Path) -> dict:
        overlay.write_bytes(b"O" * 20)
        return {
            "source_format": "fixture",
            "records": [],
            "transforms": [],
            "auditions": [],
            "write_stats": {"meta_raw_bytes": 0, "meta_comp_bytes": 0},
            "verified": None,
            "verification_state": "deferred-until-byte-win",
        }

    monkeypatch.setattr(shared, "_build_shared_candidates", fake_shared_candidates)
    monkeypatch.setattr(shared, "_overlay_retained_graph", fake_overlay)
    monkeypatch.setattr(shared, "treehash", lambda _root: expected_tree)
    monkeypatch.setattr(
        shared.G,
        "strong_verify",
        lambda _archive: (_ for _ in ()).throw(AssertionError("losing overlay must not be decoded")),
    )

    out = tmp_path / "selected.cmpct"
    result = shared.build(source, out)
    assert result["selected"] == "v029-fallback"
    assert result["losing_overlay_logical_verification_skipped"] is True
    assert result["overlay_verification_state"] == "deferred-until-byte-win"
    assert out.read_bytes() == b"F" * 10


def test_canonical_parallel_overlay_preserves_deferred_verification_contract(tmp_path: Path, monkeypatch) -> None:
    """The release-product parallel override must not resurrect eager verification or omit state metadata."""
    from experiments import entropygraph_v030_release_product as product

    private = product.C.SHARED
    graph = tmp_path / "graph.cmpct"
    graph.write_bytes(b"graph")
    overlay = tmp_path / "overlay.cmpct"

    monkeypatch.setattr(private.strict, "_read_source_records", lambda _path: ("fixture", None, {}, [b"record"]))
    monkeypatch.setattr(private.O, "_record_member_lengths", lambda _meta, _count: [6])
    monkeypatch.setattr(
        private.G,
        "_audition_record",
        lambda record_id, record, users: (record, None, {"record_id": record_id, "selected": "none"}),
    )

    def fake_write(_meta, _records, _transforms, path: Path) -> dict:
        path.write_bytes(b"overlay")
        return {"meta_raw_bytes": 0, "meta_comp_bytes": 0}

    monkeypatch.setattr(private.G, "_write_overlay", fake_write)
    monkeypatch.setattr(
        private.G,
        "strong_verify",
        lambda _archive: (_ for _ in ()).throw(AssertionError("overlay helper must defer logical verification")),
    )

    result = product._parallel_deferred_overlay(graph, overlay)
    assert overlay.read_bytes() == b"overlay"
    assert result["verified"] is None
    assert result["verification_state"] == "deferred-until-byte-win"
    assert result["audition_scheduler"] == "bounded-ordered-thread-pool-v1"
    assert result["audition_workers"] == 1


# Footnote: the identity tests deliberately compare complete archive bytes, not only selected sizes. Scheduling
# is allowed to change wall time and temporary-artifact lifetime; it is not allowed to change one stored byte.
# The losing-overlay tests narrow the optimization boundary further: only a candidate that loses exact complete
# byte pricing may skip logical verification; any byte-winning overlay is still verified before publication.
