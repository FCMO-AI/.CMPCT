import hashlib

from experiments.one.cache_fingerprints import FingerprintBlock, FingerprintCache
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


def test_exact_repeat_stays_positional_and_does_not_build_relocation_index():
    data = _blocks(8)
    first = observe_fingerprints_relocated(data, block_size=1024, chunk_size=64)
    second = observe_fingerprints_relocated(data, previous=first.cache, block_size=1024, chunk_size=64)
    assert second.fingerprints == _oracle(data, 64)
    assert second.stats.positional_reused_blocks == 8
    assert second.stats.recomputed_blocks == 0
    assert second.stats.relocation_index_entries == 0
    assert second.stats.relocation_lookups == 0


def test_single_sparse_mutation_does_not_activate_global_relocation_search():
    base = _blocks(8)
    seed = observe_fingerprints_relocated(base, block_size=1024, chunk_size=64)
    current = bytearray(base)
    current[3 * 1024 + 17] ^= 0x7F
    result = observe_fingerprints_relocated(bytes(current), previous=seed.cache, block_size=1024, chunk_size=64)
    assert result.fingerprints == _oracle(bytes(current), 64)
    assert result.stats.recomputed_blocks == 1
    assert result.stats.positional_reused_blocks == 7
    assert result.stats.relocation_index_entries == 0
    assert result.stats.relocation_lookups == 0
    assert result.stats.relocation_gate_activations == 0


def test_block_aligned_insertion_reuses_shifted_unchanged_blocks_after_gate():
    base = _blocks(6)
    seed = observe_fingerprints_relocated(base, block_size=1024, chunk_size=64)
    inserted = bytes([99]) * 1024
    current = base[: 2 * 1024] + inserted + base[2 * 1024 :]
    result = observe_fingerprints_relocated(current, previous=seed.cache, block_size=1024, chunk_size=64)
    assert result.fingerprints == _oracle(current, 64)
    assert result.stats.recomputed_blocks == 1
    assert result.stats.positional_reused_blocks == 2
    assert result.stats.relocated_reused_blocks == 4
    assert result.stats.relocation_gate_activations == 1
    assert result.stats.feature_recompute_bytes == 1024
    assert result.stats.feature_reuse_bytes == len(base)


def test_block_reorder_spends_one_probe_block_then_reuses_remainder():
    base = _blocks(8)
    seed = observe_fingerprints_relocated(base, block_size=1024, chunk_size=64)
    current = base[4 * 1024 :] + base[: 4 * 1024]
    result = observe_fingerprints_relocated(current, previous=seed.cache, block_size=1024, chunk_size=64)
    assert result.fingerprints == _oracle(current, 64)
    assert result.stats.recomputed_blocks == 1
    assert result.stats.relocated_reused_blocks == 7
    assert result.stats.relocation_gate_activations == 1


def test_repetitive_reorder_indexes_unique_content_not_duplicate_blocks():
    block_size = 1024
    a = b"A" * block_size
    b = b"B" * block_size
    base = (a + b) * 8
    current = (b + a) * 8
    seed = observe_fingerprints_relocated(base, block_size=block_size, chunk_size=64)
    result = observe_fingerprints_relocated(
        current,
        previous=seed.cache,
        block_size=block_size,
        chunk_size=64,
    )
    assert result.fingerprints == _oracle(current, 64)
    assert result.stats.recomputed_blocks == 1
    assert result.stats.relocated_reused_blocks == 15
    assert result.stats.relocation_index_entries == 2
    assert result.stats.relocation_index_payload_bytes == 96


