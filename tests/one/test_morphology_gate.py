from experiments.one.morphology_gate import (
    classify_numeric_ascii,
    observe_morphology_gated,
)
from experiments.one.observe import observe


def _diverse_numeric_root(size: int) -> bytes:
    rows = []
    index = 0
    total = 0
    while total < size:
        row = f"{1700000000 + index:010d},{(index * 7919) % 100000000:08d}.{index % 997:03d},{(index * 37) % 360:03d}\n".encode()
        rows.append(row)
        total += len(row)
        index += 1
    return b"".join(rows)[:size]


def _repetitive_numeric_root(size: int) -> bytes:
    row = b"1700000000,12345.678,-91.25,42\n"
    return (row * ((size + len(row) - 1) // len(row)))[:size]


def _numeric_island_root(size: int) -> bytes:
    data = bytearray(_diverse_numeric_root(size))
    start = size // 7 + 4096
    end = 2 * size // 7 - 4096
    data[start:end] = _repetitive_numeric_root(end - start)
    return bytes(data)


def test_diverse_numeric_root_uses_bulk_digest_and_preserves_opportunities() -> None:
    data = _diverse_numeric_root(64 * 1024)
    baseline = observe(data)
    candidate = observe_morphology_gated(data)
    assert candidate.gate.gated
    assert candidate.gate.unique_chunk_fraction >= 0.90
    assert candidate.observation.runs == baseline.runs
    assert candidate.observation.reuse == baseline.reuse
    assert candidate.observation.stats.chunk_fingerprints == baseline.stats.chunk_fingerprints
    assert candidate.observation.stats.hash_lookups == baseline.stats.hash_lookups
    assert candidate.observation.stats.reuse_opportunity_bytes == baseline.stats.reuse_opportunity_bytes
    assert candidate.observation.stats.source_scan_bytes == len(data) + candidate.gate.sample_bytes


def test_bulk_digest_preserves_incomplete_tail_policy() -> None:
    data = _diverse_numeric_root(64 * 1024 + 17)
    baseline = observe(data)
    candidate = observe_morphology_gated(data)
    assert candidate.gate.gated
    assert candidate.observation.runs == baseline.runs
    assert candidate.observation.reuse == baseline.reuse
    assert candidate.observation.stats.chunk_fingerprints == baseline.stats.chunk_fingerprints
    assert candidate.observation.stats.hash_lookups == baseline.stats.hash_lookups


def test_bulk_digest_preserves_long_run_gate_semantics() -> None:
    data = bytearray(_diverse_numeric_root(128 * 1024))
    # Keep the root globally diverse/numeric while forcing a long-run chunk boundary.
    start = 64 * 700
    data[start : start + 256] = b"0" * 256
    frozen = bytes(data)
    baseline = observe(frozen)
    assert baseline.stats.run_opportunity_bytes >= 256
    candidate = observe_morphology_gated(frozen)
    assert candidate.gate.gated
    assert candidate.observation.runs == baseline.runs
    assert candidate.observation.reuse == baseline.reuse
    assert candidate.observation.stats.hash_lookups == baseline.stats.hash_lookups


def test_repetitive_numeric_root_falls_through_to_generic_observer() -> None:
    data = _repetitive_numeric_root(64 * 1024)
    baseline = observe(data)
    assert baseline.stats.reuse_opportunity_bytes > 0
    candidate = observe_morphology_gated(data)
    assert not candidate.gate.gated
    assert candidate.gate.unique_chunk_fraction < 0.90
    assert candidate.observation == baseline


def test_diverse_prefix_repetitive_tail_falls_through() -> None:
    size = 256 * 1024
    prefix = _diverse_numeric_root(16 * 1024)
    data = prefix + _repetitive_numeric_root(size - len(prefix))
    baseline = observe(data)
    assert baseline.stats.reuse_opportunity_bytes > size // 2
    candidate = observe_morphology_gated(data)
    assert not candidate.gate.gated
    assert candidate.gate.unique_chunk_fraction < 0.90
    assert candidate.observation == baseline


def test_unsampled_repetitive_island_cannot_destroy_reuse_evidence() -> None:
    size = 256 * 1024
    data = _numeric_island_root(size)
    baseline = observe(data)
    assert baseline.stats.reuse_opportunity_bytes > size // 20
    candidate = observe_morphology_gated(data)
    # This construction deliberately evades the deterministic morphology windows.
    assert candidate.gate.gated
    # The successor survives because gating now selects an implementation rather than
    # deleting the reuse opportunity class.
    assert candidate.observation.runs == baseline.runs
    assert candidate.observation.reuse == baseline.reuse
    assert candidate.observation.stats.reuse_opportunity_bytes == baseline.stats.reuse_opportunity_bytes


def test_tiny_numeric_root_is_not_gated() -> None:
    data = _diverse_numeric_root(4096)
    candidate = observe_morphology_gated(data)
    assert not candidate.gate.gated
    assert candidate.observation == observe(data)


def test_generic_binary_falls_through_exactly() -> None:
    data = bytes(range(256)) * 256
    candidate = observe_morphology_gated(data)
    assert not candidate.gate.gated
    assert candidate.observation == observe(data)


def test_digit_bearing_prose_does_not_false_gate() -> None:
    row = b"sensor alpha reading 12345 status nominal and stable\n"
    data = (row * 2048)[:64 * 1024]
    decision = classify_numeric_ascii(data)
    assert not decision.gated
    assert decision.numeric_fraction < 0.985


def test_numeric_alphabet_without_enough_digits_does_not_gate() -> None:
    data = (b"----,,,,    \n" * 8192)[:64 * 1024]
    decision = classify_numeric_ascii(data)
    assert decision.numeric_fraction == 1.0
    assert decision.digit_fraction < 0.35
    assert not decision.gated


def test_gate_parameters_fail_closed() -> None:
    data = _diverse_numeric_root(64 * 1024)
    for kwargs in (
        {"sample_limit": 0},
        {"minimum_input": 0},
        {"diversity_chunk_size": 0},
        {"sample_windows": 0},
        {"minimum_numeric_fraction": 1.1},
        {"minimum_digit_fraction": -0.1},
        {"minimum_unique_chunk_fraction": 1.1},
    ):
        try:
            classify_numeric_ascii(data, **kwargs)
        except ValueError:
            pass
        else:
            raise AssertionError(f"expected ValueError for {kwargs}")
