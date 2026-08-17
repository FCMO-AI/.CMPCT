from __future__ import annotations

"""Generalization benchmark for the attempt-5 CMPCT research candidate.

The campaign-specific 18-workload gate has already passed.  This harness returns to the 15 public
workloads that supported v0.28 and asks whether the new compiler preserves that frontier while improving
at least one workload and staying inside the preregistered creation-cost/locality envelopes.

Three neutral/hostile workload generators contained producer metadata/path identity that was not stable
across fresh work directories.  Their historical v0.28 record remains immutable; this harness explicitly
uses the separately proven cross-path repair-v3 identities for those three rows and the historical v0.28
identities for the other twelve.

Footnote: the repair is applied to the source tree *before* ``ENGINE.build``.  The embedded v0.28 engine
and attempt #5 therefore consume exactly the same repaired bytes.  No candidate-only normalization or
baseline regeneration can become a compression win.
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
ENGINE_PATH = ROOT / "experiments" / "entropygraph_v029_residual_strict.py"
V028_HISTORY = ROOT / "benchmarks" / "history" / "2026-08-16-entropygraph-v028.json"
REPAIR_HISTORY = ROOT / "benchmarks" / "history" / "2026-08-17-neutral-hostile-determinism-repair-v3.json"
REPAIR_PATH = ROOT / "benchmarks" / "neutral_hostile_determinism_repair_v1.py"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


ENGINE = _load(ENGINE_PATH, "cmpct_v029_generalization_engine")


def _tree_stats(root: Path) -> tuple[int, int]:
    files = [path for path in root.rglob("*") if path.is_file()]
    return len(files), sum(path.stat().st_size for path in files)


def _preserved_rows() -> dict[tuple[str, str], dict]:
    historical = json.loads(V028_HISTORY.read_text(encoding="utf-8"))
    rows = {}
    for row in historical["rows"]:
        copy = dict(row)
        copy["baseline_identity"] = "historical-v0.28"
        rows[(row["suite"], row["name"])] = copy

    repair = json.loads(REPAIR_HISTORY.read_text(encoding="utf-8"))
    if repair.get("schema") != "cmpct-neutral-hostile-v1-determinism-repair-manifest-v3" or not repair.get("accepted"):
        raise RuntimeError("portable neutral/hostile repair-v3 evidence is missing or unaccepted")
    for fixed in repair["rows"]:
        key = ("neutral_hostile_v1", fixed["name"])
        inherited = dict(rows[key])
        inherited.update({
            "tree_sha256": fixed["tree_sha256"],
            "candidate_bytes": int(fixed["v028_candidate_bytes"]),
            "logical_bytes": int(fixed["logical_bytes"]),
            "baseline_identity": "neutral-hostile-repair-v3",
        })
        rows[key] = inherited
    return rows


def _measure_workload(suite: str, path: Path, archive_dir: Path, preserved: dict) -> dict:
    archive_dir.mkdir(parents=True, exist_ok=True)
    archive = archive_dir / f"{path.name}.cmpct"
    files, logical = _tree_stats(path)
    expected = preserved[(suite, path.name)]
    tree = ENGINE.BASE.treehash(path)
    baseline_tree_match = tree == expected["tree_sha256"]

    started = time.perf_counter()
    result = ENGINE.build(path, archive)
    wall = time.perf_counter() - started
    verified = ENGINE.strong_verify(archive)
    if not verified.get("ok") or verified["tree_sha256"] != tree:
        raise RuntimeError(f"attempt-5 strong verification failed for {suite}/{path.name}")

    stats = result["mosaic"]
    embedded_v028_create = float(result["v028"].get("portfolio_create_s", 0.0))
    baseline_bytes_match = int(result["v028_bytes"]) == int(expected["candidate_bytes"])
    return {
        "suite": suite,
        "name": path.name,
        "baseline_identity": expected["baseline_identity"],
        "files": files,
        "logical_bytes": logical,
        "tree_sha256": tree,
        "preserved_tree_sha256": expected["tree_sha256"],
        "baseline_tree_match": baseline_tree_match,
        "preserved_v028_bytes": int(expected["candidate_bytes"]),
        "v028_bytes": int(result["v028_bytes"]),
        "baseline_bytes_match": baseline_bytes_match,
        "candidate_bytes": int(result["archive_bytes"]),
        "research_graph_bytes": int(result["mosaic_graph_bytes"]),
        "selected": result["selected"],
        "saving_vs_v028_bytes": int(result["v028_bytes"] - result["archive_bytes"]),
        "saving_vs_v028_pct": (
            (result["v028_bytes"] - result["archive_bytes"]) / max(1, result["v028_bytes"]) * 100.0
        ),
        "mosaic_nodes": int(stats.get("mosaic_nodes", 0)),
        "residual_pack_records": int(stats.get("residual_pack_records", 0)),
        "residual_packed_delta_nodes": int(stats.get("residual_packed_delta_nodes", 0)),
        "max_mosaic_read_amplification": float(stats.get("max_mosaic_read_amplification", 0.0)),
        "max_additional_recipe_read_amplification": float(
            stats.get("max_additional_recipe_read_amplification", 0.0)
        ),
        "fast_reject_reason": result.get("fast_reject_reason"),
        "attempt5_portfolio_create_s": float(result["portfolio_create_s"]),
        "embedded_v028_portfolio_create_s": embedded_v028_create,
        "create_ratio_vs_v028": (
            float(result["portfolio_create_s"]) / embedded_v028_create if embedded_v028_create > 0 else None
        ),
        "build_wall_s": wall,
    }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    preserved = _preserved_rows()
    neutral = _load(ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py", "cmpct_v029_general_neutral")
    hostile = _load(ROOT / "benchmarks" / "resemblance_hostile_corpus_v1.py", "cmpct_v029_general_hostile")
    repair = _load(REPAIR_PATH, "cmpct_v029_general_repair")
    repair.install_generation_hooks(neutral)

    rows = []
    suites = [
        ("neutral_hostile_v1", neutral, work_root / "neutral"),
        ("resemblance_hostile_v1", hostile, work_root / "resemblance"),
    ]
    for label, builder, root in suites:
        builder.build(root)
        if label == "neutral_hostile_v1":
            repair.normalize_root(root)
        for workload in sorted(path for path in root.iterdir() if path.is_dir()):
            row = _measure_workload(label, workload, work_root / "archives" / label, preserved)
            rows.append(row)
            print(json.dumps({
                "suite": label,
                "name": workload.name,
                "baseline_identity": row["baseline_identity"],
                "v028": row["v028_bytes"],
                "candidate": row["candidate_bytes"],
                "selected": row["selected"],
                "fast_reject_reason": row["fast_reject_reason"],
                "baseline_tree_match": row["baseline_tree_match"],
                "baseline_bytes_match": row["baseline_bytes_match"],
                "create_ratio": row["create_ratio_vs_v028"],
            }), flush=True)

    v028_total = sum(row["v028_bytes"] for row in rows)
    candidate_total = sum(row["candidate_bytes"] for row in rows)
    attempt5_create = sum(row["attempt5_portfolio_create_s"] for row in rows)
    v028_create = sum(row["embedded_v028_portfolio_create_s"] for row in rows)
    totals = {
        "workloads": len(rows),
        "historical_baseline_rows": sum(row["baseline_identity"] == "historical-v0.28" for row in rows),
        "repaired_baseline_rows": sum(row["baseline_identity"] == "neutral-hostile-repair-v3" for row in rows),
        "v028_bytes": v028_total,
        "candidate_bytes": candidate_total,
        "smaller_than_v028_pct": (
            (v028_total - candidate_total) / v028_total * 100.0 if v028_total else 0.0
        ),
        "workloads_improved": sum(row["candidate_bytes"] < row["v028_bytes"] for row in rows),
        "workloads_regressed": sum(row["candidate_bytes"] > row["v028_bytes"] for row in rows),
        "research_selected": sum(row["selected"] == "mosaic" for row in rows),
        "fast_reject_rows": sum(bool(row["fast_reject_reason"]) for row in rows),
        "baseline_tree_drift_rows": sum(not row["baseline_tree_match"] for row in rows),
        "baseline_byte_drift_rows": sum(not row["baseline_bytes_match"] for row in rows),
        "mosaic_nodes": sum(row["mosaic_nodes"] for row in rows),
        "residual_pack_records": sum(row["residual_pack_records"] for row in rows),
        "residual_packed_delta_nodes": sum(row["residual_packed_delta_nodes"] for row in rows),
        "max_mosaic_read_amplification": max(
            (row["max_mosaic_read_amplification"] for row in rows), default=0.0
        ),
        "max_additional_recipe_read_amplification": max(
            (row["max_additional_recipe_read_amplification"] for row in rows), default=0.0
        ),
        "attempt5_portfolio_create_s": attempt5_create,
        "embedded_v028_portfolio_create_s": v028_create,
        "creation_ratio_vs_v028": attempt5_create / v028_create if v028_create else None,
        "median_workload_creation_ratio_vs_v028": statistics.median(
            row["create_ratio_vs_v028"] for row in rows if row["create_ratio_vs_v028"] is not None
        ),
    }
    return {
        "schema": "cmpct-v029-generalization-v2",
        "claim_boundary": (
            "attempt-5 generalization versus exact embedded v0.28 on 12 historical identities plus 3 portable repair-v3 identities"
        ),
        "engine": "experiments/entropygraph_v029_residual_strict.py",
        "preserved_baselines": [
            "benchmarks/history/2026-08-16-entropygraph-v028.json",
            "benchmarks/history/2026-08-17-neutral-hostile-determinism-repair-v3.json",
        ],
        "rows": rows,
        "totals": totals,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("CMPCT_V029_Generalization"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run(args.work_root)
    text = json.dumps(result, indent=2)
    print(json.dumps(result["totals"], indent=2))
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
