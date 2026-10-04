from __future__ import annotations

"""Transfer the frozen BytePlane4 signal onto the strong Analytics frontier.

Mission: docs/V030_ANALYTICS_BYTEPLANE4_STRONG_TRANSFER_MISSION_2026-09-12.md
Research-only. Width=4 and the level-1 structural gate are frozen; no sweep is performed.
"""

import argparse
import json
from pathlib import Path
import resource
import shutil
import statistics
import sys
import time

from benchmarks import v030_external_competitors as EXT
from benchmarks import v030_release_generalization as GENERAL
from benchmarks import v030_v025_canonical_fs_level1_oracle as CANON
from experiments import entropygraph_v025 as V25
from experiments import entropygraph_v030_release_product as PRODUCT

TARGET = "04_analytics_and_database"
WIDTH = 4
MAGIC = b"BP4\x00\x01"
ROUNDS = 3
LEVEL = 19
MIN_MARGIN_BYTES = 8192
MAX_ADDED_CREATE_S = 0.75


def _rss_kib() -> int:
    v = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return v // 1024 if sys.platform == "darwin" else v


def _shuffle4(raw: bytes) -> bytes:
    q = len(raw) // WIDTH
    main = raw[: q * WIDTH]
    return b"".join(main[i::WIDTH] for i in range(WIDTH)) + raw[q * WIDTH :]


def _unshuffle4(shuffled: bytes) -> bytes:
    q = len(shuffled) // WIDTH
    main_n = q * WIDTH
    out = bytearray(len(shuffled))
    main = shuffled[:main_n]
    for i in range(WIDTH):
        out[i:main_n:WIDTH] = main[i * q : (i + 1) * q]
    out[main_n:] = shuffled[main_n:]
    return bytes(out)


