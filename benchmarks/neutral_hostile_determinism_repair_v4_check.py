from __future__ import annotations

"""Cross-path proof for the one new repair-v4 identity: FFmpeg-independent media.

Repair-v3 already has durable accepted cross-path evidence for Office, logs, and backups. Re-running those
three inside v4 would add time without adding a new claim, so this proof imports their immutable v3 rows
verbatim and regenerates only ``03_media_library`` twice under different parent directories.

For media, round two deliberately mutates every excluded external-codec placeholder *before*
normalization. If the two normalized 14-JPEG + 10-PNG + 1-WAV trees still match, the v4 identity is
independent of the exact bytes at the historically FFmpeg-controlled paths.

Footnote: importing accepted v3 evidence is not baseline regeneration. The v3 history file is treated as
an immutable dependency and its schema/acceptance/row set are checked before use. Only the new media row
receives a fresh exact v0.28 measurement in this proof.
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
V3_HISTORY = ROOT / "benchmarks" / "history" / "2026-08-17-neutral-hostile-determinism-repair-v3.json"
V3_NAMES = ("02_office_workspace", "05_logs_and_telemetry", "06_incremental_backups")


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


def _file_manifest(path: Path) -> dict[str, dict]:
    out = {}
    for file in sorted(p for p in path.rglob("*") if p.is_file()):
        raw = file.read_bytes()
        out[file.relative_to(path).as_posix()] = {
            "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
        }
    return out


def _diff(first: dict[str, dict], second: dict[str, dict]) -> list[dict]:
    rows = []
    for rel in sorted(set(first) | set(second)):
        if first.get(rel) != second.get(rel):
            rows.append({"path": rel, "first": first.get(rel), "second": second.get(rel)})
    return rows


def _tree_shape(manifest: dict[str, dict]) -> tuple[int, int]:
    return len(manifest), sum(int(row["bytes"]) for row in manifest.values())


def _accepted_v3_rows() -> list[dict]:
    data = json.loads(V3_HISTORY.read_text(encoding="utf-8"))
    if data.get("schema") != "cmpct-neutral-hostile-v1-determinism-repair-manifest-v3":
        raise RuntimeError("unexpected repair-v3 history schema")
    if data.get("accepted") is not True:
        raise RuntimeError("repair-v3 history is not accepted")
    rows = {row["name"]: row for row in data.get("rows", [])}
    if set(rows) != set(V3_NAMES):
        raise RuntimeError(f"repair-v3 row set changed: {sorted(rows)}")

    inherited = []
    for name in V3_NAMES:
        row = dict(rows[name])
        if (
            row.get("deterministic") is not True
            or row.get("tree_sha256") != row.get("second_build_tree_sha256")
            or row.get("file_differences")
            or not int(row.get("v028_candidate_bytes", 0))
        ):
            raise RuntimeError(f"repair-v3 durable row is not internally green: {name}")
        row["repair_v4_source"] = "accepted-repair-v3-history"
        inherited.append(row)
    return inherited


def _historical_media() -> dict:
    data = json.loads(OLD_HISTORY.read_text(encoding="utf-8"))
    for row in data["rows"]:
        if row["suite"] == "neutral_hostile_v1" and row["name"] == R.MEDIA_WORKLOAD:
            return row
    raise RuntimeError("historical media baseline row missing")


def _build_media_round(work_root: Path, index: int) -> dict:
    suite_root = work_root / f"media-round-{index}"
    shutil.rmtree(suite_root, ignore_errors=True)
    suite_root.mkdir(parents=True, exist_ok=True)
    N.corpus_media(suite_root)
    workload = suite_root / R.MEDIA_WORKLOAD

    excluded_before = {}
    for member in R.VOLATILE_MEDIA:
        path = workload / member
        raw = path.read_bytes()
        excluded_before[member] = {
            "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
        }
        if index == 2:
            # Footnote: the second round changes every excluded byte source before normalization. The
            # measured tree must still be identical, proving those bytes cannot influence the v4 identity.
            path.write_bytes(raw + b"CMPCT-EXCLUDED-CODEC-INDEPENDENCE-PROBE-v4")

    R.normalize_workload(workload)
    manifest = _file_manifest(workload)
    files, logical = _tree_shape(manifest)
    return {
        "path": workload,
        "tree_sha256": N.tree_hash(workload),
        "files": files,
        "logical_bytes": logical,
        "file_manifest": manifest,
        "excluded_before_normalization": excluded_before,
    }


def _prove_media(work_root: Path) -> dict:
    rounds = [_build_media_round(work_root, 1), _build_media_round(work_root, 2)]
    differences = _diff(rounds[0]["file_manifest"], rounds[1]["file_manifest"])
    deterministic = (
        rounds[0]["tree_sha256"] == rounds[1]["tree_sha256"]
        and rounds[0]["files"] == rounds[1]["files"]
        and rounds[0]["logical_bytes"] == rounds[1]["logical_bytes"]
        and not differences
    )
    previous = _historical_media()
    row = {
        "name": R.MEDIA_WORKLOAD,
        "repair_v4_source": "fresh-cross-path-media-proof",
        "deterministic": deterministic,
        "regeneration_workspaces": [rounds[0]["path"].parent.as_posix(), rounds[1]["path"].parent.as_posix()],
        "files": rounds[0]["files"],
        "logical_bytes": rounds[0]["logical_bytes"],
        "tree_sha256": rounds[0]["tree_sha256"],
        "second_build_tree_sha256": rounds[1]["tree_sha256"],
        "second_build_logical_bytes": rounds[1]["logical_bytes"],
        "file_differences": differences,
        "excluded_before_normalization": [
            rounds[0]["excluded_before_normalization"],
            rounds[1]["excluded_before_normalization"],
        ],
        "historical_tree_sha256": previous["tree_sha256"],
        "historical_candidate_bytes": int(previous["candidate_bytes"]),
        "historical_logical_bytes": int(previous["logical_bytes"]),
    }

    if not deterministic:
        row.update({
            "v028_candidate_bytes": None,
            "v028_selected": None,
            "v028_graph_bytes": None,
            "v028_inherited_bytes": None,
            "repair_changes_tree": None,
            "repair_candidate_byte_delta": None,
        })
        return row

    archive = work_root / "v028" / f"{R.MEDIA_WORKLOAD}.cmpct"
    archive.parent.mkdir(parents=True, exist_ok=True)
    result = V028.build(rounds[0]["path"], archive)
    verify = V028.strong_verify(archive)
    if not verify.get("ok") or verify.get("tree_sha256") != rounds[0]["tree_sha256"]:
        raise RuntimeError("repair-v4 media v0.28 verification failed")
    row.update({
        "v028_candidate_bytes": int(result["archive_bytes"]),
        "v028_selected": result["selected"],
        "v028_graph_bytes": int(result["graph_bytes"]),
        "v028_inherited_bytes": int(result["legacy_bytes"]),
        "repair_changes_tree": rounds[0]["tree_sha256"] != previous["tree_sha256"],
        "repair_candidate_byte_delta": int(result["archive_bytes"]) - int(previous["candidate_bytes"]),
    })
    return row


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    inherited = _accepted_v3_rows()
    media = _prove_media(work_root)
    rows = [inherited[0], media, inherited[1], inherited[2]]
    accepted = bool(
        media["deterministic"]
        and media["files"] == 25
        and media["tree_sha256"] == media["second_build_tree_sha256"]
        and not media["file_differences"]
        and int(media.get("v028_candidate_bytes") or 0) > 0
    )
    return {
        "schema": "cmpct-neutral-hostile-v1-determinism-repair-manifest-v4",
        "date": "2026-08-17",
        "claim_boundary": "portable benchmark-substrate repair; v3 and historical v0.28 evidence remain immutable",
        "normalizer": "benchmarks/neutral_hostile_determinism_repair_v4.py",
        "evidence_dependencies": {
            "repair_v3": "benchmarks/history/2026-08-17-neutral-hostile-determinism-repair-v3.json",
            "repair_v3_rows_imported": list(V3_NAMES),
            "repair_v4_rows_freshly_proven": [R.MEDIA_WORKLOAD],
        },
        "requirements": {
            "media_two_cross_path_regenerations_match": True,
            "candidate_and_baseline_consume_same_repaired_media_tree": True,
            "historical_record_rewritten": False,
            "repair_v3_composed_not_rewritten": True,
            "media_identity_independent_of_external_ffmpeg_outputs": True,
            "media_stable_core": "14 JPEG + 10 PNG + 1 WAV",
        },
        "accepted": accepted,
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
