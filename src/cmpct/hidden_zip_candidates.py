from __future__ import annotations

"""Candidate-scoped proof for hidden-ZIP reuse ownership.

This is the shipping-side replacement for root-level discovery.  Canonical Builder owns
filesystem traversal and representation selection; this module receives only owners Builder
has already surfaced and never walks the tree itself.
"""

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
import hashlib

from .hidden_zip import (
    LOCAL_HEADER_BYTES,
    MAX_CANDIDATE_LOGICAL_BYTES,
    MAX_OBSERVATION_IO_BYTES,
    MAX_OBSERVATION_LOGICAL_BYTES,
    MIN_VERIFIED_REUSE,
    _metadata_descriptors,
    _verify_candidate,
    hidden_zip_preflight,
)
from .reuse_ownership import Identity, realized_reuse_fixed_point


@dataclass(frozen=True)
class ZipOwnerSource:
    """One Builder-surfaced physical owner.

    ``fixed`` means canonical Builder already materialized this owner as an individual
    S_VZIP.  Non-fixed sources are tentative hidden owners.  S_PACK members and explicit
    fallback blobs must never be supplied as fixed sources.
    """

    rel: str
    path: Path
    fixed: bool = False


@dataclass(frozen=True)
class CandidateOwnershipProof:
    realized: frozenset[str]
    credit: dict[str, int]
    owner_identities: dict[str, frozenset[Identity]]
    io_bytes: int
    logical_bytes: int
    rejects: tuple[tuple[str, int], ...]


def prove_candidate_zip_ownership(
    sources: tuple[ZipOwnerSource, ...] | list[ZipOwnerSource],
    *,
    min_verified_reuse: int = MIN_VERIFIED_REUSE,
    max_io_bytes: int = MAX_OBSERVATION_IO_BYTES,
    max_logical_bytes: int = MAX_OBSERVATION_LOGICAL_BYTES,
    max_candidate_logical_bytes: int = MAX_CANDIDATE_LOGICAL_BYTES,
    excluded_owners: frozenset[str] = frozenset(),
) -> CandidateOwnershipProof:
    """Prove exact stream ownership only among Builder-surfaced candidates.

    Metadata is only a cheap necessary-condition filter.  Reuse credit comes exclusively
    from validated exact compressed-stream identities and is then solved over realized
    owners.  Any budget or structural failure removes that source from the proof rather
    than partially admitting it.
    """

    sources = tuple(sources)
    if len({s.rel for s in sources}) != len(sources):
        raise ValueError("candidate owner rel paths must be unique")

    rejects: Counter[str] = Counter()
    parsed: list[tuple[ZipOwnerSource, set[tuple[int, int, int, int]], int]] = []
    metadata_owners: Counter[tuple[int, int, int, int]] = Counter()
    io_used = logical_used = 0

    for source in sources:
        pf = hidden_zip_preflight(source.path, max_read_bytes=max(0, int(max_io_bytes) - io_used))
        io_used += int(pf.head_bytes_read) + int(pf.tail_bytes_read)
        if not pf.eligible:
            rejects[pf.reason] += 1
            continue
        # ZipFile parsing necessarily re-reads the EOCD/central directory. Charge that
        # work conservatively before allowing it, matching the root observer's accounting.
        parser_charge = int(pf.tail_bytes_read) + int(pf.central_directory_size)
        if io_used + parser_charge > int(max_io_bytes):
            rejects["io_budget"] += 1
            continue
        io_used += parser_charge
        descriptors, _entries, declared_logical, reason = _metadata_descriptors(source.path)
        if descriptors is None:
            rejects[reason or "exact_parse_rejected"] += 1
            continue
        if declared_logical > int(max_candidate_logical_bytes):
            rejects["logical_work_budget"] += 1
            continue
        parsed.append((source, set(descriptors), parser_charge))
        metadata_owners.update(descriptors)

    repeated = {d for d, count in metadata_owners.items() if count >= 2}
    owner_identities: dict[str, frozenset[Identity]] = {}
    accepted_sources: dict[str, ZipOwnerSource] = {}

    for source, descriptors, parser_charge in parsed:
        hints = descriptors & repeated
        if not hints:
            owner_identities[source.rel] = frozenset()
            accepted_sources[source.rel] = source
            continue
        try:
            physical_size = int(source.path.stat().st_size)
        except OSError:
            rejects["source_changed"] += 1
            continue
        if io_used + physical_size + parser_charge > int(max_io_bytes):
            rejects["io_budget"] += 1
            continue
        # Content-bind the source before exact-stream proof. Builder will later revalidate
        # its own source identity before commit; this digest prevents a path-only proof.
        try:
            digest_before = hashlib.sha256(source.path.read_bytes()).digest()
        except OSError:
            rejects["source_changed"] += 1
            continue
        io_used += physical_size + parser_charge
        remaining_io = int(max_io_bytes) - io_used
        remaining_logical = int(max_logical_bytes) - logical_used
        verified, read, logical, reason = _verify_candidate(source.path, hints, remaining_io, remaining_logical)
        io_used += int(read)
        logical_used += int(logical)
        if verified is None:
            rejects[reason or "validation_rejected"] += 1
            continue
        try:
            digest_after = hashlib.sha256(source.path.read_bytes()).digest()
        except OSError:
            rejects["source_changed"] += 1
            continue
        # Charge the revalidation read too. A proof that cannot afford content binding is
        # not allowed to become product ownership evidence.
        io_used += physical_size
        if io_used > int(max_io_bytes):
            rejects["io_budget"] += 1
            continue
        if digest_after != digest_before:
            rejects["source_changed"] += 1
            continue
        identities = frozenset(identity for group in verified.values() for identity in group)
        owner_identities[source.rel] = identities
        accepted_sources[source.rel] = source

    fixed = {rel for rel, source in accepted_sources.items() if source.fixed}
    hidden = set(accepted_sources) - fixed
    excluded = set(excluded_owners) & hidden
    realized, credit = realized_reuse_fixed_point(
        owner_identities,
        hidden_owners=hidden,
        fixed_owners=fixed,
        excluded_owners=excluded,
        min_verified_reuse=int(min_verified_reuse),
    )
    return CandidateOwnershipProof(
        realized,
        credit,
        owner_identities,
        int(io_used),
        int(logical_used),
        tuple(sorted(rejects.items())),
    )
