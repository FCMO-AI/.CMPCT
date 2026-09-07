"""ONE-G0.2 writer-only cache for a real fused-observation feature family.

This experiment caches the aligned fixed-chunk fingerprints consumed by early ONE
observation/discovery. Current bytes are still SHA-256 identified block by block before
reuse, so validation traffic remains fully charged. The reader never sees or needs this
cache.

The point is deliberately narrow: determine whether expensive discovery features can be
reused safely enough to justify ONE-07 after paying identity, integrity, and cache-state
costs. It is not a claim that SHA validation is free or that this Python feature kernel is
a production implementation.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import hmac
import struct


_FNV64_OFFSET = 0xCBF29CE484222325
_FNV64_PRIME = 0x100000001B3
_U64_MASK = (1 << 64) - 1
_SEAL_DOMAIN = b"CMPCT1-ONE-G0.2-FINGERPRINT-CACHE\x00"
DEFAULT_FINGERPRINT_POLICY_ID = "ONE-G0.2:aligned-fnv64-v1"


@dataclass(frozen=True)
class FingerprintBlock:
    digest: bytes
    length: int
    fingerprints: tuple[int, ...]
    seal: bytes


@dataclass(frozen=True)
class FingerprintCache:
    policy_id: str
    block_size: int
    chunk_size: int
    blocks: tuple[FingerprintBlock, ...]


@dataclass(frozen=True)
class FingerprintCacheStats:
    input_bytes: int
    validation_read_bytes: int
    feature_recompute_bytes: int
    feature_reuse_bytes: int
    recomputed_blocks: int
    reused_blocks: int
    emitted_fingerprints: int
    persistent_payload_bytes: int


@dataclass(frozen=True)
class CachedFingerprints:
    fingerprints: tuple[int, ...]
    cache: FingerprintCache
    stats: FingerprintCacheStats


def _validate_shape(policy_id: str, block_size: int, chunk_size: int) -> None:
    if type(policy_id) is not str or not policy_id:
        raise ValueError("policy_id must be a non-empty string")
    if type(block_size) is not int or block_size <= 0:
        raise ValueError("block_size must be a positive integer")
    if type(chunk_size) is not int or chunk_size <= 0:
        raise ValueError("chunk_size must be a positive integer")
    # Block boundaries must also be observation-chunk boundaries; otherwise concatenating
    # cached local features would silently change the global fingerprint stream.
    if block_size % chunk_size:
        raise ValueError("block_size must be an exact multiple of chunk_size")


def _fingerprints(block: bytes, chunk_size: int) -> tuple[int, ...]:
    out: list[int] = []
    for start in range(0, len(block) - chunk_size + 1, chunk_size):
        h = _FNV64_OFFSET
        for value in block[start : start + chunk_size]:
            h ^= value
            h = (h * _FNV64_PRIME) & _U64_MASK
        out.append(h)
    return tuple(out)


def _seal(
    digest: bytes,
    length: int,
    chunk_size: int,
    fingerprints: tuple[int, ...],
    *,
    policy_id: str,
    block_size: int,
) -> bytes:
    """Seal cached feature state together with the compiler policy that gives it meaning."""
    policy = policy_id.encode("utf-8")
    h = hashlib.sha256()
    h.update(_SEAL_DOMAIN)
    h.update(struct.pack(">Q", len(policy)))
    h.update(policy)
    h.update(digest)
    h.update(struct.pack(">QQQQ", block_size, length, chunk_size, len(fingerprints)))
    for value in fingerprints:
        h.update(struct.pack(">Q", value))
    return h.digest()


def _valid_cached(
    block: object,
    *,
    policy_id: str,
    block_size: int,
    chunk_size: int,
) -> bool:
    if not isinstance(block, FingerprintBlock):
        return False
    if type(block.digest) is not bytes or len(block.digest) != 32:
        return False
    if type(block.seal) is not bytes or len(block.seal) != 32:
        return False
    if type(block.length) is not int or block.length <= 0:
        return False
    expected_count = block.length // chunk_size
    if len(block.fingerprints) != expected_count:
        return False
    if any(type(value) is not int or value < 0 or value > _U64_MASK for value in block.fingerprints):
        return False
    return hmac.compare_digest(
        block.seal,
        _seal(
            block.digest,
            block.length,
            chunk_size,
            block.fingerprints,
            policy_id=policy_id,
            block_size=block_size,
        ),
    )


def observe_fingerprints_cached(
    data: bytes,
    *,
    previous: FingerprintCache | None = None,
    block_size: int = 4096,
    chunk_size: int = 64,
    policy_id: str = DEFAULT_FINGERPRINT_POLICY_ID,
) -> CachedFingerprints:
    """Return the exact aligned fingerprint stream, reusing verified block features.

    `feature_*_bytes` count only bytes participating in full observation chunks. A short
    final suffix still contributes to `validation_read_bytes` because current content
    identity is established for the whole block, but the base observer emits no aligned
    fingerprint for that suffix either.
    """
    if type(data) is not bytes:
        raise TypeError("ONE fingerprint-cache input must be bytes")
    _validate_shape(policy_id, block_size, chunk_size)

    compatible = (
        isinstance(previous, FingerprintCache)
        and previous.policy_id == policy_id
        and previous.block_size == block_size
        and previous.chunk_size == chunk_size
    )
    prior_blocks = previous.blocks if compatible else ()

    blocks: list[FingerprintBlock] = []
    flat: list[int] = []
    recompute_bytes = 0
    reuse_bytes = 0
    recomputed_blocks = 0
    reused_blocks = 0

    for index, start in enumerate(range(0, len(data), block_size)):
        raw = data[start : start + block_size]
        digest = hashlib.sha256(raw).digest()
        cached = prior_blocks[index] if index < len(prior_blocks) else None
        feature_bytes = (len(raw) // chunk_size) * chunk_size
        if (
            _valid_cached(
                cached,
                policy_id=policy_id,
                block_size=block_size,
                chunk_size=chunk_size,
            )
            and cached.digest == digest
            and cached.length == len(raw)
        ):
            block = cached
            reuse_bytes += feature_bytes
            reused_blocks += 1
        else:
            fingerprints = _fingerprints(raw, chunk_size)
            block = FingerprintBlock(
                digest=digest,
                length=len(raw),
                fingerprints=fingerprints,
                seal=_seal(
                    digest,
                    len(raw),
                    chunk_size,
                    fingerprints,
                    policy_id=policy_id,
                    block_size=block_size,
                ),
            )
            recompute_bytes += feature_bytes
            recomputed_blocks += 1
        blocks.append(block)
        flat.extend(block.fingerprints)

    cache = FingerprintCache(
        policy_id=policy_id,
        block_size=block_size,
        chunk_size=chunk_size,
        blocks=tuple(blocks),
    )
    # Lower-bound payload accounting, excluding Python/container object overhead:
    # digest (32) + length (8) + seal (32) + one u64 per cached fingerprint.
    persistent_payload_bytes = sum(72 + 8 * len(block.fingerprints) for block in blocks)
    return CachedFingerprints(
        fingerprints=tuple(flat),
        cache=cache,
        stats=FingerprintCacheStats(
            input_bytes=len(data),
            validation_read_bytes=len(data),
            feature_recompute_bytes=recompute_bytes,
            feature_reuse_bytes=reuse_bytes,
            recomputed_blocks=recomputed_blocks,
            reused_blocks=reused_blocks,
            emitted_fingerprints=len(flat),
            persistent_payload_bytes=persistent_payload_bytes,
        ),
    )
