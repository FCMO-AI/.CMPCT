from __future__ import annotations

"""Transactional staging for speculative VZIP recipe construction."""

from pathlib import Path
from typing import Callable

from .codec import make_vzip_recipe, sha


def make_vzip_recipe_transactional(path: Path, add_content: Callable):
    """Build a recipe without mutating the real candidate store until success.

    ``make_vzip_recipe`` discovers exact member streams incrementally and can reject a later
    member after earlier ``add_content`` calls. Hidden-ZIP admission is speculative, so those
    calls are staged as immutable bytes and replayed only after the whole recipe succeeds.
    The returned references are content hashes, so staging preserves recipe identity.
    """
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

    for raw, hint, stream, expected in staged:
        got = add_content(raw, hint, stream)
        if got != expected:
            raise ValueError("transactional VZIP add_content returned a non-content-addressed reference")
    return recipe
