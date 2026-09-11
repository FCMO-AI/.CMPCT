from __future__ import annotations

"""Build the non-scoring, source-derived selective request plan for Genesis.

This script never opens or builds a contender archive. It regenerates the accepted
15-workload source substrate, proves its identities against the accepted v0.29
portable authority, and freezes logical path/range answers before the September 11
comparison can observe any contender layout.
"""

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import tempfile
from typing import Any

from benchmarks import neutral_hostile_corpus_v1 as neutral
from benchmarks import neutral_hostile_determinism_repair_v6 as repair
from benchmarks import resemblance_hostile_corpus_v1 as resemblance
from benchmarks import mosaic_v029_generalization_bench as authority

ROOT = Path(__file__).resolve().parents[2]
PREREG = ROOT / "docs" / "one" / "evidence" / "ONE_GENESIS_SELECTIVE_REQUEST_PLAN_PREREG_2026-09-09.md"


def _tree_stats(root: Path) -> tuple[int, int]:
    files = [p for p in root.rglob("*") if p.is_file() and not p.is_symlink()]
    return len(files), sum(p.stat().st_size for p in files)


def _sha256_file(path: Path) -> str:
    h = sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _range_sha256(path: Path, offset: int, length: int) -> str:
    with path.open("rb") as fh:
        fh.seek(offset)
        data = fh.read(length)
    if len(data) != length:
        raise RuntimeError(f"short source read for {path}: {len(data)} != {length}")
    return sha256(data).hexdigest()


