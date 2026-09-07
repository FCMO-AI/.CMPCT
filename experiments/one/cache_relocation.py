"""ONE-G0.2 bounded content-addressed relocation cache experiment.

This writer-only experiment extends the positional fingerprint cache to reuse unchanged
observation blocks after block-aligned movement.  It does not change ONE reader semantics
or archive bytes.

Relocation is admitted only by current SHA-256 content identity plus the existing sealed
fingerprint payload.  A global relocation index is *not* built on the first positional
miss: two consecutive misses are required as cheap evidence that content may actually
have moved.  A lone sparse mutation therefore recomputes locally and avoids O(n) search.
Index construction, lookups, seal hashing and cached-feature reads are all exposed as
stats; none are treated as free.

This does not solve arbitrary byte-shifted insertions.  Aligned FNV fingerprints are
position-relative features, so a one-byte shift legitimately changes their grouping and
must recompute until a future content-defined observation family earns different
semantics.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib

from experiments.one.cache_fingerprints import (
    DEFAULT_FINGERPRINT_POLICY_ID,
    FingerprintBlock,
    FingerprintCache,
    _fingerprints,
    _seal,
    _seal_input_bytes,
    _valid_cached,
    _validate_shape,
    _will_hash_cached_seal,
)


@dataclass(frozen=True)
class RelocationCacheStats:
    input_bytes: int
    validation_read_bytes: int
    feature_recompute_bytes: int
    feature_reuse_bytes: int
    cache_integrity_hash_bytes: int
    cache_feature_payload_read_bytes: int
    recomputed_blocks: int
    positional_reused_blocks: int
    relocated_reused_blocks: int
    relocation_index_entries: int
    relocation_index_payload_bytes: int
    relocation_lookups: int
    relocation_gate_activations: int
    emitted_fingerprints: int
    persistent_payload_bytes: int


@dataclass(frozen=True)
class RelocatedFingerprints:
    fingerprints: tuple[int, ...]
    cache: FingerprintCache
    stats: RelocationCacheStats


def observe_fingerprints_relocated(
    data: bytes,
    *,
    previous: FingerprintCache | None = None,
    block_size: int = 4096,
    chunk_size: int = 64,
    policy_id: str = DEFAULT_FINGERPRINT_POLICY_ID,
    max_relocation_entries: int = 1 << 16,
) -> RelocatedFingerprints:
    """Return exact aligned fingerprints with opportunity-gated cross-position reuse.

    Positional identity is always tried first.  One miss is treated as a local mutation;
    two consecutive positional misses activate bounded relocation search.  This sacrifices
    reuse of an isolated moved block to avoid paying a whole-cache index build for the far
    more common sparse-mutation case.  Duplicate identities are safe because a nominated
    candidate still has to pass the existing sealed-payload validation.
    """
    if type(data) is not bytes:
        raise TypeError("ONE relocation-cache input must be bytes")
    _validate_shape(policy_id, block_size, chunk_size)
    if type(max_relocation_entries) is not int or max_relocation_entries <= 0:
        raise ValueError("max_relocation_entries must be a positive integer")

    compatible = (
        isinstance(previous, FingerprintCache)
        and previous.policy_id == policy_id
        and previous.block_size == block_size
        and previous.chunk_size == chunk_size
    )
    prior_blocks = previous.blocks if compatible else ()

    relocation_index: dict[tuple[bytes, int], list[FingerprintBlock]] | None = None
    relocation_index_entries = 0
    relocation_lookups = 0
    relocation_gate_activations = 0
    consecutive_positional_misses = 0

    def ensure_relocation_index() -> dict[tuple[bytes, int], list[FingerprintBlock]]:
        nonlocal relocation_index, relocation_index_entries
        if relocation_index is not None:
            return relocation_index
        built: dict[tuple[bytes, int], list[FingerprintBlock]] = {}
        for candidate in prior_blocks:
            if relocation_index_entries >= max_relocation_entries:
                break
            # Identity fields are nomination metadata only.  Full seal validation is
            # deferred until current bytes actually nominate this candidate.
            if (
                isinstance(candidate, FingerprintBlock)
                and type(candidate.digest) is bytes
                and len(candidate.digest) == 32
                and type(candidate.length) is int
                and candidate.length > 0
            ):
                built.setdefault((candidate.digest, candidate.length), []).append(candidate)
                relocation_index_entries += 1
        relocation_index = built
        return built

    blocks: list[FingerprintBlock] = []
    flat: list[int] = []
    recompute_bytes = 0
    reuse_bytes = 0
    cache_integrity_hash_bytes = 0
    cache_feature_payload_read_bytes = 0
    recomputed_blocks = 0
    positional_reused_blocks = 0
    relocated_reused_blocks = 0

    for index, start in enumerate(range(0, len(data), block_size)):
        raw = data[start : start + block_size]
        digest = hashlib.sha256(raw).digest()
        feature_bytes = (len(raw) // chunk_size) * chunk_size
        positional = prior_blocks[index] if index < len(prior_blocks) else None

        chosen: FingerprintBlock | None = None
        positional_identity = (
            isinstance(positional, FingerprintBlock)
            and positional.digest == digest
            and positional.length == len(raw)
        )
        if positional_identity:
            if _will_hash_cached_seal(positional, chunk_size):
                cache_integrity_hash_bytes += _seal_input_bytes(
                    policy_id, len(positional.fingerprints)
                )
            if _valid_cached(
                positional,
                policy_id=policy_id,
                block_size=block_size,
                chunk_size=chunk_size,
            ):
                chosen = positional
                positional_reused_blocks += 1
                consecutive_positional_misses = 0

        if chosen is None:
            consecutive_positional_misses += 1

        if chosen is None and compatible and consecutive_positional_misses >= 2:
            if relocation_index is None:
                relocation_gate_activations += 1
            relocation_lookups += 1
            candidates = ensure_relocation_index().get((digest, len(raw)), ())
            for candidate in candidates:
                # Avoid hashing the same damaged positional candidate twice.
                if candidate is positional:
                    continue
                if _will_hash_cached_seal(candidate, chunk_size):
                    cache_integrity_hash_bytes += _seal_input_bytes(
                        policy_id, len(candidate.fingerprints)
                    )
                if _valid_cached(
                    candidate,
                    policy_id=policy_id,
                    block_size=block_size,
                    chunk_size=chunk_size,
                ):
                    chosen = candidate
                    relocated_reused_blocks += 1
                    break

        if chosen is None:
            fingerprints = _fingerprints(raw, chunk_size)
            chosen = FingerprintBlock(
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
        else:
            reuse_bytes += feature_bytes
            cache_feature_payload_read_bytes += 8 * len(chosen.fingerprints)

        blocks.append(chosen)
        flat.extend(chosen.fingerprints)

    cache = FingerprintCache(
        policy_id=policy_id,
        block_size=block_size,
        chunk_size=chunk_size,
        blocks=tuple(blocks),
    )
    persistent_payload_bytes = sum(72 + 8 * len(block.fingerprints) for block in blocks)
    # Lower-bound index payload only: digest + length + candidate reference.  Runtime
    # object/RSS overhead must be charged separately before any production claim.
    relocation_index_payload_bytes = relocation_index_entries * 48

    return RelocatedFingerprints(
        fingerprints=tuple(flat),
        cache=cache,
        stats=RelocationCacheStats(
            input_bytes=len(data),
            validation_read_bytes=len(data),
            feature_recompute_bytes=recompute_bytes,
            feature_reuse_bytes=reuse_bytes,
            cache_integrity_hash_bytes=cache_integrity_hash_bytes,
            cache_feature_payload_read_bytes=cache_feature_payload_read_bytes,
            recomputed_blocks=recomputed_blocks,
            positional_reused_blocks=positional_reused_blocks,
            relocated_reused_blocks=relocated_reused_blocks,
            relocation_index_entries=relocation_index_entries,
            relocation_index_payload_bytes=relocation_index_payload_bytes,
            relocation_lookups=relocation_lookups,
            relocation_gate_activations=relocation_gate_activations,
            emitted_fingerprints=len(flat),
            persistent_payload_bytes=persistent_payload_bytes,
        ),
    )
