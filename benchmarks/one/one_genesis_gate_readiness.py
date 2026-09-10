from __future__ import annotations

"""Non-scoring readiness check for the 2026-09-11 CMPCT1 Genesis gate.

This program intentionally does not encode any workload with CMPCT1, v0.29, or v0.30.
It proves only that the portable 15-workload substrate regenerates exactly and that the
frozen comparator checkouts are the authorities preregistered by CMPCT1 Genesis.

Authority reconciliation: the initial readiness preregistration named repair-v5 even
though the already-accepted v0.29 generalization authority consumes repair-v6 for five
portable neutral/hostile rows. Readiness therefore follows the pre-existing accepted
v0.29 substrate authority (repair-v6) rather than changing any expected identity after
observation. The failed v5 readiness artifact remains preserved as evidence of this bug.
"""

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
V029_SHA = "02b8b27cb2d97af7c6e0797984a898e8fa8a8e5d"
V030_SHA = "f4b158a55a08b9b18b50e4e4abe4b9251048c772"
PREREG = ROOT / "docs" / "one" / "evidence" / "ONE_GENESIS_GATE_READINESS_PREREG_2026-09-09.md"
RECONCILIATION = ROOT / "docs" / "one" / "evidence" / "ONE_GENESIS_GATE_READINESS_AUTHORITY_RECONCILIATION_2026-09-09.md"
GENERALIZATION = ROOT / "benchmarks" / "mosaic_v029_generalization_bench.py"

AUTHORITY_FILES = (
    ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py",
    ROOT / "benchmarks" / "resemblance_hostile_corpus_v1.py",
    ROOT / "benchmarks" / "neutral_hostile_determinism_repair_v6.py",
    ROOT / "benchmarks" / "history" / "2026-08-16-entropygraph-v028.json",
    ROOT / "benchmarks" / "history" / "2026-08-19-neutral-hostile-determinism-repair-v6.json",
    ROOT / "benchmarks" / "history" / "2026-08-17-mosaic-v029-generalization-v3.json",
    PREREG,
    RECONCILIATION,
)

REQUIRED_V029 = (
    "benchmarks/mosaic_v029_generalization_bench.py",
    "benchmarks/history/2026-08-16-entropygraph-v028.json",
    "benchmarks/history/2026-08-19-neutral-hostile-determinism-repair-v6.json",
    "benchmarks/history/2026-08-17-mosaic-v029-generalization-v3.json",
)
REQUIRED_V030 = (
    "benchmarks/geometry_v030_generalization_bench.py",
    "docs/CURRENT_STATE.md",
    "docs/PERFORMANCE_RELEASE_GATE.md",
    "docs/BREAKTHROUGH_REHABILITATION.md",
)


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _git_head(path: Path) -> str:
    return subprocess.check_output(
        ["git", "-C", str(path), "rev-parse", "HEAD"], text=True
    ).strip()


def _tree_stats(root: Path) -> tuple[int, int]:
    files = [path for path in root.rglob("*") if path.is_file()]
    return len(files), sum(path.stat().st_size for path in files)


def _checkout_check(path: Path, expected_sha: str, required: tuple[str, ...]) -> dict[str, Any]:
    observed = _git_head(path)
    missing = [item for item in required if not (path / item).is_file()]
    return {
        "path": str(path),
        "expected_sha": expected_sha,
        "observed_sha": observed,
        "head_match": observed == expected_sha,
        "required_files": list(required),
        "missing_required_files": missing,
        "pass": observed == expected_sha and not missing,
    }


def _build_identity_matrix(work_root: Path) -> tuple[list[dict[str, Any]], list[str]]:
    general = _load(GENERALIZATION, "cmpct_one_genesis_readiness_generalization")
    preserved = general._preserved_rows()
    neutral = general._load(
        ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py",
        "cmpct_one_genesis_readiness_neutral",
    )
    hostile = general._load(
        ROOT / "benchmarks" / "resemblance_hostile_corpus_v1.py",
        "cmpct_one_genesis_readiness_hostile",
    )
    # The preserved v0.29 generalization rows are explicitly repair-v6 authority.
    # Use that exact accepted producer policy; do not synthesize or update expected hashes here.
    repair = general._load(
        ROOT / "benchmarks" / "neutral_hostile_determinism_repair_v6.py",
        "cmpct_one_genesis_readiness_repair_v6",
    )
    repair.install_generation_hooks(neutral)

    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    suites = (
        ("neutral_hostile_v1", neutral, work_root / "neutral"),
        ("resemblance_hostile_v1", hostile, work_root / "resemblance"),
    )
    for suite, builder, root in suites:
        builder.build(root)
        if suite == "neutral_hostile_v1":
            repair.normalize_root(root)
        for workload in sorted(path for path in root.iterdir() if path.is_dir()):
            key = (suite, workload.name)
            expected = preserved.get(key)
            files, logical = _tree_stats(workload)
            tree = general.ENGINE.BASE.treehash(workload)
            if expected is None:
                row = {
                    "suite": suite,
                    "name": workload.name,
                    "unexpected": True,
                    "files": files,
                    "logical_bytes": logical,
                    "tree_sha256": tree,
                    "pass": False,
                }
                errors.append(f"unexpected workload {suite}/{workload.name}")
            else:
                checks = {
                    "files": files == int(expected["files"]),
                    "logical_bytes": logical == int(expected["logical_bytes"]),
                    "tree_sha256": tree == expected["tree_sha256"],
                }
                row = {
                    "suite": suite,
                    "name": workload.name,
                    "baseline_identity": expected["baseline_identity"],
                    "files": files,
                    "expected_files": int(expected["files"]),
                    "logical_bytes": logical,
                    "expected_logical_bytes": int(expected["logical_bytes"]),
                    "tree_sha256": tree,
                    "expected_tree_sha256": expected["tree_sha256"],
                    "checks": checks,
                    "pass": all(checks.values()),
                }
                if not row["pass"]:
                    errors.append(f"identity drift {suite}/{workload.name}: {checks}")
            rows.append(row)

    observed_keys = {(row["suite"], row["name"]) for row in rows}
    expected_keys = set(preserved)
    for missing in sorted(expected_keys - observed_keys):
        errors.append(f"missing workload {missing[0]}/{missing[1]}")
    if len(rows) != 15:
        errors.append(f"expected 15 workloads, observed {len(rows)}")
    neutral_count = sum(row["suite"] == "neutral_hostile_v1" for row in rows)
    hostile_count = sum(row["suite"] == "resemblance_hostile_v1" for row in rows)
    if neutral_count != 10 or hostile_count != 5:
        errors.append(f"expected suite counts 10/5, observed {neutral_count}/{hostile_count}")
    return rows, errors


