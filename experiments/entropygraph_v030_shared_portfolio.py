"""Shared v0.29/G0-G4 portfolio for the CMPCT v0.30 release path.

The first integrated G0-G4 builder had one large avoidable creation-cost regression:

    accepted-v0.29 build = v0.28 + attempt-5 graph
    then G0-G4 build     = attempt-5 graph *again*

The second graph is byte-identical work performed only because the accepted v0.29 facade publishes the winner
and discards its losing candidate.  This module makes those independent candidates a shared substrate instead:

1. build exact v0.28 and exact attempt-5 pre-fallback graph once, in spawned workers;
2. reconstruct the accepted v0.29 floor with the exact old strict-smaller/tie law and single-file fast-reject
   policy, without consuming either candidate artifact;
3. apply the owning G0-G4 transform tournament directly to that retained attempt-5 graph;
4. compare the complete G0-G4 archive against the reconstructed accepted-v0.29 floor;
5. strong-verify an overlay only when complete-artifact pricing says it actually wins;
6. publish the exact winner with same-filesystem ``os.replace`` and bounded streamed SHA-256 identity checks.

No transform rule, graph byte, codec setting, fallback threshold, fast-reject predicate or archive grammar changes.
This is shared *scheduling/materialization*, not a compression mechanism.

Footnote: single-file trees still build the attempt-5 graph because G0-G4 explicitly needs that pre-fallback
substrate even when accepted v0.29 would fast-reject it.  Running that already-required work in parallel with
v0.28 does not resurrect the old dead-end audition; it removes serial latency from work v0.30 must perform.
A losing overlay is never publishable, so decoding its entire logical tree before exact byte pricing is not a
safety check on released bytes.  Winning overlays remain strong-verified before publication.
"""
from __future__ import annotations

import multiprocessing as mp
import os
from pathlib import Path
import queue as queue_module
import tempfile
import time

from experiments import entropygraph_v029_parallel_portfolio as V029_SCHED
from experiments import entropygraph_v029_residual_fast as V029_ACCEPTED
from experiments import entropygraph_v030_geometry_overlay_g04 as G
from experiments import entropygraph_v030_geometry_overlay_g04_publish as PUB

# Re-export the owning grammar/read constants so the top-level release selector can replace its G04 provider
# without learning that scheduling changed underneath it.
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

CHILD_RESULT_TIMEOUT_S = V029_SCHED.CHILD_RESULT_TIMEOUT_S


def _sha256_file(path: Path) -> bytes:
    return PUB._sha256_file(path)


def strong_verify(archive: Path) -> dict:
    return G.strong_verify(archive)


def treehash(root: Path) -> str:
    return G.treehash(root)


def _build_shared_candidates(root: Path, temp: Path) -> dict:
    """Build v0.28 + attempt-5 once and retain both exact artifacts for the G0-G4 stage."""
    started = time.perf_counter()
    v028_path = temp / "v028.cmpct"
    graph_path = temp / "attempt5-prefallback.cmpct"
    ctx = mp.get_context("spawn")
    queue = ctx.Queue()
    processes = [
        ctx.Process(target=V029_SCHED._worker, args=("v028", str(root), str(v028_path), queue)),
        ctx.Process(target=V029_SCHED._worker, args=("attempt5", str(root), str(graph_path), queue)),
    ]
    for process in processes:
        process.start()

    results = []
    try:
        for _ in processes:
            results.append(queue.get(timeout=CHILD_RESULT_TIMEOUT_S))
    except queue_module.Empty as exc:
        for process in processes:
            if process.is_alive():
                process.terminate()
        raise RuntimeError("v0.30 shared portfolio child failed to report before timeout") from exc
    finally:
        for process in processes:
            process.join(timeout=30)
            if process.is_alive():
                process.terminate()
                process.join(timeout=5)

    failures = [result for result in results if not result.get("ok")]
    if failures or any(process.exitcode != 0 for process in processes):
        raise RuntimeError(
            f"v0.30 shared portfolio child failure: results={results!r}, "
            f"exitcodes={[process.exitcode for process in processes]!r}"
        )
    if not v028_path.is_file() or not graph_path.is_file():
        raise RuntimeError("v0.30 shared portfolio child omitted candidate artifact")

    by_kind = {result["kind"]: result for result in results}
    v028_bytes = v028_path.stat().st_size
    graph_bytes = graph_path.stat().st_size
    logical_files = V029_ACCEPTED._logical_file_count(root)
    fast_reject = V029_ACCEPTED._fast_reject(by_kind["v028"]["stats"], logical_files)

    # Accepted v0.29's single-file fast reject is a portfolio *selection* law.  The graph may exist here for
    # Geometry, but it is not allowed to retroactively change what accepted v0.29 would have published.
    if fast_reject is not None:
        floor_path = v028_path
        floor_selected = "v028-fallback"
    elif graph_bytes < v028_bytes:
        floor_path = graph_path
        floor_selected = "mosaic"
    else:
        floor_path = v028_path
        floor_selected = "v028-fallback"

    elapsed = time.perf_counter() - started
    v029_stats = {
        "selected": floor_selected,
        "archive_bytes": floor_path.stat().st_size,
        "v028_bytes": v028_bytes,
        "mosaic_graph_bytes": graph_bytes,
        "smaller_than_v028_pct": (v028_bytes - floor_path.stat().st_size) / max(1, v028_bytes) * 100.0,
        "portfolio_create_s": elapsed,
        "parallel_create_s": elapsed,
        "v028_child_s": float(by_kind["v028"]["elapsed_s"]),
        "attempt5_child_s": float(by_kind["attempt5"]["elapsed_s"]),
        "v028": by_kind["v028"]["stats"],
        "mosaic": by_kind["attempt5"]["stats"],
        "fast_reject_reason": fast_reject,
        "fast_reject_logical_files": logical_files,
        "scheduler_mode": "v030-shared-v028-attempt5-spawn",
        "accepted_engine": V029_SCHED.ACCEPTED_ENGINE,
        "selection_materialization": "retained-candidate-reference",
        "selection_extra_payload_write_bytes": 0,
    }
    return {
        "v028_path": v028_path,
        "graph_path": graph_path,
        "floor_path": floor_path,
        "floor_selected": floor_selected,
        "v028_bytes": v028_bytes,
        "graph_bytes": graph_bytes,
        "floor_bytes": floor_path.stat().st_size,
        "v029_stats": v029_stats,
        "graph_stats": by_kind["attempt5"]["stats"],
        "shared_build_s": elapsed,
    }


