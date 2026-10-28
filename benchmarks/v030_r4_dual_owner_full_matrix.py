from __future__ import annotations

"""Full 15-workload falsifier for the complementary R4 dual-owner result.

The single-workload Analytics oracle established that representing the exact CSV/JSONL relation once
and the exact external-NPY/NPZ-member relation once can beat both ordinary v0.30 and the accepted
v0.29 Analytics artifact. This diagnostic asks whether that result survives the complete frozen
Genesis matrix with exact fallback on every non-admitted workload and explicit process-tree CPU/RSS
accounting. It changes no shipping format, selector, canonical version, comparator, or ONE evidence.
"""

import argparse
import json
import os
from pathlib import Path
import resource
import shutil
import subprocess
import sys
import time

from benchmarks import mosaic_v029_generalization_bench as V029
from benchmarks import v030_r4_tabular_integrated_archive as I
from benchmarks import v030_r4_analytics_dual_owner_oracle as DUAL
from experiments import entropygraph_v030_release_product as PRODUCT

SCHEMA = "cmpct-v030-r4-dual-owner-full-matrix-v1"
ACCEPTED_V029_ANALYTICS = 6_135_172
GENESIS_V029_AGGREGATE = 137_499_525
GENESIS_V030_AGGREGATE = 150_055_575


def _cpu() -> tuple[float, float]:
    me = resource.getrusage(resource.RUSAGE_SELF)
    ch = resource.getrusage(resource.RUSAGE_CHILDREN)
    return float(me.ru_utime + me.ru_stime), float(ch.ru_utime + ch.ru_stime)


def _delta(after: tuple[float, float], before: tuple[float, float]) -> dict:
    self_cpu = after[0] - before[0]
    child_cpu = after[1] - before[1]
    return {"self_cpu_s": self_cpu, "children_cpu_s": child_cpu, "tree_cpu_s": self_cpu + child_cpu}


def _rss_snapshot() -> dict:
    me = resource.getrusage(resource.RUSAGE_SELF)
    ch = resource.getrusage(resource.RUSAGE_CHILDREN)
    return {
        "self_maxrss_bytes": int(me.ru_maxrss) * 1024,
        "children_maxrss_bytes": int(ch.ru_maxrss) * 1024,
        "max_observed_process_rss_bytes": max(int(me.ru_maxrss), int(ch.ru_maxrss)) * 1024,
        "note": "max observed process RSS; not sampled simultaneous process-tree RSS",
    }


def _dual_admissible(root: Path) -> tuple[bool, dict]:
    tab = I._discover(root)
    if len(tab["accepted"]) != 1:
        return False, {"tabular": tab, "npz": None, "reason": "tabular-count"}
    try:
        npz = DUAL._npz_relation(root)
    except RuntimeError as exc:
        return False, {"tabular": tab, "npz": None, "reason": f"npz:{exc}"}
    return True, {"tabular": tab, "npz": npz, "reason": "dual-exact"}


def _worker(mode: str, root: Path, archive: Path, work: Path, result: Path) -> None:
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    before = _cpu()
    w0 = time.perf_counter()
    if mode == "baseline":
        stats = dict(PRODUCT.build(root, archive))
        payload = {"mode": "ordinary-v030", "stored_bytes": archive.stat().st_size, "product_stats": stats}
    else:
        admitted, discovery = _dual_admissible(root)
        if admitted:
            payload = dict(DUAL._build_candidate(root, archive, work / "dual"))
            payload["mode"] = "dual-owner"
            payload["admission"] = discovery
        else:
            stats = dict(PRODUCT.build(root, archive))
            payload = {
                "mode": "ordinary-v030-fallback",
                "stored_bytes": archive.stat().st_size,
                "product_stats": stats,
                "admission": discovery,
            }
    after = _cpu()
    payload.update({
        "create_wall_s": time.perf_counter() - w0,
        "create_cpu": _delta(after, before),
        "rss": _rss_snapshot(),
    })
    result.write_text(json.dumps(payload, sort_keys=True, default=str) + "\n")


def _run_worker(script: Path, mode: str, root: Path, archive: Path, work: Path, result: Path) -> dict:
    subprocess.run([
        sys.executable, str(script), "--worker", mode,
        "--source", str(root), "--archive", str(archive),
        "--work-root", str(work), "--worker-result", str(result),
    ], check=True)
    return json.loads(result.read_text())


