import random

from experiments.one.morphology_gate import _observe_bulk_digest
from experiments.one.observe import observe


def _bulk(data: bytes, *, max_index_entries: int = 1 << 16):
    return _observe_bulk_digest(
        data,
        min_run=8,
        chunk_size=64,
        max_index_entries=max_index_entries,
        classifier_bytes=0,
    )


def _assert_opportunity_parity(data: bytes, *, max_index_entries: int = 1 << 16) -> None:
    reference = observe(data, max_index_entries=max_index_entries)
    candidate = _bulk(data, max_index_entries=max_index_entries)
    assert candidate.runs == reference.runs
    assert candidate.reuse == reference.reuse
    assert candidate.stats.run_opportunity_bytes == reference.stats.run_opportunity_bytes
    assert candidate.stats.reuse_opportunity_bytes == reference.stats.reuse_opportunity_bytes
    assert candidate.stats.chunk_fingerprints == reference.stats.chunk_fingerprints
    assert candidate.stats.hash_lookups == reference.stats.hash_lookups
    assert candidate.stats.peak_index_entries == reference.stats.peak_index_entries


def test_bulk_digest_equivalence_at_chunk_boundaries() -> None:
    rng = random.Random(0xB01C)
    for size in (0, 1, 7, 8, 63, 64, 65, 127, 128, 129, 255, 256, 257, 4095, 4096, 4097):
        _assert_opportunity_parity(rng.randbytes(size))


def test_bulk_digest_equivalence_on_runs_crossing_chunk_boundaries() -> None:
    for offset in (0, 1, 7, 31, 63):
        prefix = bytes((i * 37 + 11) & 0xFF for i in range(offset))
        for run_length in (8, 63, 64, 65, 127, 128, 129, 257):
            suffix = bytes((i * 53 + 19) & 0xFF for i in range(193))
            _assert_opportunity_parity(prefix + b"7" * run_length + suffix)


def test_bulk_digest_equivalence_with_bounded_index_pressure() -> None:
    rng = random.Random(0x1D3E)
    chunks = [rng.randbytes(64) for _ in range(40)]
    data = b"".join(chunks + chunks[5:25] + chunks[0:10])
    for max_entries in (1, 2, 3, 7, 16, 31, 64):
        _assert_opportunity_parity(data, max_index_entries=max_entries)


def test_bulk_digest_equivalence_on_repeated_and_near_repeated_chunks() -> None:
    base = bytes((i * 17 + 3) & 0xFF for i in range(64))
    mutated = bytearray(base)
    mutated[31] ^= 0x5A
    data = b"".join((base, base, bytes(mutated), base, bytes(mutated), base))
    _assert_opportunity_parity(data)
