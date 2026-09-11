from __future__ import annotations

from experiments.one.cache_fused_observe import observe_incremental
from experiments.one.fused_cache_cost_ledger import audit_integrity_cost, seal_message_bytes


def _fixture() -> bytes:
    # Exercise fingerprints, run-gate payload, and an internal-run record rather than a
    # degenerate all-random seal shape. The first block is exactly 256 bytes.
    block0 = (
        b"A" * 64
        + bytes(range(64))
        + b"B" * 64
        + bytes((index * 37 + 3) & 0xFF for index in range(64))
    )
    block1 = bytes((index * 29 + 7) & 0xFF for index in range(256))
    return block0 + block1


def test_seal_message_size_is_independent_structural_accounting() -> None:
    result = observe_incremental(_fixture(), block_size=256, chunk_size=64, min_run=8)
    block = result.cache.blocks[0]
    assert block.internal_runs  # force variable internal-run payload into the fixture
    expected = (
        len(b"CMPCT1-ONE-G0.2-FUSED-OBSERVE-CACHE\x00")
        + 8
        + len(result.cache.policy_id.encode("utf-8"))
        + 32
        + 7 * 8
        + 2
        + 8
        + 8 * len(block.fingerprints)
        + len(block.chunk_run_gate)
        + 8
        + 3 * 8 * len(block.internal_runs)
    )
    assert seal_message_bytes(result.cache.policy_id, block) == expected


def test_fresh_build_charges_every_created_seal_in_independent_ledger() -> None:
    result = observe_incremental(_fixture(), block_size=256, chunk_size=64, min_run=8)
    ledger = audit_integrity_cost(result)

    assert ledger.reused_blocks == 0
    assert ledger.recomputed_blocks == len(result.cache.blocks) == 2
    assert ledger.expected_verify_hash_bytes == 0
    assert ledger.expected_build_hash_bytes > 0
    assert ledger.expected_total_hash_bytes == ledger.expected_build_hash_bytes
    assert ledger.charged_hash_bytes >= ledger.expected_total_hash_bytes
    assert ledger.accounting_gap_bytes == max(
        0, ledger.expected_total_hash_bytes - ledger.reported_hash_bytes
    )


def test_exact_repeat_has_verify_cost_but_no_build_cost() -> None:
    fresh = observe_incremental(_fixture(), block_size=256, chunk_size=64, min_run=8)
    repeat = observe_incremental(
        _fixture(), previous=fresh.cache, block_size=256, chunk_size=64, min_run=8
    )
    ledger = audit_integrity_cost(repeat, previous=fresh.cache)

    assert ledger.reused_blocks == 2
    assert ledger.recomputed_blocks == 0
    assert ledger.expected_build_hash_bytes == 0
    assert ledger.expected_verify_hash_bytes > 0
    assert ledger.expected_total_hash_bytes == ledger.expected_verify_hash_bytes
    assert ledger.charged_hash_bytes >= ledger.expected_total_hash_bytes


def test_sparse_edit_exposes_both_verify_and_build_integrity_work() -> None:
    source = bytearray(_fixture())
    fresh = observe_incremental(bytes(source), block_size=256, chunk_size=64, min_run=8)
    source[300] ^= 0x5A  # mutate only the second observation block
    changed = observe_incremental(
        bytes(source), previous=fresh.cache, block_size=256, chunk_size=64, min_run=8
    )
    ledger = audit_integrity_cost(changed, previous=fresh.cache)

    assert ledger.reused_blocks == 1
    assert ledger.recomputed_blocks == 1
    assert ledger.expected_verify_hash_bytes > 0
    assert ledger.expected_build_hash_bytes > 0
    assert ledger.expected_total_hash_bytes == (
        ledger.expected_verify_hash_bytes + ledger.expected_build_hash_bytes
    )
    assert ledger.charged_hash_bytes >= ledger.expected_total_hash_bytes
    assert ledger.recomputed_blocks == changed.stats.recomputed_blocks
    assert ledger.reused_blocks == changed.stats.reused_blocks


def test_incompatible_previous_cache_counts_current_seals_as_builds() -> None:
    fresh = observe_incremental(_fixture(), block_size=256, chunk_size=64, min_run=8)
    changed_policy = observe_incremental(
        _fixture(),
        previous=fresh.cache,
        block_size=256,
        chunk_size=64,
        min_run=8,
        policy_id="ONE-G0.2:fused-run-fnv64-v1-policy-change",
    )
    ledger = audit_integrity_cost(changed_policy, previous=fresh.cache)

    assert ledger.reused_blocks == 0
    assert ledger.recomputed_blocks == 2
    assert ledger.expected_verify_hash_bytes == 0
    assert ledger.expected_build_hash_bytes == ledger.expected_total_hash_bytes
