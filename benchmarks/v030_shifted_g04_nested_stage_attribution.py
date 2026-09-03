from __future__ import annotations

"""Frozen D1 nested-stage attribution for the Shifted shared v0.28 + attempt-5 pair.

No product behavior changes. Fresh workers call the unchanged inherited builders while timing only their
existing internal stage boundaries. The experiment asks whether both expensive children are themselves
owned by graph-construction stages, which decides where an exact fail-open stopping proof must enter.
"""

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import statistics
import subprocess
import sys
import time

from benchmarks import v030_release_performance as PERF

ROOT = Path(__file__).resolve().parents[1]
TARGET = ("resemblance_hostile_v1", "01_shifted_versions")
REPETITIONS = 3
STAGE_DOMINANT_RATIO = 0.80
MATERIAL_SECONDARY_RATIO = 0.20
EXPECTED_V028_BYTES = 1_761_927
EXPECTED_ATTEMPT5_BYTES = 1_723_391


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _measure_v028(source: Path, archive: Path) -> dict:
    from experiments import entropygraph_v029_residual_fast as accepted

    v028 = accepted.V028
    legacy_original = v028.BASE.BASE.build
    graph_original = v028._build_graph
    stage = {"legacy_s": 0.0, "graph_s": 0.0, "legacy_calls": 0, "graph_calls": 0}

    def timed_legacy():
        started = time.perf_counter()
        try:
            return legacy_original()
        finally:
            stage["legacy_s"] += time.perf_counter() - started
            stage["legacy_calls"] += 1

    def timed_graph(root: Path, out: Path):
        started = time.perf_counter()
        try:
            return graph_original(root, out)
        finally:
            stage["graph_s"] += time.perf_counter() - started
            stage["graph_calls"] += 1

    v028.BASE.BASE.build = timed_legacy
    v028._build_graph = timed_graph
    started = time.perf_counter()
    try:
        stats = dict(v028.build(source, archive))
    finally:
        child_s = time.perf_counter() - started
        v028.BASE.BASE.build = legacy_original
        v028._build_graph = graph_original

    verified = dict(v028.strong_verify(archive))
    return {
        "kind": "v028",
        "child_s": child_s,
        "archive_bytes": archive.stat().st_size,
        "archive_sha256": _sha(archive),
        "selected": stats.get("selected"),
        "verify_ok": bool(verified.get("ok")),
        "tree_sha256": verified.get("tree_sha256"),
        **stage,
    }


def _measure_attempt5(source: Path, archive: Path) -> dict:
    from experiments import entropygraph_v029_residual_fast as accepted

    base = accepted.BASE
    placement_original = base.A4.build_graph
    residual_original = base._compile_residual
    stage = {"placement_s": 0.0, "residual_s": 0.0, "placement_calls": 0, "residual_calls": 0}

    def timed_placement(root: Path, out: Path):
        started = time.perf_counter()
        try:
            return placement_original(root, out)
        finally:
            stage["placement_s"] += time.perf_counter() - started
            stage["placement_calls"] += 1

    def timed_residual(placement: Path, out: Path):
        started = time.perf_counter()
        try:
            return residual_original(placement, out)
        finally:
            stage["residual_s"] += time.perf_counter() - started
            stage["residual_calls"] += 1

    base.A4.build_graph = timed_placement
    base._compile_residual = timed_residual
    started = time.perf_counter()
    try:
        stats = dict(accepted.build_graph(source, archive))
    finally:
        child_s = time.perf_counter() - started
        base.A4.build_graph = placement_original
        base._compile_residual = residual_original

    verified = dict(accepted.strong_verify(archive))
    return {
        "kind": "attempt5",
        "child_s": child_s,
        "archive_bytes": archive.stat().st_size,
        "archive_sha256": _sha(archive),
        "selected": stats.get("selected"),
        "verify_ok": bool(verified.get("ok")),
        "tree_sha256": verified.get("tree_sha256"),
        **stage,
    }


def _worker(kind: str, source: Path, archive: Path) -> dict:
    if kind == "v028":
        return _measure_v028(source, archive)
    if kind == "attempt5":
        return _measure_attempt5(source, archive)
    raise ValueError(kind)


