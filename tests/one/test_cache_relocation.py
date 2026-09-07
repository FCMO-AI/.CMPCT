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
    second = observe_fingerprints_relocated(
        data, previous=first.cache, block_size=1024, chunk_size=64
    )
    assert second.fingerprints == _oracle(data, 64)
    assert second.stats.positional_reused_blocks == 8
    assert second.stats.relocated_reused_blocks == 0
    assert second.stats.recomputed_blocks == 0
    assert second.stats.relocation_index_entries == 0
    assert second.stats.relocation_lookups == 0


def test_block_aligned_insertion_reuses_shifted_unchanged_blocks_by_content_identity():
    base = _blocks(6)
    seed = observe_fingerprints_relocated(base, block_size=1024, chunk_size=64)
    inserted = bytes([99]) * 1024
    current = base[: 2 * 1024] + inserted + base[2 * 1024 :]
    result = observe_fingerprints_relocated(
        current, previous=seed.cache, block_size=1024, chunk_size=64
    )
    assert result.fingerprints == _oracle(current, 64)
    assert result.stats.recomputed_blocks == 1
    assert result.stats.positional_reused_blocks == 2
    assert result.stats.relocated_reused_blocks == 4
    assert result.stats.feature_recompute_bytes == 1024
    assert result.stats.feature_reuse_bytes == len(base)
    assert result.stats.relocation_index_entries == 6


def test_block_reorder_reuses_every_block_without_recomputing_features():
    base = _blocks(5)
    seed = observe_fingerprints_relocated(base, block_size=1024, chunk_size=64)
    current = base[3 * 1024 :] + base[: 3 * 1024]
    result = observe_fingerprints_relocated(
        current, previous=seed.cache, block_size=1024, chunk_size=64
    )
    assert result.fingerprints == _oracle(current, 64)
    assert result.stats.recomputed_blocks == 0
    assert result.stats.relocated_reused_blocks == 5


def test_one_byte_insertion_does_not_fake_reuse_of_realigned_fingerprint_groups():
    base = bytes(range(251)) * 80
    seed = observe_fingerprints_relocated(base, block_size=1024, chunk_size=64)
    current = b"X" + base
    result = observe_fingerprints_relocated(
        current, previous=seed.cache, block_size=1024, chunk_size=64
    )
    assert result.fingerprints == _oracle(current, 64)
    # The candidate is deliberately not a CDC cache: byte-shifted aligned features have
    # different semantics and must not be called reusable merely because bytes resemble.
    assert result.stats.recomputed_blocks > 0


def test_relocation_index_bound_limits_memory_and_can_only_reduce_reuse():
    base = _blocks(8)
    seed = observe_fingerprints_relocated(base, block_size=1024, chunk_size=64)
    current = base[4 * 1024 :] + base[: 4 * 1024]
    result = observe_fingerprints_relocated(
        current,
        previous=seed.cache,
        block_size=1024,
        chunk_size=64,
        max_relocation_entries=2,
    )
    assert result.fingerprints == _oracle(current, 64)
    assert result.stats.relocation_index_entries == 2
    assert result.stats.relocation_index_payload_bytes == 96
    assert result.stats.recomputed_blocks > 0


def test_damaged_relocation_candidate_is_not_authority():
    base = _blocks(4)
    seed = observe_fingerprints_relocated(base, block_size=1024, chunk_size=64)
    blocks = list(seed.cache.blocks)
    victim = blocks[2]
    damaged_values = list(victim.fingerprints)
    damaged_values[0] ^= 1
    blocks[2] = FingerprintBlock(
        digest=victim.digest,
        length=victim.length,
        fingerprints=tuple(damaged_values),
        seal=victim.seal,
    )
    poisoned = FingerprintCache(
        seed.cache.policy_id, seed.cache.block_size, seed.cache.chunk_size, tuple(blocks)
    )
    current = base[2 * 1024 :] + base[: 2 * 1024]
    result = observe_fingerprints_relocated(
        current, previous=poisoned, block_size=1024, chunk_size=64
    )
    assert result.fingerprints == _oracle(current, 64)
    # At least the damaged content must be recomputed rather than inherited.
    assert result.stats.recomputed_blocks >= 1


def test_policy_relabel_cannot_make_old_seals_valid_for_relocation():
    base = _blocks(4)
    seed = observe_fingerprints_relocated(
        base, block_size=1024, chunk_size=64, policy_id="policy-a"
    )
    relabelled = FingerprintCache(
        "policy-b", seed.cache.block_size, seed.cache.chunk_size, seed.cache.blocks
    )
    current = base[2 * 1024 :] + base[: 2 * 1024]
    result = observe_fingerprints_relocated(
        current,
        previous=relabelled,
        block_size=1024,
        chunk_size=64,
        policy_id="policy-b",
    )
    assert result.fingerprints == _oracle(current, 64)
    assert result.stats.recomputed_blocks == 4
    assert result.stats.relocated_reused_blocks == 0


def test_current_digest_still_names_current_bytes_after_relocation():
    base = _blocks(3)
    seed = observe_fingerprints_relocated(base, block_size=1024, chunk_size=64)
    current = base[1024:] + base[:1024]
    result = observe_fingerprints_relocated(
        current, previous=seed.cache, block_size=1024, chunk_size=64
    )
    assert result.cache.blocks[0].digest == hashlib.sha256(current[:1024]).digest()
