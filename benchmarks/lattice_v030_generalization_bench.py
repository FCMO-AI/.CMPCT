from __future__ import annotations

"""Full-artifact public generalization gate for the CMPCT Lattice v0.30 research seed.

Each workload is generated once and remains alive while ``entropygraph_v030_lattice.build`` constructs
both the accepted v0.29 release artifact and the Lattice candidate from that exact tree. The candidate is
itself a complete-artifact portfolio, so a losing Lattice representation returns the accepted v0.29 bytes
unchanged rather than averaging a local regression away.

Footnote: this is a breakthrough-seed gate, not a release gate. It can establish a new size mechanism and
open explicit timing debt, but it cannot authorize a numeric version or canonical format revision.
"""

import argparse
import json
from pathlib import Path
import shutil
import time

from benchmarks import neutral_hostile_corpus_v1 as neutral
from benchmarks import resemblance_hostile_corpus_v1 as resemblance
from experiments import entropygraph_v030_lattice as lattice

MIN_AGGREGATE_SAVING = 128 * 1024
MIN_SINGLE_WORKLOAD_SAVING = 64 * 1024
EXPECTED_WORKLOADS = 15


def _files_and_bytes(root: Path) -> tuple[int, int]:
    files = [path for path in root.rglob("*") if path.is_file()]
    return len(files), sum(path.stat().st_size for path in files)


def _run_workload(suite: str, root: Path, work_root: Path) -> dict:
    out = work_root / f"{suite}-{root.name}.cmpct"
    started = time.perf_counter()
    result = lattice.build(root, out)
    wall = time.perf_counter() - started
    verified = lattice.strong_verify(out)
    expected_tree = lattice.treehash(root)
    if not verified.get("ok") or verified.get("tree_sha256") != expected_tree:
        raise RuntimeError(f"Lattice portfolio verification failed for {suite}/{root.name}")

    files, logical = _files_and_bytes(root)
    base = int(result["v029_bytes"])
    candidate = int(result["archive_bytes"])
    if candidate > base:
        raise RuntimeError(f"portfolio size regression for {suite}/{root.name}: {candidate}>{base}")
    graph = result.get("lattice") or {}
    row = {
        "suite": suite,
        "name": root.name,
        "files": files,
        "logical_bytes": logical,
        "tree_sha256": expected_tree,
        "selected": result["selected"],
        "v029_bytes": base,
        "candidate_bytes": candidate,
        "lattice_graph_bytes": int(result["lattice_graph_bytes"]),
        "saving_vs_v029_bytes": base - candidate,
        "saving_vs_v029_pct": (base - candidate) / max(1, base) * 100.0,
        "portfolio_create_s": float(result["portfolio_create_s"]),
        "benchmark_wall_s": wall,
        "lane_nodes": int(graph.get("lane_nodes") or 0),
        "lane_payload_saving_bytes": int(graph.get("lane_payload_saving_bytes") or 0),
        "lane_width_counts": graph.get("lane_width_counts") or {},
        "max_read_amplification": float(graph.get("max_read_amplification") or 0.0),
        "max_decode_unit": int(graph.get("max_decode_unit") or lattice.MAX_DECODE_UNIT),
    }
    print(json.dumps(row, sort_keys=True), flush=True)
    return row


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    corpus_root = work_root / "corpora"
    neutral_root = corpus_root / "neutral"
    resemblance_root = corpus_root / "resemblance"

    print("building neutral/hostile v1", flush=True)
    neutral_manifest = neutral.build(neutral_root)
    print("building resemblance-hostile v1", flush=True)
    resemblance_manifest = resemblance.build(resemblance_root)

    rows: list[dict] = []
    # The manifest itself is benchmark provenance, not part of workload logical bytes. Only the ten
    # generated workload directories are passed to the archive engines.
    for root in sorted(path for path in neutral_root.iterdir() if path.is_dir()):
        rows.append(_run_workload("neutral_hostile_v1", root, work_root))
    for root in sorted(path for path in resemblance_root.iterdir() if path.is_dir()):
        rows.append(_run_workload("resemblance_hostile_v1", root, work_root))

    if len(rows) != EXPECTED_WORKLOADS:
        raise RuntimeError(f"expected {EXPECTED_WORKLOADS} workloads, got {len(rows)}")

    baseline = sum(row["v029_bytes"] for row in rows)
    candidate = sum(row["candidate_bytes"] for row in rows)
    saving = baseline - candidate
    max_saving = max(row["saving_vs_v029_bytes"] for row in rows)
    selected = [row for row in rows if row["selected"] == "lattice"]
    regressions = [row for row in rows if row["candidate_bytes"] > row["v029_bytes"]]
    max_amp = max((row["max_read_amplification"] for row in selected), default=0.0)

    totals = {
        "workloads": len(rows),
        "v029_bytes": baseline,
        "candidate_bytes": candidate,
        "saving_vs_v029_bytes": saving,
        "smaller_than_v029_pct": saving / max(1, baseline) * 100.0,
        "workloads_improved": sum(row["candidate_bytes"] < row["v029_bytes"] for row in rows),
        "workloads_regressed": len(regressions),
        "lattice_selected": len(selected),
        "max_single_workload_saving_bytes": max_saving,
        "lane_nodes": sum(row["lane_nodes"] for row in rows),
        "lane_payload_saving_bytes": sum(row["lane_payload_saving_bytes"] for row in rows),
        "max_read_amplification": max_amp,
        "mechanism_gate": saving >= MIN_AGGREGATE_SAVING and max_saving >= MIN_SINGLE_WORKLOAD_SAVING,
    }
    return {
        "schema": "cmpct-v030-lattice-generalization-v1",
        "claim_boundary": "Research breakthrough seed only; accepted v0.29 exact fallback, canonical r24 unchanged.",
        "benchmark_contract": {
            "direct_base": "accepted v0.29 release engine built from the same live workload tree",
            "archive_size_regression_tolerance_bytes": 0,
            "expected_workloads": EXPECTED_WORKLOADS,
            "minimum_aggregate_breakthrough_saving_bytes": MIN_AGGREGATE_SAVING,
            "minimum_single_workload_breakthrough_saving_bytes": MIN_SINGLE_WORKLOAD_SAVING,
            "timing": "diagnostic only in seed stage; any confirmed debt must be rehabilitated before promotion",
            "correctness": "strong_verify tree SHA-256 must equal source tree hash for every selected artifact",
        },
        "generators": {
            "neutral": {"schema": neutral_manifest.get("schema"), "seed": neutral_manifest.get("seed")},
            "resemblance": {"schema": resemblance_manifest.get("schema"), "seed": resemblance_manifest.get("seed")},
        },
        "rows": rows,
        "totals": totals,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/lattice-v030-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/lattice-v030-generalization.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["totals"], indent=2), flush=True)
    if not result["totals"]["mechanism_gate"]:
        raise SystemExit("Lattice failed preregistered breakthrough mechanism gate")


if __name__ == "__main__":
    main()
