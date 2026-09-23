from __future__ import annotations
"""Isolated resource/economics gate for #205 actual-Builder hidden-ZIP productization.

The parent generates fresh Office trees and launches each arm in a fresh process so peak RSS is arm-local.
Each repetition uses A-B-B-A order on the exact same source tree. The candidate also instruments the existing
proof/staging return value without changing its decisions, exposing source/temp I/O and logical verification work.
"""
import argparse
import json
import os
from pathlib import Path
import resource
import shutil
import statistics
import subprocess
import sys
import time

from benchmarks import v030_release_generalization as GENERAL
from experiments import entropygraph_v030_release_product as PRODUCT

REPS = 3
MAX_RUNTIME_RATIO = 1.10
MAX_RSS_RATIO = 1.25


def _treehash(root: Path) -> str:
    return PRODUCT.treehash(root)


def _child(source: Path, arm: str, arc: Path, out: Path, result_path: Path) -> None:
    from cmpct.builder import Builder
    from cmpct.reader import CMPCT
    from cmpct import v030_hidden_zip_builder as HIDDEN_SCAN
    from cmpct import builder_hidden_zip as BRIDGE

    authority = getattr(Builder, "_cmpct_v030_authority_scan", None)
    if authority is None:
        raise RuntimeError("#205 installer did not retain authority scan")
    scan = authority if arm == "base" else HIDDEN_SCAN._scan_with_hidden_zip
    capture: dict[str, object] = {}
    original_finalize = BRIDGE.finalize_deferred_hidden_files

    def observed_finalize(builder, deferred, *, min_verified_reuse=BRIDGE.MIN_VERIFIED_REUSE):
        resolved = original_finalize(builder, deferred, min_verified_reuse=min_verified_reuse)
        cohort = resolved.cohort
        capture.update({
            "proof_io_bytes": int(resolved.proof.io_bytes),
            "proof_logical_bytes": int(resolved.proof.logical_bytes),
            "proof_rejects": list(resolved.proof.rejects),
            "stage_source_bytes_read": int(cohort.source_bytes_read),
            "stage_temp_bytes_written": int(cohort.temporary_bytes_written),
            "stage_temp_bytes_read": int(cohort.temporary_bytes_read),
            "stage_retained_candidate_bytes": int(cohort.retained_candidate_bytes),
            "stage_realized": sorted(cohort.realized),
            "stage_excluded": sorted(cohort.excluded),
        })
        return resolved

    if arm == "candidate":
        BRIDGE.finalize_deferred_hidden_files = observed_finalize
    old_scan = Builder.scan
    try:
        Builder.scan = scan
        cpu0 = time.process_time(); wall0 = time.perf_counter()
        stats = dict(Builder(source).build(arc))
        create_cpu = time.process_time() - cpu0; create_wall = time.perf_counter() - wall0
    finally:
        Builder.scan = old_scan
        BRIDGE.finalize_deferred_hidden_files = original_finalize

    want = _treehash(source); shutil.rmtree(out, ignore_errors=True)
    cpu0 = time.process_time(); wall0 = time.perf_counter()
    with CMPCT(arc) as reader:
        reader.extractall(out, metadata=True)
    extract_cpu = time.process_time() - cpu0; extract_wall = time.perf_counter() - wall0
    got = _treehash(out)
    if got != want:
        raise RuntimeError(f"tree mismatch {got} != {want}")
    result = {
        "arm": arm,
        "archive_bytes": arc.stat().st_size,
        "create_cpu_s": create_cpu, "create_wall_s": create_wall,
        "extract_cpu_s": extract_cpu, "extract_wall_s": extract_wall,
        "peak_rss_kib": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
        "tree_sha256": got, "stats": stats, "hidden_accounting": capture,
    }
    result_path.parent.mkdir(parents=True, exist_ok=True)
    result_path.write_text(json.dumps(result, indent=2) + "\n")


def _run_child(script: Path, source: Path, arm: str, root: Path, tag: str) -> dict:
    arc = root / f"{tag}.cmpct"; out = root / f"{tag}-out"; result = root / f"{tag}.json"
    env = dict(os.environ); env["PYTHONPATH"] = os.getcwd()
    subprocess.run([
        sys.executable, os.fspath(script), "--child", "--source", os.fspath(source), "--arm", arm,
        "--arc", os.fspath(arc), "--extract", os.fspath(out), "--child-output", os.fspath(result),
    ], check=True, env=env)
    return json.loads(result.read_text())


def _median(rows: list[dict], key: str) -> float:
    return float(statistics.median(float(row[key]) for row in rows))


