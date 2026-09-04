"""CMPCT v0.30 authoritative integration facade.

This module binds the system tournament to the release-rehabilitated G0-G4 builder without rewriting the
research selector. The distinction is intentional:

- ``entropygraph_v030_release_candidate`` remains the exact system-tournament implementation and causal test
  surface;
- ``entropygraph_v030_shared_portfolio`` constructs v0.28 + attempt-5 exactly once, retains the graph for
  Geometry, preserves accepted-v0.29 floor semantics, and uses bounded streamed publication identity checks;
- ``entropygraph_v030_discovery_neutral_worker`` is the accepted generic R3 worker provider: it removes the
  transfer-proven byte-dead position-independent candidate source only inside spawned attempt-5 children while
  leaving historical v0.29 modules untouched;
- this facade makes that shared, byte-compatible builder and accepted R3 worker the implementation used by
  authoritative generalization, performance and eventual release surfaces.

Footnote: the selector resolves its ``G04`` global at call time, so assigning the byte-compatible wrapper here
changes scheduling/resource behavior but not the grammar/read path. Likewise the shared builder resolves its
``V029_SCHED`` provider at call time and uses only ``CHILD_RESULT_TIMEOUT_S``, ``ACCEPTED_ENGINE`` and ``_worker``;
binding that private provider to the accepted R3 module changes child discovery work without mutating the
historical scheduler module. Complete-byte identity tests against the older duplicated builder remain mandatory;
if they ever differ, the shared scheduler or R3 promotion is invalid and promotion must fail rather than hiding
the mismatch.
"""
from __future__ import annotations

from pathlib import Path

from experiments import entropygraph_v030_discovery_neutral_worker as R3_WORKER
from experiments import entropygraph_v030_shared_portfolio as G04
from experiments import entropygraph_v030_release_candidate as RC
from experiments import entropygraph_v030_release_reader_policy as READER

# Bind the selector to the shared release-path builder. All tournament/read behavior remains single-sourced.
RC.G04 = G04

# Productize the accepted generic R3 discovery neutralization without mutating historical v0.29 state.  The
# shared builder intentionally consumes the same three worker-provider attributes exported by R3_WORKER.
G04.V029_SCHED = R3_WORKER
G04.CHILD_RESULT_TIMEOUT_S = R3_WORKER.CHILD_RESULT_TIMEOUT_S

MAX_MEMBER_READ_AMP = RC.MAX_MEMBER_READ_AMP


def build(root: Path, out: Path) -> dict:
    stats = dict(RC.build(root, out))
    stats["release_facade"] = "cmpct-v030-authoritative-integration-v1"
    g04 = stats.get("g04") or {}
    stats["g04_publication_identity_check"] = g04.get("publication_identity_check")
    stats["g04_shared_analysis_mode"] = g04.get("shared_analysis_mode")
    stats["g04_attempt5_graph_build_count"] = g04.get("attempt5_graph_build_count")
    stats["g04_attempt5_worker_provider"] = "v030-generic-r3-discovery-neutral"
    return stats


def strong_verify(archive: Path) -> dict:
    return RC.strong_verify(archive)


def extract(archive: Path, dst: Path, *, max_output_bytes: int = READER.DEFAULT_MAX_EXTRACT_BYTES) -> None:
    RC.extract(archive, dst, max_output_bytes=max_output_bytes)


def treehash(root: Path) -> str:
    return RC.treehash(root)
