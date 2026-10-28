from __future__ import annotations

"""Structural competitor sweep for the CMPCT v0.29 research candidate.

This tranche runs only after attempt #5 has passed both the frozen 18-workload Mosaic campaign and the
portable 15-workload inherited-frontier generalization gate. Each public suite is archived as one
complete recursive tree, matching the established v0.28 structural-competitor semantics.

Footnote: the neutral suite is normalized with the separately proven repair-v3 substrate *before* CMPCT
or any competitor sees it. The embedded v0.28 baseline, attempt #5, ZIP, solid tar+Zstd, 7z, ZPAQ,
DwarFS and Borg therefore consume the same bytes. Competitor availability is evidence, not a release
gate; missing tools remain explicit in the record instead of disappearing from the comparison.
"""

import argparse
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
ENGINE_PATH = ROOT / "experiments" / "entropygraph_v029_residual_strict.py"
HELPER_PATH = ROOT / "benchmarks" / "entropygraph_v028_bench.py"
NEUTRAL_PATH = ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py"
HOSTILE_PATH = ROOT / "benchmarks" / "resemblance_hostile_corpus_v1.py"
REPAIR_PATH = ROOT / "benchmarks" / "neutral_hostile_determinism_repair_v1.py"
REPAIR_HISTORY = ROOT / "benchmarks" / "history" / "2026-08-17-neutral-hostile-determinism-repair-v3.json"
GENERALIZATION_HISTORY = ROOT / "benchmarks" / "history" / "2026-08-17-mosaic-v029-generalization-v2.json"


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


def _storage_probe(path: Path) -> dict:
    """Measure a tool-produced repository without assuming it is a flat tree of regular files.

    Footnote: the first structural-competitor run exposed a real harness bug here: Borg completed but
    the inherited `Path.rglob(...).is_file()` probe reported zero bytes. The repair deliberately uses
    lstat-style accounting, does not follow symlinked directories, records both apparent and allocated
    bytes, and requires at least one regular file before a repository can become comparable evidence.
    """
    if not path.exists() and not path.is_symlink():
        return {
            "path_exists": False,
            "entries": 0,
            "regular_files": 0,
            "symlinks": 0,
            "apparent_bytes": 0,
            "allocated_bytes": 0,
        }

    entries = 0
    regular_files = 0
    symlinks = 0
    apparent_bytes = 0
    allocated_bytes = 0
    stack = [path]
    while stack:
        current = stack.pop()
        try:
            st = current.lstat()
        except OSError:
            continue
        entries += 1
        allocated_bytes += int(getattr(st, "st_blocks", 0)) * 512
        if current.is_symlink():
            symlinks += 1
            apparent_bytes += int(st.st_size)
            continue
        if current.is_dir():
            try:
                stack.extend(current.iterdir())
            except OSError:
                continue
            continue
        if current.is_file():
            regular_files += 1
            apparent_bytes += int(st.st_size)

    return {
        "path_exists": True,
        "entries": entries,
        "regular_files": regular_files,
        "symlinks": symlinks,
        "apparent_bytes": apparent_bytes,
        "allocated_bytes": allocated_bytes,
    }


def _repair_measurement(name: str, row: dict, output_path: Path) -> dict:
    """Turn an invalid optional competitor measurement into explicit negative evidence.

    Footnote: optional competitors are not allowed to abort CMPCT's own acceptance gate. A tool that is
    installed and exits successfully but cannot be measured is *not* silently dropped: the raw row is
    retained, a second filesystem probe is attached, and only a defensible positive byte count can keep
    the row `available=True` for structural comparison.
    """
    if not row.get("available") or int(row.get("bytes", 0)) > 0:
        return row

    repaired = dict(row)
    probe = _storage_probe(output_path)
    repaired["measurement_probe"] = probe
    if probe["regular_files"] > 0 and probe["apparent_bytes"] > 0:
        repaired["bytes"] = int(probe["apparent_bytes"])
        repaired["measurement_repaired"] = True
        repaired["measurement_status"] = "recovered_from_filesystem_probe"
        return repaired

    repaired["available"] = False
    repaired["tool_executed"] = True
    repaired["measurement_status"] = "invalid_zero_byte_measurement"
    repaired["reason"] = (
        f"{name} executed successfully but produced no defensible positive repository-byte measurement; "
        "the result is retained as measurement failure rather than aborting or fabricating a competitor size"
    )
    return repaired


