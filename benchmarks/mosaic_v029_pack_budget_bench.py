from __future__ import annotations

"""Inherited-frontier falsification harness for the v0.29 Locality Budget Compiler on repair-v4.

This is a research comparison against accepted attempt-5 generalization-v3 bytes, not a new version gate.
The same 15-workload frontier is regenerated through the v3 generalization harness, then every row is
checked against durable attempt-5 evidence before any additional saving is counted.

Footnote: repair-v4 makes the aggregate corpus smaller by removing unpinned external-codec outputs. The
performance ratchet therefore preserves the *old absolute* 0.05%-of-v2 hurdle: at least 68,779 additional
bytes must be saved even though 0.05% of the new aggregate is smaller. Substrate repair cannot make the
mechanism easier to pass.
"""

import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import statistics
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
ENGINE_PATH = ROOT / "experiments" / "entropygraph_v029_pack_budget.py"
GENERAL_PATH = ROOT / "benchmarks" / "mosaic_v029_generalization_bench.py"
ATTEMPT5_HISTORY = ROOT / "benchmarks" / "history" / "2026-08-17-mosaic-v029-generalization-v3.json"
ABSOLUTE_ADDITIONAL_SAVING_FLOOR = 68_779


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


ENGINE = _load(ENGINE_PATH, "cmpct_v029_pack_budget_engine")
GENERAL = _load(GENERAL_PATH, "cmpct_v029_pack_budget_generalization")


def _attempt5_rows() -> dict[tuple[str, str], dict]:
    record = json.loads(ATTEMPT5_HISTORY.read_text(encoding="utf-8"))
    if record.get("schema") != "cmpct-v029-generalization-v3":
        raise RuntimeError("unexpected attempt-5 generalization-v3 history schema")
    totals = record.get("totals", {})
    if (
        totals.get("v028_bytes") != 129_471_502
        or totals.get("baseline_tree_drift_rows") != 0
        or totals.get("baseline_byte_drift_rows") != 0
        or totals.get("workloads_regressed") != 0
    ):
        raise RuntimeError("attempt-5 generalization-v3 history is not a stable green frontier")
    return {(row["suite"], row["name"]): row for row in record["rows"]}


