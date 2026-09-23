from __future__ import annotations

"""Candidate-scoped proof for hidden-ZIP reuse ownership.

Canonical Builder owns filesystem traversal and representation selection; this module receives
only owners Builder has already surfaced and never walks the tree itself.
"""

from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from .hidden_zip import (
    MAX_CANDIDATE_LOGICAL_BYTES, MAX_OBSERVATION_CENTRAL_DIRECTORY_BYTES,
    MAX_OBSERVATION_DESCRIPTORS, MAX_OBSERVATION_FILES, MAX_OBSERVATION_IO_BYTES,
    MAX_OBSERVATION_LOGICAL_BYTES, MIN_VERIFIED_REUSE, _file_sha256_expected,
    _metadata_descriptors, _stamp, _verify_candidate, hidden_zip_preflight,
)
from .reuse_ownership import Identity, realized_reuse_fixed_point

Stamp = tuple[int, int, int, int]


@dataclass(frozen=True)
class ZipOwnerSource:
    """One Builder-surfaced physical owner; ``fixed`` means realized individual S_VZIP."""
    rel: str
    path: Path
    fixed: bool = False
    expected_stamp: Stamp | None = None
    expected_digest: bytes | None = None


@dataclass(frozen=True)
class CandidateOwnershipProof:
    realized: frozenset[str]
    credit: dict[str, int]
    owner_identities: dict[str, frozenset[Identity]]
    source_states: dict[str, tuple[Stamp, bytes]]
    io_bytes: int
    logical_bytes: int
    rejects: tuple[tuple[str, int], ...]


def _budget_refusal(reason: str, observed: int, io_bytes: int = 0, logical_bytes: int = 0) -> CandidateOwnershipProof:
    return CandidateOwnershipProof(frozenset(), {}, {}, {}, int(io_bytes), int(logical_bytes), ((reason, int(observed)),))