def test_duplicate_identity_with_damaged_representative_fails_closed():
    block_size = 1024
    a = b"A" * block_size
    b = b"B" * block_size
    base = (a + b) * 4
    seed = observe_fingerprints_relocated(base, block_size=block_size, chunk_size=64)
    blocks = list(seed.cache.blocks)
    first_a = blocks[0]
    damaged = list(first_a.fingerprints)
    damaged[0] ^= 1
    blocks[0] = FingerprintBlock(first_a.digest, first_a.length, tuple(damaged), first_a.seal)
    poisoned = FingerprintCache(
        seed.cache.policy_id,
        seed.cache.block_size,
        seed.cache.chunk_size,
        tuple(blocks),
    )
    current = (b + a) * 4
    result = observe_fingerprints_relocated(
        current,
        previous=poisoned,
        block_size=block_size,
        chunk_size=64,
    )
    assert result.fingerprints == _oracle(current, 64)
    # The first A representative is deliberately invalid. The unique-identity index is
    # allowed to lose those reuse opportunities, but it must never reuse corrupt state.
    assert result.stats.relocation_index_entries == 2
    assert result.stats.recomputed_blocks >= 2


def test_one_byte_insertion_does_not_fake_reuse_of_realigned_fingerprint_groups():
    base = bytes(range(251)) * 80
    seed = observe_fingerprints_relocated(base, block_size=1024, chunk_size=64)
    current = b"X" + base
    result = observe_fingerprints_relocated(current, previous=seed.cache, block_size=1024, chunk_size=64)
    assert result.fingerprints == _oracle(current, 64)
    assert result.stats.recomputed_blocks > 0


def test_relocation_index_bound_limits_memory_and_can_only_reduce_reuse():
    base = _blocks(8)
    seed = observe_fingerprints_relocated(base, block_size=1024, chunk_size=64)
    current = base[4 * 1024 :] + base[: 4 * 1024]
    result = observe_fingerprints_relocated(current, previous=seed.cache, block_size=1024, chunk_size=64, max_relocation_entries=2)
    assert result.fingerprints == _oracle(current, 64)
    assert result.stats.relocation_index_entries == 2
    assert result.stats.relocation_index_payload_bytes == 96
    assert result.stats.recomputed_blocks > 0


def test_damaged_relocation_candidate_is_not_authority():
    base = _blocks(6)
    seed = observe_fingerprints_relocated(base, block_size=1024, chunk_size=64)
    blocks = list(seed.cache.blocks)
    victim = blocks[3]
    damaged_values = list(victim.fingerprints)
    damaged_values[0] ^= 1
    blocks[3] = FingerprintBlock(victim.digest, victim.length, tuple(damaged_values), victim.seal)
    poisoned = FingerprintCache(seed.cache.policy_id, seed.cache.block_size, seed.cache.chunk_size, tuple(blocks))
    current = base[3 * 1024 :] + base[: 3 * 1024]
    result = observe_fingerprints_relocated(current, previous=poisoned, block_size=1024, chunk_size=64)
    assert result.fingerprints == _oracle(current, 64)
    assert result.stats.recomputed_blocks >= 1


def test_policy_relabel_cannot_make_old_seals_valid_for_relocation():
    base = _blocks(4)
    seed = observe_fingerprints_relocated(base, block_size=1024, chunk_size=64, policy_id="policy-a")
    relabelled = FingerprintCache("policy-b", seed.cache.block_size, seed.cache.chunk_size, seed.cache.blocks)
    current = base[2 * 1024 :] + base[: 2 * 1024]
    result = observe_fingerprints_relocated(current, previous=relabelled, block_size=1024, chunk_size=64, policy_id="policy-b")
    assert result.fingerprints == _oracle(current, 64)
    assert result.stats.recomputed_blocks == 4
    assert result.stats.relocated_reused_blocks == 0


def test_current_digest_still_names_current_bytes_after_relocation():
    base = _blocks(4)
    seed = observe_fingerprints_relocated(base, block_size=1024, chunk_size=64)
    current = base[2 * 1024 :] + base[: 2 * 1024]
    result = observe_fingerprints_relocated(current, previous=seed.cache, block_size=1024, chunk_size=64)
    assert result.cache.blocks[0].digest == hashlib.sha256(current[:1024]).digest()