def _verify_baseline(archive: Path, out: Path) -> dict:
    shutil.rmtree(out, ignore_errors=True)
    before = _cpu(); w0 = time.perf_counter()
    sv = dict(PRODUCT.strong_verify(archive))
    verify_wall = time.perf_counter() - w0; verify_cpu = _delta(_cpu(), before)
    before = _cpu(); w0 = time.perf_counter()
    PRODUCT.extract(archive, out)
    extract_wall = time.perf_counter() - w0; extract_cpu = _delta(_cpu(), before)
    return {"strong_verify": sv, "tree_sha256": PRODUCT.treehash(out),
            "verify_wall_s": verify_wall, "verify_cpu": verify_cpu,
            "extract_wall_s": extract_wall, "extract_cpu": extract_cpu}


def _verify_candidate(archive: Path, mode: str, out: Path) -> dict:
    shutil.rmtree(out, ignore_errors=True)
    if mode == "dual-owner":
        before = _cpu(); w0 = time.perf_counter()
        verify = DUAL._extract_candidate(archive, out)
        wall = time.perf_counter() - w0; cpu = _delta(_cpu(), before)
        return {"strong_verify": verify["base_strong_verify"], "tree_sha256": verify["tree_sha256"],
                "verify_plus_extract_wall_s": wall, "verify_plus_extract_cpu": cpu}
    return _verify_baseline(archive, out)


def _logical_bytes(root: Path) -> int:
    return sum(p.stat().st_size for p in root.rglob("*") if p.is_file() and not p.is_symlink())


