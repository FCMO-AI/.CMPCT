from __future__ import annotations

"""Transactional cohort staging after candidate-scoped hidden-ZIP ownership proof."""

from dataclasses import dataclass

from .codec import S_VZIP
from .hidden_zip import _file_sha256_expected, _stamp
from .hidden_zip_candidates import CandidateOwnershipProof, ZipOwnerSource
from .reuse_ownership import realized_reuse_fixed_point
from .vzip_transaction import StagedVzipRecipe, commit_staged_vzip, stage_vzip_recipe

MAX_STAGED_CANDIDATE_BYTES = 256 * 1024 * 1024
MAX_STAGE_SOURCE_BYTES = 256 * 1024 * 1024


@dataclass(frozen=True)
class StagedHiddenCohort:
    realized: frozenset[str]
    credit: dict[str, int]
    staged: dict[str, StagedVzipRecipe]
    excluded: frozenset[str]
    retained_candidate_bytes: int
    source_bytes_read: int


def _retained_bytes(staged: StagedVzipRecipe) -> int:
    return sum(len(raw) + (0 if stream is None else len(stream)) for raw, _hint, stream, _ref in staged.candidates)


def _source_current(source: ZipOwnerSource, proof: CandidateOwnershipProof) -> tuple[bool, int]:
    state = proof.source_states.get(source.rel)
    if state is None: return False, 0
    expected_stamp, expected_digest = state
    try: st = source.path.stat(); size = int(st.st_size)
    except OSError: return False, 0
    if _stamp(st) != expected_stamp: return False, 0
    digest = _file_sha256_expected(source.path, expected_stamp)
    return digest == expected_digest, size


def stage_stable_hidden_cohort(
    proof: CandidateOwnershipProof, sources: tuple[ZipOwnerSource, ...] | list[ZipOwnerSource], *,
    min_verified_reuse: int, max_staged_candidate_bytes: int = MAX_STAGED_CANDIDATE_BYTES,
    max_stage_source_bytes: int = MAX_STAGE_SOURCE_BYTES,
) -> StagedHiddenCohort:
    """Stage hidden winners without mutating Builder, then peel failures to stability.

    Proven source content is checked before and after recipe construction. Both hashes plus one
    conservative file-size charge for staging share a finite source-I/O account; retained raw and
    exact-stream bytes have a separate memory ceiling.
    """
    sources = tuple(sources); source_by_rel = {source.rel: source for source in sources}
    if len(source_by_rel) != len(sources): raise ValueError("candidate owner rel paths must be unique")
    fixed = {rel for rel, source in source_by_rel.items() if source.fixed and rel in proof.owner_identities}
    hidden = set(proof.owner_identities) - fixed
    initially_realized_hidden = set(proof.realized) & hidden
    staged: dict[str, StagedVzipRecipe] = {}; excluded: set[str] = set(); retained = source_read = 0
    for rel in sorted(initially_realized_hidden):
        source = source_by_rel.get(rel); state = proof.source_states.get(rel)
        if source is None or state is None:
            excluded.add(rel); continue
        physical_size = int(state[0][2]); required = physical_size * 3
        if required > int(max_stage_source_bytes) - source_read:
            excluded.add(rel); continue
        current, read = _source_current(source, proof); source_read += read
        if not current:
            excluded.add(rel); continue
        candidate = stage_vzip_recipe(source.path); source_read += physical_size
        if candidate is None:
            excluded.add(rel); continue
        current, read = _source_current(source, proof); source_read += read
        if not current:
            excluded.add(rel); continue
        cost = _retained_bytes(candidate)
        if cost > int(max_staged_candidate_bytes) - retained:
            excluded.add(rel); continue
        staged[rel] = candidate; retained += cost
    realized, credit = realized_reuse_fixed_point(
        proof.owner_identities, hidden_owners=hidden, fixed_owners=fixed,
        excluded_owners=excluded, min_verified_reuse=int(min_verified_reuse),
    )
    stable_hidden = set(realized) & hidden
    staged = {rel: recipe for rel, recipe in staged.items() if rel in stable_hidden}
    retained = sum(_retained_bytes(recipe) for recipe in staged.values())
    return StagedHiddenCohort(frozenset(realized), credit, staged, frozenset(excluded), int(retained), int(source_read))


def commit_stable_hidden_cohort(builder, cohort: StagedHiddenCohort) -> dict[str, list]:
    """Commit only a fully staged stable cohort and return each hidden file's storage recipe.

    This function intentionally does not append file-table rows. Canonical Builder retains ownership
    of filesystem metadata and fallback policy; the bridge only materializes content candidates and
    recipe ids after the economic/staging decision is final.
    """
    storage: dict[str, list] = {}
    for rel in sorted(cohort.staged):
        recipe = commit_staged_vzip(cohort.staged[rel], builder.add_content)
        rid = len(builder.recipes); builder.recipes.append(recipe)
        storage[rel] = [S_VZIP, rid]
    return storage
