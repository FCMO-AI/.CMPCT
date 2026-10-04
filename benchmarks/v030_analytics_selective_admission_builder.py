from __future__ import annotations

"""Execute the frozen Analytics proof-directed admission rule as a real writer.

The precursor oracle froze one path-blind rule without granting runtime credit:
raw physical pack >=256 KiB and its level-15 candidate ratio <=0.70. This Builder pays for that
level-15 audition, executes level 19 only for admitted level-19 pack requests, uses exact economic
fallback, and measures fresh-process creation/RSS plus unchanged-reader extraction. Research-only.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import shutil
import statistics
import subprocess
import sys
import time

from benchmarks import v030_external_competitors as EXT
from benchmarks import v030_release_generalization as GENERAL
from benchmarks import v030_v025_canonical_fs_level1_oracle as CANON
from experiments import entropygraph_v025 as V25

TARGET = "04_analytics_and_database"
ACCEPTED_V029_BYTES = 6_135_172
MIN_SIZE = 256 * 1024
MAX_CHEAP_RATIO_PPM = 700_000
ROUNDS = 3
MODES = ("l15", "selective", "l19")


def _rss_kib() -> int:
    value = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return value // 1024 if sys.platform == "darwin" else value


def _tree_logical_bytes(root: Path) -> int:
    total = 0
    for base, _dirs, files in os.walk(root, followlinks=False):
        bp = Path(base)
        for name in files:
            p = bp / name
            if not p.is_symlink():
                total += p.stat().st_size
    return total


def _pack_receipt(archive: Path) -> dict:
    V25.OUT = archive
    f, meta, po = V25.open_ar()
    try:
        rows = [
            {
                "sha256": bytes(hh).hex(), "usize": int(usize), "codec": int(codec),
                "csize": int(csize), "crc32": int(crc),
            }
            for _off, codec, usize, csize, crc, hh in po
        ]
    finally:
        f.close()
    return {
        "pack_count": len(rows),
        "max_physical_decode_unit_bytes": max((r["usize"] for r in rows), default=0),
        "raw_pack_identity": sorted((r["sha256"], r["usize"], r["crc32"]) for r in rows),
        "meta_version": int(meta["v"]),
    }


def _selective_zc(base_zc, stats: dict):
    def wrapped(raw: bytes, level: int = 19) -> bytes:
        level = int(level)
        if level < 19:
            return base_zc(raw, level)
        stats["candidate_calls"] += 1
        w0 = time.perf_counter(); c0 = time.process_time()
        cheap = base_zc(raw, 15)
        stats["cheap_cpu_s"] += time.process_time() - c0
        stats["cheap_wall_s"] += time.perf_counter() - w0
        stats["cheap_input_bytes"] += len(raw)

        o0 = time.perf_counter()
        ratio_ppm = int(1_000_000 * len(cheap) / max(1, len(raw)))
        admitted = len(raw) >= MIN_SIZE and ratio_ppm <= MAX_CHEAP_RATIO_PPM
        stats["observation_wall_s"] += time.perf_counter() - o0
        if not admitted:
            stats["rejected_calls"] += 1
            return cheap

        stats["admitted_calls"] += 1
        w0 = time.perf_counter(); c0 = time.process_time()
        expensive = base_zc(raw, 19)
        stats["expensive_cpu_s"] += time.process_time() - c0
        stats["expensive_wall_s"] += time.perf_counter() - w0
        stats["expensive_input_bytes"] += len(raw)
        if len(expensive) < len(cheap):
            stats["expensive_selected_calls"] += 1
            stats["selected_saving_bytes"] += len(cheap) - len(expensive)
            return expensive
        stats["economic_fallback_calls"] += 1
        return cheap
    return wrapped


def _worker(stage: Path, root: Path, mode: str, output: Path) -> None:
    shutil.rmtree(root, ignore_errors=True); root.mkdir(parents=True)
    stats = {
        "candidate_calls": 0, "admitted_calls": 0, "rejected_calls": 0,
        "expensive_selected_calls": 0, "economic_fallback_calls": 0,
        "cheap_input_bytes": 0, "expensive_input_bytes": 0,
        "cheap_cpu_s": 0.0, "cheap_wall_s": 0.0,
        "expensive_cpu_s": 0.0, "expensive_wall_s": 0.0,
        "observation_wall_s": 0.0, "selected_saving_bytes": 0,
    }
    base_zc = V25.zc; old_cap = CANON.LEVEL_CAP
    if mode == "l15": CANON.LEVEL_CAP = 15
    elif mode == "l19": CANON.LEVEL_CAP = 19
    elif mode == "selective":
        CANON.LEVEL_CAP = 19
        V25.zc = _selective_zc(base_zc, stats)
    else: raise RuntimeError(mode)

    rss0 = _rss_kib(); c0 = time.process_time(); w0 = time.perf_counter()
    try:
        result = CANON._canonical_v25(stage, root)
    finally:
        CANON.LEVEL_CAP = old_cap; V25.zc = base_zc
    function_cpu = time.process_time() - c0; function_wall = time.perf_counter() - w0
    rss_create = _rss_kib()
    archive = root / "candidate.cmpnx5"
    packs = _pack_receipt(archive)

    V25.OUT = archive; timed_out = root / "timed-extract"
    c0 = time.process_time(); w0 = time.perf_counter(); V25.extract(timed_out)
    extract_cpu = time.process_time() - c0; extract_wall = time.perf_counter() - w0
    rss_extract = _rss_kib(); logical = _tree_logical_bytes(root / "profile")
    output.write_text(json.dumps({
        "mode": mode, "archive_bytes": int(result["archive_bytes"]),
        "complete_verified_create_s": float(result["complete_verified_create_s"]),
        "function_cpu_s": function_cpu, "function_wall_s": function_wall,
        "filesystem_stage_s": float(result["filesystem_stage_s"]),
        "build_s": float(result["build_s"]), "strong_verify_s": float(result["strong_verify_s"]),
        "canonical_user_tree_sha256": str(result["canonical_user_tree_sha256"]),
        "filesystem_manifest_sha256": str(result["filesystem_manifest_sha256"]),
        "rss_baseline_kib": rss0, "rss_after_create_kib": rss_create,
        "rss_create_increment_kib": max(0, rss_create-rss0), "rss_after_extract_kib": rss_extract,
        "extract_cpu_s": extract_cpu, "extract_wall_s": extract_wall,
        "logical_profile_bytes": logical,
        "extract_mib_s": (logical/(1024*1024))/max(extract_wall, 1e-12),
        "packs": packs, "selector": stats,
    }, indent=2)+"\n")


def _run_worker(stage: Path, root: Path, mode: str, round_index: int) -> dict:
    worker_root = root / f"worker-{round_index}-{mode}"
    out = root / f"worker-{round_index}-{mode}.json"
    cp = subprocess.run([
        sys.executable, str(Path(__file__).resolve()), "--worker", "--stage", str(stage.resolve()),
        "--worker-root", str(worker_root.resolve()), "--worker-output", str(out.resolve()), "--mode", mode,
    ], text=True, capture_output=True)
    if cp.returncode:
        raise RuntimeError(f"worker {mode}/{round_index} failed rc={cp.returncode}\n{cp.stdout}\n{cp.stderr}")
    return json.loads(out.read_text())


def _zip_once(stage: Path, root: Path, round_index: int) -> dict:
    zroot = root / f"zip-{round_index}"; shutil.rmtree(zroot, ignore_errors=True); zroot.mkdir()
    expected = EXT._tree(stage)
    r = EXT._zip(stage, zroot/"archive.zip", zroot/"out")
    EXT._verify_extracted(zroot/"out", expected, "zip_deflate9")
    return {"archive_bytes": int(r["archive_bytes"]), "create_s": float(r["create_s"])}


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True); work_root.mkdir(parents=True)
    neutral = GENERAL.V029._load(GENERAL.V029.ROOT/"benchmarks"/"neutral_hostile_corpus_v1.py",
                                  "cmpct_v030_analytics_selective_builder_neutral")
    repair = GENERAL.V029._load(GENERAL.V029.REPAIR_PATH, "cmpct_v030_analytics_selective_builder_repair")
    repair.install_generation_hooks(neutral)
    corpus = work_root/"neutral"; neutral.build(corpus); repair.normalize_root(corpus)
    stage = EXT._normalized_stage(corpus/TARGET, work_root/"normalized")

    samples = {m: [] for m in MODES}; zip_samples = []
    for ri in range(ROUNDS):
        order = list(MODES); shift = ri % len(order); order = order[shift:]+order[:shift]
        for mode in order: samples[mode].append(_run_worker(stage, work_root, mode, ri))
        zip_samples.append(_zip_once(stage, work_root, ri))

    summaries = {}
    for mode, rows in samples.items():
        sizes = {r["archive_bytes"] for r in rows}; trees = {r["canonical_user_tree_sha256"] for r in rows}
        ids = {hashlib.sha256(json.dumps(r["packs"]["raw_pack_identity"], separators=(",",":")).encode()).hexdigest() for r in rows}
        if len(sizes)!=1 or len(trees)!=1 or len(ids)!=1: raise RuntimeError(f"nondeterministic {mode}")
        summaries[mode] = {
            "archive_bytes": next(iter(sizes)), "canonical_user_tree_sha256": next(iter(trees)),
            "raw_pack_identity_digest": next(iter(ids)), "pack_count": rows[0]["packs"]["pack_count"],
            "max_physical_decode_unit_bytes": rows[0]["packs"]["max_physical_decode_unit_bytes"],
            "median_complete_verified_create_s": statistics.median(r["complete_verified_create_s"] for r in rows),
            "median_function_cpu_s": statistics.median(r["function_cpu_s"] for r in rows),
            "median_function_wall_s": statistics.median(r["function_wall_s"] for r in rows),
            "median_peak_create_rss_kib": statistics.median(r["rss_after_create_kib"] for r in rows),
            "median_incremental_create_rss_kib": statistics.median(r["rss_create_increment_kib"] for r in rows),
            "median_extract_cpu_s": statistics.median(r["extract_cpu_s"] for r in rows),
            "median_extract_wall_s": statistics.median(r["extract_wall_s"] for r in rows),
            "median_extract_mib_s": statistics.median(r["extract_mib_s"] for r in rows), "raw": rows,
        }

    same_partition = len({summaries[m]["raw_pack_identity_digest"] for m in MODES})==1
    same_tree = len({summaries[m]["canonical_user_tree_sha256"] for m in MODES})==1
    if not same_partition or not same_tree: raise RuntimeError("physical/logical identity drift")

    sr = samples["selective"]
    count_keys = ("candidate_calls","admitted_calls","rejected_calls","expensive_selected_calls","economic_fallback_calls","selected_saving_bytes")
    selector = {}
    for key in count_keys:
        vals = {int(r["selector"][key]) for r in sr}
        if len(vals)!=1: raise RuntimeError(f"selector nondeterminism {key}: {vals}")
        selector[key] = next(iter(vals))
    for key in ("cheap_cpu_s","cheap_wall_s","expensive_cpu_s","expensive_wall_s","observation_wall_s"):
        selector[f"median_{key}"] = statistics.median(float(r["selector"][key]) for r in sr)

    zsizes = {r["archive_bytes"] for r in zip_samples}
    if len(zsizes)!=1: raise RuntimeError("ZIP byte nondeterminism")
    zipr = {"archive_bytes": next(iter(zsizes)), "median_create_s": statistics.median(r["create_s"] for r in zip_samples), "raw": zip_samples}
    sel = summaries["selective"]
    gate = {
        "same_canonical_user_tree": same_tree,
        "same_raw_physical_pack_partition": same_partition,
        "same_reader_and_decode_unit_semantics": True,
        "within_accepted_v029_bytes": sel["archive_bytes"] <= ACCEPTED_V029_BYTES,
        "verified_create_faster_than_same_runner_zip": sel["median_complete_verified_create_s"] < zipr["median_create_s"],
        "expensive_stage_within_mission_budget": selector["median_expensive_cpu_s"] <= 0.835,
        "selector_path_blind": True,
    }
    verdict = "PROMOTE_TO_HOSTILE_TRANSFER" if all(gate.values()) else "RETIRE_COARSE_ADMISSION_AS_COMPUTE_SELECTOR"
    return {
        "schema":"cmpct-v030-analytics-selective-admission-builder-v1", "target":f"neutral_hostile_v1/{TARGET}",
        "release_credit":False, "experiment_valid":True,
        "frozen_rule":{"min_raw_bytes":MIN_SIZE,"max_l15_ratio_ppm":MAX_CHEAP_RATIO_PPM,"no_threshold_search":True},
        "accepted_v029_bytes":ACCEPTED_V029_BYTES, "rounds":ROUNDS, "modes":summaries,
        "selector":selector, "same_runner_zip":zipr, "gate":gate, "verdict":verdict,
        "contract":{"same_normalized_source":True,"fresh_process_per_candidate_measurement":True,
                    "strong_verify_in_creation_time":True,"same_raw_pack_partition_required":True,"reader_unchanged":True,
                    "path_extension_workload_identity_forbidden":True,"exact_economic_fallback":True,"no_format_change":True,
                    "no_production_selector_change":True,"no_release_credit":True,"rss_baseline_reported_separately":True},
    }


def main() -> None:
    ap=argparse.ArgumentParser(); ap.add_argument("--work-root",type=Path,default=Path("benchmark-artifacts/v030-analytics-selective-builder-work")); ap.add_argument("--output",type=Path,default=Path("benchmark-artifacts/v030-analytics-selective-builder.json")); ap.add_argument("--worker",action="store_true"); ap.add_argument("--stage",type=Path); ap.add_argument("--worker-root",type=Path); ap.add_argument("--worker-output",type=Path); ap.add_argument("--mode",choices=MODES); args=ap.parse_args()
    if args.worker:
        if None in (args.stage,args.worker_root,args.worker_output,args.mode): raise SystemExit("worker args missing")
        _worker(args.stage,args.worker_root,args.mode,args.worker_output); return
    result=run(args.work_root); args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({"verdict":result["verdict"],"selective_bytes":result["modes"]["selective"]["archive_bytes"],"accepted_v029_bytes":result["accepted_v029_bytes"],"selective_verified_create_s":result["modes"]["selective"]["median_complete_verified_create_s"],"zip_create_s":result["same_runner_zip"]["median_create_s"],"selector":result["selector"],"gate":result["gate"]},indent=2),flush=True)


if __name__ == "__main__": main()