def _ranges(size: int) -> list[tuple[str, int, int]]:
    if size <= 0:
        return []
    proposed: list[tuple[str, int, int]] = [
        ("prefix64", 0, min(64, size)),
        ("prefix4k", 0, min(4096, size)),
    ]
    if size > 4096:
        proposed.append(("middle4k", (size - 4096) // 2, 4096))
    else:
        proposed.append(("middle4k", 0, size))
    if size > 4160:
        proposed.append(("cross4k", 4032, 128))
    tail = min(257, size)
    proposed.append(("suffix257", size - tail, tail))

    result: list[tuple[str, int, int]] = []
    seen: set[tuple[int, int]] = set()
    for name, offset, length in proposed:
        key = (offset, length)
        if length <= 0 or offset < 0 or offset + length > size:
            raise RuntimeError(f"invalid derived request {name}: {offset}+{length}>{size}")
        if key in seen:
            continue
        seen.add(key)
        result.append((name, offset, length))
    return result


def _select_targets(workload: Path) -> list[tuple[str, Path]]:
    files: list[Path] = []
    for path in workload.rglob("*"):
        if path.is_symlink():
            continue
        if path.is_file() and path.stat().st_size > 0:
            files.append(path)
    if not files:
        return []

    relative = lambda p: p.relative_to(workload).as_posix()
    largest = sorted(files, key=lambda p: (-p.stat().st_size, relative(p)))[0]
    selected: list[tuple[str, Path]] = [("largest", largest)]
    eligible = [p for p in files if p.stat().st_size >= 4096]
    if eligible:
        small = sorted(eligible, key=lambda p: (p.stat().st_size, relative(p)))[0]
        if small != largest:
            selected.append(("small-window", small))
    return selected


def _identity_and_requests(
    suite: str,
    workload: Path,
    expected: dict[str, Any],
) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    files, logical = _tree_stats(workload)
    tree = authority.ENGINE.BASE.treehash(workload)
    checks = {
        "files": files == int(expected["files"]),
        "logical_bytes": logical == int(expected["logical_bytes"]),
        "tree_sha256": tree == expected["tree_sha256"],
    }
    if not all(checks.values()):
        errors.append(f"identity drift {suite}/{workload.name}: {checks}")

    targets: list[dict[str, Any]] = []
    for role, path in _select_targets(workload):
        size = path.stat().st_size
        relative = path.relative_to(workload).as_posix()
        target = {
            "role": role,
            "path": relative,
            "logical_bytes": size,
            "sha256": _sha256_file(path),
            "requests": [],
        }
        for request_name, offset, length in _ranges(size):
            target["requests"].append(
                {
                    "name": request_name,
                    "offset": offset,
                    "length": length,
                    "expected_sha256": _range_sha256(path, offset, length),
                }
            )
        targets.append(target)

    return {
        "suite": suite,
        "name": workload.name,
        "baseline_identity": expected["baseline_identity"],
        "files": files,
        "logical_bytes": logical,
        "tree_sha256": tree,
        "expected_tree_sha256": expected["tree_sha256"],
        "identity_checks": checks,
        "targets": targets,
    }, errors


def run(work_root: Path) -> dict[str, Any]:
    shutil.rmtree(work_root, ignore_errors=True)
    neutral_root = work_root / "neutral"
    resemblance_root = work_root / "resemblance"
    neutral_root.parent.mkdir(parents=True, exist_ok=True)

    # Bind generation to the same already-accepted repair-v6 authority as readiness.
    repair.install_generation_hooks(neutral)
    neutral.build(neutral_root)
    repair.normalize_root(neutral_root)
    resemblance.build(resemblance_root)

    expected = authority._preserved_rows()
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    suites = (
        ("neutral_hostile_v1", neutral_root),
        ("resemblance_hostile_v1", resemblance_root),
    )
    for suite, root in suites:
        for workload in sorted(p for p in root.iterdir() if p.is_dir()):
            key = (suite, workload.name)
            expected_row = expected.get(key)
            if expected_row is None:
                errors.append(f"unexpected workload {suite}/{workload.name}")
                continue
            row, row_errors = _identity_and_requests(suite, workload, expected_row)
            rows.append(row)
            errors.extend(row_errors)

    observed_keys = {(r["suite"], r["name"]) for r in rows}
    for missing in sorted(set(expected) - observed_keys):
        errors.append(f"missing workload {missing[0]}/{missing[1]}")
    if len(rows) != 15:
        errors.append(f"expected 15 workloads, observed {len(rows)}")

    flat_requests = [
        {
            "suite": row["suite"],
            "workload": row["name"],
            "tree_sha256": row["tree_sha256"],
            "target_role": target["role"],
            "path": target["path"],
            "file_logical_bytes": target["logical_bytes"],
            "file_sha256": target["sha256"],
            **request,
        }
        for row in rows
        for target in row["targets"]
        for request in target["requests"]
    ]
    canonical_plan = json.dumps(flat_requests, sort_keys=True, separators=(",", ":")).encode("utf-8")

    return {
        "schema": "cmpct-one-genesis-selective-request-plan-v1",
        "cmpct1_source_head": os.environ.get("GITHUB_SHA") or "local-unbound",
        "experimental_state": "ONE-G0.2",
        "claim_boundary": "source-derived selective request geometry only; no contender archive encoding, layout inspection or scoring",
        "generation_authority": "neutral-hostile-repair-v6",
        "prereg": str(PREREG.relative_to(ROOT)),
        "scoring_executed": False,
        "candidate_encoding_executed": False,
        "comparator_encoding_executed": False,
        "archive_layout_inspected": False,
        "workloads": rows,
        "requests": flat_requests,
        "totals": {
            "workloads": len(rows),
            "targets": sum(len(row["targets"]) for row in rows),
            "requests": len(flat_requests),
            "all_workload_identities_exact": all(all(row["identity_checks"].values()) for row in rows) and len(rows) == 15,
            "plan_sha256": sha256(canonical_plan).hexdigest(),
        },
        "errors": errors,
        "decision": "READY_SELECTIVE_REQUEST_PLAN" if not errors else "HOLD_SELECTIVE_REQUEST_PLAN",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path)
    parser.add_argument("--output", type=Path, default=Path("one-genesis-selective-request-plan.json"))
    args = parser.parse_args()

    if args.work_root is None:
        with tempfile.TemporaryDirectory(prefix="cmpct-one-genesis-selective-plan-") as td:
            result = run(Path(td))
    else:
        result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"decision": result["decision"], "totals": result["totals"], "errors": result["errors"]}, indent=2))
    if result["decision"] != "READY_SELECTIVE_REQUEST_PLAN":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
