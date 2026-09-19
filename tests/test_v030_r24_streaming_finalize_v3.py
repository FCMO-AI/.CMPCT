from __future__ import annotations

from pathlib import Path

from cmpct.builder import Builder
from experiments.entropygraph_v030_r24_streaming_finalize import StreamingFinalizeBuilder
from experiments.entropygraph_v030_r24_streaming_finalize_v3 import (
    CONTROL_CLASS,
    EVICT_CLASS,
    ConsumedCandidateEvictingStreamingFinalizeBuilder,
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
    stats = builder.build(out)
    return builder, stats


def test_v3_owner_is_exact_v2_control_plus_one_eviction_subclass() -> None:
    assert CONTROL_CLASS is StreamingFinalizeBuilder
    assert EVICT_CLASS is ConsumedCandidateEvictingStreamingFinalizeBuilder
    assert issubclass(EVICT_CLASS, CONTROL_CLASS)


def test_consumed_candidate_eviction_preserves_exact_r24_bytes_and_drains_candidate_map(tmp_path: Path) -> None:
    source = tmp_path / "source"
    _fixture(source)

    baseline = tmp_path / "baseline.cmpct"
    control = tmp_path / "control.cmpct"
    evict_single = tmp_path / "evict-single.cmpct"
    evict_parallel = tmp_path / "evict-parallel.cmpct"

    base_builder, base_stats = _build(Builder, source, baseline, 1)
    control_builder, control_stats = _build(CONTROL_CLASS, source, control, 4)
    single_builder, single_stats = _build(EVICT_CLASS, source, evict_single, 1)
    parallel_builder, parallel_stats = _build(EVICT_CLASS, source, evict_parallel, 4)

    expected = baseline.read_bytes()
    assert control.read_bytes() == expected
    assert evict_single.read_bytes() == expected
    assert evict_parallel.read_bytes() == expected
    for stats in (control_stats, single_stats, parallel_stats):
        assert stats["bytes"] == base_stats["bytes"]
        assert stats["data_bytes"] == base_stats["data_bytes"]
        assert stats["unique_blobs"] == base_stats["unique_blobs"]
        assert stats["logical_files"] == base_stats["logical_files"]
        assert stats["recipes"] == base_stats["recipes"]

    # This is the exact ownership fact under test: v2 keeps consumed shells, v3 does not. The mature Builder is
    # included only as a byte-identity oracle; its post-build candidate-map lifetime is not a v3 hypothesis.
    assert control_builder.cands
    assert not single_builder.cands
    assert not parallel_builder.cands
    assert base_builder.cands