def run(work: Path) -> dict:
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    script = Path(__file__).resolve()
    neutral = V029._load(V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py", "cmpct_r4_dual_matrix_neutral")
    hostile = V029._load(V029.ROOT / "benchmarks" / "resemblance_hostile_corpus_v1.py", "cmpct_r4_dual_matrix_hostile")
    repair = V029._load(V029.REPAIR_PATH, "cmpct_r4_dual_matrix_repair")
    repair.install_generation_hooks(neutral)
    rows = []

    for suite, builder, root in (
        ("neutral_hostile_v1", neutral, work / "neutral"),
        ("resemblance_hostile_v1", hostile, work / "resemblance"),
    ):
        builder.build(root)
        if suite == "neutral_hostile_v1":
            repair.normalize_root(root)
        for source in sorted(p for p in root.iterdir() if p.is_dir()):
            rowdir = work / "rows" / suite / source.name
            rowdir.mkdir(parents=True)
            baseline = rowdir / "baseline.cmpct"
            candidate = rowdir / "candidate"
            br = _run_worker(script, "baseline", source, baseline, rowdir / "baseline-work", rowdir / "baseline.json")
            cr = _run_worker(script, "candidate", source, candidate, rowdir / "candidate-work", rowdir / "candidate.json")
            expected = PRODUCT.treehash(source)
            bv = _verify_baseline(baseline, rowdir / "baseline-extract")
            cv = _verify_candidate(candidate, cr["mode"], rowdir / "candidate-extract")
            if bv["tree_sha256"] != expected or cv["tree_sha256"] != expected:
                raise RuntimeError(f"tree mismatch {suite}/{source.name}")
            if cr["mode"] == "ordinary-v030-fallback" and cr["stored_bytes"] != br["stored_bytes"]:
                raise RuntimeError(f"fallback bytes changed {suite}/{source.name}")
            row = {
                "suite": suite, "name": source.name, "logical_bytes": _logical_bytes(source),
                "tree_sha256": expected, "baseline": br, "baseline_verify": bv,
                "candidate": cr, "candidate_verify": cv,
                "saving_bytes": br["stored_bytes"] - cr["stored_bytes"],
                "create_tree_cpu_delta_s": cr["create_cpu"]["tree_cpu_s"] - br["create_cpu"]["tree_cpu_s"],
                "create_wall_delta_s": cr["create_wall_s"] - br["create_wall_s"],
                "max_observed_process_rss_delta_bytes": cr["rss"]["max_observed_process_rss_bytes"] - br["rss"]["max_observed_process_rss_bytes"],
            }
            rows.append(row)
            print(json.dumps({k: row[k] for k in ("suite", "name", "saving_bytes", "create_tree_cpu_delta_s", "create_wall_delta_s")}, sort_keys=True), flush=True)

    baseline_bytes = sum(r["baseline"]["stored_bytes"] for r in rows)
    candidate_bytes = sum(r["candidate"]["stored_bytes"] for r in rows)
    baseline_cpu = sum(r["baseline"]["create_cpu"]["tree_cpu_s"] for r in rows)
    candidate_cpu = sum(r["candidate"]["create_cpu"]["tree_cpu_s"] for r in rows)
    baseline_wall = sum(r["baseline"]["create_wall_s"] for r in rows)
    candidate_wall = sum(r["candidate"]["create_wall_s"] for r in rows)
    admitted = [r for r in rows if r["candidate"]["mode"] == "dual-owner"]
    regressions = [r for r in rows if r["saving_bytes"] < 0]
    analytics = next(r for r in rows if r["suite"] == "neutral_hostile_v1" and r["name"] == "04_analytics_and_database")
    hypothesis = {
        "exactly_one_dual_owner_workload": len(admitted) == 1 and admitted[0]["name"] == "04_analytics_and_database",
        "zero_nonadmitted_byte_regressions": not regressions,
        "aggregate_smaller_than_same_run_v030": candidate_bytes < baseline_bytes,
        "analytics_beats_accepted_v029": analytics["candidate"]["stored_bytes"] < ACCEPTED_V029_ANALYTICS,
        "candidate_still_beats_genesis_v030_aggregate": candidate_bytes < GENESIS_V030_AGGREGATE,
        "candidate_beats_genesis_v029_aggregate": candidate_bytes < GENESIS_V029_AGGREGATE,
    }
    hypothesis["supported_for_product_design"] = all([
        hypothesis["exactly_one_dual_owner_workload"], hypothesis["zero_nonadmitted_byte_regressions"],
        hypothesis["aggregate_smaller_than_same_run_v030"], hypothesis["analytics_beats_accepted_v029"],
    ])
    return {
        "schema": SCHEMA, "source_commit": os.environ.get("EVIDENCE_HEAD"), "rows": rows,
        "aggregate": {
            "logical_bytes": sum(r["logical_bytes"] for r in rows),
            "baseline_v030_bytes": baseline_bytes, "candidate_bytes": candidate_bytes,
            "saving_vs_same_run_v030_bytes": baseline_bytes - candidate_bytes,
            "genesis_v030_bytes": GENESIS_V030_AGGREGATE, "genesis_v029_bytes": GENESIS_V029_AGGREGATE,
            "margin_vs_genesis_v030_bytes": GENESIS_V030_AGGREGATE - candidate_bytes,
            "margin_vs_genesis_v029_bytes": GENESIS_V029_AGGREGATE - candidate_bytes,
            "baseline_create_tree_cpu_s": baseline_cpu, "candidate_create_tree_cpu_s": candidate_cpu,
            "create_tree_cpu_delta_s": candidate_cpu - baseline_cpu,
            "baseline_create_wall_sum_s": baseline_wall, "candidate_create_wall_sum_s": candidate_wall,
            "create_wall_sum_delta_s": candidate_wall - baseline_wall,
        },
        "analytics": {
            "candidate_bytes": analytics["candidate"]["stored_bytes"],
            "baseline_v030_bytes": analytics["baseline"]["stored_bytes"],
            "accepted_v029_bytes": ACCEPTED_V029_ANALYTICS,
            "saving_vs_v030_bytes": analytics["saving_bytes"],
            "margin_vs_v029_bytes": ACCEPTED_V029_ANALYTICS - analytics["candidate"]["stored_bytes"],
        },
        "admitted": [{"suite": r["suite"], "name": r["name"]} for r in admitted],
        "regressions": [{"suite": r["suite"], "name": r["name"], "saving_bytes": r["saving_bytes"]} for r in regressions],
        "hypothesis": hypothesis,
        "contract": {
            "diagnostic_only": True, "release_credit": False, "full_15_workload_matrix": True,
            "same_semantic_tree_verified": True, "exact_fallback_required": True,
            "no_locality_claim": True, "no_threshold_sweep": True,
            "rss_is_max_observed_process_not_simultaneous_tree_peak": True,
        },
        "next_if_supported": "design a minimal authenticated dual-owner publication surface, then require physical selective-I/O/recovery/native parity before promotion",
        "next_if_falsified": "preserve negative and attribute the failing workload/resource axis; do not tune Genesis thresholds",
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r4-dual-matrix-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r4-dual-matrix.json"))
    p.add_argument("--worker", choices=["baseline", "candidate"])
    p.add_argument("--source", type=Path); p.add_argument("--archive", type=Path)
    p.add_argument("--worker-result", type=Path)
    a = p.parse_args()
    if a.worker:
        if not (a.source and a.archive and a.worker_result):
            raise SystemExit("worker mode requires --source --archive --worker-result")
        _worker(a.worker, a.source, a.archive, a.work_root, a.worker_result)
        return
    d = run(a.work_root)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(d, indent=2, default=str) + "\n")
    print(json.dumps({"aggregate": d["aggregate"], "analytics": d["analytics"], "hypothesis": d["hypothesis"], "admitted": d["admitted"], "regressions": d["regressions"]}, indent=2))


if __name__ == "__main__":
    main()
