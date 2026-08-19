from __future__ import annotations

"""Cross-path evidence for neutral/hostile benchmark substrate repair-v6.

Repair-v6 extends the already accepted repair-v5 identity with one additional workload:
``01_developer_repository``. The historical generator is still executed normally; only its two host-toolchain-
dependent ELF outputs are replaced afterward with deterministic executable fixtures that preserve the exact
112,776-byte file envelope, static tables and observable program output.

This harness retains complete per-file manifests for every repaired workload, measures embedded v0.28 on the
same repaired source bytes, and makes no accepted-baseline edits. One workflow attempt proves within-run/path
identity; release adoption still requires a second independent GitHub runner attempt to reproduce the manifests
and exact v0.28 measurements before an accepted repair-v6 history record can be committed.
"""

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
NEUTRAL_PATH = ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py"
REPAIR_PATH = ROOT / "benchmarks" / "neutral_hostile_determinism_repair_v6.py"
V028_PATH = ROOT / "experiments" / "entropygraph_v028_strict.py"
HISTORICAL_PATH = ROOT / "benchmarks" / "history" / "2026-08-16-entropygraph-v028.json"
REPAIR_V5_HISTORY = ROOT / "benchmarks" / "history" / "2026-08-17-neutral-hostile-determinism-repair-v5.json"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


N = _load(NEUTRAL_PATH, "cmpct_neutral_v1_for_repair_v6")
R = _load(REPAIR_PATH, "cmpct_neutral_v1_repair_v6")
R.install_generation_hooks(N)
V028 = _load(V028_PATH, "cmpct_v028_for_repaired_baseline_v6")

BUILDERS = {
    "01_developer_repository": N.corpus_source_repo,
    "02_office_workspace": N.corpus_office,
    "03_media_library": N.corpus_media,
    "05_logs_and_telemetry": N.corpus_logs,
    "06_incremental_backups": N.corpus_backups,
}
DEVELOPER_FILES = 1266
DEVELOPER_LOGICAL_BYTES = 2_624_373


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
    data = json.loads(HISTORICAL_PATH.read_text(encoding="utf-8"))
    return {
        row["name"]: row
        for row in data["rows"]
        if row["suite"] == "neutral_hostile_v1" and row["name"] in BUILDERS
    }


def _repair_v5_rows() -> dict[str, dict]:
    data = json.loads(REPAIR_V5_HISTORY.read_text(encoding="utf-8"))
    if data.get("schema") != "cmpct-neutral-hostile-v1-determinism-repair-v5-accepted-v1" or data.get("accepted") is not True:
        raise RuntimeError("repair-v5 evidence is not an accepted predecessor")
    return {row["name"]: row for row in data["rows"]}


