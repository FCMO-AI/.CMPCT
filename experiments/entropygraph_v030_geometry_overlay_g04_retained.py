"""G04 retained-intermediate productization prototype.

This wrapper tests the smallest production-shaped ownership change earned by the retained-attempt5 A/B:
preserve the already-computed attempt-5 candidate at the v0.29 publication boundary and hand that exact
inode to G04 instead of rebuilding the graph. Candidate construction, selection, Geometry admission,
archive bytes and reader semantics are unchanged.

The retained candidate is a same-filesystem hard link, so retention writes zero additional payload bytes.
G04 then atomically moves that retained name into its private workspace. This remains research-frontier
code until unchanged fresh-process product authority proves the gain and complete resource accounting.
"""
from __future__ import annotations

import os
from pathlib import Path
import tempfile
import time

from experiments import entropygraph_v030_geometry_overlay_g04 as G04


def build(root: Path, out: Path) -> dict:
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".cmpct-g04-retained-", dir=out.parent) as td:
        retained = Path(td) / "attempt5-retained.cmpct"
        scheduler = G04.BASE.scheduler
        original_replace = scheduler._durable_replace
        original_graph = G04.A5.build_graph
        retention: dict = {}

        def retain_before_publication(chosen: Path, destination: Path) -> str:
            attempt5 = Path(chosen).parent / "attempt5.cmpct"
            if not attempt5.is_file():
                raise RuntimeError("attempt5 candidate unavailable at v0.29 publication boundary")
            started = time.perf_counter()
            os.link(attempt5, retained)
            retention.update({
                "mode": "same-filesystem-hardlink",
                "payload_write_bytes": 0,
                "bytes": retained.stat().st_size,
                "retain_s": time.perf_counter() - started,
            })
            return original_replace(chosen, destination)

        def consume_retained(_root: Path, graph: Path) -> dict:
            if not retained.is_file():
                raise RuntimeError("retained attempt5 missing before G04 overlay")
            started = time.perf_counter()
            os.replace(retained, graph)
            return {
                "create_s": time.perf_counter() - started,
                "selected": True,
                "graph_bytes": graph.stat().st_size,
                "retained_intermediate": True,
                "retention_mode": "same-filesystem-hardlink-then-atomic-move",
                "retention_payload_write_bytes": 0,
            }

        scheduler._durable_replace = retain_before_publication
        G04.A5.build_graph = consume_retained
        try:
            stats = dict(G04.build(root, out))
        finally:
            scheduler._durable_replace = original_replace
            G04.A5.build_graph = original_graph

        stats["attempt5_retention"] = retention
        stats["productization_status"] = "research-prototype-no-release-credit"
        return stats


extract = G04.extract
strong_verify = G04.strong_verify
treehash = G04.treehash
