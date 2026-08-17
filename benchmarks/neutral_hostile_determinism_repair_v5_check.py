from __future__ import annotations

"""Cross-path proof with retained file manifests for candidate media repair-v5.

Unlike repair-v4, the evidence record deliberately retains each affected workload's file manifest.  That
makes a future *cross-run* mismatch diagnosable at file granularity instead of collapsing it into one tree
hash.  A single runner still performs two differently nested regenerations first; external acceptance
requires a second independent workflow attempt to reproduce the same manifests and exact v0.28 bytes.
"""

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
NEUTRAL_PATH = ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py"
REPAIR_PATH = ROOT / "benchmarks" / "neutral_hostile_determinism_repair_v5.py"
V028_PATH = ROOT / "experiments" / "entropygraph_v028_strict.py"
OLD_HISTORY = ROOT / "benchmarks" / "history" / "2026-08-16-entropygraph-v028.json"
REPAIR_V3_HISTORY = ROOT / "benchmarks" / "history" / "2026-08-17-neutral-hostile-determinism-repair-v3.json"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


N = _load(NEUTRAL_PATH, "cmpct_neutral_v1_for_repair_v5")
R = _load(REPAIR_PATH, "cmpct_neutral_v1_repair_v5")
R.install_generation_hooks(N)
V028 = _load(V028_PATH, "cmpct_v028_for_repaired_baseline_v5")

BUILDERS = {
    "02_office_workspace": N.corpus_office,
    "03_media_library": N.corpus_media,
    "05_logs_and_telemetry": N.corpus_logs,
    "06_incremental_backups": N.corpus_backups,
}


def _file_manifest(path: Path) -> dict[str, dict]:
    out = {}
    for file in sorted(p for p in path.rglob("*") if p.is_file()):
        raw = file.read_bytes()
        out[file.relative_to(path).as_posix()] = {
            "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
        }
    return out


def _shape(manifest: dict[str, dict]) -> tuple[int, int]:
    return len(manifest), sum(int(row["bytes"]) for row in manifest.values())


def _manifest_diff(first: dict[str, dict], second: dict[str, dict]) -> list[dict]:
    rows = []
    for rel in sorted(set(first) | set(second)):
        if first.get(rel) != second.get(rel):
            rows.append({"path": rel, "first": first.get(rel), "second": second.get(rel)})
    return rows


def _historical_rows() -> dict[str, dict]:
    data = json.loads(OLD_HISTORY.read_text(encoding="utf-8"))
    return {
        row["name"]: row
        for row in data["rows"]
        if row["suite"] == "neutral_hostile_v1" and row["name"] in BUILDERS
    }


