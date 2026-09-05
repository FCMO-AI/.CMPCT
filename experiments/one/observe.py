"""ONE-G0.2 fused observation prototype.

The observer does no compression and emits no reader-visible mechanism choice. It makes
one forward source pass and surfaces only cheap, content-derived opportunities that a
later Law compiler may accept or falsify. Discovery work/memory traffic are explicit so
they cannot disappear behind a ratio result.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RunOpportunity:
    start: int
    length: int
    value: int


@dataclass(frozen=True)
class ReuseOpportunity:
    source: int
    target: int
    length: int


@dataclass(frozen=True)
class ObservationStats:
    input_bytes: int
    source_scan_bytes: int
    chunk_fingerprints: int
    hash_lookups: int
    collision_verifications: int
    verification_read_bytes: int
    total_source_read_bytes: int
    run_candidates: int
    run_opportunity_bytes: int
    reuse_candidates: int
    reuse_opportunity_bytes: int
    peak_index_entries: int
    retained_index_payload_bytes: int


@dataclass(frozen=True)
class Observation:
    runs: tuple[RunOpportunity, ...]
    reuse: tuple[ReuseOpportunity, ...]
    stats: ObservationStats


_FNV64_OFFSET = 0xCBF29CE484222325
_FNV64_PRIME = 0x100000001B3
_U64_MASK = (1 << 64) - 1


def observe(
    data: bytes,
    *,
    min_run: int = 8,
    chunk_size: int = 64,
    max_index_entries: int = 1 << 16,
) -> Observation:
    """Observe simple Law opportunities in one bounded forward source scan.

    Fixed chunks are intentionally cheap G0.2 instrumentation, not a permanent dedup
    format. A streaming 64-bit fingerprint is updated while each source byte is already
    in hand, avoiding a second chunk-hashing source pass. Fingerprints nominate reuse,
    but exact byte equality remains mandatory before an opportunity is emitted.

    Adjacent uniquely nominated chunks are coalesced before exact verification. This
    preserves exact proof while replacing thousands of tiny Python comparisons with one
    bounded bulk comparison when the source and target ranges advance together. A chunk
    already wholly explained by an eligible run is not sent through the reuse index:
    emitting two competing cheap opportunities for the same constant region only spends
    discovery work and verification traffic without adding useful information.

    The index is insertion-bounded. Once full it stops learning new source chunks but
    continues looking up existing ones, preserving deterministic O(n) base work and
    bounded retained-source metadata. Ambiguous fingerprint buckets are verified
    immediately; a failed coalesced proof is simply discarded as discovery evidence and
    can never affect byte-exact reconstruction because no Law is emitted without proof.
    """
    if type(data) is not bytes:
        raise TypeError("ONE observation input must be bytes")
    for name, value in {
        "min_run": min_run,
        "chunk_size": chunk_size,
        "max_index_entries": max_index_entries,
    }.items():
        if type(value) is not int or value <= 0:
            raise ValueError(f"{name} must be a positive integer")

    runs: list[RunOpportunity] = []
    reuse: list[ReuseOpportunity] = []
    # Discovery-only fingerprints map to retained source offsets. Multiple offsets are
    # kept only for actual fingerprint collisions; exact repeats reuse the first source.
    index: dict[int, list[int]] = {}
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
    chunk_hash = _FNV64_OFFSET

    # One byte-forward source loop performs run observation and fingerprint formation.
    for position, value in enumerate(data):
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

        chunk_hash ^= value
        chunk_hash = (chunk_hash * _FNV64_PRIME) & _U64_MASK
        if (position + 1) % chunk_size == 0:
            start = position + 1 - chunk_size
            fingerprint = chunk_hash
            chunk_hash = _FNV64_OFFSET
            fingerprints += 1

            # If the whole aligned chunk is already inside a run that will qualify as
            # a run opportunity, a reuse lookup is redundant. This is a content-derived
            # opportunity gate, not a workload label.
            if run_length >= max(min_run, chunk_size):
                flush_pending()
                continue

            lookups += 1
            sources = index.get(fingerprint)
            matched = False
            if sources and len(sources) == 1:
                # Unique fingerprint nominations may be coalesced across adjacent
                # source/target chunks, then proven exactly as one bulk region.
                start_or_extend_pending(sources[0], start)
                matched = True
            elif sources:
                # Ambiguous buckets require immediate exact proof before selecting a
                # source; keeping this path explicit bounds adversarial collisions.
                flush_pending()
                for source in sources:
                    verifications += 1
                    verification_read_bytes += 2 * chunk_size
                    if data[source : source + chunk_size] == data[start : start + chunk_size]:
                        reuse.append(ReuseOpportunity(source, start, chunk_size))
                        matched = True
                        break
            else:
                flush_pending()

            if not matched and index_entries < max_index_entries:
                index.setdefault(fingerprint, []).append(start)
                index_entries += 1

    flush_pending()
    if run_length >= min_run:
        runs.append(RunOpportunity(run_start, run_length, run_value))

    source_scan_bytes = len(data)
    run_opportunity_bytes = sum(item.length for item in runs)
    reuse_opportunity_bytes = sum(item.length for item in reuse)
    # Algorithmic retained payload lower bound: one u64 fingerprint key per occupied
    # bucket plus one u64 source offset per retained entry. Python object overhead is
    # intentionally excluded and benchmark RSS must be used for implementation memory.
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
