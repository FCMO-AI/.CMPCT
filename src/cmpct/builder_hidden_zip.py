from __future__ import annotations

"""Bridge canonical Builder storage outcomes into candidate-scoped hidden-ZIP proof."""

from dataclasses import dataclass
import hashlib
import os
from pathlib import Path

from .codec import CHUNK, K_FILE, S_BLOB, S_CDC, S_VZIP, cdc_chunks, sha
from .hidden_zip import MAX_OBSERVATION_FILES, MAX_OBSERVATION_IO_BYTES, MIN_VERIFIED_REUSE, _stamp
from .hidden_zip_candidates import CandidateOwnershipProof, Stamp, ZipOwnerSource, prove_candidate_zip_ownership
from .hidden_zip_stage import (
    MAX_STAGED_CANDIDATE_BYTES, MAX_STAGE_SOURCE_BYTES, STAGE_SOURCE_PASSES, StagedHiddenCohort,
    commit_stable_hidden_cohort, stage_stable_hidden_cohort,
)

EXPLICIT_SUFFIXES = frozenset((".zip", ".whl"))
MAX_HIDDEN_SURFACE_PHYSICAL_BYTES = min(MAX_STAGE_SOURCE_BYTES // STAGE_SOURCE_PASSES, MAX_STAGED_CANDIDATE_BYTES // 2)
MAX_HIDDEN_SURFACE_AGGREGATE_BYTES = MAX_OBSERVATION_IO_BYTES
FALLBACK_HASH_CHUNK = 1024 * 1024


@dataclass(frozen=True)
class SurfacedHiddenCandidate:
    rel: str
    path: Path
    stamp: Stamp
    digest: bytes


@dataclass(frozen=True)
class DeferredHiddenFile:
    candidate: SurfacedHiddenCandidate
    mode: int
    mtime_ns: int
    ext: str


def hidden_candidate_size_can_stage(size: int) -> bool:
    return 0 <= int(size) <= int(MAX_HIDDEN_SURFACE_PHYSICAL_BYTES)


def hidden_cohort_within_surface_budget(deferred) -> bool:
    if len(deferred) > MAX_OBSERVATION_FILES: return False
    total = 0
    for item in deferred:
        total += int(item.candidate.stamp[2])
        if total > MAX_HIDDEN_SURFACE_AGGREGATE_BYTES: return False
    return True


def surface_hidden_candidate(rel: str, path: Path, st, raw: bytes) -> SurfacedHiddenCandidate:
    if len(raw) != int(st.st_size): raise RuntimeError("hidden candidate changed while Builder was reading it")
    return SurfacedHiddenCandidate(str(rel), Path(path), _stamp(st), sha(raw))


def validate_surfaced_candidate(candidate: SurfacedHiddenCandidate) -> bool:
    expected_size = int(candidate.stamp[2]); digest = hashlib.sha256(); read = 0
    try:
        with candidate.path.open("rb") as fh:
            if _stamp(os.fstat(fh.fileno())) != candidate.stamp: return False
            while read < expected_size:
                block = fh.read(min(FALLBACK_HASH_CHUNK, expected_size - read))
                if not block: return False
                digest.update(block); read += len(block)
            if fh.read(1): return False
            if _stamp(os.fstat(fh.fileno())) != candidate.stamp: return False
    except OSError:return False
    return read == expected_size and digest.digest() == candidate.digest


def read_surfaced_candidate(candidate: SurfacedHiddenCandidate) -> bytes | None:
    expected_size = int(candidate.stamp[2])
    try:
        with candidate.path.open("rb") as fh:
            if _stamp(os.fstat(fh.fileno())) != candidate.stamp:return None
            raw = fh.read(expected_size)
            if len(raw) != expected_size or fh.read(1):return None
            if _stamp(os.fstat(fh.fileno())) != candidate.stamp:return None
    except OSError:return None
    return raw if sha(raw) == candidate.digest else None


def ordinary_storage_for_hidden_fallback(builder, raw: bytes, ext: str) -> list:
    if len(raw) > 4 * CHUNK and ext != ".wav":
        parts = cdc_chunks(raw); entries = [[len(part), builder.add_content(part, ext)] for part in parts]
        return [S_CDC, entries]
    return [S_BLOB, builder.add_content(raw, ext)]


def _append_fallback_row(builder, item: DeferredHiddenFile, raw: bytes) -> None:
    candidate = item.candidate; storage = ordinary_storage_for_hidden_fallback(builder, raw, item.ext)
    builder.files.append([candidate.rel, K_FILE, int(item.mode), int(item.mtime_ns), int(candidate.stamp[2]), candidate.digest, storage])


def finalize_hidden_fallback_only(builder, deferred) -> None:
    for item in deferred:
        raw = read_surfaced_candidate(item.candidate)
        if raw is None: raise RuntimeError(f"hidden candidate changed before ordinary fallback: {item.candidate.rel}")
        _append_fallback_row(builder, item, raw)


@dataclass(frozen=True)
class HiddenZipResolution:
    sources: tuple[ZipOwnerSource, ...]
    proof: CandidateOwnershipProof
    cohort: StagedHiddenCohort
    storage: dict[str, list]


def ownership_sources_from_builder(builder, hidden_candidates) -> tuple[ZipOwnerSource, ...]:
    if len(hidden_candidates) > MAX_OBSERVATION_FILES:return ()
    hidden_candidates = tuple(hidden_candidates); normalized: list[tuple[str, Path, Stamp | None, bytes | None]] = []
    for item in hidden_candidates:
        if isinstance(item, SurfacedHiddenCandidate):normalized.append((item.rel, item.path, item.stamp, item.digest))
        else:
            rel, path = item; normalized.append((rel, Path(path), None, None))
    if len({rel for rel, _path, _stamp, _digest in normalized}) != len(normalized):raise ValueError("hidden candidate rel paths must be unique")
    sources: list[ZipOwnerSource] = []
    for row in builder.files:
        rel, kind, _mode, _mtime, _size, digest, storage = row
        if kind != K_FILE or not storage or storage[0] != S_VZIP:continue
        if Path(rel).suffix.lower() not in EXPLICIT_SUFFIXES:continue
        sources.append(ZipOwnerSource(rel, Path(builder.root) / rel, fixed=True, expected_digest=bytes(digest)))
    fixed_rels = {source.rel for source in sources}
    for rel, path, stamp, digest in normalized:
        if rel in fixed_rels:raise ValueError("hidden candidate collides with a realized explicit owner")
        sources.append(ZipOwnerSource(rel, path, fixed=False, expected_stamp=stamp, expected_digest=digest))
    return tuple(sources)


def prepare_hidden_zip_candidates(builder, hidden_candidates, *, min_verified_reuse: int = MIN_VERIFIED_REUSE) -> HiddenZipResolution:
    sources = ownership_sources_from_builder(builder, hidden_candidates)
    proof = prove_candidate_zip_ownership(sources, min_verified_reuse=int(min_verified_reuse))
    cohort = stage_stable_hidden_cohort(proof, sources, min_verified_reuse=int(min_verified_reuse))
    return HiddenZipResolution(sources, proof, cohort, {})


def _retain_exact_streams_for_hidden_winners(builder, cohort: StagedHiddenCohort) -> None:
    """Keep exact Deflate only for streams bought by a realized hidden winner.

    The max-speed oracle showed that global exact-stream retention restores extraction/locality while
    giving back only ~36 KiB of the ~9.37 MiB Office gain. Applying that policy globally would silently
    change inherited encoder economics. Instead, realized hidden winners fund their own exact streams.
    ``Builder._prepare_deflate_reuse`` is monotone over preselected canonical/secondary maps, so these
    marks survive the normal 64 KiB compact-policy pass without changing unrelated content.
    """
    raw_refs: set[bytes] = set()
    for staged in cohort.staged.values():
        for _raw, _hint, stream, ref in staged.candidates:
            if stream is not None: raw_refs.add(bytes(ref))
    for rawref in sorted(raw_refs):
        candidate = builder.cands.get(rawref)
        if candidate is None or not candidate.deflates: continue
        chosen_hash, (_chosen_bytes, _chosen_count) = max(
            candidate.deflates.items(), key=lambda kv: (kv[1][1], -len(kv[1][0]))
        )
        builder.canonical_deflate[rawref] = chosen_hash
        for stream_hash, (stream, _count) in candidate.deflates.items():
            if stream_hash == chosen_hash: continue
            got = builder.add_content(stream, '.opaque-deflate')
            if got != stream_hash: raise ValueError("hidden exact-stream retention lost content identity")
            builder.secondary_stream_hashes.add(stream_hash)


def _commit_hidden_winners(builder, cohort: StagedHiddenCohort) -> dict[str, list]:
    storage = commit_stable_hidden_cohort(builder, cohort)
    _retain_exact_streams_for_hidden_winners(builder, cohort)
    return storage


def resolve_hidden_zip_candidates(builder, hidden_candidates, *, min_verified_reuse: int = MIN_VERIFIED_REUSE) -> HiddenZipResolution:
    prepared = prepare_hidden_zip_candidates(builder, hidden_candidates, min_verified_reuse=int(min_verified_reuse))
    storage = _commit_hidden_winners(builder, prepared.cohort)
    return HiddenZipResolution(prepared.sources, prepared.proof, prepared.cohort, storage)


def finalize_deferred_hidden_files(builder, deferred, *, min_verified_reuse: int = MIN_VERIFIED_REUSE) -> HiddenZipResolution:
    if not hidden_cohort_within_surface_budget(deferred):raise ValueError("hidden discovery cohort exceeds source/byte ceiling; use fallback-only path")
    deferred = tuple(deferred)
    prepared = prepare_hidden_zip_candidates(builder, [item.candidate for item in deferred], min_verified_reuse=int(min_verified_reuse))
    winner_rels = set(prepared.cohort.staged); losers = [item for item in deferred if item.candidate.rel not in winner_rels]
    for item in losers:
        if not validate_surfaced_candidate(item.candidate):raise RuntimeError(f"hidden candidate changed before ordinary fallback: {item.candidate.rel}")
    storage = _commit_hidden_winners(builder, prepared.cohort)
    for item in deferred:
        candidate = item.candidate; row_storage = storage.get(candidate.rel)
        if row_storage is None:
            raw = read_surfaced_candidate(candidate)
            if raw is None:raise RuntimeError(f"hidden candidate changed during ordinary fallback: {candidate.rel}")
            _append_fallback_row(builder, item, raw); continue
        builder.files.append([candidate.rel, K_FILE, int(item.mode), int(item.mtime_ns), int(candidate.stamp[2]), candidate.digest, row_storage])
    return HiddenZipResolution(prepared.sources, prepared.proof, prepared.cohort, storage)