def run(v029_dir: Path, v030_dir: Path, work_root: Path) -> dict[str, Any]:
    source_head = os.environ.get("EVIDENCE_HEAD")
    if not source_head:
        source_head = _git_head(ROOT)

    authority_hashes = {}
    missing_authorities = []
    for path in AUTHORITY_FILES:
        rel = str(path.relative_to(ROOT))
        if path.is_file():
            authority_hashes[rel] = _sha256(path)
        else:
            missing_authorities.append(rel)

    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    try:
        rows, errors = _build_identity_matrix(work_root)
    except Exception as exc:  # readiness must preserve producer failures as evidence
        errors = [f"workload generation failed: {type(exc).__name__}: {exc}"]

    v029 = _checkout_check(v029_dir, V029_SHA, REQUIRED_V029)
    v030 = _checkout_check(v030_dir, V030_SHA, REQUIRED_V030)
    if missing_authorities:
        errors.append(f"missing current authority files: {missing_authorities}")
    if not v029["pass"]:
        errors.append("frozen v0.29 checkout mismatch or missing authority")
    if not v030["pass"]:
        errors.append("frozen v0.30 checkout mismatch or missing authority")

    all_rows_pass = len(rows) == 15 and all(row.get("pass") for row in rows)
    ready = all_rows_pass and not errors
    return {
        "schema": "cmpct-one-genesis-gate-readiness-v1",
        "claim_boundary": "non-scoring substrate/comparator readiness only; not Genesis gate evidence",
        "experimental_version": "ONE-G0.2",
        "cmpct1_source_head": source_head,
        "frozen_comparators": {"v0.29": v029, "v0.30": v030},
        "authority_sha256": authority_hashes,
        "missing_authority_files": missing_authorities,
        "workload_contract": {
            "expected_workloads": 15,
            "expected_suite_counts": {"neutral_hostile_v1": 10, "resemblance_hostile_v1": 5},
            "observed_workloads": len(rows),
            "observed_suite_counts": {
                "neutral_hostile_v1": sum(row.get("suite") == "neutral_hostile_v1" for row in rows),
                "resemblance_hostile_v1": sum(row.get("suite") == "resemblance_hostile_v1" for row in rows),
            },
            "all_rows_identity_exact": all_rows_pass,
            "rows": rows,
        },
        "scoring_executed": False,
        "candidate_encoding_executed": False,
        "comparator_encoding_executed": False,
        "errors": errors,
        "decision": "READY_FOR_GENESIS_GATE" if ready else "HOLD_GATE_READINESS",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--v029-dir", type=Path, required=True)
    parser.add_argument("--v030-dir", type=Path, required=True)
    parser.add_argument("--work-root", type=Path)
    parser.add_argument("--output", type=Path, default=Path("one-genesis-gate-readiness.json"))
    args = parser.parse_args()

    if args.work_root is None:
        with tempfile.TemporaryDirectory(prefix="cmpct-one-genesis-readiness-") as td:
            result = run(args.v029_dir, args.v030_dir, Path(td))
    else:
        result = run(args.v029_dir, args.v030_dir, args.work_root)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "decision": result["decision"],
        "cmpct1_source_head": result["cmpct1_source_head"],
        "workloads": result["workload_contract"]["observed_workloads"],
        "identity_exact": result["workload_contract"]["all_rows_identity_exact"],
        "v029_exact": result["frozen_comparators"]["v0.29"]["pass"],
        "v030_exact": result["frozen_comparators"]["v0.30"]["pass"],
        "errors": result["errors"],
    }, indent=2))
    if result["decision"] != "READY_FOR_GENESIS_GATE":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
