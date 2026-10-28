"""Release-path publication wrapper for the full G0-G4 Geometry overlay.

The G0-G4 research reactor intentionally prioritized exact-byte mechanism proof. Its first pre-fallback builder
verified ``os.replace`` by calling ``Path.read_bytes()`` before and after publication, which is semantically
correct but can materialize a complete archive twice in RAM. That is unacceptable as a promoted memory story.

This module preserves the owning reactor's exact transforms, record audition, metadata writer and complete
artifact tournament, but computes publication identity with a bounded streaming SHA-256 pass. It is therefore a
performance rehabilitation wrapper, not a new grammar.

Footnote: the stream hash adds sequential *reads*, not payload writes. Same-filesystem ``os.replace`` still
publishes the already-written winner with zero extra archive payload writes. If this wrapper ever emits bytes
that differ from the owning G0-G4 builder on a fixed source tree, the wrapper is invalid and must not be used.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import tempfile
import time

from experiments import entropygraph_v030_geometry_overlay_g04 as G

# Re-export the grammar/reader surface so callers can treat this as the release-path G0-G4 implementation.
BASE = G.BASE
A5 = G.A5
H = G.H
MAG = G.MAG
TAIL = G.TAIL
HDR = G.HDR
FTR = G.FTR
ENGINE = G.ENGINE
MAX_MEMBER_READ_AMP = G.MAX_MEMBER_READ_AMP
MAX_OVERLAY_RECORD = G.MAX_OVERLAY_RECORD
MAX_DECODE_UNIT = G.MAX_DECODE_UNIT
MAX_DECODER_MEMORY = G.MAX_DECODER_MEMORY
strict = G.strict
HG = G.HG
O = G.O


def _sha256_file(path: Path, *, block_bytes: int = 1024 * 1024) -> bytes:
    if block_bytes <= 0 or block_bytes > 8 * 1024 * 1024:
        raise ValueError("stream hash block size outside bounded policy")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while True:
            block = stream.read(block_bytes)
            if not block:
                break
            digest.update(block)
    return digest.digest()


def strong_verify(archive: Path) -> dict:
    return G.strong_verify(archive)


def treehash(root: Path) -> str:
    return G.treehash(root)


def build(root: Path, out: Path) -> dict:
    """Build the exact G0-G4/v0.29 tournament with bounded publication verification memory."""
    started = time.perf_counter()
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".cmpct-g04-overlay-", dir=out.parent) as td:
        temp = Path(td)
        base_path = temp / "accepted-v029.cmpct"
        graph_path = temp / "attempt5-prefallback.cmpct"
        overlay_path = temp / "g04-overlay.cmpct"

        base_stats = BASE.build(root, base_path)
        base_bytes = base_path.stat().st_size
        graph_stats = A5.build_graph(root, graph_path)
        pre_overlay_graph_bytes = graph_path.stat().st_size
        source_format, _source, graph_meta, graph_records = strict._read_source_records(graph_path)

        users = O._record_member_lengths(graph_meta, len(graph_records))
        records = []
        transforms = []
        auditions = []
        for record_id, record in enumerate(graph_records):
            chosen, transform, stats = G._audition_record(record_id, record, users[record_id])
            records.append(chosen)
            transforms.append(transform)
            auditions.append(stats)

        annotated_meta = dict(graph_meta)
        annotated_meta["overlay_source_format"] = source_format
        write_stats = G._write_overlay(annotated_meta, records, transforms, overlay_path)
        verified = G.strong_verify(overlay_path)
        expected_tree = G.treehash(root)
        if not verified.get("ok") or verified.get("tree_sha256") != expected_tree:
            raise RuntimeError("G0-G4 overlay verification failed before selection")

        overlay_bytes = overlay_path.stat().st_size
        if overlay_bytes < base_bytes:
            chosen_path = overlay_path
            selected = "geometry-overlay-g04"
        else:
            chosen_path = base_path
            selected = "v029-fallback"

        chosen_sha = _sha256_file(chosen_path)
        chosen_size = chosen_path.stat().st_size
        os.replace(chosen_path, out)
        if out.stat().st_size != chosen_size or _sha256_file(out) != chosen_sha:
            raise RuntimeError("G0-G4 atomic publication changed selected archive identity")

        transformed = [row for row in auditions if row.get("selected") != "none"]
        hierarchy_rows = [row for row in transformed if str(row.get("selected", "")).startswith("hierarchical")]
        final_bytes = out.stat().st_size
        return {
            "selected": selected,
            "archive_bytes": final_bytes,
            "v029_bytes": base_bytes,
            "pre_overlay_graph_bytes": pre_overlay_graph_bytes,
            "pre_overlay_graph_delta_vs_v029_bytes": pre_overlay_graph_bytes - base_bytes,
            "overlay_bytes": overlay_bytes,
            "saving_vs_v029_bytes": base_bytes - final_bytes,
            "raw_overlay_delta_vs_v029_bytes": overlay_bytes - base_bytes,
            "overlay_improvement_vs_prefallback_graph_bytes": pre_overlay_graph_bytes - overlay_bytes,
            "overlay_source_format": source_format,
            "transformed_records": len(transformed),
            "lane_records": sum(row.get("selected") == "lane" for row in transformed),
            "delimiter_records": sum(row.get("selected") == "delimiter" for row in transformed),
            "hierarchical_records": sum(row.get("selected") == "hierarchical" for row in transformed),
            "prefix_plane_records": sum(row.get("selected") == "hierarchical-prefix" for row in transformed),
            "hierarchical_total_records": len(hierarchy_rows),
            "transform_payload_saving_bytes": sum(int(row.get("payload_saving_bytes", 0)) for row in transformed),
            "hierarchical_incremental_saving_bytes": sum(
                int(row.get("hierarchical_incremental_saving_bytes", 0)) for row in hierarchy_rows
            ),
            "max_selected_member_read_amplification": max(
                (float(row.get("max_member_read_amplification", 0.0)) for row in transformed), default=0.0
            ),
            "overlay_meta_raw_bytes": write_stats["meta_raw_bytes"],
            "overlay_meta_comp_bytes": write_stats["meta_comp_bytes"],
            "portfolio_create_s": time.perf_counter() - started,
            "tree_sha256": expected_tree,
            "auditions": auditions,
            "v029": base_stats,
            "prefallback_graph": graph_stats,
            "integration_order": "attempt5-graph -> G0-G4-geometry-overlay -> accepted-v029-tournament",
            "selection_materialization": "same-filesystem-atomic-move",
            "selection_extra_payload_write_bytes": 0,
            "publication_identity_check": "streamed-sha256",
            "publication_hash_block_bytes": 1024 * 1024,
        }