def run(root: Path) -> dict:
    shutil.rmtree(root, ignore_errors=True); root.mkdir(parents=True)
    script = Path(__file__).resolve(); reps = []
    for rep in range(REPS):
        work = root / f"rep-{rep}"; suite_root = work / "neutral"
        n = GENERAL.V029._load(GENERAL.V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py", f"cmpct_hidden_resource_n_{rep}")
        repair = GENERAL.V029._load(GENERAL.V029.REPAIR_PATH, f"cmpct_hidden_resource_r_{rep}")
        repair.install_generation_hooks(n); n.build(suite_root); repair.normalize_root(suite_root)
        source = suite_root / "02_office_workspace"
        if not source.is_dir(): raise RuntimeError("Office workload missing")
        source_hash = _treehash(source); run_root = work / "runs"; run_root.mkdir(parents=True)
        sequence = []
        for idx, arm in enumerate(("base", "candidate", "candidate", "base")):
            row = _run_child(script, source, arm, run_root, f"{idx}-{arm}")
            if row["tree_sha256"] != source_hash: raise RuntimeError("child source identity drift")
            sequence.append(row)
        base = [sequence[0], sequence[3]]; candidate = [sequence[1], sequence[2]]
        reps.append({"rep": rep, "source_tree_sha256": source_hash, "sequence": sequence,
            "base_create_wall_median_s": _median(base, "create_wall_s"),
            "candidate_create_wall_median_s": _median(candidate, "create_wall_s"),
            "base_extract_wall_median_s": _median(base, "extract_wall_s"),
            "candidate_extract_wall_median_s": _median(candidate, "extract_wall_s"),
            "base_peak_rss_kib_median": _median(base, "peak_rss_kib"),
            "candidate_peak_rss_kib_median": _median(candidate, "peak_rss_kib"),
            "base_archive_bytes": base[0]["archive_bytes"], "candidate_archive_bytes": candidate[0]["archive_bytes"],
            "candidate_hidden_accounting": candidate[0]["hidden_accounting"]})

    base_create = statistics.median(r["base_create_wall_median_s"] for r in reps)
    cand_create = statistics.median(r["candidate_create_wall_median_s"] for r in reps)
    base_extract = statistics.median(r["base_extract_wall_median_s"] for r in reps)
    cand_extract = statistics.median(r["candidate_extract_wall_median_s"] for r in reps)
    base_rss = statistics.median(r["base_peak_rss_kib_median"] for r in reps)
    cand_rss = statistics.median(r["candidate_peak_rss_kib_median"] for r in reps)
    ratios = {"create_wall": cand_create / base_create, "extract_wall": cand_extract / base_extract, "peak_rss": cand_rss / base_rss}
    saving = [r["base_archive_bytes"] - r["candidate_archive_bytes"] for r in reps]
    supported = min(saving) >= 9_000_000 and ratios["create_wall"] <= MAX_RUNTIME_RATIO and ratios["extract_wall"] <= MAX_RUNTIME_RATIO and ratios["peak_rss"] <= MAX_RSS_RATIO
    return {"schema":"cmpct-v030-hidden-zip-resource-gate-v1", "source_commit":os.environ.get("EVIDENCE_HEAD"),
        "repetitions":REPS, "order":"A-B-B-A fresh child processes per repetition", "rows":reps,
        "summary":{"office_saving_bytes_by_rep":saving,"create_wall_ratio":ratios["create_wall"],"extract_wall_ratio":ratios["extract_wall"],"peak_rss_ratio":ratios["peak_rss"],
            "runtime_limit":MAX_RUNTIME_RATIO,"rss_limit":MAX_RSS_RATIO,"supported_for_promotion":supported},
        "contract":{"actual_builder_candidate":True,"same_tree_per_ABBA":True,"isolated_process_per_arm":True,"exact_tree_verified":True,"thresholds_inherited_not_retuned":True}}


def main() -> None:
    p=argparse.ArgumentParser(); p.add_argument("--work-root",type=Path,default=Path("benchmark-artifacts/hidden-zip-resource-work")); p.add_argument("--output",type=Path,default=Path("benchmark-artifacts/hidden-zip-resource.json"))
    p.add_argument("--child",action="store_true"); p.add_argument("--source",type=Path); p.add_argument("--arm",choices=("base","candidate")); p.add_argument("--arc",type=Path); p.add_argument("--extract",type=Path); p.add_argument("--child-output",type=Path); a=p.parse_args()
    if a.child:
        _child(a.source,a.arm,a.arc,a.extract,a.child_output); return
    result=run(a.work_root); a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(result,indent=2)+"\n"); print(json.dumps(result["summary"],indent=2))
    if not result["summary"]["supported_for_promotion"]: raise SystemExit(2)
if __name__ == "__main__": main()
