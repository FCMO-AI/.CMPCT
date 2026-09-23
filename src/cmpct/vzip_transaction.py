from __future__ import annotations

"""Transactional staging for speculative VZIP recipe construction."""

from dataclasses import dataclass
from pathlib import Path
from typing import Callable
import zipfile

from .codec import make_vzip_recipe, sha


@dataclass(frozen=True)
class StagedVzipRecipe:
    recipe: object
    candidates: tuple[tuple[bytes, str, bytes | None, bytes], ...]


def _staging_peak_upper_bound(path: Path) -> int | None:
    """Conservatively bound recipe-construction bytes before decoded members are allocated.

    ``make_vzip_recipe`` first retains the complete original container. Its final staged candidates
    then retain every decoded member plus exact compressed streams and a skeleton; streams+skeleton
    are disjoint slices whose total is at most one additional container size. During construction the
    original coexists with those staged bytes, so ``2*container_size + sum(member.file_size)`` bounds
    this transaction's dominant byte buffers. The estimate intentionally overcharges rather than
    calling a post-stage retained-state limit a peak-memory limit.
    """
    try:
        physical = int(path.stat().st_size)
        with zipfile.ZipFile(path) as z:
            logical = sum(int(info.file_size) for info in z.infolist() if not info.is_dir())
    except (OSError, ValueError, RuntimeError, zipfile.BadZipFile):
        return None
    return physical * 2 + logical


def stage_vzip_recipe(path: Path, *, max_retained_bytes: int | None = None) -> StagedVzipRecipe | None:
    """Build a complete recipe and candidate set without mutating Builder state.

    Cohort admission may depend on several containers all materializing. Keeping staging and
    commit separate lets the caller prove every admitted recipe first, then commit the cohort
    atomically at the decision level instead of leaving a half-realized economic proof.

    When ``max_retained_bytes`` is supplied, reject from central-directory metadata before
    ``make_vzip_recipe`` can allocate decoded member bytes. The bound covers the original container
    coexisting with staged raw/stream/skeleton buffers, not merely steady retained state after return.
    """
    if max_retained_bytes is not None:
        bound = _staging_peak_upper_bound(Path(path))
        if bound is None or bound > int(max_retained_bytes):
            return None

    staged: list[tuple[bytes, str, bytes | None, bytes]] = []

    def stage(raw: bytes, hint: str = "", deflate_stream: bytes | None = None):
        raw = bytes(raw)
        stream = None if deflate_stream is None else bytes(deflate_stream)
        ref = sha(raw)
        staged.append((raw, hint, stream, ref))
        return ref

    recipe = make_vzip_recipe(Path(path), stage)
    if recipe is None:
        return None
    return StagedVzipRecipe(recipe, tuple(staged))


def commit_staged_vzip(staged: StagedVzipRecipe, add_content: Callable):
    """Replay a previously complete stage into the real content-addressed candidate store."""
    for raw, hint, stream, expected in staged.candidates:
        got = add_content(raw, hint, stream)
        if got != expected:
            raise ValueError("transactional VZIP add_content returned a non-content-addressed reference")
    return staged.recipe


def make_vzip_recipe_transactional(path: Path, add_content: Callable):
    """Convenience wrapper for one recipe; cohort callers should stage all before any commit."""
    staged = stage_vzip_recipe(path)
    if staged is None:
        return None
    return commit_staged_vzip(staged, add_content)
