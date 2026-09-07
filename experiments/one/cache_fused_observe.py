"""ONE-G0.2 writer-only cache for fused observation state.

The earlier fingerprint-cache seed proved that aligned FNV64 features can be reused, but
`observe.py` deliberately computes run evidence and fingerprints in one source pass. A
fingerprint-only cache followed by the ordinary observer would therefore add a SHA
validation pass without removing the observer's full byte scan.

This experiment caches *enough of the fused observation state* to replay the same run and
reuse opportunities after one SHA-256 validation pass over current bytes. Unchanged
blocks reuse sealed fingerprints, per-chunk run gates, and run-boundary summaries;
changed blocks recompute those features in one local fused pass. Global reuse nomination
is replayed from cached fingerprints and still performs exact byte proof before emitting
a ReuseOpportunity. The reader never sees this state and ONE bytes are unchanged.

This first seed is positional only. Cross-position reuse belongs to the separately tested
opportunity-gated relocation layer and should be composed only after this fused cache
survives exact-oracle and resource falsification.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import hmac
import struct

from experiments.one.observe import (
    Observation,
    ObservationStats,
    ReuseOpportunity,
    RunOpportunity,
)

_FNV64_OFFSET = 0xCBF29CE484222325
_FNV64_PRIME = 0x100000001B3
_U64_MASK = (1 << 64) - 1
_SEAL_DOMAIN = b"CMPCT1-ONE-G0.2-FUSED-OBSERVE-CACHE\x00"
DEFAULT_FUSED_POLICY_ID = "ONE-G0.2:fused-run-fnv64-v1"


@dataclass(frozen=True)
class FusedObservationBlock:
    digest: bytes
    length: int
    fingerprints: tuple[int, ...]
    chunk_run_gate: tuple[bool, ...]
    prefix_value: int
    prefix_length: int
    suffix_value: int
    suffix_length: int
    whole_same: bool
    internal_runs: tuple[RunOpportunity, ...]
    seal: bytes


@dataclass(frozen=True)
class FusedObservationCache:
    policy_id: str
    block_size: int
    chunk_size: int
    min_run: int
    blocks: tuple[FusedObservationBlock, ...]


@dataclass(frozen=True)
class IncrementalObservationStats:
    input_bytes: int
    validation_read_bytes: int
    feature_recompute_bytes: int
    feature_reuse_bytes: int
    cache_integrity_hash_bytes: int
    cache_feature_payload_read_bytes: int
    recomputed_blocks: int
    reused_blocks: int
    verification_read_bytes: int
    total_source_read_bytes: int
    persistent_payload_bytes: int


@dataclass(frozen=True)
class IncrementalObservation:
    observation: Observation
    cache: FusedObservationCache
    stats: IncrementalObservationStats


def _validate_shape(
    policy_id: str,
    block_size: int,
    chunk_size: int,
    min_run: int,
    max_index_entries: int,
) -> None:
    if type(policy_id) is not str or not policy_id:
        raise ValueError("policy_id must be non-empty text")
    policy_id.encode("utf-8")
    for name, value in {
        "block_size": block_size,
        "chunk_size": chunk_size,
        "min_run": min_run,
        "max_index_entries": max_index_entries,
    }.items():
        if type(value) is not int or value <= 0:
            raise ValueError(f"{name} must be a positive integer")
    if block_size % chunk_size:
        raise ValueError("block_size must be an exact multiple of chunk_size")


def _seal_message_bytes(policy_id: str, block: FusedObservationBlock) -> int:
    # Domain + policy length/text + digest + fixed scalar fields + feature payload.
    return (
        len(_SEAL_DOMAIN)
        + 8
        + len(policy_id.encode("utf-8"))
        + 32
        + 56
        + 8 * len(block.fingerprints)
        + len(block.chunk_run_gate)
        + 24 * len(block.internal_runs)
    )


def _seal(
    *,
    policy_id: str,
    block_size: int,
    chunk_size: int,
    min_run: int,
    digest: bytes,
    length: int,
    fingerprints: tuple[int, ...],
    chunk_run_gate: tuple[bool, ...],
    prefix_value: int,
    prefix_length: int,
    suffix_value: int,
    suffix_length: int,
    whole_same: bool,
    internal_runs: tuple[RunOpportunity, ...],
) -> bytes:
    policy = policy_id.encode("utf-8")
    h = hashlib.sha256()
    h.update(_SEAL_DOMAIN)
    h.update(struct.pack(">Q", len(policy)))
    h.update(policy)
    h.update(digest)
    h.update(
        struct.pack(
            ">QQQQQQQ",
            block_size,
            chunk_size,
            min_run,
            length,
            prefix_value,
            prefix_length,
            suffix_length,
        )
    )
    h.update(bytes((suffix_value, 1 if whole_same else 0)))
    h.update(struct.pack(">Q", len(fingerprints)))
    for value in fingerprints:
        h.update(struct.pack(">Q", value))
    h.update(bytes(1 if flag else 0 for flag in chunk_run_gate))
    h.update(struct.pack(">Q", len(internal_runs)))
    for run in internal_runs:
        h.update(struct.pack(">QQQ", run.start, run.length, run.value))
    return h.digest()


def _valid_cached(
    block: object,
    *,
    policy_id: str,
    block_size: int,
    chunk_size: int,
    min_run: int,
) -> bool:
    if not isinstance(block, FusedObservationBlock):
        return False
    if type(block.digest) is not bytes or len(block.digest) != 32:
        return False
    if type(block.seal) is not bytes or len(block.seal) != 32:
        return False
    if type(block.length) is not int or block.length <= 0 or block.length > block_size:
        return False
    expected_chunks = block.length // chunk_size
    if type(block.fingerprints) is not tuple or len(block.fingerprints) != expected_chunks:
        return False
    if any(type(value) is not int or value < 0 or value > _U64_MASK for value in block.fingerprints):
        return False
    if type(block.chunk_run_gate) is not tuple or len(block.chunk_run_gate) != expected_chunks:
        return False
    if any(type(flag) is not bool for flag in block.chunk_run_gate):
        return False
    if type(block.prefix_value) is not int or not 0 <= block.prefix_value <= 255:
        return False
    if type(block.suffix_value) is not int or not 0 <= block.suffix_value <= 255:
        return False
    if type(block.prefix_length) is not int or not 1 <= block.prefix_length <= block.length:
        return False
    if type(block.suffix_length) is not int or not 1 <= block.suffix_length <= block.length:
        return False
    if type(block.whole_same) is not bool:
        return False
    if block.whole_same != (block.prefix_length == block.length == block.suffix_length):
        return False
    if block.whole_same and block.prefix_value != block.suffix_value:
        return False
    if type(block.internal_runs) is not tuple:
        return False
    for run in block.internal_runs:
        if not isinstance(run, RunOpportunity):
            return False
        if type(run.start) is not int or type(run.length) is not int or type(run.value) is not int:
            return False
        if run.start <= 0 or run.length < min_run or run.start + run.length >= block.length:
            return False
        if not 0 <= run.value <= 255:
            return False
    expected = _seal(
        policy_id=policy_id,
        block_size=block_size,
        chunk_size=chunk_size,
        min_run=min_run,
        digest=block.digest,
        length=block.length,
        fingerprints=block.fingerprints,
        chunk_run_gate=block.chunk_run_gate,
        prefix_value=block.prefix_value,
        prefix_length=block.prefix_length,
        suffix_value=block.suffix_value,
        suffix_length=block.suffix_length,
        whole_same=block.whole_same,
        internal_runs=block.internal_runs,
    )
    return hmac.compare_digest(block.seal, expected)


def _compute_block(
    raw: bytes,
    *,
    digest: bytes,
    policy_id: str,
    block_size: int,
    chunk_size: int,
    min_run: int,
) -> FusedObservationBlock:
    if not raw:
        raise ValueError("fused observation blocks must be non-empty")
    threshold = max(min_run, chunk_size)
    fingerprints: list[int] = []
    run_gate: list[bool] = []
    segments: list[tuple[int, int, int]] = []

    run_start = 0
    run_value = raw[0]
    run_length = 0
    chunk_hash = _FNV64_OFFSET
    for position, value in enumerate(raw):
        if run_length == 0:
            run_start = position
            run_value = value
            run_length = 1
        elif value == run_value:
            run_length += 1
        else:
            segments.append((run_start, run_length, run_value))
            run_start = position
            run_value = value
            run_length = 1

        chunk_hash ^= value
        chunk_hash = (chunk_hash * _FNV64_PRIME) & _U64_MASK
        if (position + 1) % chunk_size == 0:
            fingerprints.append(chunk_hash)
            run_gate.append(run_length >= threshold)
            chunk_hash = _FNV64_OFFSET
    segments.append((run_start, run_length, run_value))

    prefix_start, prefix_length, prefix_value = segments[0]
    suffix_start, suffix_length, suffix_value = segments[-1]
    assert prefix_start == 0
    whole_same = len(segments) == 1
    internal_runs = tuple(
        RunOpportunity(start, length, value)
        for start, length, value in segments[1:-1]
        if length >= min_run
    )
    block = FusedObservationBlock(
        digest=digest,
        length=len(raw),
        fingerprints=tuple(fingerprints),
        chunk_run_gate=tuple(run_gate),
        prefix_value=prefix_value,
        prefix_length=prefix_length,
        suffix_value=suffix_value,
        suffix_length=suffix_length,
        whole_same=whole_same,
        internal_runs=internal_runs,
        seal=b"",
    )
    return FusedObservationBlock(
        digest=block.digest,
        length=block.length,
        fingerprints=block.fingerprints,
        chunk_run_gate=block.chunk_run_gate,
        prefix_value=block.prefix_value,
        prefix_length=block.prefix_length,
        suffix_value=block.suffix_value,
        suffix_length=block.suffix_length,
        whole_same=block.whole_same,
        internal_runs=block.internal_runs,
        seal=_seal(
            policy_id=policy_id,
            block_size=block_size,
            chunk_size=chunk_size,
            min_run=min_run,
            digest=block.digest,
            length=block.length,
            fingerprints=block.fingerprints,
            chunk_run_gate=block.chunk_run_gate,
            prefix_value=block.prefix_value,
            prefix_length=block.prefix_length,
            suffix_value=block.suffix_value,
            suffix_length=block.suffix_length,
            whole_same=block.whole_same,
            internal_runs=block.internal_runs,
        ),
    )


def observe_incremental(
    data: bytes,
    *,
    previous: FusedObservationCache | None = None,
    min_run: int = 8,
    chunk_size: int = 64,
    block_size: int = 4096,
    max_index_entries: int = 1 << 16,
    policy_id: str = DEFAULT_FUSED_POLICY_ID,
) -> IncrementalObservation:
    """Reconstruct exact fused observation opportunities using sealed block features."""
    if type(data) is not bytes:
        raise TypeError("ONE fused-cache input must be bytes")
    _validate_shape(policy_id, block_size, chunk_size, min_run, max_index_entries)
    if not data:
        empty = Observation(
            runs=(), reuse=(),
            stats=ObservationStats(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
        )
        cache = FusedObservationCache(policy_id, block_size, chunk_size, min_run, ())
        return IncrementalObservation(
            empty, cache,
            IncrementalObservationStats(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
        )

    compatible = (
        isinstance(previous, FusedObservationCache)
        and previous.policy_id == policy_id
        and previous.block_size == block_size
        and previous.chunk_size == chunk_size
        and previous.min_run == min_run
    )
    prior_blocks = previous.blocks if compatible else ()

    blocks: list[FusedObservationBlock] = []
    recompute_bytes = 0
    reuse_bytes = 0
    integrity_hash_bytes = 0
    payload_read_bytes = 0
    recomputed_blocks = 0
    reused_blocks = 0

    for index, start in enumerate(range(0, len(data), block_size)):
        raw = data[start:start + block_size]
        digest = hashlib.sha256(raw).digest()
        candidate = prior_blocks[index] if index < len(prior_blocks) else None
        identity = (
            isinstance(candidate, FusedObservationBlock)
            and candidate.digest == digest
            and candidate.length == len(raw)
        )
        if identity and _valid_cached(
            candidate,
            policy_id=policy_id,
            block_size=block_size,
            chunk_size=chunk_size,
            min_run=min_run,
        ):
            block = candidate
            integrity_hash_bytes += _seal_message_bytes(policy_id, block)
            payload_read_bytes += (
                8 * len(block.fingerprints)
                + len(block.chunk_run_gate)
                + 24 * len(block.internal_runs)
                + 32
            )
            reuse_bytes += len(raw)
            reused_blocks += 1
        else:
            block = _compute_block(
                raw,
                digest=digest,
                policy_id=policy_id,
                block_size=block_size,
                chunk_size=chunk_size,
                min_run=min_run,
            )
            recompute_bytes += len(raw)
            recomputed_blocks += 1
        blocks.append(block)

    # Reconstruct global run opportunities from cached internal runs plus only the
    # boundaries that can change meaning when adjacent blocks meet.
    runs: list[RunOpportunity] = []
    pending_start: int | None = None
    pending_length = 0
    pending_value = 0

    def flush_run() -> None:
        nonlocal pending_start, pending_length, pending_value
        if pending_start is not None and pending_length >= min_run:
            runs.append(RunOpportunity(pending_start, pending_length, pending_value))
        pending_start = None
        pending_length = 0
        pending_value = 0

    incoming_lengths: list[int] = []
    carry_value: int | None = None
    carry_length = 0
    offset = 0
    for block in blocks:
        incoming = carry_length if carry_value == block.prefix_value else 0
        incoming_lengths.append(incoming)

        if block.whole_same:
            if pending_start is not None and pending_value == block.prefix_value:
                pending_length += block.length
            else:
                flush_run()
                pending_start = offset
                pending_length = block.length
                pending_value = block.prefix_value
        else:
            if pending_start is not None and pending_value == block.prefix_value:
                pending_length += block.prefix_length
            else:
                flush_run()
                pending_start = offset
                pending_length = block.prefix_length
                pending_value = block.prefix_value
            flush_run()
            for run in block.internal_runs:
                runs.append(RunOpportunity(offset + run.start, run.length, run.value))
            pending_start = offset + block.length - block.suffix_length
            pending_length = block.suffix_length
            pending_value = block.suffix_value

        if block.whole_same:
            carry_value = block.prefix_value
            carry_length = incoming + block.length
        else:
            carry_value = block.suffix_value
            carry_length = block.suffix_length
        offset += block.length
    flush_run()

    # Replay global reuse discovery from cached fingerprints. Exact proof remains over
    # current bytes, so a cache record can nominate but never establish equality.
    reuse: list[ReuseOpportunity] = []
    index: dict[int, list[int]] = {}
    index_entries = 0
    fingerprints_seen = 0
    lookups = 0
    verifications = 0
    verification_read_bytes = 0
    pending_source: int | None = None
    pending_target: int | None = None
    pending_reuse_length = 0

    def flush_reuse() -> None:
        nonlocal pending_source, pending_target, pending_reuse_length
        nonlocal verifications, verification_read_bytes
        if pending_source is None or pending_target is None or pending_reuse_length == 0:
            return
        verifications += 1
        verification_read_bytes += 2 * pending_reuse_length
        if data[pending_source:pending_source + pending_reuse_length] == data[
            pending_target:pending_target + pending_reuse_length
        ]:
            reuse.append(ReuseOpportunity(pending_source, pending_target, pending_reuse_length))
        pending_source = None
        pending_target = None
        pending_reuse_length = 0

    def start_or_extend(source: int, target: int) -> None:
        nonlocal pending_source, pending_target, pending_reuse_length
        if (
            pending_source is not None
            and pending_target is not None
            and pending_source + pending_reuse_length == source
            and pending_target + pending_reuse_length == target
        ):
            pending_reuse_length += chunk_size
            return
        flush_reuse()
        pending_source = source
        pending_target = target
        pending_reuse_length = chunk_size

    threshold = max(min_run, chunk_size)
    block_offset = 0
    for block_index, block in enumerate(blocks):
        incoming = incoming_lengths[block_index]
        for chunk_index, fingerprint in enumerate(block.fingerprints):
            local_end = (chunk_index + 1) * chunk_size
            fingerprints_seen += 1
            in_prefix = local_end <= block.prefix_length
            gated_by_run = (
                incoming + local_end >= threshold
                if in_prefix and incoming > 0
                else block.chunk_run_gate[chunk_index]
            )
            if gated_by_run:
                flush_reuse()
                continue

            start = block_offset + chunk_index * chunk_size
            lookups += 1
            sources = index.get(fingerprint)
            matched = False
            if sources and len(sources) == 1:
                start_or_extend(sources[0], start)
                matched = True
            elif sources:
                flush_reuse()
                for source in sources:
                    verifications += 1
                    verification_read_bytes += 2 * chunk_size
                    if data[source:source + chunk_size] == data[start:start + chunk_size]:
                        reuse.append(ReuseOpportunity(source, start, chunk_size))
                        matched = True
                        break
            else:
                flush_reuse()
            if not matched and index_entries < max_index_entries:
                index.setdefault(fingerprint, []).append(start)
                index_entries += 1
        block_offset += block.length
    flush_reuse()

    run_opportunity_bytes = sum(run.length for run in runs)
    reuse_opportunity_bytes = sum(item.length for item in reuse)
    retained_index_payload_bytes = 8 * len(index) + 8 * index_entries
    observation = Observation(
        runs=tuple(runs),
        reuse=tuple(reuse),
        stats=ObservationStats(
            input_bytes=len(data),
            source_scan_bytes=len(data),
            chunk_fingerprints=fingerprints_seen,
            hash_lookups=lookups,
            collision_verifications=verifications,
            verification_read_bytes=verification_read_bytes,
            total_source_read_bytes=len(data) + verification_read_bytes,
            run_candidates=len(runs),
            run_opportunity_bytes=run_opportunity_bytes,
            reuse_candidates=len(reuse),
            reuse_opportunity_bytes=reuse_opportunity_bytes,
            peak_index_entries=index_entries,
            retained_index_payload_bytes=retained_index_payload_bytes,
        ),
    )
    cache = FusedObservationCache(
        policy_id=policy_id,
        block_size=block_size,
        chunk_size=chunk_size,
        min_run=min_run,
        blocks=tuple(blocks),
    )
    persistent_payload_bytes = sum(
        106
        + 8 * len(block.fingerprints)
        + len(block.chunk_run_gate)
        + 24 * len(block.internal_runs)
        for block in blocks
    )
    actual_total_reads = len(data) + recompute_bytes + verification_read_bytes
    return IncrementalObservation(
        observation=observation,
        cache=cache,
        stats=IncrementalObservationStats(
            input_bytes=len(data),
            validation_read_bytes=len(data),
            feature_recompute_bytes=recompute_bytes,
            feature_reuse_bytes=reuse_bytes,
            cache_integrity_hash_bytes=integrity_hash_bytes,
            cache_feature_payload_read_bytes=payload_read_bytes,
            recomputed_blocks=recomputed_blocks,
            reused_blocks=reused_blocks,
            verification_read_bytes=verification_read_bytes,
            total_source_read_bytes=actual_total_reads,
            persistent_payload_bytes=persistent_payload_bytes,
        ),
    )
