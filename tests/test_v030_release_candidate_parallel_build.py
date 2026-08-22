from __future__ import annotations

from pathlib import Path
import threading

from experiments import entropygraph_v030_release_candidate as rc


def test_eligible_g04_and_prefixgraph_builds_overlap_without_changing_selection(tmp_path: Path, monkeypatch) -> None:
    root = tmp_path / "src"
    root.mkdir()
    (root / "a.bin").write_bytes(b"a" * 128)
    out = tmp_path / "result.cmpct"
    tree = "1" * 64
    barrier = threading.Barrier(2, timeout=2.0)
    entered: list[str] = []
    lock = threading.Lock()

    monkeypatch.setattr(rc, "treehash", lambda candidate: tree)
    monkeypatch.setattr(rc, "_prefixgraph_eligibility", lambda candidate, expected: (True, None))
    monkeypatch.setattr(rc, "_prefixgraph_locality", lambda path: {
        "max_member_read_amplification": 2.0,
        "prefix_records": 1,
        "passed": True,
        "rows": [],
    })
    monkeypatch.setattr(rc, "_verify_component", lambda path, expected, label: {
        "ok": True,
        "tree_sha256": expected,
        "engine": "test",
    })

    def fake_g04_build(candidate: Path, path: Path) -> dict:
        with lock:
            entered.append("g04")
        barrier.wait()
        path.write_bytes(rc.G04.MAG + b"g" * 992)
        return {
            "v029_bytes": 1100,
            "selected": "geometry-overlay-g04",
            "max_selected_member_read_amplification": 1.0,
        }

    def fake_pg_build(candidate: Path, path: Path) -> dict:
        with lock:
            entered.append("pg")
        barrier.wait()
        path.write_bytes(rc.PG.MAGIC + b"p" * 892)
        return {"max_dependency_depth": 1}

    monkeypatch.setattr(rc.G04, "build", fake_g04_build)
    monkeypatch.setattr(rc.PG, "build", fake_pg_build)

    stats = rc.build(root, out)

    assert sorted(entered) == ["g04", "pg"]
    assert stats["candidate_build_workers"] == 2
    assert stats["candidate_build_scheduler"] == "parallel-independent-complete-artifacts-v1"
    assert stats["selected"] == "prefixgraph"
    assert stats["archive_bytes"] == 900
    assert stats["g04_bytes"] == 1000
    assert stats["prefixgraph_bytes"] == 900
    assert stats["prefixgraph_admitted"] is True
    assert out.read_bytes().startswith(rc.PG.MAGIC)


def test_ineligible_prefixgraph_keeps_single_builder_path(tmp_path: Path, monkeypatch) -> None:
    root = tmp_path / "src"
    root.mkdir()
    (root / "a.bin").write_bytes(b"a" * 16)
    out = tmp_path / "result.cmpct"
    tree = "2" * 64

    monkeypatch.setattr(rc, "treehash", lambda candidate: tree)
    monkeypatch.setattr(rc, "_prefixgraph_eligibility", lambda candidate, expected: (False, "shape-reject"))
    monkeypatch.setattr(rc, "_verify_component", lambda path, expected, label: {
        "ok": True,
        "tree_sha256": expected,
        "engine": "test",
    })

    def fake_g04_build(candidate: Path, path: Path) -> dict:
        path.write_bytes(rc.G04.MAG + b"g" * 92)
        return {
            "v029_bytes": 120,
            "selected": "geometry-overlay-g04",
            "max_selected_member_read_amplification": 1.0,
        }

    monkeypatch.setattr(rc.G04, "build", fake_g04_build)
    monkeypatch.setattr(rc.PG, "build", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("PG built")))

    stats = rc.build(root, out)

    assert stats["candidate_build_workers"] == 1
    assert stats["candidate_build_scheduler"] == "g04-only-v1"
    assert stats["prefixgraph_contract_eligible"] is False
    assert stats["prefixgraph_reject_reason"] == "shape-reject"
    assert stats["selected"] == "g04-overlay"
