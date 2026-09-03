from __future__ import annotations


class _Queue:
    def __init__(self):
        self.rows = []

    def put(self, row):
        self.rows.append(row)


def test_canonical_shared_clone_uses_private_discovery_worker_only():
    from experiments import entropygraph_v029_parallel_portfolio as historical
    from experiments import entropygraph_v030_discovery_neutral_worker as worker
    from experiments import entropygraph_v030_profile_isolation as isolation

    assert isolation.SHARED.V029_SCHED is worker
    assert historical is not worker
    assert historical._worker is not worker._worker
    assert historical.ACCEPTED_ENGINE == worker.ACCEPTED_ENGINE


def test_attempt5_worker_neutralizes_and_restores_discovery_source(monkeypatch, tmp_path):
    from experiments import entropygraph_v030_discovery_neutral_worker as worker

    owner = worker.accepted.BASE.P
    original = owner._position_independent_candidates
    observed = {}

    def fake_build_graph(root, out):
        observed["provider"] = owner._position_independent_candidates
        observed["candidates"] = owner._position_independent_candidates([], [])
        out.write_bytes(b"candidate")
        return {"archive_bytes": len(b"candidate")}

    monkeypatch.setattr(worker.accepted, "build_graph", fake_build_graph)
    queue = _Queue()
    worker._worker("attempt5", str(tmp_path), str(tmp_path / "out.cmpct"), queue)

    assert len(queue.rows) == 1
    assert queue.rows[0]["ok"] is True
    assert observed["provider"] is worker._no_position_independent_candidates
    assert observed["candidates"] == []
    assert owner._position_independent_candidates is original


def test_attempt5_worker_restores_discovery_source_after_failure(monkeypatch, tmp_path):
    from experiments import entropygraph_v030_discovery_neutral_worker as worker

    owner = worker.accepted.BASE.P
    original = owner._position_independent_candidates

    def fail_build_graph(root, out):
        assert owner._position_independent_candidates is worker._no_position_independent_candidates
        raise RuntimeError("synthetic failure")

    monkeypatch.setattr(worker.accepted, "build_graph", fail_build_graph)
    queue = _Queue()
    worker._worker("attempt5", str(tmp_path), str(tmp_path / "out.cmpct"), queue)

    assert len(queue.rows) == 1
    assert queue.rows[0]["ok"] is False
    assert "synthetic failure" in queue.rows[0]["error"]
    assert owner._position_independent_candidates is original