def _build(stage: Path, root: Path, mode: str) -> dict:
    original_zc, original_zd = V25.zc, V25.zd
    old_cap = CANON.LEVEL_CAP
    stats = {
        "zc_calls": 0,
        "cheap_gate_auditions": 0,
        "cheap_gate_winners": 0,
        "cheap_gate_raw_bytes": 0,
        "strong_transform_auditions": 0,
        "strong_transform_raw_bytes": 0,
        "strong_transform_selected": 0,
        "direct_l19_bytes_for_selected": 0,
        "selected_framed_bytes": 0,
        "cheap_gate_cpu_s": 0.0,
        "cheap_gate_wall_s": 0.0,
        "strong_transform_cpu_s": 0.0,
        "strong_transform_wall_s": 0.0,
    }

    def transfer_zc(raw: bytes, level: int = 19) -> bytes:
        stats["zc_calls"] += 1
        direct19 = original_zc(raw, min(int(level), LEVEL))
        if int(level) < LEVEL or len(raw) < WIDTH:
            return direct19

        # Frozen path-blind structural audition from the prior BytePlane4 research line.
        stats["cheap_gate_auditions"] += 1
        stats["cheap_gate_raw_bytes"] += len(raw)
        c0 = time.process_time(); w0 = time.perf_counter()
        direct1 = original_zc(raw, 1)
        shuffled = _shuffle4(raw)
        plane1 = original_zc(shuffled, 1)
        cheap_framed = MAGIC + plane1
        stats["cheap_gate_cpu_s"] += time.process_time() - c0
        stats["cheap_gate_wall_s"] += time.perf_counter() - w0
        if len(cheap_framed) >= len(direct1):
            return direct19

        stats["cheap_gate_winners"] += 1
        stats["strong_transform_auditions"] += 1
        stats["strong_transform_raw_bytes"] += len(raw)
        c0 = time.process_time(); w0 = time.perf_counter()
        plane19 = original_zc(shuffled, LEVEL)
        stats["strong_transform_cpu_s"] += time.process_time() - c0
        stats["strong_transform_wall_s"] += time.perf_counter() - w0
        strong_framed = MAGIC + plane19
        if len(strong_framed) < len(direct19):
            stats["strong_transform_selected"] += 1
            stats["direct_l19_bytes_for_selected"] += len(direct19)
            stats["selected_framed_bytes"] += len(strong_framed)
            return strong_framed
        return direct19

    def transfer_zd(payload: bytes, usize: int) -> bytes:
        if payload.startswith(MAGIC):
            shuffled = original_zd(payload[len(MAGIC):], usize)
            raw = _unshuffle4(shuffled)
            if len(raw) != usize:
                raise RuntimeError("BytePlane4 inverse size drift")
            return raw
        return original_zd(payload, usize)

    CANON.LEVEL_CAP = LEVEL
    if mode == "candidate":
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
    result["stats"]["net_payload_saving_bytes"] = stats["direct_l19_bytes_for_selected"] - stats["selected_framed_bytes"]
    return result


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True); work_root.mkdir(parents=True)
    neutral = GENERAL.V029._load(
        GENERAL.V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py",
        "cmpct_v030_analytics_bp4_strong_neutral",
    )
    repair = GENERAL.V029._load(GENERAL.V029.REPAIR_PATH, "cmpct_v030_analytics_bp4_strong_repair")
    repair.install_generation_hooks(neutral)
    corpus = work_root / "neutral"; neutral.build(corpus); repair.normalize_root(corpus)
    source = corpus / TARGET
    stage = EXT._normalized_stage(source, work_root / "normalized")
    expected_tree = PRODUCT.treehash(stage)

    rows = {"baseline": [], "candidate": []}
    for ri in range(ROUNDS):
        order = ["baseline", "candidate"]
        if ri % 2: order.reverse()
        for mode in order:
            root = work_root / "rounds" / f"r{ri}-{mode}"; root.mkdir(parents=True, exist_ok=True)
            r = _build(stage, root, mode)
            if r["canonical_user_tree_sha256"] != expected_tree:
                raise RuntimeError(f"canonical tree drift in {mode}")
            rows[mode].append(r)

    summaries = {}
    for mode, rr in rows.items():
        sizes = {int(r["archive_bytes"]) for r in rr}
        trees = {r["canonical_user_tree_sha256"] for r in rr}
        if len(sizes) != 1 or len(trees) != 1:
            raise RuntimeError(f"nondeterminism in {mode}")
        summaries[mode] = {
            "archive_bytes": next(iter(sizes)),
            "median_complete_verified_create_s": statistics.median(float(r["complete_verified_create_s"]) for r in rr),
            "median_process_cpu_s": statistics.median(float(r["process_cpu_s"]) for r in rr),
            "median_process_wall_s": statistics.median(float(r["process_wall_s"]) for r in rr),
            "median_peak_rss_kib": statistics.median(int(r["rss_peak_kib"]) for r in rr),
            "median_incremental_rss_kib": statistics.median(int(r["rss_increment_kib"]) for r in rr),
            "raw": rr,
        }

    cstats = rows["candidate"][0]["stats"]
    deterministic_keys = (
        "zc_calls", "cheap_gate_auditions", "cheap_gate_winners", "cheap_gate_raw_bytes",
        "strong_transform_auditions", "strong_transform_raw_bytes", "strong_transform_selected",
        "direct_l19_bytes_for_selected", "selected_framed_bytes", "net_payload_saving_bytes",
    )
    for key in deterministic_keys:
        values = {int(r["stats"][key]) for r in rows["candidate"]}
        if len(values) != 1:
            raise RuntimeError(f"candidate stat nondeterminism {key}: {values}")
    stable_stats = {key: int(cstats[key]) for key in deterministic_keys}
    for key in ("cheap_gate_cpu_s", "cheap_gate_wall_s", "strong_transform_cpu_s", "strong_transform_wall_s"):
        stable_stats[f"median_{key}"] = statistics.median(float(r["stats"][key]) for r in rows["candidate"])

    saving = summaries["baseline"]["archive_bytes"] - summaries["candidate"]["archive_bytes"]
    added = summaries["candidate"]["median_complete_verified_create_s"] - summaries["baseline"]["median_complete_verified_create_s"]
    gate = {
        "exact_reconstruction": True,
        "path_blind_frozen_gate": True,
        "saving_at_least_8192_bytes": saving >= MIN_MARGIN_BYTES,
        "added_verified_create_at_most_0_75_s": added <= MAX_ADDED_CREATE_S,
    }
    verdict = "EARNED_MARGIN_FOR_ONE_SEARCH_ABLATION" if all(gate.values()) else "RETIRE_BYTEPLANE4_AS_STRONG_MARGIN_SOURCE"
    return {
        "schema": "cmpct-v030-analytics-byteplane4-strong-transfer-v1",
        "target": f"neutral_hostile_v1/{TARGET}",
        "release_credit": False,
        "experiment_valid": True,
        "rounds": ROUNDS,
        "width": WIDTH,
        "level": LEVEL,
        "modes": summaries,
        "candidate_stats": stable_stats,
        "archive_saving_bytes": saving,
        "added_complete_verified_create_s": added,
        "gate": gate,
        "verdict": verdict,
        "contract": {
            "fixed_width_no_sweep": True,
            "cheap_gate_is_prior_level1_exact_framed_win": True,
            "strong_transform_only_for_cheap_gate_winners": True,
            "path_extension_workload_identity_forbidden": True,
            "strong_verify_inside_creation_time": True,
            "production_selector_changed": False,
            "canonical_format_changed": False,
            "reader_locality_auth_recovery_credit": False,
            "release_credit": False,
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-analytics-bp4-strong-work"))
    ap.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-analytics-bp4-strong.json"))
    args = ap.parse_args()
    r = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(r, indent=2) + "\n")
    print(json.dumps({"verdict": r["verdict"], "saving": r["archive_saving_bytes"], "added_create_s": r["added_complete_verified_create_s"], "candidate_stats": r["candidate_stats"], "gate": r["gate"]}, indent=2), flush=True)


if __name__ == "__main__":
    main()
