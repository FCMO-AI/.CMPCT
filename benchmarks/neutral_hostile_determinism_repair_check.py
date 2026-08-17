from __future__ import annotations

"""Two-pass proof and v0.28 byte capture for the neutral/hostile determinism repair.

Only the three workloads that drifted during the first v0.29 inherited-frontier run are regenerated.
Each workload is built twice from scratch at the *same absolute workspace path*, normalized by
``neutral_hostile_determinism_repair_v1``, and compared at tree and individual-file level before the
repaired v0.28 baseline is accepted.

Footnote: the earlier proof used ``round-1`` and ``round-2`` directories.  ReportLab hashes image source
paths into XObject resource names, so changing the parent directory changed otherwise identical PDF page
streams and created false nondeterminism.  Reusing one path while deleting the tree between rounds tests
producer reproducibility without changing a legitimate path-dependent serialization input.
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


def _diff(first: dict[str, dict], second: dict[str, dict]) -> list[dict]:
    rows = []
    for rel in sorted(set(first) | set(second)):
        a = first.get(rel)
        b = second.get(rel)
        if a != b:
            rows.append({"path": rel, "first": a, "second": b})
    return rows


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
    scratch = work_root / "scratch"
    forensic_root = work_root / "forensics"

    for name, builder in BUILDERS.items():
        rounds = []
        for index in (1, 2):
            # Reuse the identical path for both rounds.  ReportLab resource naming legitimately depends
            # on image source paths; changing the path would be a different input, not nondeterminism.
            shutil.rmtree(scratch, ignore_errors=True)
            scratch.mkdir(parents=True, exist_ok=True)
            builder(scratch)
            workload = scratch / name

            raw_pdf = None
            if name == "02_office_workspace":
                source_pdf = workload / "client_report.pdf"
                raw = source_pdf.read_bytes()
                forensic = forensic_root / f"client_report-round-{index}-raw.pdf"
                forensic.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source_pdf, forensic)
                raw_pdf = {
                    "path": forensic.relative_to(work_root).as_posix(),
                    "bytes": len(raw),
                    "sha256": hashlib.sha256(raw).hexdigest(),
                }

            R.normalize_workload(workload)
            manifest = _file_manifest(workload)
            files, logical = _shape(manifest)
            rounds.append({
                "tree_sha256": N.tree_hash(workload),
                "files": files,
                "logical_bytes": logical,
                "file_manifest": manifest,
                "raw_pdf": raw_pdf,
            })

        file_differences = _diff(rounds[0]["file_manifest"], rounds[1]["file_manifest"])
        deterministic = (
            rounds[0]["tree_sha256"] == rounds[1]["tree_sha256"]
            and rounds[0]["logical_bytes"] == rounds[1]["logical_bytes"]
            and rounds[0]["files"] == rounds[1]["files"]
            and not file_differences
        )
        previous = old[name]
        row = {
            "name": name,
            "deterministic": deterministic,
            "regeneration_workspace": scratch.as_posix(),
            "files": rounds[0]["files"],
            "logical_bytes": rounds[0]["logical_bytes"],
            "tree_sha256": rounds[0]["tree_sha256"],
            "second_build_tree_sha256": rounds[1]["tree_sha256"],
            "second_build_logical_bytes": rounds[1]["logical_bytes"],
            "file_differences": file_differences,
            "raw_pdf_rounds": [rounds[0]["raw_pdf"], rounds[1]["raw_pdf"]] if name == "02_office_workspace" else [],
            "historical_tree_sha256": previous["tree_sha256"],
            "historical_candidate_bytes": int(previous["candidate_bytes"]),
            "historical_logical_bytes": int(previous["logical_bytes"]),
        }

        if deterministic:
            # The second regeneration currently occupies the same scratch path and is byte-identical to
            # round one, so it is the correct tree on which to measure the repaired v0.28 baseline.
            workload = scratch / name
            archive = work_root / "v028" / f"{name}.cmpct"
            archive.parent.mkdir(parents=True, exist_ok=True)
            result = V028.build(workload, archive)
            verify = V028.strong_verify(archive)
            if not verify.get("ok") or verify.get("tree_sha256") != rounds[1]["tree_sha256"]:
                raise RuntimeError(f"repaired v0.28 verification failed for {name}")
            row.update({
                "v028_candidate_bytes": int(result["archive_bytes"]),
                "v028_selected": result["selected"],
                "v028_graph_bytes": int(result["graph_bytes"]),
                "v028_inherited_bytes": int(result["legacy_bytes"]),
                "repair_changes_tree": rounds[0]["tree_sha256"] != previous["tree_sha256"],
                "repair_candidate_byte_delta": int(result["archive_bytes"]) - int(previous["candidate_bytes"]),
            })
        else:
            row.update({
                "v028_candidate_bytes": None,
                "v028_selected": None,
                "v028_graph_bytes": None,
                "v028_inherited_bytes": None,
                "repair_changes_tree": None,
                "repair_candidate_byte_delta": None,
            })
        rows.append(row)

    return {
        "schema": "cmpct-neutral-hostile-v1-determinism-repair-manifest-v2",
        "date": "2026-08-17",
        "claim_boundary": "benchmark-substrate determinism repair only; historical v0.28 evidence remains immutable",
        "normalizer": "benchmarks/neutral_hostile_determinism_repair_v1.py",
        "requirements": {
            "two_independent_regenerations_match": True,
            "same_absolute_regeneration_path": True,
            "candidate_and_baseline_consume_same_repaired_tree": True,
            "historical_record_rewritten": False,
            "broad_pdf_fixture_replacement_rejected": True,
        },
        "accepted": all(row["deterministic"] and row["v028_candidate_bytes"] for row in rows),
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
