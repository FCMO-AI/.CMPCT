from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

from benchmarks import v030_release_performance as PERF
from experiments import entropygraph_v030_release_product as PRODUCT
from experiments import entropygraph_v030_verified_restore as RESTORE

ROOT = Path(__file__).resolve().parents[1]
ORDERS = (("control", "product"), ("product", "control")) * 2


def _install_control() -> None:
    old = RESTORE._PRE_RELEASE_DELIMITER_INVERSE
    C = PRODUCT._BASE_IMPL.C
    C.SHARED.G.O.delimiter_inverse = old
    if getattr(C.POLICY.R.G04, "O", None) is not None:
        C.POLICY.R.G04.O.delimiter_inverse = old


def worker(arm: str, archive: Path, dst: Path) -> dict:
    if arm == "control":
        _install_control()
    start_cpu = time.process_time()
    start = time.perf_counter()
    PRODUCT.extract(archive, dst)
    return {
        "arm": arm,
        "wall_s": time.perf_counter() - start,
        "cpu_s": time.process_time() - start_cpu,
        "tree_sha256": PRODUCT.treehash(dst),
    }


def fresh(arm: str, archive: Path, dst: Path) -> dict:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    cp = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), "--worker", arm, "--archive", str(archive), "--dst", str(dst)],
        cwd=ROOT, env=env, check=True, capture_output=True, text=True,
    )
    return json.loads([line for line in cp.stdout.splitlines() if line.strip()][-1])


def run(root: Path) -> dict:
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True)
    src = PERF._build_corpora(root / "corpora")[("neutral_hostile_v1", "09_ml_artifacts")]
    archive = root / "ml.cmpct"
    PRODUCT.build(src, archive)
    expected = PRODUCT.treehash(src)
    pairs = []
    for rep, order in enumerate(ORDERS):
        rows = {arm: fresh(arm, archive, root / f"r{rep}-{arm}") for arm in order}
        if any(row["tree_sha256"] != expected for row in rows.values()):
            raise RuntimeError("ML bulk-varint product A/B tree drift")
        control, product = rows["control"], rows["product"]
        pairs.append({
            "rep": rep,
            "order": list(order),
            "rows": rows,
            "wall_improvement_pct": (control["wall_s"] - product["wall_s"]) / control["wall_s"] * 100.0,
            "cpu_improvement_pct": (control["cpu_s"] - product["cpu_s"]) / control["cpu_s"] * 100.0,
        })
    wall = sorted(row["wall_improvement_pct"] for row in pairs)
    cpu = sorted(row["cpu_improvement_pct"] for row in pairs)
    median_wall = (wall[1] + wall[2]) / 2.0
    median_cpu = (cpu[1] + cpu[2]) / 2.0
    return {
        "schema": "cmpct-v030-ml-bulk-varint-product-ab-v1",
        "release_credit": False,
        "source_sha": os.environ.get("EVIDENCE_HEAD"),
        "pairs": pairs,
        "median_wall_improvement_pct": median_wall,
        "median_cpu_improvement_pct": median_cpu,
        "required_relative_improvement_for_median_1_10": 8.038808244732154,
        "decision": "advance" if median_wall > 8.038808244732154 else "kill-or-reframe",
        "claim_boundary": "shipping release-only parser versus exact pre-product inverse on same source; authoritative runtime unpaid",
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--worker", choices=("control", "product"))
    ap.add_argument("--archive", type=Path)
    ap.add_argument("--dst", type=Path)
    ap.add_argument("--root", type=Path, default=Path("benchmark-artifacts/v030-ml-bulk-varint-product"))
    args = ap.parse_args()
    if args.worker:
        print(json.dumps(worker(args.worker, args.archive, args.dst), separators=(",", ":")))
    else:
        result = run(args.root)
        out = Path("benchmark-artifacts/v030-ml-bulk-varint-product.json")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(result, indent=2))
