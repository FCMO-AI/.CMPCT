"""ONE-G0.2 fused observation prototype.

The observer does no compression and emits no reader-visible mechanism choice. It makes
one forward pass over input bytes and surfaces only cheap, content-derived opportunities
that a later Law compiler may accept or falsify. All counters are evidence so discovery
cost cannot disappear behind a ratio result.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import blake2b


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
    bytes_observed: int
    chunk_fingerprints: int
    hash_lookups: int
    collision_verifications: int
    run_candidates: int
    reuse_candidates: int
    peak_index_entries: int


@dataclass(frozen=True)
class Observation:
    runs: tuple[RunOpportunity, ...]
    reuse: tuple[ReuseOpportunity, ...]
    stats: ObservationStats


def observe(
    data: bytes,
    *,
    min_run: int = 8,
    chunk_size: int = 64,
    max_index_entries: int = 1 << 16,
) -> Observation:
    """Observe simple Law opportunities in one bounded forward scan.

    Fixed chunks are intentionally cheap G0.2 instrumentation, not a permanent dedup
    format. Fingerprints nominate candidates only; byte equality verifies every reuse,
    so hash collisions can cost CPU but can never change reconstruction semantics.

    The index is insertion-bounded. Once full it stops learning new source chunks but
    continues looking up existing ones, preserving deterministic O(n) work and memory.
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
    # 64-bit fingerprints are discovery-only. Map one fingerprint to all retained
    # source offsets so a collision does not hide a later exact match.
    index: dict[bytes, list[int]] = {}
    index_entries = 0
    fingerprints = 0
    lookups = 0
    verifications = 0

    run_start = 0
    run_value = data[0] if data else 0
    run_length = 0

    # One byte-forward loop performs run observation and closes fixed chunks as their
    # final byte arrives. No second discovery pass is allowed.
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

        if (position + 1) % chunk_size == 0:
            start = position + 1 - chunk_size
            chunk = data[start : position + 1]
            fingerprint = blake2b(chunk, digest_size=8, person=b"ONE-G0.2").digest()
            fingerprints += 1
            lookups += 1
            sources = index.get(fingerprint)
            matched = False
            if sources:
                for source in sources:
                    verifications += 1
                    if data[source : source + chunk_size] == chunk:
                        reuse.append(ReuseOpportunity(source, start, chunk_size))
                        matched = True
                        break
            # Preserve the first exact source for repeated chunks; preserve collision
            # alternatives while under the memory cap.
            if not matched and index_entries < max_index_entries:
                index.setdefault(fingerprint, []).append(start)
                index_entries += 1

    if run_length >= min_run:
        runs.append(RunOpportunity(run_start, run_length, run_value))

    return Observation(
        runs=tuple(runs),
        reuse=tuple(reuse),
        stats=ObservationStats(
            input_bytes=len(data),
            bytes_observed=len(data),
            chunk_fingerprints=fingerprints,
            hash_lookups=lookups,
            collision_verifications=verifications,
            run_candidates=len(runs),
            reuse_candidates=len(reuse),
            peak_index_entries=index_entries,
        ),
    )
