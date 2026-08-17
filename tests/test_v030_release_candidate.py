from __future__ import annotations

from pathlib import Path

from experiments import entropygraph_v030_release_candidate as rc


def _fake_verify(tree: str, engine: str = "strict-reader"):
    return {"ok": True, "tree_sha256": tree, "engine": engine}


def _locality(amp: float = 2.0):
    return {
        "max_member_read_amplification": amp,
        "prefix_records": 1,
        "passed": amp <= rc.MAX_MEMBER_READ_AMP,
        "rows": [],
    }


def _patch_reader(monkeypatch, tree: str) -> None:
    # Footnote: both pre-selection admission and post-publication verification now go through this one reader
    # authority. Tests patch that authority directly rather than accidentally proving legacy G04/PG readers.
    monkeypatch.setattr(rc.READER, "strong_verify", lambda path: _fake_verify(tree))


def test_complete_artifact_tournament_selects_smaller_prefixgraph(tmp_path: Path, monkeypatch) -> None:
    root = tmp_path / "src"
    root.mkdir()
    (root / "a.bin").write_bytes(b"a" * 128)
    out = tmp_path / "result.cmpct"
    tree = rc.PG.treehash(root)
    monkeypatch.setattr(rc, "treehash", lambda candidate: tree)
    _patch_reader(monkeypatch, tree)

    def fake_g04_build(candidate, path):
        path.write_bytes(rc.G04.MAG + b"g" * 992)
        return {"v029_bytes": 1100, "selected": "geometry-overlay-g04", "max_selected_member_read_amplification": 1.5}

    def fake_pg_build(candidate, path):
        path.write_bytes(rc.PG.MAGIC + b"p" * 892)
        return {"max_dependency_depth": 1}

    monkeypatch.setattr(rc.G04, "build", fake_g04_build)
    monkeypatch.setattr(rc.PG, "build", fake_pg_build)
    monkeypatch.setattr(rc, "_prefixgraph_locality", lambda path: _locality(2.0))

    stats = rc.build(root, out)
    assert stats["selected"] == "prefixgraph"
    assert stats["archive_bytes"] == 900
    assert stats["g04_bytes"] == 1000
    assert stats["v029_bytes"] == 1100
    assert stats["saving_vs_v029_bytes"] == 200
    assert stats["saving_vs_g04_bytes"] == 100
    assert stats["max_dependency_depth"] == 1
    assert stats["max_selected_member_read_amplification"] == 2.0
    assert stats["prefixgraph_contract_eligible"] is True
    assert stats["prefixgraph_admitted"] is True
    assert stats["selection_materialization"] == "same-filesystem-atomic-move"
    assert stats["selection_extra_payload_write_bytes"] == 0
    assert stats["reader_authority"] == "v030-release-streaming-policy-v1"
    assert out.read_bytes().startswith(rc.PG.MAGIC)
    assert not any(path.name.startswith(".cmpct-v030-release-candidate-") for path in tmp_path.iterdir())


def test_exact_tie_conservatively_retains_g04_path(tmp_path: Path, monkeypatch) -> None:
    root = tmp_path / "src"
    root.mkdir()
    (root / "a.bin").write_bytes(b"a" * 128)
    out = tmp_path / "result.cmpct"
    tree = rc.PG.treehash(root)
    monkeypatch.setattr(rc, "treehash", lambda candidate: tree)
    _patch_reader(monkeypatch, tree)

    def fake_g04_build(candidate, path):
        path.write_bytes(rc.G04.MAG + b"g" * 992)
        return {"v029_bytes": 1000, "selected": "geometry-overlay-g04", "max_selected_member_read_amplification": 1.0}

    def fake_pg_build(candidate, path):
        path.write_bytes(rc.PG.MAGIC + b"p" * 992)
        return {"max_dependency_depth": 1}

    monkeypatch.setattr(rc.G04, "build", fake_g04_build)
    monkeypatch.setattr(rc.PG, "build", fake_pg_build)
    monkeypatch.setattr(rc, "_prefixgraph_locality", lambda path: _locality(2.0))

    stats = rc.build(root, out)
    assert stats["selected"] == "g04-overlay"
    assert stats["archive_bytes"] == 1000
    assert stats["saving_vs_g04_bytes"] == 0
    assert out.read_bytes().startswith(rc.G04.MAG)


def test_smaller_prefixgraph_with_locality_debt_cannot_win(tmp_path: Path, monkeypatch) -> None:
    root = tmp_path / "src"
    root.mkdir()
    (root / "a.bin").write_bytes(b"a" * 128)
    out = tmp_path / "result.cmpct"
    tree = rc.PG.treehash(root)
    monkeypatch.setattr(rc, "treehash", lambda candidate: tree)
    _patch_reader(monkeypatch, tree)

    def fake_g04_build(candidate, path):
        path.write_bytes(rc.G04.MAG + b"g" * 992)
        return {"v029_bytes": 1100, "selected": "geometry-overlay-g04", "max_selected_member_read_amplification": 1.0}

    def fake_pg_build(candidate, path):
        path.write_bytes(rc.PG.MAGIC + b"p" * 792)
        return {"max_dependency_depth": 1}

    monkeypatch.setattr(rc.G04, "build", fake_g04_build)
    monkeypatch.setattr(rc.PG, "build", fake_pg_build)
    monkeypatch.setattr(rc, "_prefixgraph_locality", lambda path: _locality(8.01))

    stats = rc.build(root, out)
    assert stats["prefixgraph_bytes"] == 800
    assert stats["prefixgraph_admitted"] is False
    assert stats["prefixgraph_reject_reason"] == "locality-ceiling"
    assert stats["selected"] == "g04-overlay"
    assert out.read_bytes().startswith(rc.G04.MAG)


def test_ineligible_prefixgraph_is_not_built(tmp_path: Path, monkeypatch) -> None:
    root = tmp_path / "src"
    root.mkdir()
    (root / "large.bin").write_bytes(b"x")
    out = tmp_path / "result.cmpct"
    tree = rc.PG.treehash(root)
    monkeypatch.setattr(rc, "treehash", lambda candidate: tree)
    monkeypatch.setattr(rc, "_prefixgraph_eligibility", lambda candidate, expected: (False, "test-ineligible"))
    _patch_reader(monkeypatch, tree)

    def fake_g04_build(candidate, path):
        path.write_bytes(rc.G04.MAG + b"g" * 92)
        return {"v029_bytes": 120, "selected": "geometry-overlay-g04", "max_selected_member_read_amplification": 1.0}

    monkeypatch.setattr(rc.G04, "build", fake_g04_build)
    monkeypatch.setattr(rc.PG, "build", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("PG built")))

    stats = rc.build(root, out)
    assert stats["selected"] == "g04-overlay"
    assert stats["prefixgraph_contract_eligible"] is False
    assert stats["prefixgraph_admitted"] is False
    assert stats["prefixgraph_reject_reason"] == "test-ineligible"
    assert stats["prefixgraph_bytes"] is None


def test_prefixgraph_eligibility_requires_shared_tree_identity(tmp_path: Path, monkeypatch) -> None:
    root = tmp_path / "src"
    root.mkdir()
    (root / "a.bin").write_bytes(b"abc")
    expected = rc.PG.treehash(root)
    eligible, reason = rc._prefixgraph_eligibility(root, expected)
    assert eligible is True
    assert reason is None

    monkeypatch.setattr(rc.PG, "treehash", lambda candidate: "0" * 64)
    eligible, reason = rc._prefixgraph_eligibility(root, expected)
    assert eligible is False
    assert reason == "tree-identity-contract-mismatch"
