from __future__ import annotations

"""Same-run structural crossing oracle for v0.29 attempt #6.

The attempt-6 inherited-frontier gate remains rejected.  This script answers a separate preregistered
question: when the resemblance-hostile suite is one complete recursive tree, can the unchanged-reader
Locality Budget Compiler become strictly smaller than both same-run tar+Zstd-19 and ZPAQ m5?

Footnote: competitor commands are inherited from the corrected structural harness so this oracle cannot
quietly choose friendlier competitor settings.  The corpus is generated once and every tool consumes that
same directory before any crossing field is calculated.
"""

import argparse
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import platform
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
ENGINE_PATH = ROOT / "experiments" / "entropygraph_v029_pack_budget.py"
HELPER_PATH = ROOT / "benchmarks" / "entropygraph_v028_bench.py"
STRUCTURAL_PATH = ROOT / "benchmarks" / "mosaic_v029_structural_competitors.py"
HOSTILE_PATH = ROOT / "benchmarks" / "resemblance_hostile_corpus_v1.py"


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

    engine = _load(ENGINE_PATH, "cmpct_v029_attempt6_structural_engine")
    helper = _load(HELPER_PATH, "cmpct_v029_attempt6_structural_helpers")
    structural = _load(STRUCTURAL_PATH, "cmpct_v029_attempt6_structural_measurement")
    hostile = _load(HOSTILE_PATH, "cmpct_v029_attempt6_structural_hostile")

    corpus = work_root / "hostile"
    hostile.build(corpus)
    files, logical = _tree_stats(corpus)
    tree_sha = engine.BASE.treehash(corpus)

    archive = work_root / "attempt6.cmpct"
    result = engine.bench(corpus, archive)
    verified = engine.strong_verify(archive)
    if not verified.get("ok") or verified.get("tree_sha256") != tree_sha:
        raise RuntimeError("attempt-6 structural candidate failed unchanged-reader verification")
    if int(result["archive_bytes"]) > int(result["attempt5_bytes"]):
        raise RuntimeError("attempt-6 structural portfolio regressed against exact attempt #5")

    competitor_dir = work_root / "competitors"
    competitor_dir.mkdir(parents=True, exist_ok=True)
    competitors = helper._competitors(corpus, competitor_dir)
    if "borg" in competitors:
        competitors["borg"] = structural._repair_measurement(
            "borg", competitors["borg"], competitor_dir / "borg-repo"
        )
    for name, row in competitors.items():
        if row.get("available") and int(row.get("bytes", 0)) <= 0:
            raise RuntimeError(f"available structural competitor {name} has non-positive bytes")

    strongest_names = ("tar_zstd19_solid", "zpaq_m5")
    strongest = {name: competitors.get(name, {}) for name in strongest_names}
    strongest_available = all(row.get("available") and int(row.get("bytes", 0)) > 0 for row in strongest.values())
    strongest_bytes = min((int(row["bytes"]) for row in strongest.values()), default=0) if strongest_available else None
    candidate_bytes = int(result["archive_bytes"])

    allocator = result.get("pack_budget_graph_stats", {}).get("pack_budget", {})
    selected_mosaic = result.get("mosaic", {})
    locality_green = (
        float(selected_mosaic.get("max_mosaic_read_amplification", 0.0)) <= 8.0
        and float(selected_mosaic.get("max_additional_recipe_read_amplification", 0.0)) <= 2.0
        and (
            not result.get("pack_budget_selected")
            or (
                float(allocator.get("read_amp", 0.0)) <= 8.0
                and float(allocator.get("worst_member_amp", 0.0)) <= 8.0
            )
        )
    )
    crossing = bool(
        strongest_available
        and candidate_bytes < int(strongest["tar_zstd19_solid"]["bytes"])
        and candidate_bytes < int(strongest["zpaq_m5"]["bytes"])
        and candidate_bytes <= int(result["attempt5_bytes"])
        and locality_green
    )

    return {
        "schema": "cmpct-v029-attempt6-structural-crossing-v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "source_commit": source_commit,
        "claim_boundary": "attempt-6 structural oracle only; inherited-frontier attempt-6 gate remains REJECT; no v0.29.0 claim",
        "preregistered_gate": {
            "same_run_tar_zstd19_required": True,
            "same_run_zpaq_m5_required": True,
            "candidate_strictly_smaller_than_both": True,
            "candidate_lte_attempt5": True,
            "weighted_pack_read_amp_lte": 8.0,
            "per_member_pack_read_amp_lte": 8.0,
            "mosaic_read_amp_lte": 8.0,
            "additional_recipe_read_amp_lte": 2.0,
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
            "tree_sha256": tree_sha,
        },
        "candidate": {
            "v028_bytes": int(result["v028_bytes"]),
            "attempt5_bytes": int(result["attempt5_bytes"]),
            "attempt6_bytes": candidate_bytes,
            "saving_vs_attempt5_bytes": int(result["attempt5_bytes"]) - candidate_bytes,
            "saving_vs_v028_bytes": int(result["v028_bytes"]) - candidate_bytes,
            "selected": result["selected"],
            "attempt5_selected": result["attempt5_selected"],
            "pack_budget_selected": bool(result["pack_budget_selected"]),
            "pack_budget_graph_bytes": int(result["pack_budget_graph_bytes"]),
            "portfolio_create_s": float(result["portfolio_create_s"]),
            "strong_verify_median_s": float(result["strong_verify_median_s"]),
            "max_mosaic_read_amplification": float(selected_mosaic.get("max_mosaic_read_amplification", 0.0)),
            "max_additional_recipe_read_amplification": float(selected_mosaic.get("max_additional_recipe_read_amplification", 0.0)),
            "pack_budget_weighted_read_amp": float(allocator.get("read_amp", 0.0)) if result.get("pack_budget_selected") else 0.0,
            "pack_budget_worst_member_amp": float(allocator.get("worst_member_amp", 0.0)) if result.get("pack_budget_selected") else 0.0,
            "locality_green": locality_green,
        },
        "competitors": competitors,
        "comparison": {
            "strongest_required_available": strongest_available,
            "strongest_same_run_bytes": strongest_bytes,
            "gap_to_tar_zstd19_bytes": (
                candidate_bytes - int(strongest["tar_zstd19_solid"]["bytes"])
                if strongest.get("tar_zstd19_solid", {}).get("available") else None
            ),
            "gap_to_zpaq_m5_bytes": (
                candidate_bytes - int(strongest["zpaq_m5"]["bytes"])
                if strongest.get("zpaq_m5", {}).get("available") else None
            ),
            "structural_crossing_pass": crossing,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("CMPCT_V029_Attempt6_Structural"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-commit")
    args = parser.parse_args()
    record = run(args.work_root, args.source_commit)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"candidate": record["candidate"], "comparison": record["comparison"]}, indent=2))


if __name__ == "__main__":
    main()
