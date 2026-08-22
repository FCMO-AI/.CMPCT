"""Historical CMPCT v0.30 convergence facade — retained for research/ablation compatibility.

This module used to be the promotion-facing binding layer while v0.30 mechanisms were still converging. T03
productization moved the actual canonical API/format boundary to ``entropygraph_v030_canonical`` because a
product archive must additionally distinguish real r24 from ``CMPNX*`` research fallbacks and preserve full
filesystem semantics through the authenticated revision-25 manifest.

The facade remains useful for old benchmark scripts and exact causal ablations. It still composes:

- shared v0.28/attempt-5 construction + G0-G4 Geometry from ``entropygraph_v030_shared_portfolio``;
- exact complete-artifact selector from ``entropygraph_v030_release_candidate``;
- strict streamed reader policy from ``entropygraph_v030_release_reader_policy``;
- metadata-only / memory-bounded PrefixGraph admission from ``entropygraph_v030_release_admission``.

It is **not** a canonical r24/r25 product entrypoint and may emit inherited ``CMPNX*`` research bytes. New
product callers must import ``entropygraph_v030_canonical`` instead.

Footnote: retaining this small adapter avoids rewriting historical benchmarks merely to reflect ownership
cleanup. Demotion is safer than deletion: causal evidence stays reproducible while the promoted path no longer
has two different modules both claiming to be authoritative.
"""
from __future__ import annotations

from pathlib import Path

from experiments import entropygraph_v030_release_candidate as RC
from experiments import entropygraph_v030_release_reader_policy as READER
from experiments import entropygraph_v030_release_admission as ADMISSION
from experiments import entropygraph_v030_shared_portfolio as G04

# Historical convergence bindings. New canonical code binds the same semantic owners directly so this module is
# no longer on the promoted import path.
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
            "historical_convergence_facade": True,
            "canonical_product_entrypoint": "experiments.entropygraph_v030_canonical",
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
