from __future__ import annotations

"""Bridge canonical Builder storage outcomes into candidate-scoped hidden-ZIP proof."""

from dataclasses import dataclass
import os
from pathlib import Path

from .codec import CHUNK, K_FILE, S_BLOB, S_CDC, S_VZIP, cdc_chunks, sha
from .hidden_zip import MAX_OBSERVATION_FILES, MIN_VERIFIED_REUSE, _stamp
from .hidden_zip_candidates import CandidateOwnershipProof, Stamp, ZipOwnerSource, prove_candidate_zip_ownership
from .hidden_zip_stage import (
    MAX_STAGED_CANDIDATE_BYTES, MAX_STAGE_SOURCE_BYTES, StagedHiddenCohort,
    commit_stable_hidden_cohort, stage_stable_hidden_cohort,
)

EXPLICIT_SUFFIXES = frozenset((".zip", ".whl"))
MAX_HIDDEN_SURFACE_PHYSICAL_BYTES = min(MAX_STAGE_SOURCE_BYTES // 4, MAX_STAGED_CANDIDATE_BYTES // 2)


@dataclass(frozen=True)
class SurfacedHiddenCandidate:
    """Hidden candidate tied to the exact filesystem object and bytes Builder observed."""
    rel: str
    path: Path
    stamp: Stamp
    digest: bytes


@dataclass(frozen=True)
class DeferredHiddenFile:
    """File-table metadata retained while a surfaced hidden candidate awaits cohort resolution."""
    candidate: SurfacedHiddenCandidate
    mode: int
    mtime_ns: int
    ext: str


def hidden_candidate_size_can_stage(size: int) -> bool:
    """Cheap impossibility filter derived only from downstream hard resource contracts."""
    return 0 <= int(size) <= int(MAX_HIDDEN_SURFACE_PHYSICAL_BYTES)


def surface_hidden_candidate(rel: str, path: Path, st, raw: bytes) -> SurfacedHiddenCandidate:
    """Bind a Builder-read hidden candidate to the exact scan snapshot without rereading it."""
    if len(raw) != int(st.st_size):
        raise RuntimeError("hidden candidate changed while Builder was reading it")
    return SurfacedHiddenCandidate(str(rel), Path(path), _stamp(st), sha(raw))


def read_surfaced_candidate(candidate: SurfacedHiddenCandidate) -> bytes | None:
    """Return fallback bytes only if the exact Builder-surfaced source object is still present."""
    expected_size = int(candidate.stamp[2])
    try:
        with candidate.path.open("rb") as fh:
            if _stamp(os.fstat(fh.fileno())) != candidate.stamp: return None
            raw = fh.read(expected_size)
            if len(raw) != expected_size: return None
            if _stamp(os.fstat(fh.fileno())) != candidate.stamp: return None
    except OSError:
        return None
    return raw if sha(raw) == candidate.digest else None


def ordinary_storage_for_hidden_fallback(builder, raw: bytes, ext: str) -> list:
    """Apply Builder's inherited ordinary BLOB/CDC policy only to rejected hidden candidates."""
    if len(raw) > 4 * CHUNK and ext != ".wav":
        parts = cdc_chunks(raw)
        entries = [[len(part), builder.add_content(part, ext)] for part in parts]
        return [S_CDC, entries]
    return [S_BLOB, builder.add_content(raw, ext)]


@dataclass(frozen=True)
class HiddenZipResolution:
    sources: tuple[ZipOwnerSource, ...]
    proof: CandidateOwnershipProof
    cohort: StagedHiddenCohort
    storage: dict[str, list]


def ownership_sources_from_builder(
    builder,
    hidden_candidates: tuple[tuple[str, Path] | SurfacedHiddenCandidate, ...] | list[tuple[str, Path] | SurfacedHiddenCandidate],
) -> tuple[ZipOwnerSource, ...]:
    """Return only owners allowed to participate in hidden reuse proof."""
    if len(hidden_candidates) > MAX_OBSERVATION_FILES: return ()
    hidden_candidates = tuple(hidden_candidates); normalized: list[tuple[str, Path, Stamp | None, bytes | None]] = []
    for item in hidden_candidates:
        if isinstance(item, SurfacedHiddenCandidate): normalized.append((item.rel, item.path, item.stamp, item.digest))
        else:
            rel, path = item; normalized.append((rel, Path(path), None, None))
    if len({rel for rel, _path, _stamp, _digest in normalized}) != len(normalized): raise ValueError("hidden candidate rel paths must be unique")

    sources: list[ZipOwnerSource] = []
    for row in builder.files:
        rel, kind, _mode, _mtime, _size, digest, storage = row
        if kind != K_FILE or not storage or storage[0] != S_VZIP: continue
        if Path(rel).suffix.lower() not in EXPLICIT_SUFFIXES: continue
        sources.append(ZipOwnerSource(rel, Path(builder.root) / rel, fixed=True, expected_digest=bytes(digest)))

    fixed_rels = {source.rel for source in sources}
    for rel, path, stamp, digest in normalized:
        if rel in fixed_rels: raise ValueError("hidden candidate collides with a realized explicit owner")
        sources.append(ZipOwnerSource(rel, path, fixed=False, expected_stamp=stamp, expected_digest=digest))
    return tuple(sources)


def resolve_hidden_zip_candidates(
    builder,
    hidden_candidates: tuple[tuple[str, Path] | SurfacedHiddenCandidate, ...] | list[tuple[str, Path] | SurfacedHiddenCandidate],
    *, min_verified_reuse: int = MIN_VERIFIED_REUSE,
) -> HiddenZipResolution:
    """Resolve surfaced hidden candidates transactionally against actual Builder outcomes."""
    sources = ownership_sources_from_builder(builder, hidden_candidates)
    proof = prove_candidate_zip_ownership(sources, min_verified_reuse=int(min_verified_reuse))
    cohort = stage_stable_hidden_cohort(proof, sources, min_verified_reuse=int(min_verified_reuse))
    storage = commit_stable_hidden_cohort(builder, cohort)
    return HiddenZipResolution(sources, proof, cohort, storage)


def finalize_deferred_hidden_files(
    builder, deferred: tuple[DeferredHiddenFile, ...] | list[DeferredHiddenFile], *,
    min_verified_reuse: int = MIN_VERIFIED_REUSE,
) -> HiddenZipResolution:
    """Resolve a bounded hidden cohort and append exact file rows for winners and ordinary losers.

    This is the transaction boundary canonical ``Builder.scan`` should call after explicit ZIP/WHL
    resolution. It owns neither traversal nor explicit cohort selection. A fallback reread must match
    the surfaced object+digest; drift aborts rather than emitting old metadata for new bytes.
    """
    deferred = tuple(deferred)
    resolution = resolve_hidden_zip_candidates(
        builder, [item.candidate for item in deferred], min_verified_reuse=int(min_verified_reuse)
    )
    for item in deferred:
        candidate = item.candidate
        storage = resolution.storage.get(candidate.rel)
        if storage is None:
            raw = read_surfaced_candidate(candidate)
            if raw is None:
                raise RuntimeError(f"hidden candidate changed before ordinary fallback: {candidate.rel}")
            storage = ordinary_storage_for_hidden_fallback(builder, raw, item.ext)
        builder.files.append([
            candidate.rel, K_FILE, int(item.mode), int(item.mtime_ns), int(candidate.stamp[2]),
            candidate.digest, storage,
        ])
    return resolution
