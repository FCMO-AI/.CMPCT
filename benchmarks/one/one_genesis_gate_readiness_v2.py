from __future__ import annotations

"""Corrected non-scoring readiness check for the 2026-09-11 CMPCT1 Genesis gate.

V1 correctly refused to score the gate, but mixed the accepted v0.29 repair-v6
identity authority with repair-v5 neutral-workload generation. V2 preserves the
same no-scoring boundary and comparator SHAs while binding generation and expected
identity to the same already-accepted repair-v6 substrate.
"""

import argparse
import json
from pathlib import Path
import sys
import tempfile
from typing import Any

from benchmarks.one import one_genesis_gate_readiness as base

ROOT = Path(__file__).resolve().parents[2]
PREREG = ROOT / "docs" / "one" / "evidence" / "ONE_GENESIS_GATE_READINESS_V2_PREREG_2026-09-09.md"
REPAIR_V6 = ROOT / "benchmarks" / "neutral_hostile_determinism_repair_v6.py"
REPAIR_V6_HISTORY = ROOT / "benchmarks" / "history" / "2026-08-19-neutral-hostile-determinism-repair-v6.json"
DEVELOPER_V6_SHA = "d1706c497de75764b6bd0f49c5d8bdde251694eea40fc683dcbbfed5027c2f49"


def _build_identity_matrix_v6(work_root: Path) -> tuple[list[dict[str, Any]], list[str]]:
    general = base._load(base.GENERALIZATION, "cmpct_one_genesis_readiness_v2_generalization")
    preserved = general._preserved_rows()
    neutral = general._load(
        ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py",
        "cmpct_one_genesis_readiness_v2_neutral",
    )
    hostile = general._load(
        ROOT / "benchmarks" / "resemblance_hostile_corpus_v1.py",
        "cmpct_one_genesis_readiness_v2_hostile",
    )
    repair = general._load(REPAIR_V6, "cmpct_one_genesis_readiness_v2_repair_v6")
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
            files, logical = base._tree_stats(workload)
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

    developer = next(
        (row for row in rows if row.get("suite") == "neutral_hostile_v1" and row.get("name") == "01_developer_repository"),
        None,
    )
    if developer is None:
        errors.append("repair-v6 developer workload missing")
    elif developer.get("tree_sha256") != DEVELOPER_V6_SHA:
        errors.append(
            "repair-v6 developer identity mismatch: "
            f"{developer.get('tree_sha256')} != {DEVELOPER_V6_SHA}"
        )
    return rows, errors


def run(v029_dir: Path, v030_dir: Path, work_root: Path) -> dict[str, Any]:
    # Preserve V1's exact checkout/evidence machinery but replace only the stale
    # repair-v5 substrate binding with the already-accepted repair-v6 authority.
    original_builder = base._build_identity_matrix
    original_authorities = base.AUTHORITY_FILES
    try:
        base._build_identity_matrix = _build_identity_matrix_v6
        base.AUTHORITY_FILES = (
            ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py",
            ROOT / "benchmarks" / "resemblance_hostile_corpus_v1.py",
            REPAIR_V6,
            ROOT / "benchmarks" / "history" / "2026-08-16-entropygraph-v028.json",
            REPAIR_V6_HISTORY,
            ROOT / "benchmarks" / "history" / "2026-08-17-mosaic-v029-generalization-v3.json",
            base.GENERALIZATION,
            PREREG,
        )
        result = base.run(v029_dir, v030_dir, work_root)
    finally:
        base._build_identity_matrix = original_builder
        base.AUTHORITY_FILES = original_authorities

    result["schema"] = "cmpct-one-genesis-gate-readiness-v2"
    result["readiness_revision"] = {
        "generation_authority": "neutral-hostile-repair-v6",
        "repair_source": str(REPAIR_V6.relative_to(ROOT)),
        "repair_history": str(REPAIR_V6_HISTORY.relative_to(ROOT)),
        "developer_expected_tree_sha256": DEVELOPER_V6_SHA,
        "v1_failure_owner": "readiness harness mixed repair-v6 expected identities with repair-v5 generation",
        "expected_hashes_changed": False,
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--v029-dir", type=Path, required=True)
    parser.add_argument("--v030-dir", type=Path, required=True)
    parser.add_argument("--work-root", type=Path)
    parser.add_argument("--output", type=Path, default=Path("one-genesis-gate-readiness-v2.json"))
    args = parser.parse_args()

    if args.work_root is None:
        with tempfile.TemporaryDirectory(prefix="cmpct-one-genesis-readiness-v2-") as td:
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
        "repair": result["readiness_revision"],
        "errors": result["errors"],
    }, indent=2))
    if result["decision"] != "READY_FOR_GENESIS_GATE":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
