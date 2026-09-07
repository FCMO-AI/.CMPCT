from experiments.one.cache import ObservationCache, observe_cached


def _aggregate(cache: ObservationCache) -> tuple[int, int, int, int, int, int]:
    return (
        sum(block.length for block in cache.blocks),
        sum(block.byte_sum for block in cache.blocks),
        sum(block.transitions for block in cache.blocks),
        sum(block.zero_bytes for block in cache.blocks),
        min((block.min_byte for block in cache.blocks), default=0),
        max((block.max_byte for block in cache.blocks), default=0),
    )


def test_exact_repeat_reuses_all_features_but_charges_validation_scan():
    data = bytes(range(256)) * 32
    first = observe_cached(data, block_size=1024)
    second = observe_cached(data, previous=first.cache, block_size=1024)
    assert second.cache == first.cache
    assert second.stats.validation_read_bytes == len(data)
    assert second.stats.feature_recompute_bytes == 0
    assert second.stats.feature_reuse_bytes == len(data)
    assert second.stats.recomputed_blocks == 0
    assert second.stats.reused_blocks == 8


def test_one_byte_edit_recomputes_only_affected_feature_block():
    base = bytearray(bytes(range(256)) * 32)
    first = observe_cached(bytes(base), block_size=1024)
    base[3 * 1024 + 17] ^= 0x5A
    current = bytes(base)
    incremental = observe_cached(current, previous=first.cache, block_size=1024)
    fresh = observe_cached(current, block_size=1024)
    assert incremental.cache == fresh.cache
    assert _aggregate(incremental.cache) == _aggregate(fresh.cache)
    assert incremental.stats.feature_recompute_bytes == 1024
    assert incremental.stats.feature_reuse_bytes == len(current) - 1024
    assert incremental.stats.recomputed_blocks == 1
    assert incremental.stats.reused_blocks == 7


def test_policy_change_invalidates_every_cached_synopsis():
    data = b"abc123" * 2048
    first = observe_cached(data, block_size=2048, policy_id="policy-a")
    changed_policy = observe_cached(
        data, previous=first.cache, block_size=2048, policy_id="policy-b"
    )
    assert changed_policy.stats.feature_reuse_bytes == 0
    assert changed_policy.stats.feature_recompute_bytes == len(data)
    assert changed_policy.cache.policy_id == "policy-b"


def test_block_size_change_invalidates_cache():
    data = b"abcdefgh" * 2048
    first = observe_cached(data, block_size=1024)
    changed = observe_cached(data, previous=first.cache, block_size=2048)
    assert changed.stats.feature_reuse_bytes == 0
    assert changed.stats.feature_recompute_bytes == len(data)


def test_corrupt_cached_digest_cannot_authorize_stale_synopsis():
    data = b"A" * 4096 + b"B" * 4096
    first = observe_cached(data, block_size=4096)
    blocks = list(first.cache.blocks)
    original = blocks[0]
    blocks[0] = type(original)(
        digest=b"\x00" * 32,
        length=original.length,
        byte_sum=0,
        transitions=999,
        zero_bytes=original.length,
        min_byte=0,
        max_byte=0,
    )
    poisoned = ObservationCache(first.cache.policy_id, first.cache.block_size, tuple(blocks))
    recovered = observe_cached(data, previous=poisoned, block_size=4096)
    fresh = observe_cached(data, block_size=4096)
    assert recovered.cache == fresh.cache
    assert recovered.stats.recomputed_blocks == 1
    assert recovered.stats.reused_blocks == 1


def test_shifted_insertion_is_conservatively_not_relocated():
    base = bytes(range(251)) * 40
    first = observe_cached(base, block_size=512)
    shifted = b"X" + base
    incremental = observe_cached(shifted, previous=first.cache, block_size=512)
    fresh = observe_cached(shifted, block_size=512)
    assert incremental.cache == fresh.cache
    # Position-keyed reuse must not pretend to solve shifted insertion.  A future
    # relocation index has to earn its memory and lookup traffic independently.
    assert incremental.stats.feature_recompute_bytes > 0


def test_empty_input_has_no_phantom_cache_entry():
    result = observe_cached(b"")
    assert result.cache.blocks == ()
    assert result.stats.input_bytes == 0
    assert result.stats.persistent_payload_bytes == 0