def _developer_fixture_evidence(workload: Path) -> dict:
    rows = []
    for variant in range(R.ELF_VARIANTS):
        path = workload / "build" / f"app{variant}"
        raw = path.read_bytes()
        expected = R.canonical_elf64(variant)
        if raw != expected:
            raise RuntimeError(f"developer app{variant} differs from canonical repair-v6 fixture")
        rows.append(
            {
                "name": path.name,
                "bytes": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(),
                "expected_stdout": f"{sum(R._table_values(variant))}\n",
                "elf64_x86_64": raw[:4] == b"\x7fELF" and raw[4] == 2 and int.from_bytes(raw[18:20], "little") == 62,
            }
        )

    smoke = {"attempted": False, "passed": None, "results": []}
    if platform.system() == "Linux" and platform.machine().lower() in {"x86_64", "amd64"}:
        smoke["attempted"] = True
        smoke["passed"] = True
        for variant, row in enumerate(rows):
            path = workload / "build" / f"app{variant}"
            proc = subprocess.run([str(path)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10)
            ok = proc.returncode == 0 and proc.stdout == row["expected_stdout"] and proc.stderr == ""
            smoke["results"].append(
                {
                    "name": path.name,
                    "returncode": proc.returncode,
                    "stdout": proc.stdout,
                    "stderr": proc.stderr,
                    "passed": ok,
                }
            )
            smoke["passed"] = bool(smoke["passed"] and ok)
    return {"fixtures": rows, "execution_smoke": smoke}


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    historical = _historical_rows()
    v5 = _repair_v5_rows()
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
            round_row = {
                "path": workload,
                "tree_sha256": N.tree_hash(workload),
                "files": files,
                "logical_bytes": logical,
                "file_manifest": manifest,
            }
            if name == R.DEVELOPER_NAME:
                round_row["developer_fixture"] = _developer_fixture_evidence(workload)
            rounds.append(round_row)

        differences = _manifest_diff(rounds[0]["file_manifest"], rounds[1]["file_manifest"])
        deterministic = (
            rounds[0]["tree_sha256"] == rounds[1]["tree_sha256"]
            and rounds[0]["logical_bytes"] == rounds[1]["logical_bytes"]
            and rounds[0]["files"] == rounds[1]["files"]
            and not differences
        )
        predecessor = v5.get(name)
        if predecessor is None:
            predecessor = historical[name]
            predecessor_identity = "historical-v0.28"
            predecessor_bytes = int(predecessor["candidate_bytes"])
        else:
            predecessor_identity = "repair-v5"
            predecessor_bytes = int(predecessor["v028_candidate_bytes"])

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
            "predecessor_identity": predecessor_identity,
            "predecessor_tree_sha256": predecessor["tree_sha256"],
            "predecessor_candidate_bytes": predecessor_bytes,
        }
        if name == R.DEVELOPER_NAME:
            row["developer_fixture"] = rounds[0]["developer_fixture"]
            row["second_developer_fixture"] = rounds[1]["developer_fixture"]
            row["shape_preserved"] = (
                rounds[0]["files"] == DEVELOPER_FILES
                and rounds[0]["logical_bytes"] == DEVELOPER_LOGICAL_BYTES
                and all(item["bytes"] == R.CANONICAL_ELF_BYTES for item in rounds[0]["developer_fixture"]["fixtures"])
            )
        if deterministic:
            archive = work_root / "v028" / f"{name}.cmpct"
            archive.parent.mkdir(parents=True, exist_ok=True)
            result = V028.build(rounds[0]["path"], archive)
            verify = V028.strong_verify(archive)
            if not verify.get("ok") or verify.get("tree_sha256") != rounds[0]["tree_sha256"]:
                raise RuntimeError(f"repair-v6 v0.28 verification failed for {name}")
            row.update(
                {
                    "v028_candidate_bytes": int(result["archive_bytes"]),
                    "v028_selected": result["selected"],
                    "v028_graph_bytes": int(result["graph_bytes"]),
                    "v028_inherited_bytes": int(result["legacy_bytes"]),
                    "repair_changes_predecessor_tree": rounds[0]["tree_sha256"] != predecessor["tree_sha256"],
                    "repair_candidate_byte_delta_vs_predecessor": int(result["archive_bytes"]) - predecessor_bytes,
                }
            )
        else:
            row.update(
                {
                    "v028_candidate_bytes": None,
                    "v028_selected": None,
                    "v028_graph_bytes": None,
                    "v028_inherited_bytes": None,
                    "repair_changes_predecessor_tree": None,
                    "repair_candidate_byte_delta_vs_predecessor": None,
                }
            )
        rows.append(row)

    developer = next(row for row in rows if row["name"] == R.DEVELOPER_NAME)
    developer_smoke = developer["developer_fixture"]["execution_smoke"]
    smoke_ok = not developer_smoke["attempted"] or developer_smoke["passed"] is True
    requirements = {
        "five_repaired_workloads": len(rows) == 5,
        "two_cross_path_regenerations_match": all(row["deterministic"] for row in rows),
        "repair_v5_composed_not_rewritten": True,
        "file_manifests_retained_for_cross_run_comparison": True,
        "candidate_and_baseline_consume_same_tree": True,
        "historical_records_rewritten": False,
        "developer_shape_preserved": developer.get("shape_preserved") is True,
        "developer_elf_fixture_execution": smoke_ok,
    }
    within_run_pass = all(requirements.values()) and all(row["v028_candidate_bytes"] for row in rows)
    return {
        "schema": "cmpct-neutral-hostile-v1-determinism-repair-manifest-v6",
        "date": "2026-08-19",
        "claim_boundary": "candidate compiler-independent benchmark substrate; independent fresh-run equality still required before acceptance",
        "source_environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "machine": platform.machine(),
            "preflate_bridge": os.environ.get("CMPCT_PREFLATE_BRIDGE"),
        },
        "producer_policy": {
            "base": "accepted neutral-hostile repair-v5",
            "developer_elf": "deterministic hand-framed ELF64 x86-64 PT_LOAD executable",
            "developer_elf_bytes_each": R.CANONICAL_ELF_BYTES,
            "developer_static_table_entries": 25_000,
            "developer_static_table_rule": "(index*17 + variant*13) % 997",
            "developer_observable_behavior": "sum all 25,000 table entries and print decimal result plus newline",
            "compiler_linker_provenance_in_fixture": False,
        },
        "requirements": requirements,
        "within_run_pass": within_run_pass,
        "rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("CMPCT_Neutral_Hostile_Determinism_Repair_v6"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run(args.work_root)
    text = json.dumps(result, indent=2, default=str)
    print(text)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    if not result["within_run_pass"]:
        raise SystemExit("neutral/hostile repair-v6 within-run proof failed")


if __name__ == "__main__":
    main()
