from __future__ import annotations

from pathlib import Path

from experiments import entropygraph_v030_geometry_overlay_prefallback as P


def _install_fake_pipeline(monkeypatch, tmp_path: Path, *, base_bytes: int, overlay_bytes: int):
    calls: list[str] = []
    tree = "a" * 64

    def fake_base_build(_root: Path, out: Path):
        calls.append("accepted-v029")
        out.write_bytes(b"B" * base_bytes)
        return {"selected": "inherited-fallback"}

    def fake_build_graph(_root: Path, out: Path):
        calls.append("prefallback-graph")
        out.write_bytes(b"G" * (base_bytes + 17))
        return {"selected": "placement-v4"}

    fake_record = (0, 1, b"x", 0, b"h" * 32)

    def fake_read_source_records(_path: Path):
        calls.append("read-prefallback-graph")
        return "placement-v4", None, {"files": {"f": [[0], 1, b"q" * 32]}}, [fake_record]

    def fake_users(_meta, _count):
        calls.append("member-locality-map")
        return [[1]]

    def fake_audition(record_id, record, users):
        calls.append("geometry-audition")
        assert record_id == 0
        assert record is fake_record
        assert users == [1]
        return record, ["lane", 4], {
            "selected": "lane",
            "payload_saving_bytes": 9,
            "max_member_read_amplification": 1.0,
        }

    def fake_write_overlay(_meta, _records, _transforms, out: Path):
        calls.append("write-overlay")
        out.write_bytes(b"O" * overlay_bytes)
        return {"meta_raw_bytes": 10, "meta_comp_bytes": 5}

    def fake_verify(_path: Path):
        calls.append("verify-overlay")
        return {"ok": True, "tree_sha256": tree}

    monkeypatch.setattr(P.BASE, "build", fake_base_build)
    monkeypatch.setattr(P.A5, "build_graph", fake_build_graph)
    monkeypatch.setattr(P.strict, "_read_source_records", fake_read_source_records)
    monkeypatch.setattr(P.O, "_record_member_lengths", fake_users)
    monkeypatch.setattr(P.O, "_audition_record", fake_audition)
    monkeypatch.setattr(P.O, "_write_overlay", fake_write_overlay)
    monkeypatch.setattr(P.strict, "strong_verify", fake_verify)
    monkeypatch.setattr(P.O, "treehash", lambda _root: tree)
    return calls, tree


def test_prefallback_graph_is_transformed_before_release_tournament(tmp_path: Path, monkeypatch) -> None:
    calls, tree = _install_fake_pipeline(monkeypatch, tmp_path, base_bytes=100, overlay_bytes=80)
    root = tmp_path / "root"
    root.mkdir()
    out = tmp_path / "winner.cmpct"

    stats = P.build(root, out)

    # Footnote: the causal law is the test. The accepted release is only the immutable floor; Geometry must
    # touch attempt5's candidate graph before the final complete-artifact tournament or inherited fallbacks can
    # make the transform unreachable, which is exactly what invalidated overlay V1.
    assert calls == [
        "accepted-v029",
        "prefallback-graph",
        "read-prefallback-graph",
        "member-locality-map",
        "geometry-audition",
        "write-overlay",
        "verify-overlay",
    ]
    assert stats["selected"] == "geometry-overlay"
    assert stats["integration_order"] == "attempt5-graph -> geometry-overlay -> accepted-v029-tournament"
    assert stats["tree_sha256"] == tree
    assert stats["pre_overlay_graph_bytes"] == 117
    assert stats["overlay_bytes"] == 80
    assert stats["saving_vs_v029_bytes"] == 20
    assert out.read_bytes() == b"O" * 80


def test_prefallback_overlay_can_never_regress_accepted_v029(tmp_path: Path, monkeypatch) -> None:
    _calls, _tree = _install_fake_pipeline(monkeypatch, tmp_path, base_bytes=100, overlay_bytes=140)
    root = tmp_path / "root"
    root.mkdir()
    out = tmp_path / "winner.cmpct"

    stats = P.build(root, out)

    assert stats["selected"] == "v029-fallback"
    assert stats["archive_bytes"] == stats["v029_bytes"] == 100
    assert stats["saving_vs_v029_bytes"] == 0
    assert stats["raw_overlay_delta_vs_v029_bytes"] == 40
    assert out.read_bytes() == b"B" * 100
