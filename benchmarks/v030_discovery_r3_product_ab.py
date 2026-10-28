"""Frozen Builder receipt for the v0.30 position-independent discovery R3 neutralization.

This instrument compares the exact canonical private shared-portfolio implementation twice on the same
15 deterministic generalization trees. The only A/B difference is which child worker provider the private
shared module uses: historical accepted-v0.29 scheduling versus the transfer-proven v0.30 neutral worker.

Stored-byte identity is required on every row. Runtime evidence is deliberately restricted to the three
frozen release-runtime targets and is repeated ABBA-style; non-exercising rows grant no speed claim.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import statistics
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from benchmarks import mosaic_v029_generalization_bench as generalization
from benchmarks import neutral_hostile_determinism_repair_v5 as _unused_repair_v5  # noqa: F401
from experiments import entropygraph_v029_parallel_portfolio as historical_sched
from experiments import entropygraph_v030_discovery_neutral_worker as neutral_sched
from experiments import entropygraph_v030_profile_isolation as isolation

RUNTIME_TARGETS = {
    ("neutral_hostile_v1", "05_logs_and_telemetry"),
    ("neutral_hostile_v1", "09_ml_artifacts"),
    ("resemblance_hostile_v1", "01_shifted_versions"),
}
ROUNDS = 2
# The frozen Builder preregistration inherits the normative release timing-confidence rule:
# a slowdown is material only when it clears both the relative and absolute thresholds.
TIMING_REGRESSION_REL = 0.05
TIMING_REGRESSION_ABS_S = 0.003


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _material_runtime_regression(baseline_s: float, candidate_s: float) -> bool:
    return (
        candidate_s > baseline_s * (1.0 + TIMING_REGRESSION_REL)
        and candidate_s - baseline_s > TIMING_REGRESSION_ABS_S
    )


def _one(workload: Path, out: Path, provider) -> dict:
    isolation.SHARED.V029_SCHED = provider
    started = time.perf_counter()
    stats = isolation.SHARED.build(workload, out)
    wall = time.perf_counter() - started
    verified = isolation.SHARED.strong_verify(out)
    tree = isolation.SHARED.treehash(workload)
    if not verified.get("ok") or verified.get("tree_sha256") != tree:
        raise RuntimeError(f"strong verification failed for {workload}")
    return {
        "bytes": out.stat().st_size,
        "sha256": _sha(out),
        "tree_sha256": tree,
        "wall_s": wall,
        "selected": stats.get("selected"),
        "v029_floor_selected": stats.get("v029_floor_selected"),
        "attempt5_child_s": float(stats.get("attempt5_child_s", 0.0)),
        "v028_child_s": float(stats.get("v028_child_s", 0.0)),
        "max_selected_member_read_amplification": float(stats.get("max_selected_member_read_amplification", 0.0)),
        "archive_bytes_from_stats": int(stats.get("archive_bytes", -1)),
    }


def _build_suites(root: Path):
    neutral = generalization._load(ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py", "cmpct_r3_product_neutral")
    hostile = generalization._load(ROOT / "benchmarks" / "resemblance_hostile_corpus_v1.py", "cmpct_r3_product_hostile")
    repair = generalization._load(generalization.REPAIR_PATH, "cmpct_r3_product_repair")
    repair.install_generation_hooks(neutral)
    suites = [
        ("neutral_hostile_v1", neutral, root / "neutral"),
        ("resemblance_hostile_v1", hostile, root / "resemblance"),
    ]
    for label, builder, path in suites:
        builder.build(path)
        if label == "neutral_hostile_v1":
            repair.normalize_root(path)
    return suites


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    rows = []
    suites = _build_suites(work_root / "trees")
    try:
        for suite, _builder, root in suites:
            for workload in sorted(path for path in root.iterdir() if path.is_dir()):
                key = (suite, workload.name)
                archive_dir = work_root / "archives" / suite / workload.name
                archive_dir.mkdir(parents=True, exist_ok=True)

                # One exact full-matrix A/B is authoritative for byte/generalization identity.
                base = _one(workload, archive_dir / "baseline.cmpct", historical_sched)
                candidate = _one(workload, archive_dir / "candidate.cmpct", neutral_sched)
                if base["bytes"] != candidate["bytes"] or base["sha256"] != candidate["sha256"]:
                    raise RuntimeError(f"R3 byte identity failed for {suite}/{workload.name}")
                if base["tree_sha256"] != candidate["tree_sha256"]:
                    raise RuntimeError(f"R3 tree identity failed for {suite}/{workload.name}")
                if base["selected"] != candidate["selected"] or base["v029_floor_selected"] != candidate["v029_floor_selected"]:
                    raise RuntimeError(f"R3 selection drift for {suite}/{workload.name}")
                if base["max_selected_member_read_amplification"] != candidate["max_selected_member_read_amplification"]:
                    raise RuntimeError(f"R3 locality drift for {suite}/{workload.name}")

                timing_pairs = []
                if key in RUNTIME_TARGETS:
                    # Two fresh archive pairs, alternating order by round. The earlier full-matrix A/B is not
                    # reused as timing evidence, keeping identity and runtime claims causally separate.
                    for round_index in range(ROUNDS):
                        order = (
                            (("baseline", historical_sched), ("candidate", neutral_sched))
                            if round_index % 2 == 0
                            else (("candidate", neutral_sched), ("baseline", historical_sched))
                        )
                        measured = {}
                        for arm, provider in order:
                            measured[arm] = _one(
                                workload,
                                archive_dir / f"timing-r{round_index + 1}-{arm}.cmpct",
                                provider,
                            )
                        if measured["baseline"]["sha256"] != measured["candidate"]["sha256"]:
                            raise RuntimeError(f"R3 timed-pair byte identity failed for {suite}/{workload.name}")
                        timing_pairs.append({
                            "round": round_index + 1,
                            "order": [arm for arm, _provider in order],
                            "baseline_wall_s": measured["baseline"]["wall_s"],
                            "candidate_wall_s": measured["candidate"]["wall_s"],
                            "baseline_attempt5_child_s": measured["baseline"]["attempt5_child_s"],
                            "candidate_attempt5_child_s": measured["candidate"]["attempt5_child_s"],
                        })

                row = {
                    "suite": suite,
                    "name": workload.name,
                    "bytes": base["bytes"],
                    "sha256": base["sha256"],
                    "tree_sha256": base["tree_sha256"],
                    "selected": base["selected"],
                    "v029_floor_selected": base["v029_floor_selected"],
                    "max_selected_member_read_amplification": base["max_selected_member_read_amplification"],
                    "byte_identical": True,
                    "timing_pairs": timing_pairs,
                }
                if timing_pairs:
                    base_wall = [p["baseline_wall_s"] for p in timing_pairs]
                    cand_wall = [p["candidate_wall_s"] for p in timing_pairs]
                    base_child = [p["baseline_attempt5_child_s"] for p in timing_pairs]
                    cand_child = [p["candidate_attempt5_child_s"] for p in timing_pairs]
                    baseline_wall_median = statistics.median(base_wall)
                    candidate_wall_median = statistics.median(cand_wall)
                    material_regression = _material_runtime_regression(
                        baseline_wall_median, candidate_wall_median
                    )
                    row["timing"] = {
                        "baseline_wall_median_s": baseline_wall_median,
                        "candidate_wall_median_s": candidate_wall_median,
                        "wall_delta_s": candidate_wall_median - baseline_wall_median,
                        "wall_ratio": candidate_wall_median / max(baseline_wall_median, 1e-12),
                        "material_runtime_regression": material_regression,
                        "baseline_attempt5_child_median_s": statistics.median(base_child),
                        "candidate_attempt5_child_median_s": statistics.median(cand_child),
                        "attempt5_child_ratio": statistics.median(cand_child) / max(statistics.median(base_child), 1e-12),
                    }
                rows.append(row)
                print(json.dumps({"suite": suite, "name": workload.name, "bytes": base["bytes"], "timing": row.get("timing")}), flush=True)
    finally:
        isolation.SHARED.V029_SCHED = neutral_sched

    if len(rows) != 15:
        raise RuntimeError(f"expected complete 15-workload matrix, got {len(rows)}")
    if not all(row["byte_identical"] for row in rows):
        raise RuntimeError("R3 product matrix contains byte drift")
    if max(row["max_selected_member_read_amplification"] for row in rows) > isolation.SHARED.MAX_MEMBER_READ_AMP:
        raise RuntimeError("R3 product matrix violates locality ceiling")

    runtime_regressions = [
        f"{row['suite']}/{row['name']}"
        for row in rows
        if row.get("timing", {}).get("material_runtime_regression", False)
    ]
    decision = (
        "REJECT_GLOBAL_NEUTRALIZATION"
        if runtime_regressions
        else "PROMOTE_R3_PRODUCT_NEUTRALIZATION"
    )

    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    return {
        "schema": "cmpct-v030-discovery-r3-product-ab-v1",
        "source_commit": head,
        "frozen_prereg": "docs/v030-rnd/R25_DISCOVERY_SOURCE_GENERIC_R3_BUILDER_PREREG.md",
        "arms": {
            "baseline": "canonical private shared portfolio + historical accepted-v0.29 worker",
            "candidate": "canonical private shared portfolio + v0.30 child-scoped discovery neutral worker",
        },
        "timing_regression_rule": {
            "relative": TIMING_REGRESSION_REL,
            "absolute_s": TIMING_REGRESSION_ABS_S,
            "material_only_if_both_exceeded": True,
            "authority": "docs/PERFORMANCE_RELEASE_GATE.md",
        },
        "rows": rows,
        "totals": {
            "workloads": len(rows),
            "byte_identical_rows": sum(row["byte_identical"] for row in rows),
            "runtime_targets": sum(bool(row["timing_pairs"]) for row in rows),
            "material_runtime_regressions": len(runtime_regressions),
            "runtime_regression_rows": runtime_regressions,
            "max_selected_member_read_amplification": max(row["max_selected_member_read_amplification"] for row in rows),
        },
        "decision": decision,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("CMPCT_V030_Discovery_R3_Product_AB"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["totals"], indent=2), flush=True)


if __name__ == "__main__":
    main()
