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


def test_diverse_numeric_root_gates_reuse_but_preserves_runs() -> None:
    data = _diverse_numeric_root(64 * 1024)
    baseline = observe(data)
    candidate = observe_morphology_gated(data)
    assert candidate.gate.gated
    assert candidate.gate.unique_chunk_fraction >= 0.90
    assert candidate.observation.runs == baseline.runs
    assert candidate.observation.reuse == ()
    assert candidate.observation.stats.chunk_fingerprints == 0
    assert candidate.observation.stats.hash_lookups == 0
    assert candidate.observation.stats.retained_index_payload_bytes == 0
    assert candidate.observation.stats.source_scan_bytes == len(data) + candidate.gate.sample_bytes


def test_repetitive_numeric_root_falls_through_to_preserve_reuse_laws() -> None:
    data = _repetitive_numeric_root(64 * 1024)
    baseline = observe(data)
    assert baseline.stats.reuse_opportunity_bytes > 0
    candidate = observe_morphology_gated(data)
    assert not candidate.gate.gated
    assert candidate.gate.unique_chunk_fraction < 0.90
    assert candidate.observation == baseline


def test_diverse_prefix_repetitive_tail_does_not_fool_sampling() -> None:
    size = 256 * 1024
    prefix = _diverse_numeric_root(16 * 1024)
    data = prefix + _repetitive_numeric_root(size - len(prefix))
    baseline = observe(data)
    assert baseline.stats.reuse_opportunity_bytes > size // 2
    candidate = observe_morphology_gated(data)
    assert not candidate.gate.gated
    assert candidate.gate.unique_chunk_fraction < 0.90
    assert candidate.observation == baseline


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