def _overlay_retained_graph(graph_path: Path, overlay_path: Path) -> dict:
    """Apply the exact owning G0-G4 writer to a retained attempt-5 graph artifact.

    Full logical verification is deliberately deferred until complete-artifact pricing proves the overlay beats
    the accepted-v0.29 floor. A losing artifact cannot be published; decoding it here would only add creation
    latency. The build tournament below strong-verifies every byte-winning overlay before publication.
    """
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
    return {
        "source_format": source_format,
        "records": records,
        "transforms": transforms,
        "auditions": auditions,
        "write_stats": write_stats,
        "verified": None,
        "verification_state": "deferred-until-byte-win",
    }


def build(root: Path, out: Path) -> dict:
    """Build byte-identical G0-G4 output while constructing the expensive attempt-5 graph only once."""
    started = time.perf_counter()
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".cmpct-v030-shared-portfolio-", dir=out.parent) as td:
        temp = Path(td)
        overlay_path = temp / "g04-overlay.cmpct"
        shared = _build_shared_candidates(root, temp)
        graph_path = shared["graph_path"]
        floor_path = shared["floor_path"]
        floor_bytes = int(shared["floor_bytes"])
        graph_bytes = int(shared["graph_bytes"])

        overlay = _overlay_retained_graph(graph_path, overlay_path)
        expected_tree = treehash(root)
        overlay_bytes = overlay_path.stat().st_size

        if overlay_bytes < floor_bytes:
            # Exact bytes earned consideration. Verify logical identity before this candidate can be published.
            verified = G.strong_verify(overlay_path)
            if not verified.get("ok") or verified.get("tree_sha256") != expected_tree:
                raise RuntimeError("shared G0-G4 overlay failed exact logical-tree verification")
            overlay["verified"] = verified
            overlay["verification_state"] = "verified-before-publication"
            chosen_path = overlay_path
            selected = "geometry-overlay-g04"
        else:
            chosen_path = floor_path
            selected = "v029-fallback"

        chosen_sha = _sha256_file(chosen_path)
        chosen_size = chosen_path.stat().st_size
        os.replace(chosen_path, out)
        if out.stat().st_size != chosen_size or _sha256_file(out) != chosen_sha:
            raise RuntimeError("shared G0-G4 publication changed selected archive identity")

        auditions = overlay["auditions"]
        transformed = [row for row in auditions if row.get("selected") != "none"]
        hierarchy_rows = [row for row in transformed if str(row.get("selected", "")).startswith("hierarchical")]
        write_stats = overlay["write_stats"]
        final_bytes = out.stat().st_size
        return {
            "selected": selected,
            "archive_bytes": final_bytes,
            "v029_bytes": floor_bytes,
            "v029_floor_selected": shared["floor_selected"],
            "v028_bytes": int(shared["v028_bytes"]),
            "pre_overlay_graph_bytes": graph_bytes,
            "pre_overlay_graph_delta_vs_v029_bytes": graph_bytes - floor_bytes,
            "overlay_bytes": overlay_bytes,
            "saving_vs_v029_bytes": floor_bytes - final_bytes,
            "raw_overlay_delta_vs_v029_bytes": overlay_bytes - floor_bytes,
            "overlay_improvement_vs_prefallback_graph_bytes": graph_bytes - overlay_bytes,
            "overlay_source_format": overlay["source_format"],
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
            "v029": shared["v029_stats"],
            "prefallback_graph": shared["graph_stats"],
            "shared_candidate_build_s": float(shared["shared_build_s"]),
            "v028_child_s": float(shared["v029_stats"]["v028_child_s"]),
            "attempt5_child_s": float(shared["v029_stats"]["attempt5_child_s"]),
            "integration_order": "shared(v028,attempt5-graph) -> G0-G4-overlay -> accepted-v029-tournament",
            "shared_analysis_mode": "attempt5-graph-built-once",
            "attempt5_graph_build_count": 1,
            "selection_materialization": "same-filesystem-atomic-move",
            "selection_extra_payload_write_bytes": 0,
            "publication_identity_check": "streamed-sha256",
            "publication_hash_block_bytes": 1024 * 1024,
            "overlay_verification_state": overlay["verification_state"],
            "losing_overlay_logical_verification_skipped": selected == "v029-fallback",
        }
