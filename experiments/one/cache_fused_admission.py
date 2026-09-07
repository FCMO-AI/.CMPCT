"""ONE-G0.2 bounded admission for the positional fused-observation cache.

The fused cache is very profitable when positional content identity persists, but whole-
writer evidence shows that unconditional use is expensive when every block changes. This
module performs a tiny stratified SHA-256 probe against previous cache block identities.
The probe can only choose writer implementation policy; cached state still has to pass
all ordinary digest/seal validation before reuse, and rejected updates fall back to the
fresh observer.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib

from experiments.one.cache_fused_observe import (
    DEFAULT_FUSED_POLICY_ID,
    FusedObservationBlock,
    FusedObservationCache,
    IncrementalObservation,
    observe_incremental,
)
from experiments.one.observe import Observation, observe


@dataclass(frozen=True)
class FusedCacheAdmissionDecision:
    compatible_previous: bool
    admitted: bool
    sampled_blocks: int
    matching_blocks: int
    probe_read_bytes: int
    probe_hash_bytes: int
    minimum_match_fraction: float

    @property
    def match_fraction(self) -> float:
        return self.matching_blocks / self.sampled_blocks if self.sampled_blocks else 0.0


@dataclass(frozen=True)
class AdmittedFusedObservation:
    observation: Observation
    cache: FusedObservationCache | None
    incremental: IncrementalObservation | None
    admission: FusedCacheAdmissionDecision


def _sample_indices(block_count: int, sample_blocks: int) -> tuple[int, ...]:
    if block_count <= 0:
        return ()
    count = min(block_count, sample_blocks)
    if count == 1:
        return (0,)
    # Stable stratification includes both ends and avoids absolute byte-phase heuristics.
    return tuple(round(i * (block_count - 1) / (count - 1)) for i in range(count))


def classify_fused_cache_admission(
    data: bytes,
    *,
    previous: FusedObservationCache | None,
    block_size: int = 4096,
    chunk_size: int = 64,
    min_run: int = 8,
    policy_id: str = DEFAULT_FUSED_POLICY_ID,
    sample_blocks: int = 8,
    minimum_match_fraction: float = 0.25,
) -> FusedCacheAdmissionDecision:
    """Return a bounded performance-policy decision without trusting cache payload state."""
    if type(data) is not bytes:
        raise TypeError("ONE fused-cache admission input must be bytes")
    for name, value in {
        "block_size": block_size,
        "chunk_size": chunk_size,
        "min_run": min_run,
        "sample_blocks": sample_blocks,
    }.items():
        if type(value) is not int or value <= 0:
            raise ValueError(f"{name} must be a positive integer")
    if block_size % chunk_size:
        raise ValueError("block_size must be an exact multiple of chunk_size")
    if not 0.0 <= minimum_match_fraction <= 1.0:
        raise ValueError("minimum_match_fraction must be in [0, 1]")

    compatible = (
        isinstance(previous, FusedObservationCache)
        and previous.policy_id == policy_id
        and previous.block_size == block_size
        and previous.chunk_size == chunk_size
        and previous.min_run == min_run
        and type(previous.blocks) is tuple
    )
    if not compatible or not data:
        return FusedCacheAdmissionDecision(
            compatible_previous=compatible,
            admitted=False,
            sampled_blocks=0,
            matching_blocks=0,
            probe_read_bytes=0,
            probe_hash_bytes=0,
            minimum_match_fraction=minimum_match_fraction,
        )

    block_count = (len(data) + block_size - 1) // block_size
    indices = _sample_indices(block_count, sample_blocks)
    matches = 0
    read_bytes = 0
    prior_blocks = previous.blocks
    for index in indices:
        start = index * block_size
        raw = data[start:start + block_size]
        read_bytes += len(raw)
        digest = hashlib.sha256(raw).digest()
        prior = prior_blocks[index] if index < len(prior_blocks) else None
        # Probe metadata is untrusted writer state. Malformed candidates simply fail to
        # match; they never get to raise or gain authority from the admission layer.
        if (
            isinstance(prior, FusedObservationBlock)
            and type(prior.digest) is bytes
            and len(prior.digest) == 32
            and type(prior.length) is int
            and prior.digest == digest
            and prior.length == len(raw)
        ):
            matches += 1

    fraction = matches / len(indices) if indices else 0.0
    return FusedCacheAdmissionDecision(
        compatible_previous=True,
        admitted=bool(indices) and fraction >= minimum_match_fraction,
        sampled_blocks=len(indices),
        matching_blocks=matches,
        probe_read_bytes=read_bytes,
        probe_hash_bytes=read_bytes,
        minimum_match_fraction=minimum_match_fraction,
    )


def observe_admitted(
    data: bytes,
    *,
    previous: FusedObservationCache | None = None,
    min_run: int = 8,
    chunk_size: int = 64,
    block_size: int = 4096,
    max_index_entries: int = 1 << 16,
    policy_id: str = DEFAULT_FUSED_POLICY_ID,
    sample_blocks: int = 8,
    minimum_match_fraction: float = 0.25,
) -> AdmittedFusedObservation:
    """Use fused-cache observation only when the bounded positional probe admits it.

    Rejected updates intentionally do not build a new fused cache. This preserves the
    measured immediate-update economics and leaves re-seeding as explicit follow-up debt.
    """
    decision = classify_fused_cache_admission(
        data,
        previous=previous,
        block_size=block_size,
        chunk_size=chunk_size,
        min_run=min_run,
        policy_id=policy_id,
        sample_blocks=sample_blocks,
        minimum_match_fraction=minimum_match_fraction,
    )
    if decision.admitted:
        incremental = observe_incremental(
            data,
            previous=previous,
            min_run=min_run,
            chunk_size=chunk_size,
            block_size=block_size,
            max_index_entries=max_index_entries,
            policy_id=policy_id,
        )
        return AdmittedFusedObservation(
            observation=incremental.observation,
            cache=incremental.cache,
            incremental=incremental,
            admission=decision,
        )

    fresh = observe(
        data,
        min_run=min_run,
        chunk_size=chunk_size,
        max_index_entries=max_index_entries,
    )
    return AdmittedFusedObservation(
        observation=fresh,
        cache=None,
        incremental=None,
        admission=decision,
    )
