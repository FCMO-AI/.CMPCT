from __future__ import annotations

"""Balanced create-time rehabilitation proof for the v0.30 shared portfolio.

The mechanism under test is intentionally byte-neutral: build v0.28 + attempt-5 once and reuse the retained
attempt-5 graph for G0-G4 instead of constructing that graph a second time.  The exact public ML workload is
used because it is already a frozen Geometry identity and materially exercises the expensive graph/compiler.

Four paired repetitions use ABBA ordering.  Every pair must produce byte-identical complete archives and clear
both inherited scheduler hurdles: >=20% wall-clock improvement and >=5 seconds saved.  The median pair must
clear the same thresholds.  Those hurdles are frozen before this optimization has independent CI timing.

Footnote: this benchmark compares two byte-compatible *v0.30 implementations*, not v0.30 against released
v0.29.  A green result proves the duplicate-build regression was materially rehabilitated; release still needs
a separate v0.30-vs-v0.29 create/extract/selective-read/memory gate.
"""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import statistics
import time

from benchmarks import neutral_hostile_corpus_v1 as neutral
from benchmarks import neutral_hostile_determinism_repair_v5 as repair
from experiments import entropygraph_v030_geometry_overlay_g04_publish as duplicated
from experiments import entropygraph_v030_shared_portfolio as shared

EXPECTED_TREE = "efc09910fea8ef67d24cd8957d3d576df3a7cc7f10f14585e3a3ae269017901d"
MIN_WALLCLOCK_IMPROVEMENT_PCT = 20.0
MIN_ABSOLUTE_IMPROVEMENT_S = 5.0
BALANCED_ORDER = ("duplicated-first", "shared-first", "shared-first", "duplicated-first")


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _build_source(root: Path) -> Path:
    corpus = root / "corpus"
    repair.install_generation_hooks(neutral)
    neutral.corpus_ml(corpus)
    repair.normalize_root(corpus)
    source = corpus / "09_ml_artifacts"
    got = shared.treehash(source)
    if got != EXPECTED_TREE:
        raise RuntimeError(f"shared-portfolio timing source drift: {got} != {EXPECTED_TREE}")
    return source


def _one(builder, source: Path, archive: Path) -> tuple[dict, float]:
    started = time.perf_counter()
    stats = builder.build(source, archive)
    elapsed = time.perf_counter() - started
    verified = builder.strong_verify(archive)
    if not verified.get("ok") or verified.get("tree_sha256") != EXPECTED_TREE:
        raise RuntimeError("timed G0-G4 implementation failed exact strong verification")
    return stats, elapsed


def _pair_passes(old_s: float, new_s: float) -> bool:
    saved = old_s - new_s
    pct = saved / max(old_s, 1e-9) * 100.0
    return saved >= MIN_ABSOLUTE_IMPROVEMENT_S and pct >= MIN_WALLCLOCK_IMPROVEMENT_PCT


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    source = _build_source(work_root)
    rows = []
    duplicated_times = []
    shared_times = []

    for rep, order in enumerate(BALANCED_ORDER):
        old_archive = work_root / f"duplicated-{rep}.cmpct"
        new_archive = work_root / f"shared-{rep}.cmpct"
        if order == "duplicated-first":
            old_stats, old_s = _one(duplicated, source, old_archive)
            new_stats, new_s = _one(shared, source, new_archive)
        else:
            new_stats, new_s = _one(shared, source, new_archive)
            old_stats, old_s = _one(duplicated, source, old_archive)

        old_sha = _sha(old_archive)
        new_sha = _sha(new_archive)
        if old_sha != new_sha or old_archive.stat().st_size != new_archive.stat().st_size:
            raise RuntimeError("shared portfolio changed complete G0-G4 archive identity")
        if old_stats["selected"] != new_stats["selected"] or old_stats["v029_bytes"] != new_stats["v029_bytes"]:
            raise RuntimeError("shared portfolio changed G0-G4 selection/floor semantics")
        if new_stats.get("attempt5_graph_build_count") != 1:
            raise RuntimeError("shared portfolio did not prove exactly one attempt-5 graph build")

        saved = old_s - new_s
        pct = saved / max(old_s, 1e-9) * 100.0
        duplicated_times.append(old_s)
        shared_times.append(new_s)
        rows.append(
            {
                "rep": rep,
                "execution_order": order,
                "archive_bytes": old_archive.stat().st_size,
                "archive_sha256": old_sha,
                "selected": old_stats["selected"],
                "v029_bytes": old_stats["v029_bytes"],
                "duplicated_create_s": old_s,
                "shared_create_s": new_s,
                "wallclock_saved_s": saved,
                "wallclock_improvement_pct": pct,
                "byte_identical": True,
                "attempt5_graph_build_count": new_stats["attempt5_graph_build_count"],
                "pair_gate_pass": _pair_passes(old_s, new_s),
            }
        )

    old_median = statistics.median(duplicated_times)
    new_median = statistics.median(shared_times)
    saved = old_median - new_median
    improvement_pct = saved / max(old_median, 1e-9) * 100.0
    median_pass = saved >= MIN_ABSOLUTE_IMPROVEMENT_S and improvement_pct >= MIN_WALLCLOCK_IMPROVEMENT_PCT
    gate = {
        "exact_tree": shared.treehash(source) == EXPECTED_TREE,
        "all_byte_identical": all(row["byte_identical"] for row in rows),
        "all_single_attempt5_build": all(row["attempt5_graph_build_count"] == 1 for row in rows),
        "every_pair_pass": all(row["pair_gate_pass"] for row in rows),
        "median_pass": median_pass,
    }
    gate["passed"] = all(gate.values())
    return {
        "schema": "cmpct-v030-shared-portfolio-rehab-v1",
        "contract": {
            "tree_sha256": EXPECTED_TREE,
            "balanced_order": list(BALANCED_ORDER),
            "minimum_wallclock_improvement_pct": MIN_WALLCLOCK_IMPROVEMENT_PCT,
            "minimum_absolute_improvement_s": MIN_ABSOLUTE_IMPROVEMENT_S,
            "complete_archive_identity_required": True,
            "attempt5_graph_build_count": 1,
        },
        "rows": rows,
        "duplicated_median_s": old_median,
        "shared_median_s": new_median,
        "median_wallclock_saved_s": saved,
        "median_wallclock_improvement_pct": improvement_pct,
        "gate": gate,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-shared-rehab-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-shared-rehab.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2), flush=True)
    if not result["gate"]["passed"]:
        raise SystemExit("v0.30 shared portfolio rehabilitation gate failed")


if __name__ == "__main__":
    main()
