from __future__ import annotations

"""Reuse the already-computed BP4 level-1 audition as final payload when profitable.

Mission: docs/V030_ANALYTICS_BYTEPLANE4_AUDITION_REUSE_MISSION_2026-09-12.md
Research-only; fixed level=17, width=4, no threshold sweep.
"""

import argparse
import json
from pathlib import Path
import resource
import shutil
import statistics
import sys
import time

from benchmarks import v030_analytics_byteplane4_strong_transfer_referee as BP
from benchmarks import v030_external_competitors as EXT
from benchmarks import v030_release_generalization as GENERAL
from benchmarks import v030_v025_canonical_fs_level1_oracle as CANON
from experiments import entropygraph_v025 as V25
from experiments import entropygraph_v030_release_product as PRODUCT

TARGET = "04_analytics_and_database"
LEVEL17 = 17
LEVEL19 = 19
WIDTH = 4
ROUNDS = 3
ACCEPTED_V029_BYTES = 6_135_172
MIN_SPEEDUP_VS_STRONG = 0.10
MAX_ADDED_VS_L17_S = 0.35


def _rss_kib() -> int:
    v = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return v // 1024 if sys.platform == "darwin" else v


def _build_reuse(stage: Path, root: Path) -> dict:
    original_zc, original_zd = V25.zc, V25.zd
    old_cap = CANON.LEVEL_CAP
    stats = {
        "zc_calls": 0,
        "cheap_gate_auditions": 0,
        "cheap_gate_winners": 0,
        "cheap_gate_cpu_s": 0.0,
        "cheap_gate_wall_s": 0.0,
        "reused_level1_selected": 0,
        "selected_direct_l17_bytes": 0,
        "selected_framed_level1_bytes": 0,
        "net_payload_saving_bytes": 0,
        "transformed_l17_calls": 0,
    }

    def transfer_zc(raw: bytes, level: int = 19) -> bytes:
        stats["zc_calls"] += 1
        direct17 = original_zc(raw, min(int(level), LEVEL17))
        if int(level) < LEVEL17 or len(raw) < WIDTH:
            return direct17
        stats["cheap_gate_auditions"] += 1
        c0 = time.process_time(); w0 = time.perf_counter()
        direct1 = original_zc(raw, 1)
        shuffled = BP._shuffle4(raw)
        plane1 = original_zc(shuffled, 1)
        framed1 = BP.MAGIC + plane1
        stats["cheap_gate_cpu_s"] += time.process_time() - c0
        stats["cheap_gate_wall_s"] += time.perf_counter() - w0
        if len(framed1) >= len(direct1):
            return direct17
        stats["cheap_gate_winners"] += 1
        # Reuse proof bytes directly; no transformed level-17 compression is permitted.
        if len(framed1) < len(direct17):
            stats["reused_level1_selected"] += 1
            stats["selected_direct_l17_bytes"] += len(direct17)
            stats["selected_framed_level1_bytes"] += len(framed1)
            stats["net_payload_saving_bytes"] += len(direct17) - len(framed1)
            return framed1
        return direct17

    def transfer_zd(payload: bytes, usize: int) -> bytes:
        if payload.startswith(BP.MAGIC):
            shuffled = original_zd(payload[len(BP.MAGIC):], usize)
            raw = BP._unshuffle4(shuffled)
            if len(raw) != usize:
                raise RuntimeError("BytePlane4 inverse size drift")
            return raw
        return original_zd(payload, usize)

    CANON.LEVEL_CAP = LEVEL17
    V25.zc, V25.zd = transfer_zc, transfer_zd
    rss0 = _rss_kib(); c0 = time.process_time(); w0 = time.perf_counter()
    try:
        result = dict(CANON._canonical_v25(stage, root))
    finally:
        CANON.LEVEL_CAP = old_cap
        V25.zc, V25.zd = original_zc, original_zd
    result["process_cpu_s"] = time.process_time() - c0
    result["process_wall_s"] = time.perf_counter() - w0
    result["rss_baseline_kib"] = rss0
    result["rss_peak_kib"] = _rss_kib()
    result["rss_increment_kib"] = max(0, result["rss_peak_kib"] - rss0)
    result["stats"] = stats
    return result


def _build_strong(stage: Path, root: Path, level: int, candidate: bool) -> dict:
    old = BP.LEVEL
    try:
        BP.LEVEL = level
        return BP._build(stage, root, "candidate" if candidate else "baseline")
    finally:
        BP.LEVEL = old


def _summary(rr: list[dict]) -> dict:
    sizes = {int(r["archive_bytes"]) for r in rr}
    trees = {r["canonical_user_tree_sha256"] for r in rr}
    if len(sizes) != 1 or len(trees) != 1:
        raise RuntimeError("mode nondeterminism")
    return {
        "archive_bytes": next(iter(sizes)),
        "median_complete_verified_create_s": statistics.median(float(r["complete_verified_create_s"]) for r in rr),
        "median_process_cpu_s": statistics.median(float(r["process_cpu_s"]) for r in rr),
        "median_process_wall_s": statistics.median(float(r["process_wall_s"]) for r in rr),
        "median_peak_rss_kib": statistics.median(int(r["rss_peak_kib"]) for r in rr),
    }


