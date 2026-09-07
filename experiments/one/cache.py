"""ONE-G0.2 discovery-cache / changed-cone experiment.

This cache is writer-only acceleration. It is never part of ONE reader semantics and it
never makes cached decisions authoritative. Every current block is re-identified from
current bytes; only an exactly matching, policy-compatible, internally sealed synopsis
may be reused.

The experiment deliberately separates *validation traffic* (bytes that must still be
read to establish current content identity) from *feature work* (bytes whose synopsis
must be recomputed). This prevents incremental compilation from claiming that unchanged
bytes were never touched when they were in fact hashed for safe cache reuse.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import hmac
import struct


DEFAULT_POLICY_ID = "ONE-G0.2:block-synopsis-v1"
_SYNOPSIS_SEAL_DOMAIN = b"CMPCT1-ONE-G0.2-SYNOPSIS\x00"


@dataclass(frozen=True)
class BlockSynopsis:
    digest: bytes
    length: int
    byte_sum: int
    transitions: int
    zero_bytes: int
    min_byte: int
    max_byte: int
    seal: bytes


@dataclass(frozen=True)
class ObservationCache:
    policy_id: str
    block_size: int
    blocks: tuple[BlockSynopsis, ...]


@dataclass(frozen=True)
class CacheStats:
    input_bytes: int
    validation_read_bytes: int
    feature_recompute_bytes: int
    feature_reuse_bytes: int
    recomputed_blocks: int
    reused_blocks: int
    persistent_payload_bytes: int


@dataclass(frozen=True)
class CachedObservation:
    cache: ObservationCache
    stats: CacheStats


def _validate_policy(policy_id: str, block_size: int) -> None:
    if type(policy_id) is not str or not policy_id:
        raise ValueError("policy_id must be a non-empty string")
    if type(block_size) is not int or block_size <= 0:
        raise ValueError("block_size must be a positive integer")


def _digest(block: bytes) -> bytes:
    # A cryptographic identity is used for cache admission because a collision here can
    # only cost writer performance today, but future cached Law fragments must never be
    # allowed to inherit a weak-fingerprint correctness assumption.
    return hashlib.sha256(block).digest()


def _seal_fields(
    digest: bytes,
    length: int,
    byte_sum: int,
    transitions: int,
    zero_bytes: int,
    min_byte: int,
    max_byte: int,
) -> bytes:
    """Seal cached derived state against accidental/stale cache corruption.

    This is an integrity checksum for writer-owned cache state, not an authorization MAC.
    A cache controlled by an active attacker remains outside the trust contract; archive
    correctness never depends on this cache being present. The seal closes the practical
    failure where a valid current block digest could accompany silently corrupted derived
    fields and thereby violate fresh-vs-incremental equivalence.
    """
    h = hashlib.sha256()
    h.update(_SYNOPSIS_SEAL_DOMAIN)
    h.update(digest)
    h.update(struct.pack(">QQQQBB", length, byte_sum, transitions, zero_bytes, min_byte, max_byte))
    return h.digest()


def _seal_valid(value: object) -> bool:
    if not isinstance(value, BlockSynopsis):
        return False
    if len(value.digest) != 32 or len(value.seal) != 32:
        return False
    if value.length <= 0:
        return False
    if not (0 <= value.min_byte <= 255 and 0 <= value.max_byte <= 255):
        return False
    expected = _seal_fields(
        value.digest,
        value.length,
        value.byte_sum,
        value.transitions,
        value.zero_bytes,
        value.min_byte,
        value.max_byte,
    )
    return hmac.compare_digest(value.seal, expected)


def _synopsis(block: bytes, digest: bytes | None = None) -> BlockSynopsis:
    if not block:
        raise ValueError("empty blocks are not cache entries")
    transitions = 0
    previous = block[0]
    zero_bytes = 1 if previous == 0 else 0
    byte_sum = previous
    min_byte = previous
    max_byte = previous
    for value in block[1:]:
        transitions += value != previous
        previous = value
        zero_bytes += value == 0
        byte_sum += value
        min_byte = min(min_byte, value)
        max_byte = max(max_byte, value)
    digest = _digest(block) if digest is None else digest
    seal = _seal_fields(
        digest,
        len(block),
        byte_sum,
        transitions,
        zero_bytes,
        min_byte,
        max_byte,
    )
    return BlockSynopsis(
        digest=digest,
        length=len(block),
        byte_sum=byte_sum,
        transitions=transitions,
        zero_bytes=zero_bytes,
        min_byte=min_byte,
        max_byte=max_byte,
        seal=seal,
    )


def observe_cached(
    data: bytes,
    *,
    previous: ObservationCache | None = None,
    block_size: int = 4096,
    policy_id: str = DEFAULT_POLICY_ID,
) -> CachedObservation:
    """Build exact block synopses while reusing only authenticated unchanged entries.

    Reuse is positional in this G0.2 experiment. Shifted insertions intentionally miss;
    content-addressed relocation is a later hypothesis and must earn its index/memory
    traffic separately.
    """
    if type(data) is not bytes:
        raise TypeError("ONE cached observation input must be bytes")
    _validate_policy(policy_id, block_size)

    compatible = (
        isinstance(previous, ObservationCache)
        and previous.policy_id == policy_id
        and previous.block_size == block_size
    )
    prior_blocks = previous.blocks if compatible else ()

    blocks: list[BlockSynopsis] = []
    recompute_bytes = 0
    reuse_bytes = 0
    recomputed_blocks = 0
    reused_blocks = 0

    for index, start in enumerate(range(0, len(data), block_size)):
        block = data[start : start + block_size]
        digest = _digest(block)
        cached = prior_blocks[index] if index < len(prior_blocks) else None
        if (
            _seal_valid(cached)
            and cached.digest == digest
            and cached.length == len(block)
        ):
            blocks.append(cached)
            reuse_bytes += len(block)
            reused_blocks += 1
        else:
            blocks.append(_synopsis(block, digest))
            recompute_bytes += len(block)
            recomputed_blocks += 1

    cache = ObservationCache(policy_id=policy_id, block_size=block_size, blocks=tuple(blocks))
    # Payload accounting is a representation lower bound, not Python heap RSS: digest
    # (32) + length/byte_sum/transitions/zero count (4*u64) + min/max (2) + seal (32).
    persistent_payload_bytes = len(blocks) * (32 + 32 + 2 + 32)
    return CachedObservation(
        cache=cache,
        stats=CacheStats(
            input_bytes=len(data),
            validation_read_bytes=len(data),
            feature_recompute_bytes=recompute_bytes,
            feature_reuse_bytes=reuse_bytes,
            recomputed_blocks=recomputed_blocks,
            reused_blocks=reused_blocks,
            persistent_payload_bytes=persistent_payload_bytes,
        ),
    )
