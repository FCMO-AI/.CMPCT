from __future__ import annotations

from pathlib import Path

from benchmarks import v030_perf_worker_v2 as worker
from benchmarks import v030_release_performance as base
from benchmarks import v030_release_performance_v2 as runtime_v2


def test_runtime_v2_worker_uses_promoted_release_product() -> None:
    engine = worker._engine("v030")
    assert engine.__name__ == "experiments.entropygraph_v030_release_product"
    assert "historical_convergence_facade" not in engine.__dict__


def test_runtime_v2_keeps_engine_owned_tree_identity_domains(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "payload.bin").write_bytes(b"cmpct-v030-runtime-v2")

    historical = "11" * 32
    canonical = "22" * 32
    monkeypatch.setattr(runtime_v2.PRODUCT, "treehash", lambda _source: canonical)

    assert runtime_v2._expected_tree_for_runtime_v2("v029", source, historical) == historical
    assert runtime_v2._expected_tree_for_runtime_v2("v030", source, historical) == canonical
    assert base._expected_tree_for_engine("v030", source, historical) == canonical


def test_runtime_v2_thresholds_remain_frozen() -> None:
    assert base.MAX_MEDIAN_RATIO == 1.10
    assert base.MAX_WORKLOAD_RATIO == 1.25
    assert base.MAX_PEAK_RSS_RATIO == 1.25
