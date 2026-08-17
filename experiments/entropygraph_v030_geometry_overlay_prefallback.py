"""Pre-fallback Geometry overlay for the CMPCT v0.30 composition oracle.

The first strict overlay attached Geometry to the *selected* accepted-v0.29 archive.  That ordering is wrong
whenever the outer v0.29 portfolio selects an inherited v0.28/v0.25 fallback: the Placement/Residual graph is
discarded before Geometry gets a chance to improve its physical records, so a potentially rehabilitated graph
is never measured.

This facade keeps accepted v0.29 as the immutable complete-artifact floor, but independently builds the
attempt-5 graph **before its outer fallback tournament**, overlays Geometry on that graph, strong-verifies the
transformed graph to the same logical tree, then tournaments the complete transformed artifact against the
accepted release bytes.

Footnote: this changes integration order, not either mechanism.  The v0.29 floor, Placement/Residual graph,
Geometry transform, locality law, metadata/recovery costs, strong verifier and strict final byte comparison are
unchanged.  If the transformed graph still misses the frozen >=256 KiB hurdle, that is a genuine composition
rejection rather than an eligibility artifact.
"""
from __future__ import annotations

from pathlib import Path
import shutil
import tempfile
import time

from experiments import entropygraph_v030_geometry_overlay_strict as strict

O = strict.O
A5 = strict.A5
BASE = strict.BASE


def build(root: Path, out: Path) -> dict:
    started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="cmpct-geometry-overlay-prefallback-") as td:
        temp = Path(td)
        base_path = temp / "accepted-v029.cmpct"
        graph_path = temp / "attempt5-prefallback.cmpct"
        overlay_path = temp / "geometry-overlay.cmpct"

        # The release artifact is the non-regression floor.  It may legitimately be an inherited fallback.
        base_stats = BASE.build(root, base_path)
        base_bytes = base_path.stat().st_size

        # Crucial ordering fix: build the best Placement/Residual graph *before* v0.29 compares it to v0.28.
        # Geometry is allowed to rehabilitate this graph, but never to weaken the accepted fallback floor.
        graph_stats = A5.build_graph(root, graph_path)
        pre_overlay_graph_bytes = graph_path.stat().st_size
        source_format, _source, graph_meta, graph_records = strict._read_source_records(graph_path)

        users = O._record_member_lengths(graph_meta, len(graph_records))
        records = []
        transforms = []
        auditions = []
        for record_id, record in enumerate(graph_records):
            chosen, transform, stats = O._audition_record(record_id, record, users[record_id])
            records.append(chosen)
            transforms.append(transform)
            auditions.append(stats)

        annotated_meta = dict(graph_meta)
        annotated_meta["overlay_source_format"] = source_format
        write_stats = O._write_overlay(annotated_meta, records, transforms, overlay_path)
        verified = strict.strong_verify(overlay_path)
        expected_tree = O.treehash(root)
        if not verified.get("ok") or verified.get("tree_sha256") != expected_tree:
            raise RuntimeError("pre-fallback Geometry overlay verification failed before selection")

        overlay_bytes = overlay_path.stat().st_size
        if overlay_bytes < base_bytes:
            shutil.copyfile(overlay_path, out)
            selected = "geometry-overlay"
        else:
            shutil.copyfile(base_path, out)
            selected = "v029-fallback"

        transformed = [row for row in auditions if row["selected"] != "none"]
        return {
            "selected": selected,
            "archive_bytes": out.stat().st_size,
            "v029_bytes": base_bytes,
            "pre_overlay_graph_bytes": pre_overlay_graph_bytes,
            "pre_overlay_graph_delta_vs_v029_bytes": pre_overlay_graph_bytes - base_bytes,
            "overlay_bytes": overlay_bytes,
            "saving_vs_v029_bytes": base_bytes - out.stat().st_size,
            "raw_overlay_delta_vs_v029_bytes": overlay_bytes - base_bytes,
            "overlay_improvement_vs_prefallback_graph_bytes": pre_overlay_graph_bytes - overlay_bytes,
            "overlay_source_format": source_format,
            "transformed_records": len(transformed),
            "lane_records": sum(row["selected"] == "lane" for row in transformed),
            "delimiter_records": sum(row["selected"] == "delimiter" for row in transformed),
            "transform_payload_saving_bytes": sum(row["payload_saving_bytes"] for row in transformed),
            "max_selected_member_read_amplification": max(
                (row["max_member_read_amplification"] for row in transformed), default=0.0
            ),
            "overlay_meta_raw_bytes": write_stats["meta_raw_bytes"],
            "overlay_meta_comp_bytes": write_stats["meta_comp_bytes"],
            "portfolio_create_s": time.perf_counter() - started,
            "tree_sha256": expected_tree,
            "auditions": auditions,
            "v029": base_stats,
            "prefallback_graph": graph_stats,
            "integration_order": "attempt5-graph -> geometry-overlay -> accepted-v029-tournament",
        }


strong_verify = strict.strong_verify
treehash = O.treehash
MAX_MEMBER_READ_AMP = O.MAX_MEMBER_READ_AMP

if __name__ == "__main__":
    O._main()