def run(work_root: Path) -> dict:
    if BP.WIDTH != WIDTH:
        raise RuntimeError("frozen width drift")
    shutil.rmtree(work_root, ignore_errors=True); work_root.mkdir(parents=True)
    neutral = GENERAL.V029._load(GENERAL.V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py", "cmpct_bp4_reuse_neutral")
    repair = GENERAL.V029._load(GENERAL.V029.REPAIR_PATH, "cmpct_bp4_reuse_repair")
    repair.install_generation_hooks(neutral)
    corpus = work_root / "neutral"; neutral.build(corpus); repair.normalize_root(corpus)
    stage = EXT._normalized_stage(corpus / TARGET, work_root / "normalized")
    expected = PRODUCT.treehash(stage)

    modes = ["direct_l17", "reuse_l1", "strong_l17", "direct_l19"]
    rows = {m: [] for m in modes}
    for ri in range(ROUNDS):
        order = modes[ri:] + modes[:ri]
        for mode in order:
            root = work_root / "rounds" / f"r{ri}-{mode}"; root.mkdir(parents=True, exist_ok=True)
            if mode == "reuse_l1":
                r = _build_reuse(stage, root)
            elif mode == "strong_l17":
                r = _build_strong(stage, root, LEVEL17, True)
            elif mode == "direct_l17":
                r = _build_strong(stage, root, LEVEL17, False)
            else:
                r = _build_strong(stage, root, LEVEL19, False)
            if r["canonical_user_tree_sha256"] != expected:
                raise RuntimeError(f"tree drift {mode}")
            rows[mode].append(r)

    summaries = {m: _summary(rr) for m, rr in rows.items()}
    first = rows["reuse_l1"][0]["stats"]
    stable_keys = ("zc_calls", "cheap_gate_auditions", "cheap_gate_winners", "reused_level1_selected", "selected_direct_l17_bytes", "selected_framed_level1_bytes", "net_payload_saving_bytes", "transformed_l17_calls")
    for key in stable_keys:
        vals = {int(r["stats"][key]) for r in rows["reuse_l1"]}
        if len(vals) != 1:
            raise RuntimeError(f"reuse stat nondeterminism {key}: {vals}")
    stats = {k: int(first[k]) for k in stable_keys}
    stats["median_cheap_gate_cpu_s"] = statistics.median(float(r["stats"]["cheap_gate_cpu_s"]) for r in rows["reuse_l1"])
    stats["median_cheap_gate_wall_s"] = statistics.median(float(r["stats"]["cheap_gate_wall_s"]) for r in rows["reuse_l1"])

    reuse = summaries["reuse_l1"]; strong = summaries["strong_l17"]; l17 = summaries["direct_l17"]
    speedup_vs_strong = 1.0 - float(reuse["median_complete_verified_create_s"]) / max(float(strong["median_complete_verified_create_s"]), 1e-12)
    added_vs_l17 = float(reuse["median_complete_verified_create_s"]) - float(l17["median_complete_verified_create_s"])
    gate = {
        "candidate_at_or_below_v029": int(reuse["archive_bytes"]) <= ACCEPTED_V029_BYTES,
        "exact_deterministic": True,
        "speedup_vs_strong_l17_at_least_10pct": speedup_vs_strong >= MIN_SPEEDUP_VS_STRONG,
        "added_vs_direct_l17_at_most_0_35_s": added_vs_l17 <= MAX_ADDED_VS_L17_S,
        "zero_transformed_l17_calls": stats["transformed_l17_calls"] == 0,
        "fixed_level17_width4_no_sweep": True,
    }
    verdict = "AUDITION_BYTES_ARE_PRODUCTIVE_OUTPUT" if all(gate.values()) else "RETIRE_AUDITION_REUSE"
    return {
        "schema": "cmpct-v030-analytics-bp4-audition-reuse-v1",
        "experiment_valid": True,
        "release_credit": False,
        "target": f"neutral_hostile_v1/{TARGET}",
        "accepted_v029_bytes": ACCEPTED_V029_BYTES,
        "rounds": ROUNDS,
        "modes": summaries,
        "reuse_stats": stats,
        "speedup_vs_strong_l17_fraction": speedup_vs_strong,
        "added_complete_verified_create_vs_l17_s": added_vs_l17,
        "gate": gate,
        "verdict": verdict,
        "contract": {
            "same_bp4_level1_audition": True,
            "proof_bytes_reused_as_payload": True,
            "transformed_level17_forbidden": True,
            "path_extension_workload_identity_forbidden": True,
            "no_level_width_threshold_sweep": True,
            "strong_verify_inside_creation_time": True,
            "canonical_format_changed": False,
            "release_credit": False,
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-bp4-reuse-work"))
    ap.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-bp4-reuse.json"))
    args = ap.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"verdict": result["verdict"], "modes": result["modes"], "reuse_stats": result["reuse_stats"], "gate": result["gate"]}, indent=2), flush=True)


if __name__ == "__main__":
    main()
