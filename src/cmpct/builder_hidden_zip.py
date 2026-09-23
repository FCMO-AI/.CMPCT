from __future__ import annotations

"""Bridge canonical Builder storage outcomes into candidate-scoped hidden-ZIP proof."""

from pathlib import Path

from .codec import K_FILE, S_VZIP
from .hidden_zip_candidates import ZipOwnerSource

EXPLICIT_SUFFIXES = frozenset((".zip", ".whl"))


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

    for rel, path in hidden_candidates:
        if rel in {source.rel for source in sources}:
            raise ValueError("hidden candidate collides with a realized explicit owner")
        sources.append(ZipOwnerSource(rel, Path(path), fixed=False))
    return tuple(sources)
