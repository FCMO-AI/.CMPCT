from __future__ import annotations

import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "benchmarks" / "score_established_corpora.py"
spec = importlib.util.spec_from_file_location("score_established_corpora", MODULE_PATH)
assert spec and spec.loader
scorecard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scorecard)


def cell(*, bytes_: int, create: float, extract: float, rss: int) -> dict:
    return {
        "status": "ok",
        "bytes": bytes_,
        "create": {"median_s": create},
        "extract": {"median_s": extract},
        "create_peak_rss_kib_samples": [rss],
        "extract_peak_rss_kib_samples": [rss],
    }


def test_pairwise_indices_are_100_at_parity_and_above_100_when_cmpct_is_better() -> None:
    corpora = {
        "toy": {
            "logical_bytes": 1000,
            "results": {
                "cmpct-v0.29-shipping-r24": cell(bytes_=400, create=2.0, extract=1.0, rss=200),
                "zip-deflate-9": cell(bytes_=500, create=1.0, extract=2.0, rss=100),
            },
        }
    }
    p = scorecard.pairwise(corpora, "cmpct-v0.29-shipping-r24", "zip-deflate-9")
    assert p["size_index"] == 125.0
    assert p["create_speed_index"] == 50.0
    assert p["extract_speed_index"] == 200.0
    assert p["create_memory_index"] == 50.0
    assert (p["size_wins"], p["size_ties"], p["size_losses"]) == (1, 0, 0)


def test_failures_reduce_coverage_instead_of_disappearing() -> None:
    corpora = {
        "ok": {
            "logical_bytes": 1000,
            "results": {"cmpct-v0.29-research": cell(bytes_=300, create=1.0, extract=1.0, rss=100)},
        },
        "timeout": {
            "logical_bytes": 1000,
            "results": {"cmpct-v0.29-research": {"status": "timeout", "timeout_ceiling_s": 10}},
        },
    }
    s = scorecard.engine_summary(corpora, "cmpct-v0.29-research")
    assert s["attempted_corpora"] == 2
    assert s["successful_corpora"] == 1
    assert s["coverage_pct"] == 50.0
    assert s["timeout_corpora"] == 1
