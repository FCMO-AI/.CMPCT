from __future__ import annotations

from benchmarks import v030_perf_worker as worker


def test_v030_runtime_worker_uses_promoted_release_product_front_door() -> None:
    engine = worker._engine("v030")
    assert engine.__name__ == "experiments.entropygraph_v030_release_product"
    assert engine.PROMOTED_LOGS_INVERSE is True
    assert engine.PROMOTED_R24_OPAQUE_MEDIA_TERMINAL is True
    assert engine.PROMOTED_R24_COMPACT_CONTROL_TERMINAL is True
    assert engine.PROMOTED_R24_DEAD_DICTIONARY_ELISION is True


def test_v029_runtime_worker_keeps_accepted_historical_engine() -> None:
    engine = worker._engine("v029")
    assert engine.__name__ == "experiments.entropygraph_v029_release"
