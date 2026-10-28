from __future__ import annotations

"""Same-run hostile structural oracle for attempt #7 cross-base residual packing."""

import argparse
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import platform
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
ENGINE_PATH = ROOT / "experiments" / "entropygraph_v029_crossbase_residual.py"
HELPER_PATH = ROOT / "benchmarks" / "entropygraph_v028_bench.py"
STRUCTURAL_PATH = ROOT / "benchmarks" / "mosaic_v029_structural_competitors.py"
HOSTILE_PATH = ROOT / "benchmarks" / "resemblance_hostile_corpus_v1.py"
MIN_MARGIN_BELOW_STRONGEST = 16 * 1024


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _tree_stats(root: Path) -> tuple[int, int]:
    files = [path for path in root.rglob("*") if path.is_file()]
    return len(files), sum(path.stat().st_size for path in files)


def run(work_root: Path, source_commit: str | None) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    engine = _load(ENGINE_PATH, "cmpct_v029_crossbase_structural_engine")
    helper = _load(HELPER_PATH, "cmpct_v029_crossbase_structural_helpers")
    structural = _load(STRUCTURAL_PATH, "cmpct_v029_crossbase_structural_measurement")
    hostile = _load(HOSTILE_PATH, "cmpct_v029_crossbase_structural_hostile")

    corpus = work_root / "hostile"
    hostile.build(corpus)
    files, logical = _tree_stats(corpus)
    tree = engine.BASE.treehash(corpus)

    archive = work_root / "attempt7.cmpct"
    result = engine.bench(corpus, archive)
    verified = engine.strong_verify(archive)
    if not verified.get("ok") or verified.get("tree_sha256") != tree:
        raise RuntimeError("attempt-7 structural candidate failed unchanged-reader verification")
    if int(result["archive_bytes"]) > int(result["attempt5_bytes"]):
        raise RuntimeError("attempt-7 exact portfolio regressed against attempt #5")

    competitors_dir = work_root / "competitors"
    competitors_dir.mkdir(parents=True, exist_ok=True)
    competitors = helper._competitors(corpus, competitors_dir)
    if "borg" in competitors:
        competitors["borg"] = structural._repair_measurement(
            "borg", competitors["borg"], competitors_dir / "borg-repo"
        )
    for name, row in competitors.items():
        if row.get("available") and int(row.get("bytes", 0)) <= 0:
            raise RuntimeError(f"available competitor {name} has non-positive bytes")

    required = {name: competitors.get(name, {}) for name in ("tar_zstd19_solid", "zpaq_m5")}
    available = all(row.get("available") and int(row.get("bytes", 0)) > 0 for row in required.values())
    strongest = min(int(row["bytes"]) for row in required.values()) if available else None
    candidate = int(result["archive_bytes"])
    attempt5 = int(result["attempt5_bytes"])
    margin = (strongest - candidate) if strongest is not None else None
    stats = result.get("mosaic", {})
    plan = result.get("crossbase_residual_plan", {})
    locality_green = float(stats.get("max_additional_recipe_read_amplification", 0.0)) <= 2.0
    causal_crossbase = bool(
        result.get("selected") == "crossbase-residual"
        and candidate < attempt5
        and plan.get("selected_crossbase_plan") is True
        and int(plan.get("mixed_base_groups", 0)) >= 1
        and int(plan.get("mixed_base_members", 0)) >= 2
    )
    crossing = bool(
        available
        and causal_crossbase
        and candidate < int(required["tar_zstd19_solid"]["bytes"])
        and candidate < int(required["zpaq_m5"]["bytes"])
        and margin is not None and margin >= MIN_MARGIN_BELOW_STRONGEST
        and locality_green
        and candidate <= attempt5
    )

    return {
        "schema": "cmpct-v029-crossbase-residual-structural-v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "source_commit": source_commit,
        "claim_boundary": "attempt-7 falsification oracle; no v0.29.0 claim",
        "preregistered_gate": {
            "same_run_tar_zstd19_required": True,
            "same_run_zpaq_m5_required": True,
            "candidate_strictly_smaller_than_attempt5": True,
            "causal_mixed_base_plan_required": True,
            "candidate_margin_below_strongest_gte_bytes": MIN_MARGIN_BELOW_STRONGEST,
            "additional_recipe_read_amp_lte": 2.0,
            "unchanged_attempt5_reader": True,
        },
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "tools": structural._tool_identities(),
        },
        "corpus": {
            "suite": "resemblance_hostile_v1_aggregate",
            "files": files,
            "logical_bytes": logical,
            "tree_sha256": tree,
        },
        "candidate": {
            "v028_bytes": int(result["v028_bytes"]),
            "attempt5_bytes": attempt5,
            "attempt7_bytes": candidate,
            "saving_vs_attempt5_bytes": attempt5 - candidate,
            "crossbase_graph_bytes": int(result["crossbase_graph_bytes"]),
            "selected": result["selected"],
            "attempt5_selected": result["attempt5_selected"],
            "max_additional_recipe_read_amplification": float(
                stats.get("max_additional_recipe_read_amplification", 0.0)
            ),
            "strong_verify_median_s": float(result["strong_verify_median_s"]),
            "crossbase_plan": plan,
            "causal_crossbase_selection": causal_crossbase,
        },
        "competitors": competitors,
        "comparison": {
            "required_competitors_available": available,
            "strongest_required_bytes": strongest,
            "margin_below_strongest_bytes": margin,
            "structural_gate_pass": crossing,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("CMPCT_V029_CrossBase_Structural"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-commit")
    args = parser.parse_args()
    result = run(args.work_root, args.source_commit)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"candidate": result["candidate"], "comparison": result["comparison"]}, indent=2))


if __name__ == "__main__":
    main()
