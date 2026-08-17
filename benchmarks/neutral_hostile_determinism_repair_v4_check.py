from __future__ import annotations

"""Cross-path proof for neutral/hostile repair-v4 including an FFmpeg-independent media identity.

Each affected workload is regenerated under two different parent directories and normalized. For the
media row, round two deliberately mutates every external-codec output *before* normalization. If the
normalized trees still match, portable identity no longer depends on the exact FFmpeg/x264/LAME/FLAC
bitstream emitted by the runner.
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
REPAIR_PATH = ROOT / "benchmarks" / "neutral_hostile_determinism_repair_v4.py"
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


N = _load(NEUTRAL_PATH, "cmpct_neutral_v1_for_repair_v4")
R = _load(REPAIR_PATH, "cmpct_neutral_v1_repair_v4")
R.install_generation_hooks(N)
V028 = _load(V028_PATH, "cmpct_v028_for_repaired_baseline_v4")

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
        out[file.relative_to(path).as_posix()] = {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
    return out


def _diff(first: dict[str, dict], second: dict[str, dict]) -> list[dict]:
    rows = []
    for rel in sorted(set(first) | set(second)):
        if first.get(rel) != second.get(rel):
            rows.append({"path": rel, "first": first.get(rel), "second": second.get(rel)})
    return rows


def _tree_shape(manifest: dict[str, dict]) -> tuple[int, int]:
    return len(manifest), sum(int(row["bytes"]) for row in manifest.values())


def _historical_rows() -> dict[str, dict]:
    data = json.loads(OLD_HISTORY.read_text(encoding="utf-8"))
    return {
        row["name"]: row
        for row in data["rows"]
        if row["suite"] == "neutral_hostile_v1" and row["name"] in BUILDERS
    }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    old = _historical_rows()
    rows = []

    for name, builder in BUILDERS.items():
        rounds = []
        for index in (1, 2):
            suite_root = work_root / f"round-{index}"
            suite_root.mkdir(parents=True, exist_ok=True)
            builder(suite_root)
            workload = suite_root / name

            volatile_before = {}
            if name == R.MEDIA_WORKLOAD:
                for member in R.VOLATILE_MEDIA:
                    path = workload / member
                    raw = path.read_bytes()
                    volatile_before[member] = {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
                    if index == 2:
                        # Footnote: this deliberate perturbation proves those bytes are outside the v4
                        # identity. It is applied before normalization and never reaches the measured tree.
                        path.write_bytes(raw + b"CMPCT-FFMPEG-INDEPENDENCE-PROBE-v4")

            R.normalize_workload(workload)
            manifest = _file_manifest(workload)
            files, logical = _tree_shape(manifest)
            rounds.append({
                "path": workload,
                "tree_sha256": N.tree_hash(workload),
                "files": files,
                "logical_bytes": logical,
                "file_manifest": manifest,
                "volatile_before_normalization": volatile_before,
            })

        differences = _diff(rounds[0]["file_manifest"], rounds[1]["file_manifest"])
        deterministic = (
            rounds[0]["tree_sha256"] == rounds[1]["tree_sha256"]
            and rounds[0]["files"] == rounds[1]["files"]
            and rounds[0]["logical_bytes"] == rounds[1]["logical_bytes"]
            and not differences
        )
        previous = old[name]
        row = {
            "name": name,
            "deterministic": deterministic,
            "files": rounds[0]["files"],
            "logical_bytes": rounds[0]["logical_bytes"],
            "tree_sha256": rounds[0]["tree_sha256"],
            "second_build_tree_sha256": rounds[1]["tree_sha256"],
            "second_build_logical_bytes": rounds[1]["logical_bytes"],
            "file_differences": differences,
            "volatile_before_normalization": [
                rounds[0]["volatile_before_normalization"], rounds[1]["volatile_before_normalization"]
            ] if name == R.MEDIA_WORKLOAD else [],
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
                raise RuntimeError(f"repair-v4 v0.28 verification failed for {name}")
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
        "schema": "cmpct-neutral-hostile-v1-determinism-repair-manifest-v4",
        "date": "2026-08-17",
        "claim_boundary": "portable benchmark-substrate repair; v3 and historical v0.28 evidence remain immutable",
        "normalizer": "benchmarks/neutral_hostile_determinism_repair_v4.py",
        "requirements": {
            "two_cross_path_regenerations_match": True,
            "candidate_and_baseline_consume_same_repaired_tree": True,
            "historical_record_rewritten": False,
            "repair_v3_composed_not_rewritten": True,
            "media_identity_independent_of_external_ffmpeg_outputs": True,
            "media_stable_core": "14 JPEG + 10 PNG + 1 WAV",
        },
        "accepted": all(row["deterministic"] and row["v028_candidate_bytes"] for row in rows),
        "rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("CMPCT_Neutral_Hostile_Determinism_Repair_v4"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
