"""CMPCT v0.30 authoritative release facade.

This is the promotion-facing binding layer.  It composes only previously isolated, independently testable
components and keeps the research implementations available unchanged for causal ablation:

- shared v0.28/attempt-5 construction + G0-G4 Geometry from ``entropygraph_v030_shared_portfolio``;
- exact complete-artifact selector from ``entropygraph_v030_release_candidate``;
- strict streamed reader policy from ``entropygraph_v030_release_reader_policy``;
- metadata-only / memory-bounded PrefixGraph admission from ``entropygraph_v030_release_admission``.

The selector resolves these globals at runtime.  Binding them here changes release scheduling/resource policy,
not archive grammar.  Complete-byte identity and broad no-regression gates remain mandatory.

Footnote: keeping this final binding in a small facade is deliberate multi-agent hygiene.  Parallel research
branches can continue to evolve their mechanisms without silently changing the version under promotion; only
an explicit import/binding change here can alter the authoritative candidate.
"""
from __future__ import annotations

from pathlib import Path

from experiments import entropygraph_v030_release_candidate as RC
from experiments import entropygraph_v030_release_reader_policy as READER
from experiments import entropygraph_v030_release_admission as ADMISSION
from experiments import entropygraph_v030_shared_portfolio as G04

# Explicit promotion bindings.  These assignments are intentionally visible rather than hidden in import side
# effects so reviewers can audit exactly which implementation owns each release responsibility.
RC.G04 = G04
RC._prefixgraph_eligibility = ADMISSION.prefixgraph_eligibility
RC._prefixgraph_locality = ADMISSION.prefixgraph_locality

MAX_MEMBER_READ_AMP = RC.MAX_MEMBER_READ_AMP


def build(root: Path, out: Path) -> dict:
    stats = dict(RC.build(root, out))
    g04 = stats.get("g04") or {}
    stats.update(
        {
            "release_facade": "cmpct-v030-authoritative-v2",
            "g04_shared_analysis_mode": g04.get("shared_analysis_mode"),
            "g04_attempt5_graph_build_count": g04.get("attempt5_graph_build_count"),
            "g04_publication_identity_check": g04.get("publication_identity_check"),
            "prefixgraph_admission": "metadata-only-locality+256MiB-encoder-family-ceiling",
        }
    )
    return stats


def strong_verify(archive: Path) -> dict:
    return RC.strong_verify(archive)


def extract(archive: Path, dst: Path, *, max_output_bytes: int = READER.DEFAULT_MAX_EXTRACT_BYTES) -> None:
    RC.extract(archive, dst, max_output_bytes=max_output_bytes)


def treehash(root: Path) -> str:
    return RC.treehash(root)
