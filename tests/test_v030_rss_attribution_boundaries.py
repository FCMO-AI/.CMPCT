from __future__ import annotations

from pathlib import Path

from benchmarks import v030_product_phase_rss_oracle as PRODUCT_PHASE
from benchmarks import v030_r25_candidate_phase_rss_oracle as CANDIDATE_PHASE


def test_candidate_phase_uses_total_fresh_process_peak_for_decisive_ratio(monkeypatch, tmp_path: Path) -> None:
    target = ("suite", "workload")
    source = tmp_path / "source"
    source.mkdir()
    monkeypatch.setattr(CANDIDATE_PHASE, "TARGETS", (target,))
    monkeypatch.setattr(CANDIDATE_PHASE.PERF, "_build_corpora", lambda _: {target: source})
    monkeypatch.setattr(CANDIDATE_PHASE.CAND, "treehash", lambda _: "tree")
    monkeypatch.setattr(CANDIDATE_PHASE, "_source_commit", lambda: "a" * 40)
    monkeypatch.setattr(CANDIDATE_PHASE, "_receipt_identity_valid", lambda *args: True)

    values = {
        "shipping": (100, 10),
        "g04": (150, 20),
        "prefixgraph": (120, 40),
    }

    def fake_worker(mode: str, _source: Path, archive: Path) -> dict:
        peak, incremental = values[mode]
        return {
            "mode": mode,
            "eligible": True,
            "worker_failed": False,
            "peak_rss_kib": peak,
            "incremental_peak_rss_kib": incremental,
            "wall_s": 1.0,
        }

    monkeypatch.setattr(CANDIDATE_PHASE, "_run_worker", fake_worker)
    result = CANDIDATE_PHASE.run(tmp_path / "work")
    row = result["rows"][0]

    assert row["g04_to_shipping_peak_rss_ratio"] == 1.5
    assert row["g04_to_shipping_rss_ratio"] == 2.0
    assert result["contract"]["release_boundary_attribution_uses_total_fresh_process_peak_rss"] is True
    assert result["contract"]["baseline_subtracted_ru_maxrss_is_diagnostic_only"] is True


def test_product_phase_uses_total_fresh_process_peak_for_decisive_ratio(monkeypatch, tmp_path: Path) -> None:
    target = ("suite", "workload")
    source = tmp_path / "source"
    source.mkdir()
    monkeypatch.setattr(PRODUCT_PHASE.PERF, "TARGETS", (target,))
    monkeypatch.setattr(PRODUCT_PHASE.PERF, "_build_corpora", lambda _: {target: source})
    monkeypatch.setattr(PRODUCT_PHASE.GENERAL, "_accepted_v029_rows", lambda: {target: {"tree_sha256": "tree"}})
    monkeypatch.setattr(PRODUCT_PHASE.GENERAL, "_historical_treehash", lambda _: "tree")
    monkeypatch.setattr(PRODUCT_PHASE, "product_tree_for_source", lambda _: "tree")

    values = {
        "r24": (100, 10),
        "profile": (120, 20),
        "full": (180, 60),
    }

    def fake_worker(mode: str, _source: Path, _root: Path) -> dict:
        peak, incremental = values[mode]
        receipt = {
            "mode": mode,
            "source_tree_sha256": "tree",
            "wall_s": 1.0,
            "baseline_rss_kib": peak - incremental,
            "operation_peak_rss_kib": peak,
            "incremental_peak_rss_kib": incremental,
        }
        if mode in {"r24", "full"}:
            receipt.update({"archive_sha256": mode, "archive_bytes": 100, "verified_tree_sha256": "tree"})
        return receipt

    monkeypatch.setattr(PRODUCT_PHASE, "_run_worker", fake_worker)
    result = PRODUCT_PHASE.run(tmp_path / "work")
    row = result["rows"][0]

    assert row["full_to_max_isolated_peak_rss_ratio"] == 1.5
    assert row["full_to_max_isolated_incremental_ratio"] == 3.0
    assert result["contract"]["release_boundary_attribution_uses_total_fresh_process_peak_rss"] is True
    assert result["contract"]["baseline_subtracted_ru_maxrss_is_diagnostic_only"] is True
