from __future__ import annotations

"""Transactional cohort staging after candidate-scoped hidden-ZIP ownership proof."""

from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import struct
import tempfile
import zipfile

from .codec import S_VZIP
from .hidden_zip import _stamp
from .hidden_zip_candidates import CandidateOwnershipProof, ZipOwnerSource
from .reuse_ownership import realized_reuse_fixed_point
from .vzip_transaction import StagedVzipRecipe, commit_staged_vzip, stage_vzip_recipe

MAX_STAGED_CANDIDATE_BYTES = 256 * 1024 * 1024
MAX_STAGE_SOURCE_BYTES = 256 * 1024 * 1024
SNAPSHOT_CHUNK = 1024 * 1024
# Conservative total staging-I/O charge after snapshotting: source read (1), private snapshot write (1),
# metadata peak-bound parser (1), and recipe construction (up to 2 snapshot reads). The parser never
# consumes the mutable source path after the snapshot has been content-bound.
STAGE_SOURCE_PASSES = 5
STAGE_REJECTS = (OSError, ValueError, RuntimeError, struct.error, zipfile.BadZipFile)


@dataclass(frozen=True)
class StagedHiddenCohort:
    realized: frozenset[str]
    credit: dict[str, int]
    staged: dict[str, StagedVzipRecipe]
    excluded: frozenset[str]
    retained_candidate_bytes: int
    source_bytes_read: int
    temporary_bytes_written: int = 0
    temporary_bytes_read: int = 0


def _retained_bytes(staged: StagedVzipRecipe) -> int:
    return sum(len(raw) + (0 if stream is None else len(stream)) for raw, _hint, stream, _ref in staged.candidates)


def _snapshot_proven_source(source: ZipOwnerSource, proof: CandidateOwnershipProof, destination: Path) -> tuple[bool, int]:
    """Copy exactly the proven object to a private file while binding both ends of the read.

    A path can change after ownership proof. Staging directly from that path makes parser resource bounds
    raceable even if a later digest check protects archive correctness. The private snapshot makes the
    bytes consumed by ZIP parsing immutable relative to the source namespace.
    """
    state = proof.source_states.get(source.rel)
    if state is None: return False, 0
    expected_stamp, expected_digest = state; expected_size = int(expected_stamp[2]); digest = hashlib.sha256(); read = 0
    try:
        with source.path.open("rb") as src, destination.open("wb") as dst:
            if _stamp(os.fstat(src.fileno())) != expected_stamp: return False, 0
            while read < expected_size:
                block = src.read(min(SNAPSHOT_CHUNK, expected_size - read))
                if not block: return False, read
                dst.write(block); digest.update(block); read += len(block)
            if src.read(1): return False, read
            if _stamp(os.fstat(src.fileno())) != expected_stamp: return False, read
            dst.flush()
        if read != expected_size or digest.digest() != expected_digest: return False, read
        if int(destination.stat().st_size) != expected_size: return False, read
    except OSError:
        return False, read
    return True, read


def stage_stable_hidden_cohort(
    proof: CandidateOwnershipProof, sources: tuple[ZipOwnerSource, ...] | list[ZipOwnerSource], *,
    min_verified_reuse: int, max_staged_candidate_bytes: int = MAX_STAGED_CANDIDATE_BYTES,
    max_stage_source_bytes: int = MAX_STAGE_SOURCE_BYTES,
) -> StagedHiddenCohort:
    sources = tuple(sources); source_by_rel = {source.rel: source for source in sources}
    if len(source_by_rel) != len(sources): raise ValueError("candidate owner rel paths must be unique")
    fixed = {rel for rel, source in source_by_rel.items() if source.fixed and rel in proof.owner_identities}
    hidden = set(proof.owner_identities) - fixed
    initially_realized_hidden = set(proof.realized) & hidden
    staged: dict[str, StagedVzipRecipe] = {}; excluded: set[str] = set()
    retained = source_read = temp_written = temp_read = 0
    for rel in sorted(initially_realized_hidden):
        source = source_by_rel.get(rel); state = proof.source_states.get(rel)
        if source is None or state is None:
            excluded.add(rel); continue
        physical_size = int(state[0][2]); required = physical_size * STAGE_SOURCE_PASSES
        if required > int(max_stage_source_bytes) - (source_read + temp_written + temp_read):
            excluded.add(rel); continue
        remaining_retained = int(max_staged_candidate_bytes) - retained
        candidate = None
        try:
            with tempfile.TemporaryDirectory(prefix="cmpct-hidden-vzip-") as td:
                snapshot = Path(td) / "candidate.zip"
                current, read = _snapshot_proven_source(source, proof, snapshot); source_read += read
                if not current:
                    excluded.add(rel); continue
                temp_written += physical_size
                try:
                    candidate = stage_vzip_recipe(snapshot, max_retained_bytes=max(0, remaining_retained))
                except STAGE_REJECTS:
                    candidate = None
                # Metadata peak-bound parser is one P and recipe construction is conservatively two P.
                temp_read += physical_size * 3
        except OSError:
            candidate = None
        if candidate is None:
            excluded.add(rel); continue
        cost = _retained_bytes(candidate)
        if cost > remaining_retained:
            excluded.add(rel); continue
        staged[rel] = candidate; retained += cost
    realized, credit = realized_reuse_fixed_point(
        proof.owner_identities, hidden_owners=hidden, fixed_owners=fixed,
        excluded_owners=excluded, min_verified_reuse=int(min_verified_reuse),
    )
    stable_hidden = set(realized) & hidden
    staged = {rel: recipe for rel, recipe in staged.items() if rel in stable_hidden}
    retained = sum(_retained_bytes(recipe) for recipe in staged.values())
    return StagedHiddenCohort(
        frozenset(realized), credit, staged, frozenset(excluded), int(retained), int(source_read),
        int(temp_written), int(temp_read),
    )


def commit_stable_hidden_cohort(builder, cohort: StagedHiddenCohort) -> dict[str, list]:
    storage: dict[str, list] = {}
    for rel in sorted(cohort.staged):
        recipe = commit_staged_vzip(cohort.staged[rel], builder.add_content)
        rid = len(builder.recipes); builder.recipes.append(recipe); storage[rel] = [S_VZIP, rid]
    return storage
