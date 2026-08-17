from __future__ import annotations

"""Two-pass proof and v0.28 byte capture for the neutral/hostile determinism repair.

Only the three workloads that drifted during the first v0.29 inherited-frontier run are regenerated.
Each is built twice from scratch, normalized by `neutral_hostile_determinism_repair_v1`, and required to
produce the same exact logical tree hash before a repaired v0.28 baseline artifact is measured.

Footnote: this script never mutates `2026-08-16-entropygraph-v028.json`. Its output is a new evidence
class: a benchmark-substrate repair manifest that can be adopted explicitly by later gates.
"""

import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
NEUTRAL_PATH = ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py"
REPAIR_PATH = ROOT / "benchmarks" / "neutral_hostile_determinism_repair_v1.py"
V028_PATH = ROOT / "experiments" / "entropygraph_v028_strict.py"
OLD_HISTORY = ROOT / "benchmarks" / "history" / "2026-08-16-entropygraph-v028.json"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


N = _load(NEUTRAL_PATH, "cmpct_neutral_v1_for_repair")
R = _load(REPAIR_PATH, "cmpct_neutral_v1_repair")
V028 = _load(V028_PATH, "cmpct_v028_for_repaired_baseline")

BUILDERS = {
    "02_office_workspace": N.corpus_office,
    "05_logs_and_telemetry": N.corpus_logs,
    "06_incremental_backups": N.corpus_backups,
}


def _stats(path: Path) -> tuple[int, int]:
    files = [p for p in path.rglob("*") if p.is_file()]
    return len(files), sum(p.stat().st_size for p in files)


def _old_rows() -> dict[str, dict]:
    data = json.loads(OLD_HISTORY.read_text(encoding="utf-8"))
    return {
        row["name"]: row
        for row in data["rows"]
        if row["suite"] == "neutral_hostile_v1" and row["name"] in BUILDERS
    }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    old = _old_rows()
    rows = []

    for name, builder in BUILDERS.items():
        rounds = []
        for index in (1, 2):
            round_root = work_root / f"round-{index}" / name
            round_root.parent.mkdir(parents=True, exist_ok=True)
            # Builder APIs expect the suite root and create their named workload below it.
            builder(round_root.parent)
            workload = round_root.parent / name
            R.normalize_workload(workload)
            files, logical = _stats(workload)
            rounds.append({
                "tree_sha256": N.tree_hash(workload),
                "files": files,
                "logical_bytes": logical,
                "path": workload,
            })

        if rounds[0]["tree_sha256"] != rounds[1]["tree_sha256"]:
            raise RuntimeError(f"determinism repair failed tree identity for {name}: {rounds}")
        if rounds[0]["logical_bytes"] != rounds[1]["logical_bytes"] or rounds[0]["files"] != rounds[1]["files"]:
            raise RuntimeError(f"determinism repair failed shape identity for {name}: {rounds}")

        archive = work_root / "v028" / f"{name}.cmpct"
        archive.parent.mkdir(parents=True, exist_ok=True)
        result = V028.build(rounds[0]["path"], archive)
        verify = V028.strong_verify(archive)
        if not verify.get("ok") or verify.get("tree_sha256") != rounds[0]["tree_sha256"]:
            raise RuntimeError(f"repaired v0.28 verification failed for {name}")

        previous = old[name]
        rows.append({
            "name": name,
            "files": rounds[0]["files"],
            "logical_bytes": rounds[0]["logical_bytes"],
            "tree_sha256": rounds[0]["tree_sha256"],
            "second_build_tree_sha256": rounds[1]["tree_sha256"],
            "v028_candidate_bytes": int(result["archive_bytes"]),
            "v028_selected": result["selected"],
            "v028_graph_bytes": int(result["graph_bytes"]),
            "v028_inherited_bytes": int(result["legacy_bytes"]),
            "historical_tree_sha256": previous["tree_sha256"],
            "historical_candidate_bytes": int(previous["candidate_bytes"]),
            "historical_logical_bytes": int(previous["logical_bytes"]),
            "repair_changes_tree": rounds[0]["tree_sha256"] != previous["tree_sha256"],
            "repair_candidate_byte_delta": int(result["archive_bytes"]) - int(previous["candidate_bytes"]),
        })

    return {
        "schema": "cmpct-neutral-hostile-v1-determinism-repair-manifest-v1",
        "date": "2026-08-17",
        "claim_boundary": "benchmark-substrate determinism repair only; historical v0.28 evidence remains immutable",
        "normalizer": "benchmarks/neutral_hostile_determinism_repair_v1.py",
        "requirements": {
            "two_independent_regenerations_match": True,
            "candidate_and_baseline_consume_same_repaired_tree": True,
            "historical_record_rewritten": False,
        },
        "rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("CMPCT_Neutral_Hostile_Determinism_Repair"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run(args.work_root)
    text = json.dumps(result, indent=2)
    print(text)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
