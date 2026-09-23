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
    """Conservatively bound dominant recipe-construction byte buffers before allocation.

    ``make_vzip_recipe`` can simultaneously hold: the original container (P), a mutable skeleton
    copy (P), the immutable skeleton bytes passed to staging (P), exact compressed streams whose
    aggregate is at most P, and decoded member payloads (L). Therefore ``4*P + L`` is the relevant
    conservative peak bound for this implementation, not the smaller steady retained state after the
    original/skeleton temporaries leave scope.
    """
    try:
        physical = int(path.stat().st_size)
        with zipfile.ZipFile(path) as z:
            logical = sum(int(info.file_size) for info in z.infolist() if not info.is_dir())
    except (OSError, ValueError, RuntimeError, zipfile.BadZipFile):
        return None
    return physical * 4 + logical


def stage_vzip_recipe(path: Path, *, max_retained_bytes: int | None = None) -> StagedVzipRecipe | None:
    """Build a complete recipe/candidate set without mutating Builder state.

    ``max_retained_bytes`` is a peak staging-memory ceiling despite the historical parameter name.
    Refusal happens from central-directory metadata before ``make_vzip_recipe`` can allocate decoded
    member/skeleton buffers; a separate post-stage check remains at the cohort layer.
    """
    if max_retained_bytes is not None:
        bound = _staging_peak_upper_bound(Path(path))
        if bound is None or bound > int(max_retained_bytes): return None
    staged: list[tuple[bytes, str, bytes | None, bytes]] = []
    def stage(raw: bytes, hint: str = "", deflate_stream: bytes | None = None):
        raw = bytes(raw); stream = None if deflate_stream is None else bytes(deflate_stream); ref = sha(raw)
        staged.append((raw, hint, stream, ref)); return ref
    recipe = make_vzip_recipe(Path(path), stage)
    if recipe is None:return None
    return StagedVzipRecipe(recipe, tuple(staged))


def commit_staged_vzip(staged: StagedVzipRecipe, add_content: Callable):
    for raw, hint, stream, expected in staged.candidates:
        got = add_content(raw, hint, stream)
        if got != expected:raise ValueError("transactional VZIP add_content returned a non-content-addressed reference")
    return staged.recipe


def make_vzip_recipe_transactional(path: Path, add_content: Callable):
    staged = stage_vzip_recipe(path)
    if staged is None:return None
    return commit_staged_vzip(staged, add_content)
