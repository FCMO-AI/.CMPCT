from __future__ import annotations

"""Bridge canonical Builder storage outcomes into candidate-scoped hidden-ZIP proof."""

from dataclasses import dataclass
from pathlib import Path

from .codec import K_FILE, S_VZIP
from .hidden_zip import MAX_OBSERVATION_FILES, MIN_VERIFIED_REUSE
from .hidden_zip_candidates import CandidateOwnershipProof, Stamp, ZipOwnerSource, prove_candidate_zip_ownership
from .hidden_zip_stage import StagedHiddenCohort, commit_stable_hidden_cohort, stage_stable_hidden_cohort

EXPLICIT_SUFFIXES = frozenset((".zip", ".whl"))


@dataclass(frozen=True)
class SurfacedHiddenCandidate:
    """Hidden candidate tied to the exact filesystem object Builder originally observed."""
    rel: str
    path: Path
    stamp: Stamp


@dataclass(frozen=True)
class HiddenZipResolution:
    """Decision-complete hidden-container result for the Builder integration seam."""
    sources: tuple[ZipOwnerSource, ...]
    proof: CandidateOwnershipProof
    cohort: StagedHiddenCohort
    storage: dict[str, list]


def ownership_sources_from_builder(
    builder,
    hidden_candidates: tuple[tuple[str, Path] | SurfacedHiddenCandidate, ...] | list[tuple[str, Path] | SurfacedHiddenCandidate],
) -> tuple[ZipOwnerSource, ...]:
    """Return exactly the physical owners allowed to participate in hidden reuse proof.

    The canonical Builder decision is authoritative. An explicit archive becomes fixed evidence
    only when its final scan row is an individual ``S_VZIP``. S_PACK members, fallback blobs and
    merely parseable ZIPs are absent by construction. Hidden candidates are supplied separately,
    so they cannot change the explicit ZIP/WHL cohort cardinality that chooses S_PACK.
    """
    if len(hidden_candidates) > MAX_OBSERVATION_FILES:
        return ()
    hidden_candidates = tuple(hidden_candidates)
    normalized: list[SurfacedHiddenCandidate] = []
    for item in hidden_candidates:
        if isinstance(item, SurfacedHiddenCandidate):
            normalized.append(item)
        else:
            rel, path = item
            # Compatibility for substrate tests/callers predating the canonical scan seam. Shipping
            # Builder integration must use SurfacedHiddenCandidate so scan identity is mandatory.
            normalized.append(SurfacedHiddenCandidate(rel, Path(path), None))  # type: ignore[arg-type]
    hidden_rels = {item.rel for item in normalized}
    if len(hidden_rels) != len(normalized):
        raise ValueError("hidden candidate rel paths must be unique")

    sources: list[ZipOwnerSource] = []
    for row in builder.files:
        rel, kind, _mode, _mtime, _size, _digest, storage = row
        if kind != K_FILE or not storage or storage[0] != S_VZIP:
            continue
        if Path(rel).suffix.lower() not in EXPLICIT_SUFFIXES:
            continue
        sources.append(ZipOwnerSource(rel, Path(builder.root) / rel, fixed=True))

    fixed_rels = {source.rel for source in sources}
    for item in normalized:
        if item.rel in fixed_rels:
            raise ValueError("hidden candidate collides with a realized explicit owner")
        sources.append(ZipOwnerSource(item.rel, item.path, fixed=False, expected_stamp=item.stamp))
    return tuple(sources)


def resolve_hidden_zip_candidates(
    builder,
    hidden_candidates: tuple[tuple[str, Path] | SurfacedHiddenCandidate, ...] | list[tuple[str, Path] | SurfacedHiddenCandidate],
    *,
    min_verified_reuse: int = MIN_VERIFIED_REUSE,
) -> HiddenZipResolution:
    """Resolve surfaced hidden candidates transactionally against actual Builder outcomes.

    This is deliberately downstream of canonical explicit ZIP/WHL resolution: S_PACK members and
    explicit fallbacks therefore cannot subsidize hidden admission. Proof and staging mutate no
    Builder candidate/recipe state. Only the final stable cohort crosses the commit boundary.

    Shipping Builder must supply ``SurfacedHiddenCandidate`` records so proof cannot switch to a
    replacement object between the scan read and deferred resolution. The caller still owns final
    file-table rows and exact ordinary fallback.
    """
    sources = ownership_sources_from_builder(builder, hidden_candidates)
    proof = prove_candidate_zip_ownership(sources, min_verified_reuse=int(min_verified_reuse))
    cohort = stage_stable_hidden_cohort(proof, sources, min_verified_reuse=int(min_verified_reuse))
    storage = commit_stable_hidden_cohort(builder, cohort)
    return HiddenZipResolution(sources, proof, cohort, storage)
