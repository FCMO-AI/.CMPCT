"""ONE-G0.2 morphology-aware observation experiment.

This is writer-side discovery policy only. It does not add a reader-visible opcode or
change ONE reconstruction semantics. Strong numeric morphology selects a chunk-bulk
fingerprint implementation that preserves run/reuse discovery rather than deleting
reuse evidence for speed.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import blake2b

from .observe import Observation, ObservationStats, ReuseOpportunity, RunOpportunity, observe

_NUMERIC_ASCII = frozenset(b"0123456789+-.eE,;:|/ _\t\r\n")
_DIGITS = frozenset(b"0123456789")


@dataclass(frozen=True)
class MorphologyGateDecision:
    gated: bool
    sample_bytes: int
    numeric_like_bytes: int
    digit_bytes: int
    numeric_fraction: float
    digit_fraction: float
    sampled_chunks: int
    unique_sampled_chunks: int
    unique_chunk_fraction: float


@dataclass(frozen=True)
class MorphologyObservation:
    observation: Observation
    gate: MorphologyGateDecision


def _stratified_sample(data: bytes, *, sample_limit: int, windows: int = 8) -> bytes:
    if len(data) <= sample_limit:
        return data
    windows = max(1, min(windows, sample_limit))
    base = sample_limit // windows
    remainder = sample_limit % windows
    pieces: list[bytes] = []
    for index in range(windows):
        width = base + (1 if index < remainder else 0)
        if width <= 0:
            continue
        start = 0 if windows == 1 else round(index * (len(data) - width) / (windows - 1))
        pieces.append(data[start : start + width])
    return b"".join(pieces)


def classify_numeric_ascii(
    data: bytes,
    *,
    sample_limit: int = 4096,
    minimum_input: int = 16384,
    diversity_chunk_size: int = 64,
    sample_windows: int = 8,
    minimum_numeric_fraction: float = 0.985,
    minimum_digit_fraction: float = 0.35,
    minimum_unique_chunk_fraction: float = 0.90,
) -> MorphologyGateDecision:
    """Bounded selector for strongly numeric, locally diverse ASCII roots.

    The selector controls writer implementation only. The selected bulk observer still
    discovers reuse and proves every emitted opportunity by exact byte equality, so a
    false morphology classification cannot by itself discard reuse evidence.
    """
    if type(data) is not bytes:
        raise TypeError("ONE morphology input must be bytes")
    for name, value in {
        "sample_limit": sample_limit,
        "minimum_input": minimum_input,
        "diversity_chunk_size": diversity_chunk_size,
        "sample_windows": sample_windows,
    }.items():
        if type(value) is not int or value <= 0:
            raise ValueError(f"{name} must be a positive integer")
    for name, value in {
        "minimum_numeric_fraction": minimum_numeric_fraction,
        "minimum_digit_fraction": minimum_digit_fraction,
        "minimum_unique_chunk_fraction": minimum_unique_chunk_fraction,
    }.items():
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"{name} must be in [0, 1]")

    sample = _stratified_sample(data, sample_limit=sample_limit, windows=sample_windows)
    sample_bytes = len(sample)
    if sample_bytes == 0:
        return MorphologyGateDecision(False, 0, 0, 0, 0.0, 0.0, 0, 0, 0.0)

    numeric_like = sum(value in _NUMERIC_ASCII for value in sample)
    digits = sum(value in _DIGITS for value in sample)
    numeric_fraction = numeric_like / sample_bytes
    digit_fraction = digits / sample_bytes

    complete_bytes = sample_bytes - (sample_bytes % diversity_chunk_size)
    chunks = tuple(
        sample[offset : offset + diversity_chunk_size]
        for offset in range(0, complete_bytes, diversity_chunk_size)
    )
    sampled_chunks = len(chunks)
    unique_sampled_chunks = len(set(chunks))
    unique_chunk_fraction = unique_sampled_chunks / sampled_chunks if sampled_chunks else 0.0

    gated = (
        len(data) >= minimum_input
        and numeric_fraction >= minimum_numeric_fraction
        and digit_fraction >= minimum_digit_fraction
        and sampled_chunks >= 4
        and unique_chunk_fraction >= minimum_unique_chunk_fraction
    )
    return MorphologyGateDecision(
        gated,
        sample_bytes,
        numeric_like,
        digits,
        numeric_fraction,
        digit_fraction,
        sampled_chunks,
        unique_sampled_chunks,
        unique_chunk_fraction,
    )


def _observe_bulk_digest(
    data: bytes,
    *,
    min_run: int,
    chunk_size: int,
    max_index_entries: int,
    classifier_bytes: int,
) -> Observation:
    """Discover the same opportunity classes with chunk-bulk BLAKE2b-64 nomination.

    The source is consumed in aligned chunks. Run detection iterates each temporary
    chunk while BLAKE2b fingerprints the same chunk in optimized native code. Digest
    collisions can only add ambiguity: exact equality is still mandatory before reuse
    is emitted. Collision bucket behavior may differ from FNV64, so hostile tests compare
    emitted opportunity semantics on the benchmark matrix rather than assuming identity.
    """
    runs: list[RunOpportunity] = []
    reuse: list[ReuseOpportunity] = []
    index: dict[bytes, list[int]] = {}
    index_entries = 0
    fingerprints = 0
    lookups = 0
    verifications = 0
    verification_read_bytes = 0

    pending_source: int | None = None
    pending_target: int | None = None
    pending_length = 0

    def flush_pending() -> None:
        nonlocal pending_source, pending_target, pending_length
        nonlocal verifications, verification_read_bytes
        if pending_source is None or pending_target is None or pending_length == 0:
            return
        verifications += 1
        verification_read_bytes += 2 * pending_length
        if data[pending_source : pending_source + pending_length] == data[
            pending_target : pending_target + pending_length
        ]:
            reuse.append(ReuseOpportunity(pending_source, pending_target, pending_length))
        pending_source = None
        pending_target = None
        pending_length = 0

    def start_or_extend_pending(source: int, target: int) -> None:
        nonlocal pending_source, pending_target, pending_length
        if (
            pending_source is not None
            and pending_target is not None
            and pending_source + pending_length == source
            and pending_target + pending_length == target
        ):
            pending_length += chunk_size
            return
        flush_pending()
        pending_source = source
        pending_target = target
        pending_length = chunk_size

    run_start = 0
    run_value = data[0] if data else 0
    run_length = 0
    position = 0

    for chunk_start in range(0, len(data), chunk_size):
        chunk = data[chunk_start : chunk_start + chunk_size]
        for value in chunk:
            if run_length == 0:
                run_start = position
                run_value = value
                run_length = 1
            elif value == run_value:
                run_length += 1
            else:
                if run_length >= min_run:
                    runs.append(RunOpportunity(run_start, run_length, run_value))
                run_start = position
                run_value = value
                run_length = 1
            position += 1

        # Match the reference observer: an incomplete tail is not reuse-indexed in G0.2.
        if len(chunk) != chunk_size:
            continue
        fingerprints += 1
        if run_length >= max(min_run, chunk_size):
            flush_pending()
            continue

        fingerprint = blake2b(chunk, digest_size=8).digest()
        lookups += 1
        sources = index.get(fingerprint)
        matched = False
        if sources and len(sources) == 1:
            start_or_extend_pending(sources[0], chunk_start)
            matched = True
        elif sources:
            flush_pending()
            for source in sources:
                verifications += 1
                verification_read_bytes += 2 * chunk_size
                if data[source : source + chunk_size] == chunk:
                    reuse.append(ReuseOpportunity(source, chunk_start, chunk_size))
                    matched = True
                    break
        else:
            flush_pending()

        if not matched and index_entries < max_index_entries:
            index.setdefault(fingerprint, []).append(chunk_start)
            index_entries += 1

    flush_pending()
    if run_length >= min_run:
        runs.append(RunOpportunity(run_start, run_length, run_value))

    run_opportunity_bytes = sum(item.length for item in runs)
    reuse_opportunity_bytes = sum(item.length for item in reuse)
    source_scan_bytes = len(data) + classifier_bytes
    retained_index_payload_bytes = 8 * len(index) + 8 * index_entries
    return Observation(
        runs=tuple(runs),
        reuse=tuple(reuse),
        stats=ObservationStats(
            input_bytes=len(data),
            source_scan_bytes=source_scan_bytes,
            chunk_fingerprints=fingerprints,
            hash_lookups=lookups,
            collision_verifications=verifications,
            verification_read_bytes=verification_read_bytes,
            total_source_read_bytes=source_scan_bytes + verification_read_bytes,
            run_candidates=len(runs),
            run_opportunity_bytes=run_opportunity_bytes,
            reuse_candidates=len(reuse),
            reuse_opportunity_bytes=reuse_opportunity_bytes,
            peak_index_entries=index_entries,
            retained_index_payload_bytes=retained_index_payload_bytes,
        ),
    )


def observe_morphology_gated(
    data: bytes,
    *,
    min_run: int = 8,
    chunk_size: int = 64,
    max_index_entries: int = 1 << 16,
    sample_limit: int = 4096,
    minimum_input: int = 16384,
    diversity_chunk_size: int = 64,
    sample_windows: int = 8,
    minimum_numeric_fraction: float = 0.985,
    minimum_digit_fraction: float = 0.35,
    minimum_unique_chunk_fraction: float = 0.90,
) -> MorphologyObservation:
    """Select bulk digest observation only for bounded strong numeric evidence."""
    decision = classify_numeric_ascii(
        data,
        sample_limit=sample_limit,
        minimum_input=minimum_input,
        diversity_chunk_size=diversity_chunk_size,
        sample_windows=sample_windows,
        minimum_numeric_fraction=minimum_numeric_fraction,
        minimum_digit_fraction=minimum_digit_fraction,
        minimum_unique_chunk_fraction=minimum_unique_chunk_fraction,
    )
    if decision.gated:
        observation = _observe_bulk_digest(
            data,
            min_run=min_run,
            chunk_size=chunk_size,
            max_index_entries=max_index_entries,
            classifier_bytes=decision.sample_bytes,
        )
    else:
        observation = observe(
            data,
            min_run=min_run,
            chunk_size=chunk_size,
            max_index_entries=max_index_entries,
        )
    return MorphologyObservation(observation=observation, gate=decision)