def _version_output(executable: str, args: list[str]) -> str | None:
    try:
        proc = subprocess.run(
            [executable, *args], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=15, text=True
        )
    except Exception as exc:
        return f"version probe failed: {type(exc).__name__}: {exc}"
    lines = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
    return " | ".join(lines[:3])[:600] if lines else f"exit={proc.returncode}; no version output"


def _tool_identities() -> dict[str, dict]:
    probes = {
        "zstd": ["--version"],
        "7z": ["i"],
        "zpaq": [],
        "mkdwarfs": ["--version"],
        "borg": ["--version"],
    }
    result = {}
    for name, args in probes.items():
        executable = shutil.which(name)
        result[name] = {
            "available_on_path": bool(executable),
            "executable": executable,
            "version": _version_output(executable, args) if executable else None,
        }
    return result


def _validated_repair_record() -> dict:
    record = json.loads(REPAIR_HISTORY.read_text(encoding="utf-8"))
    if record.get("schema") != "cmpct-neutral-hostile-v1-determinism-repair-manifest-v3":
        raise RuntimeError("unexpected neutral/hostile repair evidence schema")
    if record.get("accepted") is not True:
        raise RuntimeError("neutral/hostile repair-v3 evidence is not accepted")
    return record


def _validated_generalization_record() -> dict:
    record = json.loads(GENERALIZATION_HISTORY.read_text(encoding="utf-8"))
    if record.get("schema") != "cmpct-v029-generalization-v2":
        raise RuntimeError("unexpected v0.29 generalization evidence schema")
    totals = record.get("totals", {})
    if totals.get("workloads_regressed") != 0 or not totals.get("candidate_bytes", 0) < totals.get("v028_bytes", 0):
        raise RuntimeError("v0.29 generalization evidence is not a green frontier")
    if not totals.get("creation_ratio_vs_v028", 99) <= 3.0:
        raise RuntimeError("v0.29 generalization evidence violates the preregistered creation ceiling")
    return record


def _run_suite(engine, helper, suite_name: str, root: Path, work: Path) -> dict:
    archive = work / f"{suite_name}.cmpct"
    result = engine.bench(root, archive)
    files, logical = _tree_stats(root)

    if int(result["archive_bytes"]) > int(result["v028_bytes"]):
        raise RuntimeError(f"attempt #5 aggregate size regression on {suite_name}")
    if result.get("tree_sha256") != engine.BASE.treehash(root):
        raise RuntimeError(f"attempt #5 tree verification mismatch on {suite_name}")

    competitor_dir = work / f"{suite_name}-competitors"
    competitor_dir.mkdir(parents=True, exist_ok=True)
    competitors = helper._competitors(root, competitor_dir)

    # Footnote: the inherited helper predates the structural sweep and can return an execution-success
    # row whose byte probe is not comparable on a particular tool/version. Repair only the measurement
    # boundary here; never alter the competitor payload, command, corpus, or CMPCT acceptance threshold.
    if "borg" in competitors:
        competitors["borg"] = _repair_measurement(
            "borg", competitors["borg"], competitor_dir / "borg-repo"
        )

    for name, row in competitors.items():
        # Footnote: unavailable or unmeasurable competitors remain first-class rows. Any row still marked
        # available must retain a positive byte measurement and semantic description before comparison.
        if row.get("available"):
            if int(row.get("bytes", 0)) <= 0:
                raise RuntimeError(f"available competitor {name} returned no byte measurement")
            if not row.get("semantics"):
                raise RuntimeError(f"available competitor {name} lost its semantic boundary")

    mosaic = result.get("mosaic", {})
    return {
        "suite": suite_name,
        "files": files,
        "logical_bytes": logical,
        "tree_sha256": result["tree_sha256"],
        "v028_bytes": int(result["v028_bytes"]),
        "candidate_bytes": int(result["archive_bytes"]),
        "candidate_saving_bytes": int(result["v028_bytes"] - result["archive_bytes"]),
        "candidate_smaller_than_v028_pct": (
            (int(result["v028_bytes"]) - int(result["archive_bytes"])) / max(1, int(result["v028_bytes"])) * 100.0
        ),
        "selected": result["selected"],
        "candidate_portfolio_create_s": float(result["portfolio_create_s"]),
        "embedded_v028_portfolio_create_s": float(result["v028"].get("portfolio_create_s", 0.0)),
        "strong_verify_median_s": float(result["strong_verify_median_s"]),
        "mosaic_nodes": int(mosaic.get("mosaic_nodes", 0)),
        "residual_pack_records": int(mosaic.get("residual_pack_records", 0)),
        "residual_packed_delta_nodes": int(mosaic.get("residual_packed_delta_nodes", 0)),
        "max_mosaic_read_amplification": float(mosaic.get("max_mosaic_read_amplification", 0.0)),
        "max_additional_recipe_read_amplification": float(
            mosaic.get("max_additional_recipe_read_amplification", 0.0)
        ),
        "fast_reject_reason": result.get("fast_reject_reason"),
        "competitors": competitors,
    }


