from __future__ import annotations

"""Transactional cohort staging after candidate-scoped hidden-ZIP ownership proof."""

from dataclasses import dataclass

from .hidden_zip_candidates import CandidateOwnershipProof, ZipOwnerSource
from .reuse_ownership import realized_reuse_fixed_point
from .vzip_transaction import StagedVzipRecipe, stage_vzip_recipe

MAX_STAGED_CANDIDATE_BYTES = 256 * 1024 * 1024


@dataclass(frozen=True)
class StagedHiddenCohort:
    """A stable hidden cohort whose recipes exist but have not touched Builder state."""

    realized: frozenset[str]
    credit: dict[str, int]
    staged: dict[str, StagedVzipRecipe]
    excluded: frozenset[str]
    retained_candidate_bytes: int


def _retained_bytes(staged: StagedVzipRecipe) -> int:
    # Count the bytes actually retained by transactional staging. Raw member bytes and an
    # exact Deflate stream can coexist in one staged candidate, so charge both rather than
    # pretending the logical member size is the memory footprint.
    return sum(len(raw) + (0 if stream is None else len(stream)) for raw, _hint, stream, _ref in staged.candidates)


def stage_stable_hidden_cohort(
    proof: CandidateOwnershipProof,
    sources: tuple[ZipOwnerSource, ...] | list[ZipOwnerSource],
    *,
    min_verified_reuse: int,
    max_staged_candidate_bytes: int = MAX_STAGED_CANDIDATE_BYTES,
) -> StagedHiddenCohort:
    """Stage tentative hidden winners, then peel any owner that cannot materialize.

    No real ``Builder.add_content`` call occurs here. A stage failure or aggregate retained-memory
    refusal becomes an excluded hidden owner and the already-proven ownership graph is solved again.
    Recipes staged for owners removed by that cascade are simply discarded. The caller may commit
    only the returned ``staged`` mapping after independently revalidating source identity.
    """

    source_by_rel = {source.rel: source for source in sources}
    if len(source_by_rel) != len(tuple(sources)):
        raise ValueError("candidate owner rel paths must be unique")
    fixed = {rel for rel, source in source_by_rel.items() if source.fixed and rel in proof.owner_identities}
    hidden = set(proof.owner_identities) - fixed
    initially_realized_hidden = set(proof.realized) & hidden

    staged: dict[str, StagedVzipRecipe] = {}
    excluded: set[str] = set()
    retained = 0
    for rel in sorted(initially_realized_hidden):
        source = source_by_rel.get(rel)
        if source is None:
            excluded.add(rel)
            continue
        candidate = stage_vzip_recipe(source.path)
        if candidate is None:
            excluded.add(rel)
            continue
        cost = _retained_bytes(candidate)
        if cost > int(max_staged_candidate_bytes) - retained:
            excluded.add(rel)
            continue
        staged[rel] = candidate
        retained += cost

    realized, credit = realized_reuse_fixed_point(
        proof.owner_identities,
        hidden_owners=hidden,
        fixed_owners=fixed,
        excluded_owners=excluded,
        min_verified_reuse=int(min_verified_reuse),
    )
    stable_hidden = set(realized) & hidden
    staged = {rel: recipe for rel, recipe in staged.items() if rel in stable_hidden}
    retained = sum(_retained_bytes(recipe) for recipe in staged.values())

    return StagedHiddenCohort(
        frozenset(realized),
        credit,
        staged,
        frozenset(excluded),
        int(retained),
    )