def prove_candidate_zip_ownership(
    sources: tuple[ZipOwnerSource, ...] | list[ZipOwnerSource], *,
    min_verified_reuse: int = MIN_VERIFIED_REUSE,
    max_io_bytes: int = MAX_OBSERVATION_IO_BYTES,
    max_logical_bytes: int = MAX_OBSERVATION_LOGICAL_BYTES,
    max_candidate_logical_bytes: int = MAX_CANDIDATE_LOGICAL_BYTES,
    max_sources: int = MAX_OBSERVATION_FILES,
    max_descriptors: int = MAX_OBSERVATION_DESCRIPTORS,
    max_central_directory_bytes: int = MAX_OBSERVATION_CENTRAL_DIRECTORY_BYTES,
    excluded_owners: frozenset[str] = frozenset(),
) -> CandidateOwnershipProof:
    """Prove exact stream ownership only among Builder-surfaced candidates."""
    if len(sources) > int(max_sources): return _budget_refusal("source_budget", len(sources))
    sources = tuple(sources)
    if len({s.rel for s in sources}) != len(sources): raise ValueError("candidate owner rel paths must be unique")

    rejects: Counter[str] = Counter(); physical: dict[tuple[int, int], list[str]] = {}; source_physical: dict[str, tuple[int, int]] = {}
    for source in sources:
        try:
            st = source.path.stat(); stamp = _stamp(st); key = (int(st.st_dev), int(st.st_ino))
        except OSError:
            rejects["source_changed"] += 1; continue
        if source.expected_stamp is not None and stamp != source.expected_stamp:
            rejects["source_changed"] += 1; continue
        source_physical[source.rel] = key; physical.setdefault(key, []).append(source.rel)
    aliased = {rel for rels in physical.values() if len(rels) > 1 for rel in rels}

    parsed: list[tuple[ZipOwnerSource, set[tuple[int, int, int, int]], int]] = []
    metadata_owners: Counter[tuple[int, int, int, int]] = Counter()
    io_used = logical_used = declared_logical_used = descriptor_used = central_directory_used = 0
    for source in sources:
        if source.rel not in source_physical: continue
        if source.rel in aliased:
            rejects["physical_alias"] += 1; continue
        pf = hidden_zip_preflight(source.path, max_read_bytes=max(0, int(max_io_bytes) - io_used))
        io_used += int(pf.head_bytes_read) + int(pf.tail_bytes_read)
        if not pf.eligible:
            rejects[pf.reason] += 1; continue
        central_directory_used += int(pf.central_directory_size)
        if central_directory_used > int(max_central_directory_bytes): return _budget_refusal("central_directory_budget", central_directory_used, io_used, logical_used)
        parser_charge = int(pf.tail_bytes_read) + int(pf.central_directory_size)
        if io_used + parser_charge > int(max_io_bytes):
            rejects["io_budget"] += 1; continue
        io_used += parser_charge
        descriptors, entries, declared_logical, reason = _metadata_descriptors(source.path)
        if descriptors is None:
            rejects[reason or "exact_parse_rejected"] += 1; continue
        descriptor_used += int(entries)
        if descriptor_used > int(max_descriptors): return _budget_refusal("descriptor_budget", descriptor_used, io_used, logical_used)
        if declared_logical > int(max_candidate_logical_bytes) or declared_logical_used + int(declared_logical) > int(max_logical_bytes):
            rejects["logical_work_budget"] += 1; continue
        declared_logical_used += int(declared_logical)
        parsed.append((source, set(descriptors), parser_charge)); metadata_owners.update(descriptors)

    repeated = {d for d, count in metadata_owners.items() if count >= 2}
    owner_identities: dict[str, frozenset[Identity]] = {}; source_states: dict[str, tuple[Stamp, bytes]] = {}; accepted_sources: dict[str, ZipOwnerSource] = {}
    for source, descriptors, parser_charge in parsed:
        hints = descriptors & repeated
        if not hints:
            owner_identities[source.rel] = frozenset(); accepted_sources[source.rel] = source; continue
        try:
            st = source.path.stat(); stamp = _stamp(st); physical_size = int(st.st_size)
        except OSError:
            rejects["source_changed"] += 1; continue
        if source.expected_stamp is not None and stamp != source.expected_stamp:
            rejects["source_changed"] += 1; continue
        if (int(st.st_dev), int(st.st_ino)) != source_physical[source.rel]:
            rejects["source_changed"] += 1; continue
        if io_used + physical_size + parser_charge > int(max_io_bytes):
            rejects["io_budget"] += 1; continue
        digest_before = _file_sha256_expected(source.path, stamp)
        if digest_before is None or (source.expected_digest is not None and digest_before != source.expected_digest):
            rejects["source_changed"] += 1; continue
        io_used += physical_size + parser_charge
        verified, read, logical, reason = _verify_candidate(source.path, hints, int(max_io_bytes) - io_used, int(max_logical_bytes) - logical_used)
        io_used += int(read); logical_used += int(logical)
        if verified is None:
            rejects[reason or "validation_rejected"] += 1; continue
        if io_used + physical_size > int(max_io_bytes):
            rejects["io_budget"] += 1; continue
        digest_after = _file_sha256_expected(source.path, stamp); io_used += physical_size
        if digest_after is None or digest_after != digest_before:
            rejects["source_changed"] += 1; continue
        owner_identities[source.rel] = frozenset(identity for group in verified.values() for identity in group)
        source_states[source.rel] = (stamp, digest_after); accepted_sources[source.rel] = source

    fixed = {rel for rel, source in accepted_sources.items() if source.fixed}; hidden = set(accepted_sources) - fixed
    excluded = set(excluded_owners) & hidden
    realized, credit = realized_reuse_fixed_point(owner_identities, hidden_owners=hidden, fixed_owners=fixed, excluded_owners=excluded, min_verified_reuse=int(min_verified_reuse))
    return CandidateOwnershipProof(realized, credit, owner_identities, source_states, int(io_used), int(logical_used), tuple(sorted(rejects.items())))