def _repair_v3_rows() -> dict[str, dict]:
    data = json.loads(REPAIR_V3_HISTORY.read_text(encoding="utf-8"))
    if data.get("schema") != "cmpct-neutral-hostile-v1-determinism-repair-manifest-v3" or data.get("accepted") is not True:
        raise RuntimeError("repair-v3 evidence is not an accepted predecessor")
    return {row["name"]: row for row in data["rows"]}


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    historical = _historical_rows()
    v3 = _repair_v3_rows()
    rows = []

    for name, builder in BUILDERS.items():
        rounds = []
        for index, relroot in ((1, "alpha/deep"), (2, "beta")):
            suite_root = work_root / relroot / f"round-{index}"
            shutil.rmtree(suite_root, ignore_errors=True)
            suite_root.mkdir(parents=True, exist_ok=True)
            builder(suite_root)
            workload = suite_root / name
            R.normalize_workload(workload)
            manifest = _file_manifest(workload)
            files, logical = _shape(manifest)
            rounds.append({
                "path": workload,
                "tree_sha256": N.tree_hash(workload),
                "files": files,
                "logical_bytes": logical,
                "file_manifest": manifest,
            })

        differences = _manifest_diff(rounds[0]["file_manifest"], rounds[1]["file_manifest"])
        deterministic = (
            rounds[0]["tree_sha256"] == rounds[1]["tree_sha256"]
            and rounds[0]["logical_bytes"] == rounds[1]["logical_bytes"]
            and rounds[0]["files"] == rounds[1]["files"]
            and not differences
        )
        old = historical[name]
        predecessor = v3.get(name)
        predecessor_tree = predecessor["tree_sha256"] if predecessor else old["tree_sha256"]
        predecessor_bytes = int(predecessor["v028_candidate_bytes"] if predecessor else old["candidate_bytes"])
        row = {
            "name": name,
            "deterministic": deterministic,
            "files": rounds[0]["files"],
            "logical_bytes": rounds[0]["logical_bytes"],
            "tree_sha256": rounds[0]["tree_sha256"],
            "second_build_tree_sha256": rounds[1]["tree_sha256"],
            "file_manifest": rounds[0]["file_manifest"],
            "second_build_file_manifest": rounds[1]["file_manifest"],
            "file_differences": differences,
            "predecessor_identity": "repair-v3" if predecessor else "historical-v0.28",
            "predecessor_tree_sha256": predecessor_tree,
            "predecessor_candidate_bytes": predecessor_bytes,
        }
        if deterministic:
            archive = work_root / "v028" / f"{name}.cmpct"
            archive.parent.mkdir(parents=True, exist_ok=True)
            result = V028.build(rounds[0]["path"], archive)
            verify = V028.strong_verify(archive)
            if not verify.get("ok") or verify.get("tree_sha256") != rounds[0]["tree_sha256"]:
                raise RuntimeError(f"repair-v5 v0.28 verification failed for {name}")
            row.update({
                "v028_candidate_bytes": int(result["archive_bytes"]),
                "v028_selected": result["selected"],
                "v028_graph_bytes": int(result["graph_bytes"]),
                "v028_inherited_bytes": int(result["legacy_bytes"]),
                "repair_changes_predecessor_tree": rounds[0]["tree_sha256"] != predecessor_tree,
                "repair_candidate_byte_delta_vs_predecessor": int(result["archive_bytes"]) - predecessor_bytes,
            })
        else:
            row.update({
                "v028_candidate_bytes": None,
                "v028_selected": None,
                "v028_graph_bytes": None,
                "v028_inherited_bytes": None,
                "repair_changes_predecessor_tree": None,
                "repair_candidate_byte_delta_vs_predecessor": None,
            })
        rows.append(row)

    media = next(row for row in rows if row["name"] == "03_media_library")
    return {
        "schema": "cmpct-neutral-hostile-v1-determinism-repair-manifest-v5",
        "date": "2026-08-17",
        "claim_boundary": "candidate CPU-canonical benchmark substrate; external fresh-run equality still required before acceptance",
        "producer_policy": {
            "ffmpeg_cpuflags": "0",
            "ffmpeg_cpucount": 1,
            "ffmpeg_bitexact": True,
            "encoder_threads": 1,
            "filter_threads": 1,
            "x264_params": R.X264_CANONICAL_PARAMS,
        },
        "requirements": {
            "two_cross_path_regenerations_match": all(row["deterministic"] for row in rows),
            "repair_v3_composed_not_rewritten": True,
            "file_manifests_retained_for_cross_run_comparison": True,
            "candidate_and_baseline_consume_same_tree": True,
            "historical_record_rewritten": False,
        },
        "within_run_pass": all(row["deterministic"] and row["v028_candidate_bytes"] for row in rows),
        "media": {
            "deterministic": media["deterministic"],
            "tree_sha256": media["tree_sha256"],
            "logical_bytes": media["logical_bytes"],
            "v028_candidate_bytes": media["v028_candidate_bytes"],
            "file_manifest": media["file_manifest"],
        },
        "rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("CMPCT_Neutral_Hostile_Determinism_Repair_v5"))
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
