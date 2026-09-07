import hashlib

from experiments.one.cache_fingerprints import (
    FingerprintBlock,
    FingerprintCache,
    observe_fingerprints_cached,
)


_OFFSET = 0xCBF29CE484222325
_PRIME = 0x100000001B3
_MASK = (1 << 64) - 1


def _oracle(data: bytes, chunk_size: int) -> tuple[int, ...]:
    """Independent aligned-FNV oracle; does not call the candidate feature kernel."""
    out = []
    for start in range(0, len(data) - chunk_size + 1, chunk_size):
        value = _OFFSET
        for byte in data[start : start + chunk_size]:
            value ^= byte
            value = (value * _PRIME) & _MASK
        out.append(value)
    return tuple(out)


def test_fresh_and_cached_fingerprint_stream_matches_independent_oracle():
    data = bytes(range(251)) * 97 + b"tail"
    first = observe_fingerprints_cached(data, block_size=1024, chunk_size=64)
    second = observe_fingerprints_cached(
        data, previous=first.cache, block_size=1024, chunk_size=64
    )
    expected = _oracle(data, 64)
    assert first.fingerprints == expected
    assert second.fingerprints == expected
    assert second.stats.validation_read_bytes == len(data)
    assert second.stats.feature_recompute_bytes == 0
    assert second.stats.reused_blocks == len(first.cache.blocks)


def test_sparse_edit_recomputes_only_changed_feature_block():
    base = bytearray(bytes(range(256)) * 64)
    first = observe_fingerprints_cached(bytes(base), block_size=4096, chunk_size=64)
    base[2 * 4096 + 17] ^= 0x55
    current = bytes(base)
    incremental = observe_fingerprints_cached(
        current, previous=first.cache, block_size=4096, chunk_size=64
    )
    fresh = observe_fingerprints_cached(current, block_size=4096, chunk_size=64)
    assert incremental.fingerprints == fresh.fingerprints == _oracle(current, 64)
    assert incremental.stats.recomputed_blocks == 1
    assert incremental.stats.feature_recompute_bytes == 4096
    assert incremental.stats.feature_reuse_bytes == len(current) - 4096


def test_cache_feature_corruption_with_valid_content_digest_fails_closed():
    data = bytes(range(256)) * 32
    first = observe_fingerprints_cached(data, block_size=4096, chunk_size=64)
    blocks = list(first.cache.blocks)
    original = blocks[0]
    damaged = list(original.fingerprints)
    damaged[3] ^= 1
    blocks[0] = FingerprintBlock(
        digest=original.digest,
        length=original.length,
        fingerprints=tuple(damaged),
        seal=original.seal,
    )
    poisoned = FingerprintCache(
        first.cache.policy_id, first.cache.block_size, first.cache.chunk_size, tuple(blocks)
    )
    recovered = observe_fingerprints_cached(
        data, previous=poisoned, block_size=4096, chunk_size=64
    )
    assert recovered.fingerprints == _oracle(data, 64)
    assert recovered.stats.recomputed_blocks == 1
    assert recovered.stats.reused_blocks == 1


def test_shape_or_policy_change_invalidates_all_entries():
    data = b"abcdefgh" * 4096
    first = observe_fingerprints_cached(
        data, block_size=4096, chunk_size=64, policy_id="a"
    )
    policy = observe_fingerprints_cached(
        data, previous=first.cache, block_size=4096, chunk_size=64, policy_id="b"
    )
    shape = observe_fingerprints_cached(
        data, previous=first.cache, block_size=2048, chunk_size=64, policy_id="a"
    )
    assert policy.stats.reused_blocks == 0
    assert shape.stats.reused_blocks == 0


def test_relabelled_cache_policy_cannot_reuse_blocks_sealed_under_old_policy():
    """Hostile reviewer: cache metadata alone must not redefine feature semantics."""
    data = b"policy-sensitive-observation" * 4096
    first = observe_fingerprints_cached(
        data, block_size=4096, chunk_size=64, policy_id="policy-a"
    )
    # Simulate stale/corrupted persisted cache metadata that is relabelled without
    # regenerating its feature entries. A top-level compatibility check alone would
    # accept every unchanged block under policy-b.
    relabelled = FingerprintCache(
        policy_id="policy-b",
        block_size=first.cache.block_size,
        chunk_size=first.cache.chunk_size,
        blocks=first.cache.blocks,
    )
    recovered = observe_fingerprints_cached(
        data,
        previous=relabelled,
        block_size=4096,
        chunk_size=64,
        policy_id="policy-b",
    )
    assert recovered.fingerprints == _oracle(data, 64)
    assert recovered.stats.reused_blocks == 0
    assert recovered.stats.recomputed_blocks == len(first.cache.blocks)


def test_misaligned_block_shape_is_rejected_instead_of_changing_fingerprint_semantics():
    try:
        observe_fingerprints_cached(b"x" * 8192, block_size=1000, chunk_size=64)
    except ValueError as exc:
        assert "multiple" in str(exc)
    else:
        raise AssertionError("misaligned block/chunk geometry must fail closed")


def test_shifted_insertion_does_not_claim_relocation_reuse():
    base = bytes(range(251)) * 100
    first = observe_fingerprints_cached(base, block_size=1024, chunk_size=64)
    shifted = b"X" + base
    result = observe_fingerprints_cached(
        shifted, previous=first.cache, block_size=1024, chunk_size=64
    )
    assert result.fingerprints == _oracle(shifted, 64)
    assert result.stats.recomputed_blocks > 0


def test_digest_is_sha256_of_current_block_not_cached_feature_state():
    data = b"A" * 4096
    result = observe_fingerprints_cached(data, block_size=4096, chunk_size=64)
    assert result.cache.blocks[0].digest == hashlib.sha256(data).digest()