def _measure_workload(suite: str, path: Path, archive_dir: Path, preserved: dict, attempt5: dict) -> dict:
    archive_dir.mkdir(parents=True, exist_ok=True)
    archive = archive_dir / f"{path.name}.cmpct"
    files, logical = GENERAL._tree_stats(path)
    expected_v028 = preserved[(suite, path.name)]
    expected_attempt5 = attempt5[(suite, path.name)]
    tree = ENGINE.BASE.treehash(path)

    started = time.perf_counter()
    result = ENGINE.build(path, archive)
    wall = time.perf_counter() - started
    verified = ENGINE.strong_verify(archive)
    if not verified.get("ok") or verified["tree_sha256"] != tree:
        raise RuntimeError(f"pack-budget strong verification failed for {suite}/{path.name}")

    attempt5_bytes = int(result["attempt5_bytes"])
    preserved_attempt5_bytes = int(expected_attempt5["candidate_bytes"])
    allocator_stats = result["pack_budget_graph_stats"].get("pack_budget", {})
    allocator_selected = bool(allocator_stats.get("selected"))
    allocator_worst = float(allocator_stats.get("worst_member_amp", 0.0))
    selected_stats = result["mosaic"]
    embedded_v028_create = float(result["v028"].get("portfolio_create_s", 0.0))
    return {
        "suite": suite,
        "name": path.name,
        "baseline_identity": expected_v028["baseline_identity"],
        "files": files,
        "logical_bytes": logical,
        "tree_sha256": tree,
        "preserved_tree_sha256": expected_v028["tree_sha256"],
        "baseline_tree_match": tree == expected_v028["tree_sha256"],
        "v028_bytes": int(result["v028_bytes"]),
        "preserved_v028_bytes": int(expected_v028["candidate_bytes"]),
        "v028_bytes_match": int(result["v028_bytes"]) == int(expected_v028["candidate_bytes"]),
        "attempt5_bytes": attempt5_bytes,
        "preserved_attempt5_bytes": preserved_attempt5_bytes,
        "attempt5_bytes_match": attempt5_bytes == preserved_attempt5_bytes,
        "candidate_bytes": int(result["archive_bytes"]),
        "saving_vs_attempt5_bytes": attempt5_bytes - int(result["archive_bytes"]),
        "saving_vs_v028_bytes": int(result["v028_bytes"] - result["archive_bytes"]),
        "selected": result["selected"],
        "attempt5_selected": result["attempt5_selected"],
        "pack_budget_selected": bool(result["pack_budget_selected"]),
        "pack_budget_graph_bytes": int(result["pack_budget_graph_bytes"]),
        "pack_budget_root_saving_vs_global": int(allocator_stats.get("saving_vs_global", 0)),
        "pack_budget_strategy": allocator_stats.get("strategy"),
        "pack_budget_exact_cost_probes": int(allocator_stats.get("exact_cost_probes", 0)),
        "pack_budget_weighted_read_amp": float(allocator_stats.get("read_amp", 0.0)) if allocator_selected else 0.0,
        "pack_budget_worst_member_amp": allocator_worst if allocator_selected else 0.0,
        "pack_budget_worst_member_over_budget": bool(
            allocator_selected and allocator_worst > ENGINE.MAX_READ_AMP + 1e-12
        ),
        "pack_read_amplification": float(selected_stats.get("pack_read_amplification", 0.0)),
        "max_mosaic_read_amplification": float(selected_stats.get("max_mosaic_read_amplification", 0.0)),
        "max_additional_recipe_read_amplification": float(
            selected_stats.get("max_additional_recipe_read_amplification", 0.0)
        ),
        "portfolio_create_s": float(result["portfolio_create_s"]),
        "pack_budget_graph_create_s": float(result["pack_budget_graph_create_s"]),
        "embedded_v028_portfolio_create_s": embedded_v028_create,
        "oracle_create_ratio_vs_v028": (
            float(result["portfolio_create_s"]) / embedded_v028_create if embedded_v028_create > 0 else None
        ),
        "build_wall_s": wall,
    }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    preserved = GENERAL._preserved_rows()
    attempt5 = _attempt5_rows()
    neutral = GENERAL._load(ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py", "cmpct_v029_budget_neutral")
    hostile = GENERAL._load(ROOT / "benchmarks" / "resemblance_hostile_corpus_v1.py", "cmpct_v029_budget_hostile")
    repair = GENERAL._load(GENERAL.REPAIR_PATH, "cmpct_v029_budget_repair_v4")
    repair.install_generation_hooks(neutral)

    rows = []
    for label, builder, root in (
        ("neutral_hostile_v1", neutral, work_root / "neutral"),
        ("resemblance_hostile_v1", hostile, work_root / "resemblance"),
    ):
        builder.build(root)
        if label == "neutral_hostile_v1":
            repair.normalize_root(root)
        for workload in sorted(path for path in root.iterdir() if path.is_dir()):
            row = _measure_workload(label, workload, work_root / "archives" / label, preserved, attempt5)
            rows.append(row)
            print(json.dumps({
                "suite": label,
                "name": workload.name,
                "v028": row["v028_bytes"],
                "attempt5": row["attempt5_bytes"],
                "candidate": row["candidate_bytes"],
                "saving_vs_attempt5": row["saving_vs_attempt5_bytes"],
                "pack_budget_selected": row["pack_budget_selected"],
                "strategy": row["pack_budget_strategy"],
                "root_pack_saving": row["pack_budget_root_saving_vs_global"],
                "weighted_read_amp": row["pack_budget_weighted_read_amp"],
                "worst_member_amp": row["pack_budget_worst_member_amp"],
            }), flush=True)

    v028_total = sum(row["v028_bytes"] for row in rows)
    attempt5_total = sum(row["attempt5_bytes"] for row in rows)
    candidate_total = sum(row["candidate_bytes"] for row in rows)
    additional = attempt5_total - candidate_total
    total_saving_vs_v028 = v028_total - candidate_total
    current_pct_floor = (v028_total + 1999) // 2000
    required_additional = max(ABSOLUTE_ADDITIONAL_SAVING_FLOOR, current_pct_floor)
    identity_green = all(
        row["attempt5_bytes_match"] and row["v028_bytes_match"] and row["baseline_tree_match"] for row in rows
    )
    no_regression = all(row["candidate_bytes"] <= row["attempt5_bytes"] for row in rows)
    locality_green = (
        all(not row["pack_budget_worst_member_over_budget"] for row in rows)
        and max((row["pack_budget_weighted_read_amp"] for row in rows), default=0.0) <= ENGINE.MAX_READ_AMP
        and max((row["pack_read_amplification"] for row in rows if row["pack_budget_selected"]), default=0.0)
            <= ENGINE.MAX_READ_AMP
    )
    research_pass = (
        identity_green
        and no_regression
        and locality_green
        and additional >= required_additional
        and sum(row["candidate_bytes"] < row["attempt5_bytes"] for row in rows) >= 2
    )
    totals = {
        "workloads": len(rows),
        "v028_bytes": v028_total,
        "attempt5_bytes": attempt5_total,
        "candidate_bytes": candidate_total,
        "attempt5_saving_vs_v028_bytes": v028_total - attempt5_total,
        "candidate_saving_vs_v028_bytes": total_saving_vs_v028,
        "additional_saving_vs_attempt5_bytes": additional,
        "additional_saving_vs_attempt5_pct_of_v028": additional / max(1, v028_total) * 100.0,
        "current_0_05pct_floor_bytes": current_pct_floor,
        "preserved_absolute_floor_bytes": ABSOLUTE_ADDITIONAL_SAVING_FLOOR,
        "required_additional_saving_bytes": required_additional,
        "candidate_smaller_than_v028_pct": total_saving_vs_v028 / max(1, v028_total) * 100.0,
        "workloads_improved_vs_attempt5": sum(row["candidate_bytes"] < row["attempt5_bytes"] for row in rows),
        "workloads_regressed_vs_attempt5": sum(row["candidate_bytes"] > row["attempt5_bytes"] for row in rows),
        "pack_budget_selected_rows": sum(row["pack_budget_selected"] for row in rows),
        "pack_budget_worst_member_over_budget_rows": sum(row["pack_budget_worst_member_over_budget"] for row in rows),
        "baseline_tree_drift_rows": sum(not row["baseline_tree_match"] for row in rows),
        "v028_byte_drift_rows": sum(not row["v028_bytes_match"] for row in rows),
        "attempt5_byte_drift_rows": sum(not row["attempt5_bytes_match"] for row in rows),
        "max_pack_budget_weighted_read_amp": max((row["pack_budget_weighted_read_amp"] for row in rows), default=0.0),
        "max_pack_budget_worst_member_amp": max((row["pack_budget_worst_member_amp"] for row in rows), default=0.0),
        "max_selected_pack_read_amplification": max(
            (row["pack_read_amplification"] for row in rows if row["pack_budget_selected"]), default=0.0
        ),
        "max_selected_mosaic_read_amplification": max((row["max_mosaic_read_amplification"] for row in rows), default=0.0),
        "max_selected_additional_recipe_read_amplification": max(
            (row["max_additional_recipe_read_amplification"] for row in rows), default=0.0
        ),
        "max_pack_budget_exact_cost_probes": max((row["pack_budget_exact_cost_probes"] for row in rows), default=0),
        "oracle_portfolio_create_s": sum(row["portfolio_create_s"] for row in rows),
        "embedded_v028_portfolio_create_s": sum(row["embedded_v028_portfolio_create_s"] for row in rows),
        "median_oracle_create_ratio_vs_v028": statistics.median(
            row["oracle_create_ratio_vs_v028"] for row in rows if row["oracle_create_ratio_vs_v028"] is not None
        ),
        "research_gate_pass": research_pass,
    }
    return {
        "schema": "cmpct-v029-pack-budget-oracle-v2",
        "claim_boundary": "attempt-6 Locality Budget Compiler oracle versus accepted generalization-v3 attempt-5 bytes; no v0.29.0 claim",
        "engine": "experiments/entropygraph_v029_pack_budget.py",
        "preregistered_research_gate": {
            "attempt5_and_v028_identity_drift_rows_eq": 0,
            "workload_regressions_vs_attempt5_eq": 0,
            "additional_saving_vs_attempt5_gte_pct_of_v028": 0.05,
            "preserved_absolute_additional_saving_floor_bytes": ABSOLUTE_ADDITIONAL_SAVING_FLOOR,
            "workloads_improved_vs_attempt5_gte": 2,
            "weighted_pack_read_amplification_lte": 8.0,
            "per_member_pack_read_amplification_lte": 8.0,
            "final_selected_pack_read_amplification_lte": 8.0,
        },
        "rows": rows,
        "totals": totals,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("CMPCT_V029_Pack_Budget_v2"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["totals"], indent=2))


if __name__ == "__main__":
    main()
