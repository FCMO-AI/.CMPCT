"""Independent ONE-G0.2 cost ledger for fused observation-cache integrity work.

`cache_fused_observe.observe_incremental()` already performs SHA-256 sealing for every
newly computed observation block and validates the seal of every reused block.  Its
resource statistics historically exposed the validation-side hash input only.  This
module deliberately lives outside that implementation so the scientific gate can charge
both sides without trusting the meter it is auditing.

This is writer/research instrumentation only.  It changes no ONE representation bytes or
reader semantics.
"""
from __future__ import annotations

from dataclasses import dataclass

from experiments.one.cache_fused_observe import (
    FusedObservationBlock,
    FusedObservationCache,
    IncrementalObservation,
)

_SEAL_DOMAIN = b"CMPCT1-ONE-G0.2-FUSED-OBSERVE-CACHE\x00"


@dataclass(frozen=True)
class FusedCacheIntegrityLedger:
    """Independent accounting for integrity SHA input bytes.

    `reported_hash_bytes` is whatever the implementation currently exposes.
    `expected_verify_hash_bytes` and `expected_build_hash_bytes` are reconstructed from
    returned cache state.  `charged_hash_bytes` is conservative: it never charges less
    than the independently reconstructed total and never discards a larger future meter.
    """

    expected_verify_hash_bytes: int
    expected_build_hash_bytes: int
    expected_total_hash_bytes: int
    reported_hash_bytes: int
    accounting_gap_bytes: int
    charged_hash_bytes: int
    reused_blocks: int
    recomputed_blocks: int


def seal_message_bytes(policy_id: str, block: FusedObservationBlock) -> int:
    """Return exact bytes fed to SHA-256 for one fused-cache seal.

    This intentionally mirrors the *wire shape*, not the implementation helper: domain,
    policy length/text, digest, seven u64 scalars, two one-byte values, fingerprint count
    and payload, run-gate payload, internal-run count, and 3-u64 run records.
    """
    if type(policy_id) is not str or not policy_id:
        raise ValueError("policy_id must be non-empty text")
    if not isinstance(block, FusedObservationBlock):
        raise TypeError("block must be FusedObservationBlock")
    return (
        len(_SEAL_DOMAIN)
        + 8
        + len(policy_id.encode("utf-8"))
        + 32
        + 7 * 8
        + 2
        + 8
        + 8 * len(block.fingerprints)
        + len(block.chunk_run_gate)
        + 8
        + 3 * 8 * len(block.internal_runs)
    )


def _compatible(previous: FusedObservationCache | None, current: FusedObservationCache) -> bool:
    return (
        isinstance(previous, FusedObservationCache)
        and previous.policy_id == current.policy_id
        and previous.block_size == current.block_size
        and previous.chunk_size == current.chunk_size
        and previous.min_run == current.min_run
    )


def audit_integrity_cost(
    result: IncrementalObservation,
    *,
    previous: FusedObservationCache | None = None,
) -> FusedCacheIntegrityLedger:
    """Audit integrity-hash traffic for an in-process observation result.

    The observer preserves the exact cached block object when a positional reuse is
    admitted.  Object identity therefore distinguishes reuse from recomputation without
    re-running private validity logic.  This helper is intentionally scoped to immediate
    experiment/benchmark auditing, not serialized cache analysis.
    """
    if not isinstance(result, IncrementalObservation):
        raise TypeError("result must be IncrementalObservation")

    current = result.cache
    prior_blocks = previous.blocks if _compatible(previous, current) else ()
    verify = 0
    build = 0
    reused = 0
    recomputed = 0

    for index, block in enumerate(current.blocks):
        reused_here = index < len(prior_blocks) and block is prior_blocks[index]
        cost = seal_message_bytes(current.policy_id, block)
        if reused_here:
            verify += cost
            reused += 1
        else:
            build += cost
            recomputed += 1

    expected_total = verify + build
    reported = result.stats.cache_integrity_hash_bytes
    gap = max(0, expected_total - reported)
    charged = max(expected_total, reported)

    return FusedCacheIntegrityLedger(
        expected_verify_hash_bytes=verify,
        expected_build_hash_bytes=build,
        expected_total_hash_bytes=expected_total,
        reported_hash_bytes=reported,
        accounting_gap_bytes=gap,
        charged_hash_bytes=charged,
        reused_blocks=reused,
        recomputed_blocks=recomputed,
    )
