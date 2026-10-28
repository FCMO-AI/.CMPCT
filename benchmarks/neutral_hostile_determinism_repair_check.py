from __future__ import annotations

"""Cross-path determinism proof and repaired v0.28 byte capture.

The three historically drifting neutral/hostile workloads are regenerated under two *different* parent
directories.  The repair is accepted only when both normalized trees are byte-identical.  This is stronger
than the earlier same-path proof and makes the baseline portable across CI work directories.

Footnote: ReportLab filenames legitimately influenced internal XObject names in the historical builder.
``neutral_hostile_determinism_repair_v1.install_generation_hooks`` changes only that resource-name input
from filename identity to image-content identity.  Raw PDFs are retained before metadata normalization so
the remaining producer differences can be inspected rather than hidden.
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
R.install_generation_hooks(N)
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
    forensic_root = work_root / "forensics"

    for name, builder in BUILDERS.items():
        rounds = []
        for index in (1, 2):
            suite_root = work_root / f"round-{index}"
            shutil.rmtree(suite_root, ignore_errors=True)
            suite_root.mkdir(parents=True, exist_ok=True)
            builder(suite_root)
            workload = suite_root / name

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
                "path": workload,
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
            "regeneration_workspaces": [rounds[0]["path"].parent.as_posix(), rounds[1]["path"].parent.as_posix()],
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
            archive = work_root / "v028" / f"{name}.cmpct"
            archive.parent.mkdir(parents=True, exist_ok=True)
            result = V028.build(rounds[0]["path"], archive)
            verify = V028.strong_verify(archive)
            if not verify.get("ok") or verify.get("tree_sha256") != rounds[0]["tree_sha256"]:
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
        "schema": "cmpct-neutral-hostile-v1-determinism-repair-manifest-v3",
        "date": "2026-08-17",
        "claim_boundary": "portable benchmark-substrate determinism repair only; historical v0.28 evidence remains immutable",
        "normalizer": "benchmarks/neutral_hostile_determinism_repair_v1.py",
        "requirements": {
            "two_cross_path_regenerations_match": True,
            "content_derived_reportlab_xobject_identity": True,
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