def run(work_root: Path, source_commit: str | None) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)

    repair_record = _validated_repair_record()
    generalization = _validated_generalization_record()
    engine = _load(ENGINE_PATH, "cmpct_v029_structural_engine")
    helper = _load(HELPER_PATH, "cmpct_v029_structural_helpers")
    neutral = _load(NEUTRAL_PATH, "cmpct_v029_structural_neutral")
    hostile = _load(HOSTILE_PATH, "cmpct_v029_structural_hostile")
    repair = _load(REPAIR_PATH, "cmpct_v029_structural_repair")
    repair.install_generation_hooks(neutral)

    neutral_root = work_root / "neutral"
    neutral.build(neutral_root)
    repair.normalize_root(neutral_root)

    hostile_root = work_root / "hostile"
    hostile.build(hostile_root)

    rows = [
        _run_suite(engine, helper, "neutral_hostile_v1_aggregate", neutral_root, work_root),
        _run_suite(engine, helper, "resemblance_hostile_v1_aggregate", hostile_root, work_root),
    ]

    record = {
        "schema": "cmpct-v029-structural-competitors-v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "source_commit": source_commit,
        "candidate": {
            "name": "attempt #5 Mosaic Placement + Residual Program Packing portfolio",
            "engine": "experiments/entropygraph_v029_residual_strict.py",
            "status": "research frontier; no v0.29.0 or canonical grammar claim",
            "canonical_format_revision": 24,
            "max_dependency_depth": 1,
        },
        "evidence_dependencies": {
            "repair_v3": "benchmarks/history/2026-08-17-neutral-hostile-determinism-repair-v3.json",
            "repair_v3_schema": repair_record["schema"],
            "generalization_v2": "benchmarks/history/2026-08-17-mosaic-v029-generalization-v2.json",
            "generalization_creation_ratio_vs_v028": generalization["totals"]["creation_ratio_vs_v028"],
        },
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "cpu_count": os.cpu_count(),
            "preflate_bridge": os.environ.get("CMPCT_PREFLATE_BRIDGE"),
            "tools": _tool_identities(),
        },
        "rows": rows,
        "totals": {
            "suites": len(rows),
            "v028_bytes": sum(row["v028_bytes"] for row in rows),
            "candidate_bytes": sum(row["candidate_bytes"] for row in rows),
            "candidate_regressed_suites": sum(row["candidate_bytes"] > row["v028_bytes"] for row in rows),
            "candidate_improved_suites": sum(row["candidate_bytes"] < row["v028_bytes"] for row in rows),
            "available_competitor_measurements": sum(
                1 for row in rows for competitor in row["competitors"].values() if competitor.get("available")
            ),
            "competitor_measurement_failures": sum(
                1
                for row in rows
                for competitor in row["competitors"].values()
                if competitor.get("measurement_status") == "invalid_zero_byte_measurement"
            ),
        },
        "method": {
            "aggregation": "each deterministic public suite is archived once as one complete recursive tree",
            "neutral_substrate": "portable repair-v3 applied before every tool sees the neutral aggregate",
            "competitor_availability_is_hard_gate": False,
            "invalid_measurements_are_retained": True,
            "semantic_mismatches_recorded": True,
            "ranking_policy": "no scalar winner; compare exact bytes/time only within each recorded tool semantics",
        },
    }
    return record


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("CMPCT_V029_Structural_Competitors"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-commit")
    args = parser.parse_args()
    record = run(args.work_root, args.source_commit)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(record["totals"], indent=2))


if __name__ == "__main__":
    main()