def _fresh(kind: str, source: Path, archive: Path) -> dict:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    proc = subprocess.run(
        [sys.executable, __file__, "--worker", kind, "--source", os.fspath(source), "--archive", os.fspath(archive)],
        cwd=ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    if proc.returncode != 0 or not lines:
        raise RuntimeError(
            f"fresh nested-stage worker failed kind={kind} rc={proc.returncode} "
            f"stdout={proc.stdout[-2000:]!r} stderr={proc.stderr[-4000:]!r}"
        )
    return json.loads(lines[-1])


def run(work_root: Path) -> dict:
    work_root = Path(work_root)
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    source = PERF._build_corpora(work_root / "corpora")[TARGET]
    rows = []
    for rep in range(1, REPETITIONS + 1):
        order = ("v028", "attempt5") if rep % 2 else ("attempt5", "v028")
        measured = {}
        for kind in order:
            measured[kind] = _fresh(kind, source, work_root / f"rep-{rep}-{kind}.cmpct")
        rows.append({"rep": rep, "order": list(order), **measured})

    expected_tree = rows[0]["v028"]["tree_sha256"]
    invalid = []
    for row in rows:
        for kind, expected_bytes in (("v028", EXPECTED_V028_BYTES), ("attempt5", EXPECTED_ATTEMPT5_BYTES)):
            item = row[kind]
            checks = {
                "positive_child": math.isfinite(float(item["child_s"])) and float(item["child_s"]) > 0,
                "expected_bytes": int(item["archive_bytes"]) == expected_bytes,
                "verify": item["verify_ok"] is True,
                "tree_identity": item["tree_sha256"] == expected_tree,
                "single_stage_calls": (
                    int(item["legacy_calls"]) == 1 and int(item["graph_calls"]) == 1
                    if kind == "v028"
                    else int(item["placement_calls"]) == 1 and int(item["residual_calls"]) == 1
                ),
            }
            if kind == "v028":
                checks["finite_stages"] = all(
                    math.isfinite(float(item[k])) and float(item[k]) >= 0 for k in ("legacy_s", "graph_s")
                )
            else:
                checks["finite_stages"] = all(
                    math.isfinite(float(item[k])) and float(item[k]) >= 0 for k in ("placement_s", "residual_s")
                )
            item["checks"] = checks
            invalid.extend(f"rep-{row['rep']}:{kind}:{name}" for name, ok in checks.items() if not ok)

    def med(kind: str, field: str) -> float:
        return float(statistics.median(float(row[kind][field]) for row in rows))

    v_child = med("v028", "child_s")
    v_legacy = med("v028", "legacy_s")
    v_graph = med("v028", "graph_s")
    a_child = med("attempt5", "child_s")
    a_place = med("attempt5", "placement_s")
    a_residual = med("attempt5", "residual_s")
    v_legacy_ratio = v_legacy / max(v_child, 1e-12)
    v_graph_ratio = v_graph / max(v_child, 1e-12)
    a_place_ratio = a_place / max(a_child, 1e-12)
    a_residual_ratio = a_residual / max(a_child, 1e-12)

    if invalid:
        decision = "INVALID"
    elif v_graph_ratio >= STAGE_DOMINANT_RATIO and a_place_ratio >= STAGE_DOMINANT_RATIO:
        decision = "SHIFTED_G04_SHARED_NESTED_GRAPH_CONSTRUCTION_OWNS"
    elif v_legacy_ratio >= MATERIAL_SECONDARY_RATIO and a_residual_ratio < MATERIAL_SECONDARY_RATIO:
        decision = "SHIFTED_G04_SHARED_V028_LEGACY_STAGE_MATERIAL"
    elif a_residual_ratio >= MATERIAL_SECONDARY_RATIO and v_legacy_ratio < MATERIAL_SECONDARY_RATIO:
        decision = "SHIFTED_G04_SHARED_ATTEMPT5_RESIDUAL_STAGE_MATERIAL"
    else:
        decision = "SHIFTED_G04_SHARED_NESTED_STAGE_MIXED"

    return {
        "schema": "cmpct-v030-shifted-g04-nested-stage-attribution-v1",
        "source_commit": os.environ.get("EVIDENCE_HEAD"),
        "target": "/".join(TARGET),
        "rows": rows,
        "medians": {
            "v028_child_s": v_child,
            "v028_legacy_s": v_legacy,
            "v028_graph_s": v_graph,
            "v028_legacy_ratio": v_legacy_ratio,
            "v028_graph_ratio": v_graph_ratio,
            "attempt5_child_s": a_child,
            "attempt5_placement_s": a_place,
            "attempt5_residual_s": a_residual,
            "attempt5_placement_ratio": a_place_ratio,
            "attempt5_residual_ratio": a_residual_ratio,
        },
        "decision": decision,
        "invalid_reasons": invalid,
        "contract": {
            "repetitions": REPETITIONS,
            "stage_dominant_ratio": STAGE_DOMINANT_RATIO,
            "material_secondary_ratio": MATERIAL_SECONDARY_RATIO,
            "expected_v028_bytes": EXPECTED_V028_BYTES,
            "expected_attempt5_bytes": EXPECTED_ATTEMPT5_BYTES,
            "instrumentation_only": True,
            "product_changed": False,
            "release_credit": False,
        },
        "release_credit": False,
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path)
    p.add_argument("--output", type=Path)
    p.add_argument("--worker", choices=("v028", "attempt5"))
    p.add_argument("--source", type=Path)
    p.add_argument("--archive", type=Path)
    args = p.parse_args()
    if args.worker:
        if args.source is None or args.archive is None:
            p.error("worker mode requires --source and --archive")
        print(json.dumps(_worker(args.worker, args.source, args.archive), separators=(",", ":"), default=str))
        return
    if args.work_root is None or args.output is None:
        p.error("measurement mode requires --work-root and --output")
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"decision": result["decision"], "medians": result["medians"]}, separators=(",", ":")))


if __name__ == "__main__":
    main()
