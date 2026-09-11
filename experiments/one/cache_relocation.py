"""ONE-G0.2 bounded content-addressed relocation cache experiment.

This writer-only experiment extends the positional fingerprint cache to reuse unchanged
observation blocks after block-aligned movement. It does not change ONE reader semantics
or archive bytes.

Relocation is admitted only by current SHA-256 content identity plus the existing sealed
fingerprint payload. A global relocation directory is *not* consulted on the first
positional miss: two consecutive misses are required as cheap evidence that content may
actually have moved. A lone sparse mutation therefore recomputes locally and avoids
unnecessary global lookup work.

A relocation directory can be carried between versions, but exact-head evidence showed
that always building it can tax ordinary exact-repeat work. ``persist_directory=False``
therefore exercises the causally simpler shape: build a bounded relocation index lazily
from the prior cache only after movement evidence appears, and emit no next-generation
directory. This keeps the reader and archive unchanged while letting the writer pay
relocation bookkeeping only on the rare path that uses it.

Directory entries are nomination metadata only: the pointed-to cached block still must
match the key and pass its sealed-feature validation. Corrupt/stale directory state can
only lose reuse and force recomputation.

This does not solve arbitrary byte-shifted insertions. Aligned FNV fingerprints are
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
class RelocationDirectoryEntry:
    digest: bytes
    length: int
    block_index: int


@dataclass(frozen=True)
class RelocationDirectory:
    policy_id: str
    block_size: int
    chunk_size: int
    entries: tuple[RelocationDirectoryEntry, ...]


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
    prior_cache_index_scan_blocks: int
    directory_output_entries: int
    directory_output_payload_bytes: int
    emitted_fingerprints: int
    persistent_payload_bytes: int


@dataclass(frozen=True)
class RelocatedFingerprints:
    fingerprints: tuple[int, ...]
    cache: FingerprintCache
    directory: RelocationDirectory
    stats: RelocationCacheStats


def _directory_compatible(
    directory: object,
    *,
    policy_id: str,
    block_size: int,
    chunk_size: int,
) -> bool:
    return (
        isinstance(directory, RelocationDirectory)
        and directory.policy_id == policy_id
        and directory.block_size == block_size
        and directory.chunk_size == chunk_size
        and isinstance(directory.entries, tuple)
    )


def observe_fingerprints_relocated(
    data: bytes,
    *,
    previous: FingerprintCache | None = None,
    previous_directory: RelocationDirectory | None = None,
    block_size: int = 4096,
    chunk_size: int = 64,
    policy_id: str = DEFAULT_FINGERPRINT_POLICY_ID,
    max_relocation_entries: int = 1 << 16,
    persist_directory: bool = True,
) -> RelocatedFingerprints:
    """Return exact aligned fingerprints with opportunity-gated cross-position reuse.

    Positional identity is always tried first. One miss is treated as a local mutation;
    two consecutive positional misses activate bounded relocation search. This sacrifices
    reuse of an isolated moved block to avoid paying global relocation machinery for the
    far more common sparse-mutation case.

    When a compatible prior relocation directory is supplied, relocation lookup does not
    scan the previous cache. The directory itself is not trusted: a nominated block must
    still exist at the recorded index, reproduce the directory key, and pass the normal
    sealed fingerprint validation. If no compatible directory exists, a bounded lazy
    index is built from the prior cache only after the two-miss movement gate fires.

    ``persist_directory=False`` emits an empty next-generation directory. It is the
    opportunity-gated candidate: ordinary exact repeats and sparse edits therefore pay no
    output-directory construction cost; aligned movement may pay one bounded prior-cache
    scan after evidence says that relocation is useful.
    """
    if type(data) is not bytes:
        raise TypeError("ONE relocation-cache input must be bytes")
    _validate_shape(policy_id, block_size, chunk_size)
    if type(max_relocation_entries) is not int or max_relocation_entries <= 0:
        raise ValueError("max_relocation_entries must be a positive integer")
    if type(persist_directory) is not bool:
        raise TypeError("persist_directory must be bool")

    compatible = (
        isinstance(previous, FingerprintCache)
        and previous.policy_id == policy_id
        and previous.block_size == block_size
        and previous.chunk_size == chunk_size
    )
    prior_blocks = previous.blocks if compatible else ()
    directory_compatible = compatible and _directory_compatible(
        previous_directory,
        policy_id=policy_id,
        block_size=block_size,
        chunk_size=chunk_size,
    )

    relocation_index: dict[tuple[bytes, int], int] | None = None
    relocation_index_entries = 0
    relocation_lookups = 0
    relocation_gate_activations = 0
    prior_cache_index_scan_blocks = 0
    consecutive_positional_misses = 0

    def build_index_from_directory() -> dict[tuple[bytes, int], int]:
        built: dict[tuple[bytes, int], int] = {}
        if not directory_compatible or previous_directory is None:
            return built
        for entry in previous_directory.entries:
            if len(built) >= max_relocation_entries:
                break
            if not isinstance(entry, RelocationDirectoryEntry):
                continue
            if type(entry.digest) is not bytes or len(entry.digest) != 32:
                continue
            if type(entry.length) is not int or entry.length <= 0:
                continue
            if type(entry.block_index) is not int or entry.block_index < 0:
                continue
            built.setdefault((entry.digest, entry.length), entry.block_index)
        return built

    def ensure_relocation_index() -> dict[tuple[bytes, int], int]:
        nonlocal relocation_index, relocation_index_entries, prior_cache_index_scan_blocks
        if relocation_index is not None:
            return relocation_index
        if directory_compatible:
            built = build_index_from_directory()
        else:
            built = {}
            for block_index, candidate in enumerate(prior_blocks):
                prior_cache_index_scan_blocks += 1
                if len(built) >= max_relocation_entries:
                    break
                if (
                    isinstance(candidate, FingerprintBlock)
                    and type(candidate.digest) is bytes
                    and len(candidate.digest) == 32
                    and type(candidate.length) is int
                    and candidate.length > 0
                ):
                    built.setdefault((candidate.digest, candidate.length), block_index)
        relocation_index_entries = len(built)
        relocation_index = built
        return built

    blocks: list[FingerprintBlock] = []
    flat: list[int] = []
    output_directory_map: dict[tuple[bytes, int], int] | None = {} if persist_directory else None
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
            candidate_index = ensure_relocation_index().get((digest, len(raw)))
            candidate = (
                prior_blocks[candidate_index]
                if type(candidate_index) is int and 0 <= candidate_index < len(prior_blocks)
                else None
            )
            # The directory/index is nomination metadata, not authority. Re-check the
            # key against the actual cached block before spending seal-validation work.
            candidate_identity = (
                isinstance(candidate, FingerprintBlock)
                and candidate.digest == digest
                and candidate.length == len(raw)
            )
            # Avoid hashing the same damaged positional representative twice.
            if candidate_identity and candidate is not positional:
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
        if output_directory_map is not None and len(output_directory_map) < max_relocation_entries:
            output_directory_map.setdefault((digest, len(raw)), index)

    cache = FingerprintCache(
        policy_id=policy_id,
        block_size=block_size,
        chunk_size=chunk_size,
        blocks=tuple(blocks),
    )
    output_entries = () if output_directory_map is None else tuple(
        RelocationDirectoryEntry(digest=key[0], length=key[1], block_index=block_index)
        for key, block_index in output_directory_map.items()
    )
    directory = RelocationDirectory(
        policy_id=policy_id,
        block_size=block_size,
        chunk_size=chunk_size,
        entries=output_entries,
    )
    persistent_payload_bytes = sum(72 + 8 * len(block.fingerprints) for block in blocks)
    # Lower-bound directory/index payload only: digest + length + representative index.
    # Runtime object/RSS overhead must be charged separately before any production claim.
    relocation_index_payload_bytes = relocation_index_entries * 48
    directory_output_payload_bytes = len(output_entries) * 48

    return RelocatedFingerprints(
        fingerprints=tuple(flat),
        cache=cache,
        directory=directory,
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
            prior_cache_index_scan_blocks=prior_cache_index_scan_blocks,
            directory_output_entries=len(output_entries),
            directory_output_payload_bytes=directory_output_payload_bytes,
            emitted_fingerprints=len(flat),
            persistent_payload_bytes=persistent_payload_bytes,
        ),
    )
