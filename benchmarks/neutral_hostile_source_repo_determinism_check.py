from __future__ import annotations

"""File-granular determinism proof for the neutral/hostile developer-repository workload.

The canonical v0.30 gate found that ``01_developer_repository`` no longer reproduces the tree SHA recorded
by the accepted v0.28 evidence even though the generator source and the recorded Python/NumPy/GCC versions
match. This probe answers the prerequisite question before anyone edits a frozen hash: does the workload
reproduce *itself* byte-for-byte on the current release substrate, and if not, which files drift?

Footnote: this module is intentionally diagnostic and read-only with respect to the corpus. It records
per-file hashes plus compiler/linker identity and ELF note/build-id metadata, but never normalizes bytes or
updates benchmark expectations. A later repair must therefore explain the evidence rather than hiding it.
"""

import argparse
import hashlib
import importlib.util
import json
import platform
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
GENERATOR_PATH = ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py"
HISTORY_PATH = ROOT / "benchmarks" / "history" / "2026-08-16-entropygraph-v028.json"
WORKLOAD = "01_developer_repository"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _command(argv: list[str]) -> dict:
    try:
        proc = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=30)
    except Exception as exc:  # diagnostic evidence must survive a missing optional tool
        return {"argv": argv, "returncode": None, "output": f"{type(exc).__name__}: {exc}"}
    return {"argv": argv, "returncode": proc.returncode, "output": proc.stdout.strip()}


def _manifest(root: Path) -> dict[str, dict]:
    rows: dict[str, dict] = {}
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        raw = path.read_bytes()
        rows[path.relative_to(root).as_posix()] = {
            "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
        }
    return rows


def _diff(first: dict[str, dict], second: dict[str, dict]) -> list[dict]:
    rows = []
    for rel in sorted(set(first) | set(second)):
        a = first.get(rel)
        b = second.get(rel)
        if a != b:
            rows.append({"path": rel, "first": a, "second": b})
    return rows


def _historical_row() -> dict:
    data = json.loads(HISTORY_PATH.read_text(encoding="utf-8"))
    for row in data["rows"]:
        if row.get("suite") == "neutral_hostile_v1" and row.get("name") == WORKLOAD:
            return row
    raise RuntimeError("accepted v0.28 history is missing developer-repository row")


def _elf_notes(workload: Path) -> dict[str, dict]:
    out = {}
    for name in ("app0", "app1"):
        path = workload / "build" / name
        raw = path.read_bytes()
        out[name] = {
            "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "notes": _command(["readelf", "-n", str(path)]),
            "comment": _command(["readelf", "-p", ".comment", str(path)]),
        }
    return out


def run(work_root: Path) -> dict:
    generator = _load(GENERATOR_PATH, "cmpct_neutral_source_repo_probe")
    historical = _historical_row()
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True, exist_ok=True)

    rounds = []
    for index, parent_name in enumerate(("path-alpha", "path-beta"), start=1):
        parent = work_root / parent_name
        parent.mkdir(parents=True, exist_ok=True)
        generator.corpus_source_repo(parent)
        workload = parent / WORKLOAD
        manifest = _manifest(workload)
        rounds.append(
            {
                "round": index,
                "parent": parent.as_posix(),
                "tree_sha256": generator.tree_hash(workload),
                "files": len(manifest),
                "logical_bytes": sum(int(row["bytes"]) for row in manifest.values()),
                "manifest": manifest,
                "elf": _elf_notes(workload),
            }
        )

    differences = _diff(rounds[0]["manifest"], rounds[1]["manifest"])
    deterministic = (
        rounds[0]["tree_sha256"] == rounds[1]["tree_sha256"]
        and rounds[0]["files"] == rounds[1]["files"]
        and rounds[0]["logical_bytes"] == rounds[1]["logical_bytes"]
        and not differences
    )
    historical_tree = str(historical["tree_sha256"])

    return {
        "schema": "cmpct-neutral-hostile-source-repo-determinism-probe-v1",
        "workload": WORKLOAD,
        "claim_boundary": "diagnostic only; no corpus normalization and no historical expectation rewrite",
        "generator_blob_note": "workflow records repository SHA separately; this report fingerprints generated bytes",
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "gcc": _command(["gcc", "--version"]),
            "ld": _command(["ld", "--version"]),
            "as": _command(["as", "--version"]),
            "readelf": _command(["readelf", "--version"]),
        },
        "historical": {
            "tree_sha256": historical_tree,
            "files": int(historical["files"]),
            "logical_bytes": int(historical["logical_bytes"]),
            "candidate_bytes": int(historical["candidate_bytes"]),
        },
        "current": {
            "tree_sha256": rounds[0]["tree_sha256"],
            "second_tree_sha256": rounds[1]["tree_sha256"],
            "files": rounds[0]["files"],
            "logical_bytes": rounds[0]["logical_bytes"],
            "deterministic_across_paths": deterministic,
            "matches_historical_tree": rounds[0]["tree_sha256"] == historical_tree,
            "file_differences_between_rounds": differences,
            "elf_rounds": [rounds[0]["elf"], rounds[1]["elf"]],
        },
        # Footnote: retaining both manifests makes a future substrate comparison possible without preserving
        # the multi-megabyte corpus itself, while hashes ensure no private or mutable source content is copied.
        "round_manifests": [rounds[0]["manifest"], rounds[1]["manifest"]],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("CMPCT_Source_Repo_Determinism_Probe"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run(args.work_root)
    text = json.dumps(result, indent=2)
    print(text)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    if not result["current"]["deterministic_across_paths"]:
        raise SystemExit("developer-repository workload is not deterministic across generation paths")


if __name__ == "__main__":
    main()
