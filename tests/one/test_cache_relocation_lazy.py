import hashlib

import pytest

from experiments.one.cache_relocation import observe_fingerprints_relocated


_OFFSET = 0xCBF29CE484222325
_PRIME = 0x100000001B3
_MASK = (1 << 64) - 1


def _oracle(data: bytes, chunk_size: int) -> tuple[int, ...]:
    out = []
    for start in range(0, len(data) - chunk_size + 1, chunk_size):
        value = _OFFSET
        for byte in data[start : start + chunk_size]:
            value ^= byte
            value = (value * _PRIME) & _MASK
        out.append(value)
    return tuple(out)


def _blocks(count: int, block_size: int = 1024) -> bytes:
    return b"".join(bytes([index + 1]) * block_size for index in range(count))


def test_no_carry_exact_repeat_emits_no_directory_and_scans_nothing():
    data = _blocks(8)
    seed = observe_fingerprints_relocated(data, block_size=1024, chunk_size=64, persist_directory=False)
    second = observe_fingerprints_relocated(
        data,
        previous=seed.cache,
        block_size=1024,
        chunk_size=64,
        persist_directory=False,
    )
    assert second.fingerprints == _oracle(data, 64)
    assert second.directory.entries == ()
    assert second.stats.directory_output_entries == 0
    assert second.stats.directory_output_payload_bytes == 0
    assert second.stats.prior_cache_index_scan_blocks == 0
    assert second.stats.relocation_gate_activations == 0
    assert second.stats.recomputed_blocks == 0


def test_no_carry_sparse_mutation_stays_local():
    base = _blocks(8)
    seed = observe_fingerprints_relocated(base, block_size=1024, chunk_size=64, persist_directory=False)
    current = bytearray(base)
    current[3 * 1024 + 19] ^= 0xA5
    result = observe_fingerprints_relocated(
        bytes(current),
        previous=seed.cache,
        block_size=1024,
        chunk_size=64,
        persist_directory=False,
    )
    assert result.fingerprints == _oracle(bytes(current), 64)
    assert result.directory.entries == ()
    assert result.stats.prior_cache_index_scan_blocks == 0
    assert result.stats.relocation_gate_activations == 0
    assert result.stats.recomputed_blocks == 1
    assert result.stats.positional_reused_blocks == 7


def test_no_carry_aligned_insertion_pays_one_scan_then_reuses():
    base = _blocks(6)
    seed = observe_fingerprints_relocated(base, block_size=1024, chunk_size=64, persist_directory=False)
    inserted = b"Z" * 1024
    current = base[: 2 * 1024] + inserted + base[2 * 1024 :]
    result = observe_fingerprints_relocated(
        current,
        previous=seed.cache,
        block_size=1024,
        chunk_size=64,
        persist_directory=False,
    )
    assert result.fingerprints == _oracle(current, 64)
    assert result.directory.entries == ()
    assert result.stats.prior_cache_index_scan_blocks == 6
    assert result.stats.recomputed_blocks == 1
    assert result.stats.relocated_reused_blocks == 4
    assert result.stats.feature_recompute_bytes == 1024
    assert result.stats.feature_reuse_bytes == len(base)


def test_no_carry_reorder_is_exact_and_bounded():
    base = _blocks(8)
    seed = observe_fingerprints_relocated(base, block_size=1024, chunk_size=64, persist_directory=False)
    current = base[4 * 1024 :] + base[: 4 * 1024]
    result = observe_fingerprints_relocated(
        current,
        previous=seed.cache,
        block_size=1024,
        chunk_size=64,
        persist_directory=False,
    )
    assert result.fingerprints == _oracle(current, 64)
    assert result.stats.prior_cache_index_scan_blocks == 8
    assert result.stats.recomputed_blocks == 1
    assert result.stats.relocated_reused_blocks == 7


def test_no_carry_one_byte_shift_never_fakes_aligned_reuse():
    base = bytes(range(251)) * 80
    seed = observe_fingerprints_relocated(base, block_size=1024, chunk_size=64, persist_directory=False)
    current = b"X" + base
    result = observe_fingerprints_relocated(
        current,
        previous=seed.cache,
        block_size=1024,
        chunk_size=64,
        persist_directory=False,
    )
    assert result.fingerprints == _oracle(current, 64)
    assert result.directory.entries == ()
    assert result.stats.recomputed_blocks > 0


def test_persist_directory_flag_rejects_non_bool():
    with pytest.raises(TypeError):
        observe_fingerprints_relocated(b"abc", persist_directory=1)


def test_current_digest_is_still_current_content_identity_without_directory():
    base = _blocks(4)
    seed = observe_fingerprints_relocated(base, block_size=1024, chunk_size=64, persist_directory=False)
    current = base[2 * 1024 :] + base[: 2 * 1024]
    result = observe_fingerprints_relocated(
        current,
        previous=seed.cache,
        block_size=1024,
        chunk_size=64,
        persist_directory=False,
    )
    assert result.cache.blocks[0].digest == hashlib.sha256(current[:1024]).digest()
