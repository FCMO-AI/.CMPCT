"""CMPCT v0.30 authoritative integration facade.

This module binds the system tournament to the release-rehabilitated G0-G4 builder without rewriting the
research selector.  The distinction is intentional:

- ``entropygraph_v030_release_candidate`` remains the exact system-tournament implementation and causal test
  surface;
- ``entropygraph_v030_geometry_overlay_g04_publish`` removes archive-sized publication RAM copies while
  preserving G0-G4 bytes;
- this facade makes that rehabilitated builder the implementation used by authoritative generalization,
  performance and eventual release surfaces.

Footnote: the selector resolves its ``G04`` global at call time, so assigning the byte-compatible wrapper here
changes build resource behavior but not the grammar/read path.  If exact-byte identity tests ever show a
difference between research and rehabilitated G0-G4 builders, this facade must fail promotion rather than hide
that mismatch.
"""
from __future__ import annotations

from pathlib import Path

from experiments import entropygraph_v030_geometry_overlay_g04_publish as G04
from experiments import entropygraph_v030_release_candidate as RC
from experiments import entropygraph_v030_release_reader_policy as READER

# Bind the selector to the release-path builder. All other selector behavior remains single-sourced in RC.
RC.G04 = G04

MAX_MEMBER_READ_AMP = RC.MAX_MEMBER_READ_AMP


def build(root: Path, out: Path) -> dict:
    stats = RC.build(root, out)
    stats = dict(stats)
    stats["release_facade"] = "cmpct-v030-authoritative-integration-v1"
    g04 = stats.get("g04") or {}
    stats["g04_publication_identity_check"] = g04.get("publication_identity_check")
    return stats


def strong_verify(archive: Path) -> dict:
    return RC.strong_verify(archive)


def extract(archive: Path, dst: Path, *, max_output_bytes: int = READER.DEFAULT_MAX_EXTRACT_BYTES) -> None:
    RC.extract(archive, dst, max_output_bytes=max_output_bytes)


def treehash(root: Path) -> str:
    return RC.treehash(root)
