from __future__ import annotations

from pathlib import Path

from cmpct.builder import Builder
from experiments.entropygraph_v030_r24_streaming_finalize import (
    MAX_IN_FLIGHT_FACTOR,
    PROMOTION_BOUNDARY,
    StreamingFinalizeBuilder,
)


def _fixture(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "alpha.txt").write_text("alpha-beta-gamma\n" * 80, encoding="utf-8")
    (root / "beta.json").write_text('{"k":"v","n":123}\n' * 70, encoding="utf-8")
    nested = root / "nested"
    nested.mkdir()
    (nested / "binary.bin").write_bytes(bytes(range(256)) * 12)
    (nested / "duplicate.txt").write_bytes((root / "alpha.txt").read_bytes())


def _build(builder_type, root: Path, out: Path, workers: int):
    builder = builder_type(root, workers=workers, reproducible=True, reproducible_epoch_ns=0)
    return builder.build(out)


def test_streaming_finalize_is_exact_r24_byte_identity_single_and_parallel(tmp_path: Path) -> None:
    source = tmp_path / "source"
    _fixture(source)

    baseline = tmp_path / "baseline.cmpct"
    streaming_single = tmp_path / "streaming-single.cmpct"
    streaming_parallel = tmp_path / "streaming-parallel.cmpct"

    base_stats = _build(Builder, source, baseline, 1)
    single_stats = _build(StreamingFinalizeBuilder, source, streaming_single, 1)
    parallel_stats = _build(StreamingFinalizeBuilder, source, streaming_parallel, 4)

    expected = baseline.read_bytes()
    assert streaming_single.read_bytes() == expected
    assert streaming_parallel.read_bytes() == expected
    for stats in (single_stats, parallel_stats):
        assert stats["bytes"] == base_stats["bytes"]
        assert stats["data_bytes"] == base_stats["data_bytes"]
        assert stats["unique_blobs"] == base_stats["unique_blobs"]
        assert stats["logical_files"] == base_stats["logical_files"]
        assert stats["recipes"] == base_stats["recipes"]


def test_streaming_finalize_does_not_queue_more_full_results_than_workers() -> None:
    # The RSS refinement deliberately permits no speculative second wave of full encoded results. Worker-level
    # raw buffers are released as soon as their codec competition completes; exact byte identity above guards the
    # CRC/header consequence of moving that release earlier than ordered publication.
    assert MAX_IN_FLIGHT_FACTOR == 1


def test_streaming_finalize_remains_research_only_until_rss_authority() -> None:
    assert PROMOTION_BOUNDARY == {
        "archive_bytes_changed": False,
        "grammar_changed": False,
        "codec_policy_changed": False,
        "selector_changed": False,
        "release_credit": False,
        "next_gate": "exact r24 + promoted-product identity, RSS and wall-time oracle",
    }
