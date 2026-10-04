from __future__ import annotations

import argparse
import json
from pathlib import Path
import resource
import shutil
import statistics
import subprocess
import sys
import time

from benchmarks import v030_release_performance as PERF
from experiments import entropygraph_v030_release_product as PRODUCT
from experiments import entropygraph_v030_verified_restore as VR

POLICY = VR.C.POLICY
R = POLICY.R


def _usage() -> dict:
    r = resource.getrusage(resource.RUSAGE_SELF)
    return {
        "cpu_s": float(r.ru_utime + r.ru_stime),
        "maxrss_kib": int(r.ru_maxrss),
        "inblock": int(r.ru_inblock),
        "oublock": int(r.ru_oublock),
    }


def _strict_staging(archive: Path, staging: Path, *, max_output_bytes: int = R.DEFAULT_MAX_EXTRACT_BYTES) -> dict:
    max_output_bytes = R._int(max_output_bytes, "extraction output budget", minimum=1, maximum=R.MAX_DECLARED_LOGICAL_BYTES)
    archive = Path(archive)
    staging = Path(staging)
    if staging.exists() and any(staging.iterdir()):
        raise RuntimeError("verified staging extraction requires an empty target directory")
    staging.mkdir(parents=True, exist_ok=True)
    magic = R._magic(archive)
    if magic == R.G04.MAG:
        return R._stream_g04(archive, staging, max_output_bytes, verify_nested_semantic_sha=True)
    if magic == R.PG.MAGIC:
        return R._stream_pg(archive, staging, max_output_bytes)
    raise RuntimeError("verified staging extraction accepts canonical r25 graph profiles only")


def _child(mode: str, archive: Path, dst: Path, expected_tree: str) -> dict:
    if mode == "control":
        POLICY.extract_verified_into_staging = _strict_staging
    elif mode != "candidate":
        raise RuntimeError(mode)
    shutil.rmtree(dst, ignore_errors=True)
    before = _usage()
    t0 = time.perf_counter()
    PRODUCT.extract(archive, dst)
    wall = time.perf_counter() - t0
    after = _usage()
    tree = PRODUCT.treehash(dst)
    if tree != expected_tree:
        raise RuntimeError(f"tree mismatch: {tree} != {expected_tree}")
    return {
        "mode": mode,
        "wall_s": wall,
        "cpu_s": after["cpu_s"] - before["cpu_s"],
        "maxrss_kib": after["maxrss_kib"],
        "inblock_delta": after["inblock"] - before["inblock"],
        "oublock_delta": after["oublock"] - before["oublock"],
        "tree_sha256": tree,
    }


def _spawn(mode: str, archive: Path, dst: Path, expected_tree: str) -> dict:
    proc = subprocess.run(
        [sys.executable, __file__, "--child", mode, "--archive", str(archive), "--dst", str(dst), "--expected-tree", expected_tree],
        check=True,
        text=True,
        capture_output=True,
    )
    return json.loads(proc.stdout)


def run(root: Path, pairs: int = 4) -> dict:
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True)
    src = PERF._build_corpora(root / "corpora")[("neutral_hostile_v1", "09_ml_artifacts")]
    archive = root / "ml.cmpct"
    PRODUCT.build(src, archive)
    expected_tree = PRODUCT.treehash(src)
    source_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()

    rows = []
    for pair in range(pairs):
        order = ("control", "candidate") if pair % 2 == 0 else ("candidate", "control")
        pair_rows = {}
        for mode in order:
            row = _spawn(mode, archive, root / f"out-{pair}-{mode}", expected_tree)
            row["pair"] = pair
            pair_rows[mode] = row
            rows.append(row)
        c = pair_rows["control"]
        x = pair_rows["candidate"]
        x["wall_improvement_pct_vs_pair_control"] = (c["wall_s"] - x["wall_s"]) / c["wall_s"] * 100.0
        x["cpu_improvement_pct_vs_pair_control"] = (c["cpu_s"] - x["cpu_s"]) / c["cpu_s"] * 100.0

    improvements = [r["wall_improvement_pct_vs_pair_control"] for r in rows if r["mode"] == "candidate"]
    cpu_improvements = [r["cpu_improvement_pct_vs_pair_control"] for r in rows if r["mode"] == "candidate"]
    return {
        "schema": "cmpct-v030-ml-verification-fold-product-ab-v1",
        "release_credit": False,
        "source_sha": source_sha,
        "pairs": pairs,
        "expected_tree_sha256": expected_tree,
        "rows": rows,
        "median_wall_improvement_pct": statistics.median(improvements),
        "median_cpu_improvement_pct": statistics.median(cpu_improvements),
        "required_transfer_of_oracle_pct": 45.51,
        "decision": "product evidence only; release authority remains the unchanged strict runtime/extraction gate",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--child", choices=("control", "candidate"))
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--dst", type=Path)
    parser.add_argument("--expected-tree")
    parser.add_argument("--root", type=Path, default=Path("benchmark-artifacts/v030-ml-verification-fold-product-ab"))
    parser.add_argument("--pairs", type=int, default=4)
    args = parser.parse_args()
    if args.child:
        if args.archive is None or args.dst is None or args.expected_tree is None:
            parser.error("child mode requires --archive --dst --expected-tree")
        print(json.dumps(_child(args.child, args.archive, args.dst, args.expected_tree)))
        return
    result = run(args.root, args.pairs)
    out = args.root.parent / "v030-ml-verification-fold-product-ab.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
