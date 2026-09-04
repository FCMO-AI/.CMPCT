from __future__ import annotations

import random

import pytest

from experiments.one.observe import observe


def test_fused_observer_finds_run_without_unseen_unaligned_reuse() -> None:
    chunk = bytes(range(64))
    data = b"\0" * 16 + chunk + bytes(reversed(chunk)) + chunk
    result = observe(data, min_run=8, chunk_size=64)
    assert result.stats.source_scan_bytes == len(data)
    assert result.stats.chunk_fingerprints == len(data) // 64
    assert result.stats.hash_lookups == result.stats.chunk_fingerprints
    assert result.runs[0].start == 0
    assert result.runs[0].length == 16
    # Alignment after the 16-byte prefix means the two `chunk` values are not fixed-
    # chunk aligned. G0.2 must not invent a reuse candidate it did not actually see.
    assert result.reuse == ()
    assert result.stats.total_source_read_bytes == len(data)


def test_aligned_reuse_is_nominated_only_after_byte_verification() -> None:
    source = bytes(range(64))
    data = source + bytes(reversed(source)) + source
    result = observe(data, chunk_size=64)
    assert len(result.reuse) == 1
    reuse = result.reuse[0]
    assert (reuse.source, reuse.target, reuse.length) == (0, 128, 64)
    assert data[reuse.source : reuse.source + reuse.length] == data[reuse.target : reuse.target + reuse.length]
    assert result.stats.collision_verifications == 1
    assert result.stats.verification_read_bytes == 128
    assert result.stats.total_source_read_bytes == len(data) + 128


def test_incompressible_random_input_has_sparse_false_pattern_surface() -> None:
    data = random.Random(7).randbytes(64 * 1024)
    result = observe(data, min_run=8, chunk_size=64)
    assert result.stats.source_scan_bytes == len(data)
    assert result.stats.chunk_fingerprints == 1024
    assert result.stats.reuse_candidates == 0
    assert result.stats.run_candidates == 0
    assert result.stats.collision_verifications == 0
    assert result.stats.total_source_read_bytes == len(data)


def test_index_cap_bounds_discovery_memory_without_stopping_scan() -> None:
    chunks = [bytes([value]) * 64 for value in range(20)]
    data = b"".join(chunks)
    result = observe(data, min_run=128, chunk_size=64, max_index_entries=3)
    assert result.stats.peak_index_entries == 3
    assert result.stats.chunk_fingerprints == 20
    assert result.stats.hash_lookups == 20
    assert result.stats.source_scan_bytes == len(data)


def test_empty_and_partial_chunk_inputs_are_deterministic() -> None:
    assert observe(b"").stats.source_scan_bytes == 0
    tiny = observe(b"abc", chunk_size=64)
    assert tiny.stats.chunk_fingerprints == 0
    assert tiny.runs == ()
    assert tiny.reuse == ()


@pytest.mark.parametrize(
    "kwargs",
    [
        {"min_run": 0},
        {"chunk_size": 0},
        {"max_index_entries": 0},
        {"chunk_size": True},
    ],
)
def test_invalid_observation_budgets_fail_closed(kwargs: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        observe(b"abc", **kwargs)  # type: ignore[arg-type]


def test_non_bytes_input_is_rejected() -> None:
    with pytest.raises(TypeError):
        observe(bytearray(b"abc"))  # type: ignore[arg-type]
