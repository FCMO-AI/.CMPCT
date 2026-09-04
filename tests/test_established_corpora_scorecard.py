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


def test_zero_duration_samples_are_censored_from_timing_indices() -> None:
    corpora = {
        "timer-floor": {
            "logical_bytes": 1000,
            "results": {
                "cmpct-v0.29-shipping-r24": cell(bytes_=400, create=0.00, extract=0.01, rss=200),
                "zip-deflate-9": cell(bytes_=500, create=0.01, extract=0.00, rss=100),
            },
        }
    }
    p = scorecard.pairwise(corpora, "cmpct-v0.29-shipping-r24", "zip-deflate-9")
    assert p["size_index"] == 125.0
    assert p["create_speed_index"] is None
    assert p["create_speed_index_corpora"] == 0
    assert p["extract_speed_index"] is None
    assert p["extract_speed_index_corpora"] == 0


def test_mature_size_frontier_uses_best_successful_mature_result_per_corpus() -> None:
    corpora = {
        "a": {
            "logical_bytes": 1000,
            "results": {
                "cmpct-v0.29-shipping-r24": cell(bytes_=400, create=1, extract=1, rss=100),
                "zip-deflate-9": cell(bytes_=500, create=1, extract=1, rss=100),
                "zstd-19": cell(bytes_=300, create=1, extract=1, rss=100),
            },
        },
        "b": {
            "logical_bytes": 1000,
            "results": {
                "cmpct-v0.29-shipping-r24": cell(bytes_=200, create=1, extract=1, rss=100),
                "zip-deflate-9": cell(bytes_=250, create=1, extract=1, rss=100),
                "zstd-19": {"status": "timeout"},
            },
        },
    }
    f = scorecard.mature_size_frontier(corpora, "cmpct-v0.29-shipping-r24")
    assert f["corpora"] == 2
    assert (f["size_wins"], f["size_ties"], f["size_losses"]) == (1, 0, 1)
    # Per-corpus ratios are 300/400 and 250/200; geometric mean is sqrt(.9375).
    assert round(f["size_index"], 6) == round(100 * (0.9375 ** 0.5), 6)
