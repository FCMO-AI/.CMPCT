from __future__ import annotations

from pathlib import Path

from benchmarks.one.one_g03_statistical_law_opportunity import (
    H0_MODEL_BYTES,
    H1_MODEL_BYTES,
    observe_workload,
)


def test_statistical_observer_counts_exact_bytes_and_resets_file_context(tmp_path: Path) -> None:
    root = tmp_path / "tree"
    root.mkdir()
    (root / "a.bin").write_bytes(b"A" * 4096)
    (root / "b.bin").write_bytes(b"B" * 4096)

    result = observe_workload(root)

    assert result["regular_files"] == 2
    assert result["measured_bytes"] == 8192
    assert result["observation_passes"] == 1
    assert result["h0"]["model_charge_bytes"] == H0_MODEL_BYTES
    assert result["h1"]["model_charge_bytes"] == H1_MODEL_BYTES
    # One deterministic symbol per file is perfectly predictable after the first byte;
    # the large dense H1 charge remains explicit rather than being optimized away.
    assert result["h1"]["ideal_surprise_bytes"] <= 1
    assert result["h1"]["modeled_payload_bytes"] >= H1_MODEL_BYTES


def test_statistical_observer_does_not_create_cross_file_transition(tmp_path: Path) -> None:
    root = tmp_path / "tree"
    root.mkdir()
    (root / "a.bin").write_bytes(bytes(range(256)))
    (root / "b.bin").write_bytes(bytes(range(255, -1, -1)))

    result = observe_workload(root)

    assert result["measured_bytes"] == 512
    assert result["h0"]["ideal_surprise_bytes"] == 512
    # The metric is an opportunity diagnostic, not a hidden product compressor.
    assert result["h0"]["modeled_payload_bytes"] == 512 + H0_MODEL_BYTES
    assert result["h1"]["modeled_payload_bytes"] >= H1_MODEL_BYTES
