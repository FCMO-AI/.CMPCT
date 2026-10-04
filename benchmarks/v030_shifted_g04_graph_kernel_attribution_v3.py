from __future__ import annotations

"""Superseding Shifted graph-kernel attribution v3.

V3 reuses the frozen v1 experiment and v2 owner correction. Its only scientific-instrument repair is
attaching the attempt-5 primitive timers to the Placement Compiler module that actually owns them.
"""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

from benchmarks import v030_shifted_g04_graph_kernel_attribution_v1 as V1
from benchmarks import v030_shifted_g04_nested_stage_attribution as PARENT

ROOT = V1.ROOT


def _measure(kind: str, source: Path, archive: Path) -> dict:
    from experiments import entropygraph_v029_residual_fast as accepted

    acc: dict[str, float | int] = {}
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
        placement = accepted.BASE.P
        names = [
            (placement, "delta_encode", "delta"),
            (placement, "mosaic_delta_encode", "mosaic_delta"),
            (placement, "_compress_record", "compress"),
            (placement, "_position_independent_candidates", "position_candidates"),
            (accepted.V028, "_choose_pack_plan", "pack_plan"),
        ]
    else:
        raise ValueError(kind)

    for _, _, key in names:
        acc[key + "_s"] = 0.0
        acc[key + "_calls"] = 0
    try:
        for owner, name, key in names:
            original = V1._timed(owner, name, key, acc)
            restores.append((owner, name, original))
        row = PARENT._measure_v028(source, archive) if kind == "v028" else PARENT._measure_attempt5(source, archive)
    finally:
        V1._restore(restores)

    stage_s = float(row["graph_s"] if kind == "v028" else row["placement_s"])
    row["kernel"] = acc
    row["kernel"]["stage_s"] = stage_s
    row["kernel"]["delta_kernel_s"] = float(acc["delta_s"] + acc.get("mosaic_delta_s", 0.0))
    row["kernel"]["delta_kernel_ratio"] = row["kernel"]["delta_kernel_s"] / max(stage_s, 1e-12)
    row["kernel"]["compress_ratio"] = float(acc["compress_s"]) / max(stage_s, 1e-12)
    row["kernel"]["primitive_residual_floor_s"] = max(
        0.0, stage_s - row["kernel"]["delta_kernel_s"] - float(acc["compress_s"])
    )
    row["kernel"]["primitive_residual_floor_ratio"] = row["kernel"]["primitive_residual_floor_s"] / max(stage_s, 1e-12)
    return row


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
            f"kernel worker failed kind={kind} rc={proc.returncode} stdout={proc.stdout[-2000:]!r} stderr={proc.stderr[-4000:]!r}"
        )
    return json.loads(lines[-1])


def run(work_root: Path) -> dict:
    original_fresh = V1._fresh
    try:
        V1._fresh = _fresh
        result = V1.run(work_root)
    finally:
        V1._fresh = original_fresh
    result["schema"] = "cmpct-v030-shifted-g04-graph-kernel-attribution-v3"
    result["supersedes"] = "cmpct-v030-shifted-g04-graph-kernel-attribution-v2"
    result["instrument_repair"] = {
        "v1_pack_plan_owner_bug": True,
        "v2_attempt5_primitive_owner_bug": True,
        "v3_attempt5_primitive_owner": "accepted.BASE.P",
        "v3_pack_plan_owner": "accepted.V028",
        "scientific_contract_changed": False,
    }
    return result


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
