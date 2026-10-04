from __future__ import annotations

"""Exact public-corpus payload oracle for Hierarchical Geometry / Prefix Planes.

This probe intentionally measures one causal layer: level-19 physical payload bytes for the six raw log
streams after the same <=512 KiB balanced chunking used by the standalone Geometry seed.  It does *not*
claim complete-archive bytes.  The accepted v0.29 workload result remains the release floor until the new
transform is integrated at the authenticated physical-record boundary and a full artifact is rebuilt.

Footnote: the logs workload is regenerated from the public neutral/hostile generator, repair-v5 is applied,
and the historical tree SHA is asserted before a byte is measured.  This prevents a producer drift from
turning a source change into an apparent compression breakthrough.
"""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import time

from benchmarks import neutral_hostile_corpus_v1 as neutral
from benchmarks import neutral_hostile_determinism_repair_v5 as repair
from experiments import entropygraph_v030_hierarchical_geometry as H
from experiments import entropygraph_v030_lattice as L

EXPECTED_TREE_SHA256 = "7356b866d7b99bfce2dd1fc6ef86d61d09c9d8a38a2ff3fec7d9a92e46020931"
EXPECTED_RAW_FILES = 6
EXPECTED_CHUNKS = 30
MIN_TOTAL_SAVING = 640 * 1024
MIN_PER_CHUNK_SAVING = 16 * 1024


def _zstd_version() -> str:
    try:
        result = subprocess.run(["zstd", "--version"], check=True, text=True, capture_output=True)
        return result.stdout.strip()
    except Exception:
        return "unavailable"


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    corpus_root = work_root / "corpus"
    corpus_root.mkdir(parents=True, exist_ok=True)

    # Footnote: generating only this workload avoids paying for unrelated images/video/office fixtures while
    # preserving byte identity because every public workload owns an independently reseeded PRNG stream.
    neutral.corpus_logs(corpus_root)
    target = corpus_root / "05_logs_and_telemetry"
    repair.normalize_workload(target)
    tree_sha = neutral.tree_hash(target)
    if tree_sha != EXPECTED_TREE_SHA256:
        raise RuntimeError(f"logs corpus identity drifted: {tree_sha}")

    raw_files = sorted(target.glob("*.log"))
    if len(raw_files) != EXPECTED_RAW_FILES:
        raise RuntimeError(f"expected {EXPECTED_RAW_FILES} raw logs, found {len(raw_files)}")

    rows: list[dict] = []
    started = time.perf_counter()
    for path in raw_files:
        raw = path.read_bytes()
        for chunk_index, chunk in enumerate(L._balanced_chunks(raw)):
            _, direct_payload = H.G._compress_physical(chunk)
            chosen = H.audition(chunk)
            if chosen["kind"] == "hierarchical":
                if H.hierarchy_inverse(chosen["physical"], len(chunk)) != chunk:
                    raise RuntimeError("Hierarchical Geometry probe failed exact inverse")
            candidate_bytes = int(chosen["payload_bytes"])
            direct_bytes = len(direct_payload)
            if candidate_bytes > direct_bytes:
                raise RuntimeError("Hierarchical Geometry violated exact payload fallback")
            rows.append({
                "file": path.name,
                "chunk": chunk_index,
                "logical_bytes": len(chunk),
                "logical_sha256": hashlib.sha256(chunk).hexdigest(),
                "direct_zstd19_bytes": direct_bytes,
                "candidate_bytes": candidate_bytes,
                "saving_bytes": direct_bytes - candidate_bytes,
                "selected": chosen["kind"],
                "primary": chosen["primary"],
                "secondary": chosen["secondary"],
                "prefix_planes": bool(chosen["prefix_planes"]),
                "screened_candidates": int(chosen["screened_candidates"]),
                "exact_finalists": int(chosen["exact_finalists"]),
            })

    if len(rows) != EXPECTED_CHUNKS:
        raise RuntimeError(f"expected {EXPECTED_CHUNKS} balanced raw-log chunks, found {len(rows)}")
    direct_total = sum(row["direct_zstd19_bytes"] for row in rows)
    candidate_total = sum(row["candidate_bytes"] for row in rows)
    saving = direct_total - candidate_total
    selected = [row for row in rows if row["selected"] == "hierarchical"]
    min_selected_saving = min((row["saving_bytes"] for row in selected), default=0)
    totals = {
        "raw_files": len(raw_files),
        "chunks": len(rows),
        "direct_zstd19_bytes": direct_total,
        "candidate_bytes": candidate_total,
        "saving_bytes": saving,
        "smaller_than_direct_pct": saving / max(1, direct_total) * 100.0,
        "hierarchical_chunks": len(selected),
        "prefix_plane_chunks": sum(row["prefix_planes"] for row in selected),
        "min_selected_chunk_saving_bytes": min_selected_saving,
        "max_selected_chunk_saving_bytes": max((row["saving_bytes"] for row in selected), default=0),
        "mechanism_gate": (
            saving >= MIN_TOTAL_SAVING
            and len(selected) == EXPECTED_CHUNKS
            and min_selected_saving >= MIN_PER_CHUNK_SAVING
        ),
        "elapsed_s": time.perf_counter() - started,
    }
    return {
        "schema": "cmpct-v030-hierarchical-geometry-logs-probe-v1",
        "status": "DETACHED_PAYLOAD_ORACLE_NOT_RELEASE_EVIDENCE",
        "claim_boundary": (
            "Exact public-tree raw-log physical-payload evidence only; no complete CMPCT archive size claim. "
            "Canonical r24 and accepted v0.29 remain unchanged."
        ),
        "source_tree_sha256": tree_sha,
        "zstd_version": _zstd_version(),
        "resource_limits": H.RESOURCE_LIMITS,
        "contract": {
            "minimum_total_saving_bytes": MIN_TOTAL_SAVING,
            "minimum_each_selected_chunk_saving_bytes": MIN_PER_CHUNK_SAVING,
            "expected_raw_files": EXPECTED_RAW_FILES,
            "expected_chunks": EXPECTED_CHUNKS,
            "payload_regression_tolerance_bytes": 0,
            "exact_inverse_required": True,
        },
        "totals": totals,
        "rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["totals"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
