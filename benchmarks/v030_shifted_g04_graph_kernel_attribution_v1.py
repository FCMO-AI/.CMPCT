from __future__ import annotations

"""Frozen Shifted graph-kernel attribution; instrumentation only, zero product/release credit."""

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
from benchmarks import v030_shifted_g04_nested_stage_attribution as PARENT
from benchmarks import v030_shifted_g04_nested_stage_attribution_v2 as STABLE

ROOT = Path(__file__).resolve().parents[1]
TARGET = PARENT.TARGET
REPETITIONS = 3
FIXED_NS = STABLE.FIXED_NS
EXPECTED_TREE = STABLE.EXPECTED_TREE
EXPECTED = {
    "v028": (1_761_588, "b483d7e1dda93b86c874eab4bf20649eedb709c42a5a8be428a8d7449786a851"),
    "attempt5": (1_723_056, "791baff9fe09b18588f26bdc47ff1b13f160ca095dff2e47b5523241e85c91e9"),
}
MATERIAL = 0.20


def _timed(module, name: str, key: str, acc: dict):
    original = getattr(module, name)
    def wrapped(*args, **kwargs):
        started = time.perf_counter()
        try:
            return original(*args, **kwargs)
        finally:
            acc[key + "_s"] += time.perf_counter() - started
            acc[key + "_calls"] += 1
    setattr(module, name, wrapped)
    return original


def _restore(items):
    for module, name, original in reversed(items):
        setattr(module, name, original)


def _measure(kind: str, source: Path, archive: Path) -> dict:
    from experiments import entropygraph_v029_residual_fast as accepted

    acc = {}
    restores = []
    if kind == "v028":
        module = accepted.V028
        names = [
            (module, "delta_encode", "delta"),
            (module, "_compress_record", "compress"),
            (module, "similarity_sketch", "sketch"),
            (module, "lsh_candidates", "lsh"),
            (module, "_choose_pack_plan", "pack_plan"),
        ]
    elif kind == "attempt5":
        module = accepted.BASE.A4
        names = [
            (module, "delta_encode", "delta"),
            (module, "mosaic_delta_encode", "mosaic_delta"),
            (module, "_compress_record", "compress"),
            (module, "_position_independent_candidates", "position_candidates"),
            (module.V028, "_choose_pack_plan", "pack_plan"),
        ]
    else:
        raise ValueError(kind)

    for _, _, key in names:
        acc[key + "_s"] = 0.0
        acc[key + "_calls"] = 0
    try:
        for owner, name, key in names:
            original = _timed(owner, name, key, acc)
            restores.append((owner, name, original))
        row = PARENT._measure_v028(source, archive) if kind == "v028" else PARENT._measure_attempt5(source, archive)
    finally:
        _restore(restores)

    stage_s = float(row["graph_s"] if kind == "v028" else row["placement_s"])
    row["kernel"] = acc
    row["kernel"]["stage_s"] = stage_s
    row["kernel"]["delta_kernel_s"] = float(acc["delta_s"] + (acc.get("mosaic_delta_s", 0.0)))
    row["kernel"]["delta_kernel_ratio"] = row["kernel"]["delta_kernel_s"] / max(stage_s, 1e-12)
    row["kernel"]["compress_ratio"] = float(acc["compress_s"]) / max(stage_s, 1e-12)
    row["kernel"]["primitive_residual_floor_s"] = max(0.0, stage_s - row["kernel"]["delta_kernel_s"] - float(acc["compress_s"]))
    row["kernel"]["primitive_residual_floor_ratio"] = row["kernel"]["primitive_residual_floor_s"] / max(stage_s, 1e-12)
    return row


def _fresh(kind: str, source: Path, archive: Path) -> dict:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    proc = subprocess.run(
        [sys.executable, __file__, "--worker", kind, "--source", os.fspath(source), "--archive", os.fspath(archive)],
        cwd=ROOT, env=env, check=False, capture_output=True, text=True,
    )
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    if proc.returncode != 0 or not lines:
        raise RuntimeError(f"kernel worker failed kind={kind} rc={proc.returncode} stdout={proc.stdout[-2000:]!r} stderr={proc.stderr[-4000:]!r}")
    return json.loads(lines[-1])


