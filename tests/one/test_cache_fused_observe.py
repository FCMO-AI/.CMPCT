from dataclasses import replace

from experiments.one.cache_fused_observe import observe_incremental
from experiments.one.observe import observe


def _assert_semantics(data: bytes, *, previous=None, block_size=1024, chunk_size=64, min_run=8):
    expected = observe(data, min_run=min_run, chunk_size=chunk_size)
    actual = observe_incremental(
        data,
        previous=previous,
        min_run=min_run,
        chunk_size=chunk_size,
        block_size=block_size,
    )
    assert actual.observation.runs == expected.runs
    assert actual.observation.reuse == expected.reuse
    assert actual.observation.stats.chunk_fingerprints == expected.stats.chunk_fingerprints
    assert actual.observation.stats.hash_lookups == expected.stats.hash_lookups
    assert actual.observation.stats.collision_verifications == expected.stats.collision_verifications
    assert actual.observation.stats.verification_read_bytes == expected.stats.verification_read_bytes
    assert actual.observation.stats.run_opportunity_bytes == expected.stats.run_opportunity_bytes
    assert actual.observation.stats.reuse_opportunity_bytes == expected.stats.reuse_opportunity_bytes
    assert actual.observation.stats.peak_index_entries == expected.stats.peak_index_entries
    return actual


def test_empty_matches_reference():
    result = _assert_semantics(b"")
    assert result.cache.blocks == ()
    assert result.stats.total_source_read_bytes == 0


def test_exact_repeat_reuses_all_fused_blocks():
    data = bytes(range(251)) * 80
    first = _assert_semantics(data)
    second = _assert_semantics(data, previous=first.cache)
    assert second.stats.recomputed_blocks == 0
    assert second.stats.reused_blocks == len(first.cache.blocks)
    assert second.stats.feature_recompute_bytes == 0
    assert second.stats.validation_read_bytes == len(data)


def test_one_byte_edit_recomputes_only_changed_block_and_matches_oracle():
    data = bytearray(bytes(range(251)) * 80)
    first = _assert_semantics(bytes(data))
    data[3 * 1024 + 17] ^= 0x5A
    second = _assert_semantics(bytes(data), previous=first.cache)
    assert second.stats.recomputed_blocks == 1
    assert second.stats.feature_recompute_bytes == 1024
    assert second.stats.reused_blocks == len(second.cache.blocks) - 1


def test_long_run_crossing_block_boundary_matches_reference():
    data = b"abc" * 200 + b"Z" * 1700 + b"tail" * 300
    first = _assert_semantics(data)
    second = _assert_semantics(data, previous=first.cache)
    assert second.observation.runs == observe(data).runs


def test_short_boundary_runs_merge_into_qualifying_global_run():
    # Each side of the 1024-byte boundary contributes only 6 X bytes; globally the run
    # is 12 and must be emitted for min_run=8 even though neither local boundary piece
    # qualifies on its own.
    left = b"A" * (1024 - 6) + b"X" * 6
    right = b"X" * 6 + b"B" * (1024 - 6)
    data = left + right
    result = _assert_semantics(data)
    assert any(run.start == 1018 and run.length == 12 and run.value == ord("X") for run in result.observation.runs)


def test_cross_block_reuse_opportunities_match_reference():
    block = bytes((i * 17 + 3) & 0xFF for i in range(1024))
    data = block + bytes((i * 31 + 9) & 0xFF for i in range(1024)) + block
    first = _assert_semantics(data)
    second = _assert_semantics(data, previous=first.cache)
    assert second.observation.reuse == observe(data).reuse
    assert second.observation.reuse


def test_run_gating_across_block_boundary_matches_reference():
    # A constant run begins before the boundary and continues far enough into the next
    # block that early chunks there must be suppressed from reuse indexing exactly as in
    # the fused reference observer.
    data = b"P" * 900 + b"Q" * 900 + b"R" * 900 + b"Q" * 900
    first = _assert_semantics(data)
    second = _assert_semantics(data, previous=first.cache)
    assert second.observation.reuse == observe(data).reuse


def test_policy_change_recomputes_all_blocks():
    data = bytes(range(251)) * 40
    first = observe_incremental(data, block_size=1024, chunk_size=64, policy_id="policy-a")
    second = observe_incremental(
        data,
        previous=first.cache,
        block_size=1024,
        chunk_size=64,
        policy_id="policy-b",
    )
    assert second.observation.runs == observe(data).runs
    assert second.observation.reuse == observe(data).reuse
    assert second.stats.reused_blocks == 0
    assert second.stats.recomputed_blocks == len(second.cache.blocks)


def test_corrupt_cached_feature_state_fails_closed():
    data = bytes(range(251)) * 40
    first = observe_incremental(data, block_size=1024, chunk_size=64)
    blocks = list(first.cache.blocks)
    victim = blocks[2]
    corrupted = list(victim.fingerprints)
    corrupted[0] ^= 1
    blocks[2] = replace(victim, fingerprints=tuple(corrupted))
    poisoned = replace(first.cache, blocks=tuple(blocks))
    second = _assert_semantics(data, previous=poisoned)
    assert second.stats.recomputed_blocks == 1


def test_tiny_and_incompressible_cases_match_reference():
    for data in (
        b"x",
        b"abcdefg",
        bytes(range(64)),
        bytes((i * 97 + 11) & 0xFF for i in range(4097)),
    ):
        first = _assert_semantics(data)
        _assert_semantics(data, previous=first.cache)
