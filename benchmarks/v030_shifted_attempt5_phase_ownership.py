from __future__ import annotations

"""Frozen R0 attribution oracle for the Shifted attempt-5 post-Placement seam.

The wrappers in this file are observational only. They time the exact accepted attempt-4 Placement builder
and the exact residual-pack compiler while ``entropygraph_v029_residual_fast.build_graph`` runs unchanged.
The final archive must be deterministic and strong-verify to the generated source tree before any timing
interpretation is admitted.
"""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import statistics
import tempfile
import time

from benchmarks import resemblance_hostile_corpus_v1 as CORPUS
from experiments import entropygraph_v029_residual_fast as A5

SCHEMA = "cmpct-v030-shifted-attempt5-phase-ownership-v1"
REPETITIONS = 2
POST_PLACEMENT_FRACTION_CEILING = 0.15


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _run_one(root: Path, out: Path, rep: int) -> dict:
    base = A5.BASE
    original_placement = base.A4.build_graph
    original_residual = base._compile_residual
    phase: dict[str, float] = {}
    calls = {"placement": 0, "residual": 0}

    def timed_placement(*args, **kwargs):
        calls["placement"] += 1
        started = time.perf_counter()
        try:
            return original_placement(*args, **kwargs)
        finally:
            phase["placement_s"] = phase.get("placement_s", 0.0) + (time.perf_counter() - started)

    def timed_residual(*args, **kwargs):
        calls["residual"] += 1
        started = time.perf_counter()
        try:
            return original_residual(*args, **kwargs)
        finally:
            phase["residual_s"] = phase.get("residual_s", 0.0) + (time.perf_counter() - started)

    base.A4.build_graph = timed_placement
    base._compile_residual = timed_residual
    started = time.perf_counter()
    try:
        stats = A5.build_graph(root, out)
    finally:
        total = time.perf_counter() - started
        base.A4.build_graph = original_placement
        base._compile_residual = original_residual

    if calls != {"placement": 1, "residual": 1}:
        raise RuntimeError(f"unexpected attempt-5 phase call counts: {calls!r}")
    if "placement_s" not in phase or "residual_s" not in phase:
        raise RuntimeError("attempt-5 phase timer failed to observe both owners")
    if phase["placement_s"] > total + 1e-6 or phase["residual_s"] > total + 1e-6:
        raise RuntimeError("phase timing exceeds enclosing attempt-5 wall")

    verified = A5.strong_verify(out)
    source_tree = CORPUS.tree_hash(root)
    if not verified.get("ok") or verified.get("tree_sha256") != source_tree:
        raise RuntimeError("instrumented attempt-5 archive failed strong tree verification")

    placement_s = float(phase["placement_s"])
    residual_s = float(phase["residual_s"])
    post_tail_s = max(0.0, total - placement_s)
    return {
        "rep": rep,
        "attempt5_total_s": total,
        "placement_s": placement_s,
        "residual_compile_s": residual_s,
        "unowned_tail_s": max(0.0, total - placement_s - residual_s),
        "placement_fraction": placement_s / max(total, 1e-12),
        "post_placement_tail_s": post_tail_s,
        "post_placement_tail_fraction": post_tail_s / max(total, 1e-12),
        "archive_bytes": out.stat().st_size,
        "archive_sha256": _sha256(out),
        "tree_sha256": source_tree,
        "selected_residual_pack": bool(stats.get("residual_selected")),
        "residual_pack_records": int(stats.get("residual_pack_records", 0)),
        "residual_packed_delta_nodes": int(stats.get("residual_packed_delta_nodes", 0)),
        "delta_auditions": int(stats.get("delta_auditions", 0)),
        "subset_trials": int(stats.get("subset_trials", 0)),
        "mosaic_auditions": int(stats.get("mosaic_auditions", 0)),
        "strong_verify_ok": True,
    }


def measure(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    corpus_root = work_root / "corpus"
    CORPUS.shifted_versions(corpus_root)
    root = corpus_root / "01_shifted_versions"
    source_tree = CORPUS.tree_hash(root)

    rows: list[dict] = []
    for rep in range(REPETITIONS):
        out = work_root / f"attempt5-{rep}.cmpct"
        rows.append(_run_one(root, out, rep))

    archive_shas = {row["archive_sha256"] for row in rows}
    archive_sizes = {row["archive_bytes"] for row in rows}
    tree_shas = {row["tree_sha256"] for row in rows}
    identity_ok = len(archive_shas) == 1 and len(archive_sizes) == 1 and tree_shas == {source_tree}
    every_below = all(row["post_placement_tail_fraction"] < POST_PLACEMENT_FRACTION_CEILING for row in rows)
    if not identity_ok:
        decision = "CANDIDATE_INVALID"
    elif every_below:
        decision = "POST_PLACEMENT_STOPPING_SEAM_RETIRED"
    else:
        decision = "POST_PLACEMENT_STOPPING_SEAM_REMAINS_PLAUSIBLE"

    return {
        "schema": SCHEMA,
        "status": "result-bearing-r0-attribution",
        "diagnosis": "D2/D3",
        "instrument_radicality": "R0",
        "saturation_trigger": "S5",
        "research_priority_score": 91,
        "corpus": "resemblance_hostile_v1/01_shifted_versions",
        "tree_sha256": source_tree,
        "repetitions": REPETITIONS,
        "post_placement_fraction_ceiling": POST_PLACEMENT_FRACTION_CEILING,
        "rows": rows,
        "median_attempt5_total_s": statistics.median(row["attempt5_total_s"] for row in rows),
        "median_placement_s": statistics.median(row["placement_s"] for row in rows),
        "median_residual_compile_s": statistics.median(row["residual_compile_s"] for row in rows),
        "median_post_placement_tail_s": statistics.median(row["post_placement_tail_s"] for row in rows),
        "median_post_placement_tail_fraction": statistics.median(
            row["post_placement_tail_fraction"] for row in rows
        ),
        "archive_identity_stable": identity_ok,
        "decision": decision,
        "release_credit": False,
        "interpretation": (
            "post-Placement stopping is too late to be the primary Shifted runtime repair"
            if decision == "POST_PLACEMENT_STOPPING_SEAM_RETIRED"
            else "a post-Placement stopping seam still has enough optimistic wall budget to test"
            if decision == "POST_PLACEMENT_STOPPING_SEAM_REMAINS_PLAUSIBLE"
            else "instrument/candidate identity invalid; no timing interpretation"
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = measure(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    if result["decision"] == "CANDIDATE_INVALID":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