def run(work_root: Path) -> dict:
    work_root = Path(work_root)
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    source = PERF._build_corpora(work_root / "corpora")[TARGET]
    before_tree = PERF.GENERAL._historical_treehash(source)
    STABLE._fix_times(source)
    after_tree = PERF.GENERAL._historical_treehash(source)
    mtimes_fixed = STABLE._all_mtimes_fixed(source)

    rows = []
    for rep in range(1, REPETITIONS + 1):
        order = ("v028", "attempt5") if rep % 2 else ("attempt5", "v028")
        measured = {}
        for kind in order:
            measured[kind] = _fresh(kind, source, work_root / f"rep-{rep}-{kind}.cmpct")
        rows.append({"rep": rep, "order": list(order), **measured})

    invalid = []
    if before_tree != EXPECTED_TREE: invalid.append("tree_before")
    if after_tree != EXPECTED_TREE: invalid.append("tree_after")
    if not mtimes_fixed: invalid.append("mtime_normalization")
    for row in rows:
        for kind in ("v028", "attempt5"):
            item = row[kind]
            expected_bytes, expected_sha = EXPECTED[kind]
            if int(item["archive_bytes"]) != expected_bytes: invalid.append(f"rep-{row['rep']}:{kind}:bytes")
            if item["archive_sha256"] != expected_sha: invalid.append(f"rep-{row['rep']}:{kind}:sha")
            if item["verify_ok"] is not True or item["tree_sha256"] != EXPECTED_TREE: invalid.append(f"rep-{row['rep']}:{kind}:verify")
            stage_calls = int(item["graph_calls"] if kind == "v028" else item["placement_calls"])
            if stage_calls != 1: invalid.append(f"rep-{row['rep']}:{kind}:stage_calls")
            for key, value in item["kernel"].items():
                if key.endswith("_s") or key.endswith("_ratio"):
                    if not math.isfinite(float(value)) or float(value) < 0:
                        invalid.append(f"rep-{row['rep']}:{kind}:{key}")

    def med(kind: str, key: str) -> float:
        return float(statistics.median(float(row[kind]["kernel"][key]) for row in rows))

    vm = {key: med("v028", key) for key in rows[0]["v028"]["kernel"] if key.endswith("_s") or key.endswith("_ratio")}
    am = {key: med("attempt5", key) for key in rows[0]["attempt5"]["kernel"] if key.endswith("_s") or key.endswith("_ratio")}
    vd, ad = vm["delta_kernel_ratio"], am["delta_kernel_ratio"]
    vc, ac = vm["compress_ratio"], am["compress_ratio"]
    if invalid:
        decision = "INVALID"
    elif vd >= MATERIAL and ad >= MATERIAL:
        decision = "SHIFTED_G04_DELTA_KERNEL_MATERIAL_BOTH"
    elif vd >= MATERIAL:
        decision = "SHIFTED_G04_DELTA_KERNEL_MATERIAL_V028_ONLY"
    elif ad >= MATERIAL:
        decision = "SHIFTED_G04_DELTA_KERNEL_MATERIAL_ATTEMPT5_ONLY"
    elif vc >= MATERIAL or ac >= MATERIAL:
        decision = "SHIFTED_G04_COMPRESSION_KERNEL_MATERIAL"
    else:
        decision = "SHIFTED_G04_GRAPH_CONTROL_OR_NOMINATION_DOMINATES"

    return {
        "schema": "cmpct-v030-shifted-g04-graph-kernel-attribution-v1",
        "source_commit": os.environ.get("EVIDENCE_HEAD"),
        "target": "/".join(TARGET),
        "fixture": {"fixed_ns": FIXED_NS, "tree_before": before_tree, "tree_after": after_tree, "mtimes_fixed": mtimes_fixed},
        "rows": rows,
        "medians": {"v028": vm, "attempt5": am},
        "decision": decision,
        "invalid_reasons": invalid,
        "contract": {"repetitions": REPETITIONS, "material_ratio": MATERIAL, "expected_tree": EXPECTED_TREE, "fixed_ns": FIXED_NS, "instrumentation_only": True, "product_changed": False, "release_credit": False},
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
        print(json.dumps(_measure(args.worker, args.source, args.archive), separators=(",", ":"), default=str))
        return
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"decision": result["decision"], "medians": result["medians"]}, separators=(",", ":")))


if __name__ == "__main__":
    main()
