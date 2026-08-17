from __future__ import annotations

"""Structural-competitor v2 wrapper for the accepted repair-v4 neutral substrate.

The original structural-v1 harness and its partial/failure history remain immutable. This wrapper reuses
its exact CMPCT and competitor execution logic, but swaps only evidence dependencies:

- neutral normalization -> repair-v4;
- prerequisite frontier -> accepted generalization-v3;
- result schema/evidence labels -> structural-competitors-v2.

Footnote: no competitor command, compression level, timeout, size accounting, CMPCT engine, locality
threshold, or ranking policy is changed here. A new schema prevents repair-v4 measurements from being
mistaken for the older repair-v3 aggregate.
"""

import argparse
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
BASE_PATH = ROOT / "benchmarks" / "mosaic_v029_structural_competitors.py"
REPAIR_PATH = ROOT / "benchmarks" / "neutral_hostile_determinism_repair_v4.py"
REPAIR_HISTORY = ROOT / "benchmarks" / "history" / "2026-08-17-neutral-hostile-determinism-repair-v4.json"
GENERALIZATION_HISTORY = ROOT / "benchmarks" / "history" / "2026-08-17-mosaic-v029-generalization-v3.json"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


BASE = _load(BASE_PATH, "cmpct_v029_structural_v1_for_repair_v4")
BASE.REPAIR_PATH = REPAIR_PATH
BASE.REPAIR_HISTORY = REPAIR_HISTORY
BASE.GENERALIZATION_HISTORY = GENERALIZATION_HISTORY


def _validated_repair_record() -> dict:
    record = json.loads(REPAIR_HISTORY.read_text(encoding="utf-8"))
    if record.get("schema") != "cmpct-neutral-hostile-v1-determinism-repair-manifest-v4":
        raise RuntimeError("unexpected repair-v4 evidence schema")
    if record.get("accepted") is not True:
        raise RuntimeError("repair-v4 evidence is not accepted")
    media = next((row for row in record.get("rows", []) if row.get("name") == "03_media_library"), None)
    if not media or media.get("excluded_mutation_proven") is not True:
        raise RuntimeError("repair-v4 media evidence lost explicit mutation proof")
    return record


def _validated_generalization_record() -> dict:
    record = json.loads(GENERALIZATION_HISTORY.read_text(encoding="utf-8"))
    if record.get("schema") != "cmpct-v029-generalization-v3":
        raise RuntimeError("unexpected generalization-v3 evidence schema")
    totals = record.get("totals", {})
    if totals.get("baseline_tree_drift_rows") != 0 or totals.get("baseline_byte_drift_rows") != 0:
        raise RuntimeError("generalization-v3 baseline identity is not stable")
    if totals.get("workloads_regressed") != 0 or not totals.get("candidate_bytes", 0) < totals.get("v028_bytes", 0):
        raise RuntimeError("generalization-v3 is not a green frontier")
    if totals.get("v028_bytes") != 129_471_502:
        raise RuntimeError("generalization-v3 exact v0.28 aggregate changed")
    if not totals.get("creation_ratio_vs_v028", 99) <= 3.0:
        raise RuntimeError("generalization-v3 violates the frozen creation ceiling")
    return record


BASE._validated_repair_record = _validated_repair_record
BASE._validated_generalization_record = _validated_generalization_record


def run(work_root: Path, source_commit: str | None) -> dict:
    record = BASE.run(work_root, source_commit)
    repair = _validated_repair_record()
    generalization = _validated_generalization_record()
    record["schema"] = "cmpct-v029-structural-competitors-v2"
    record["evidence_dependencies"] = {
        "repair_v4": "benchmarks/history/2026-08-17-neutral-hostile-determinism-repair-v4.json",
        "repair_v4_schema": repair["schema"],
        "generalization_v3": "benchmarks/history/2026-08-17-mosaic-v029-generalization-v3.json",
        "generalization_v3_candidate_bytes": int(generalization["totals"]["candidate_bytes"]),
        "generalization_creation_ratio_vs_v028": float(generalization["totals"]["creation_ratio_vs_v028"]),
    }
    record["method"] = dict(record["method"])
    record["method"]["neutral_substrate"] = (
        "portable repair-v4 applied before every tool sees the neutral aggregate; media core is 14 JPEG + 10 PNG + 1 WAV"
    )
    return record


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("CMPCT_V029_Structural_Competitors_v4"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-commit")
    args = parser.parse_args()
    record = run(args.work_root, args.source_commit)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(record["totals"], indent=2))


if __name__ == "__main__":
    main()
