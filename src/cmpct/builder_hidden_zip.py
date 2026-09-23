from __future__ import annotations

"""Bridge canonical Builder storage outcomes into candidate-scoped hidden-ZIP proof."""

from dataclasses import dataclass
from pathlib import Path

from .codec import K_FILE, S_VZIP
from .hidden_zip import MAX_OBSERVATION_FILES, MIN_VERIFIED_REUSE
from .hidden_zip_candidates import CandidateOwnershipProof, ZipOwnerSource, prove_candidate_zip_ownership
from .hidden_zip_stage import StagedHiddenCohort, commit_stable_hidden_cohort, stage_stable_hidden_cohort

EXPLICIT_SUFFIXES = frozenset((".zip", ".whl"))


@dataclass(frozen=True)
class HiddenZipResolution:
    """Decision-complete hidden-container result for the Builder integration seam."""
    sources: tuple[ZipOwnerSource, ...]
    proof: CandidateOwnershipProof
    cohort: StagedHiddenCohort
    storage: dict[str, list]


def ownership_sources_from_builder(
    builder,
    hidden_candidates: tuple[tuple[str, Path], ...] | list[tuple[str, Path]],
) -> tuple[ZipOwnerSource, ...]:
    """Return exactly the physical owners allowed to participate in hidden reuse proof.

    The canonical Builder decision is authoritative. An explicit archive becomes fixed evidence
    only when its final scan row is an individual ``S_VZIP``. S_PACK members, fallback blobs and
    merely parseable ZIPs are absent by construction. Hidden candidates are supplied separately,
    so they cannot change the explicit ZIP/WHL cohort cardinality that chooses S_PACK.
    """
    # Builder will eventually enforce this while surfacing candidates, but keep the bridge itself
    # fail-closed: a hostile caller must not trigger another tuple/set allocation before proof limits.
    if len(hidden_candidates) > MAX_OBSERVATION_FILES:
        return ()
    hidden_candidates = tuple(hidden_candidates)
    hidden_rels = {rel for rel, _path in hidden_candidates}
    if len(hidden_rels) != len(hidden_candidates):
        raise ValueError("hidden candidate rel paths must be unique")

    sources: list[ZipOwnerSource] = []
    for row in builder.files:
        rel, kind, _mode, _mtime, _size, _digest, storage = row
        if kind != K_FILE or not storage or storage[0] != S_VZIP:
            continue
        if Path(rel).suffix.lower() not in EXPLICIT_SUFFIXES:
            continue
        # Explicit rows come from Builder's own deferred cohort. Reconstruct the source path
        # from canonical root + logical rel rather than accepting a second caller-owned path.
        sources.append(ZipOwnerSource(rel, Path(builder.root) / rel, fixed=True))

    fixed_rels = {source.rel for source in sources}
    for rel, path in hidden_candidates:
        if rel in fixed_rels:
            raise ValueError("hidden candidate collides with a realized explicit owner")
        sources.append(ZipOwnerSource(rel, Path(path), fixed=False))
    return tuple(sources)


def resolve_hidden_zip_candidates(
    builder,
    hidden_candidates: tuple[tuple[str, Path], ...] | list[tuple[str, Path]],
    *,
    min_verified_reuse: int = MIN_VERIFIED_REUSE,
) -> HiddenZipResolution:
    """Resolve surfaced hidden candidates transactionally against actual Builder outcomes.

    This is deliberately downstream of canonical explicit ZIP/WHL resolution: S_PACK members and
    explicit fallbacks therefore cannot subsidize hidden admission. Proof and staging mutate no
    Builder candidate/recipe state. Only the final stable cohort crosses the commit boundary.

    The caller still owns file-table rows and ordinary fallback. In particular, canonical
    ``Builder.scan`` must surface hidden candidates before ordinary BLOB/CDC storage so a rejected
    hidden candidate can take exactly the inherited ordinary path without leaving speculative
    candidates behind.
    """
    sources = ownership_sources_from_builder(builder, hidden_candidates)
    proof = prove_candidate_zip_ownership(sources, min_verified_reuse=int(min_verified_reuse))
    cohort = stage_stable_hidden_cohort(proof, sources, min_verified_reuse=int(min_verified_reuse))
    storage = commit_stable_hidden_cohort(builder, cohort)
    return HiddenZipResolution(sources, proof, cohort, storage)
