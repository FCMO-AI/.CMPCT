from __future__ import annotations

"""Physical compression-cost referee for the frozen Analytics 4 KiB prefix selector.

This follows the successful research oracle at 3d83895 and asks one narrow causal
question: does replacing the full-pack L15 admission proof with a bounded 4 KiB
Zstd-1 prefix proof materially remove selector overhead while preserving the exact
same final per-pack choices and archive-byte accounting?

Timed surfaces deliberately start from already materialized raw physical packs, so
this is a compression-stage referee, not a complete-create/product benchmark.
No release/R4/runtime/product credit is possible here. A positive result only earns
a complete-create implementation/referee.
"""

import argparse
import json
from pathlib import Path
import shutil
import statistics
import time

import zstandard as zstd

from benchmarks import v030_analytics_proof_directed_admission_oracle as BASE

TARGET = "04_analytics_and_database"
ACCEPTED_V029_BYTES = 6_135_172
EXPECTED_PREFIX_ARCHIVE_BYTES = 6_134_940
PREFIX_BYTES = 4096
MIN_SIZE = 256 * 1024
MAX_RATIO_PPM = 700_000
ROUNDS = 5


def _stored_size(raw: bytes, compressed: bytes) -> int:
    """Mirror CMPNX5's physical-pack STORE-vs-Zstd admission exactly."""
    return len(compressed) if len(compressed) + 8 < len(raw) else len(raw)


def _prepare(work_root: Path):
    neutral = BASE.GENERAL.V029._load(
        BASE.GENERAL.V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py",
        "cmpct_v030_analytics_prefix_physical_neutral",
    )
    repair = BASE.GENERAL.V029._load(
        BASE.GENERAL.V029.REPAIR_PATH,
        "cmpct_v030_analytics_prefix_physical_repair",
    )
    repair.install_generation_hooks(neutral)
    corpus = work_root / "neutral"
    neutral.build(corpus)
    repair.normalize_root(corpus)
    stage = BASE.EXT._normalized_stage(corpus / TARGET, work_root / "normalized")
    low = BASE._build(stage, work_root / "level-15", 15)
    high = BASE._build(stage, work_root / "level-19", 19)
    lo = {p["sha256"]: p for p in low["packs"]}
    hi = {p["sha256"]: p for p in high["packs"]}
    if set(lo) != set(hi):
        raise RuntimeError("raw physical pack identity drift")
    rows = []
    for hh in sorted(lo):
        a, b = lo[hh], hi[hh]
        if a["raw"] != b["raw"] or a["usize"] != b["usize"] or a["crc32"] != b["crc32"]:
            raise RuntimeError(f"raw pack proof drift for {hh}")
        raw = a["raw"]
        z15 = BASE.V25.zc(raw, 15)
        z19 = BASE.V25.zc(raw, 19)
        final15 = _stored_size(raw, z15)
        final19 = _stored_size(raw, z19)
        # _build() reports the selected physical payload size, which can be raw
        # bytes when Zstd expands a pack.  Prove that distinction explicitly.
        if final15 != a["csize"]:
            raise RuntimeError(f"L15 selected-payload drift for {hh}: {final15} != {a['csize']}")
        if final19 != b["csize"]:
            raise RuntimeError(f"L19 selected-payload drift for {hh}: {final19} != {b['csize']}")
        rows.append(
            {
                "sha256": hh,
                "raw": raw,
                "z15": len(z15),
                "z19": len(z19),
                "l15": final15,
                "l19": final19,
            }
        )
    overhead = int(low["archive_bytes"] - sum(r["l15"] for r in rows))
    if overhead != int(high["archive_bytes"] - sum(r["l19"] for r in rows)):
        raise RuntimeError("non-payload archive overhead drift across effort controls")
    return rows, overhead, low, high


def _prefix_admits(raw: bytes, sample_c: zstd.ZstdCompressor) -> bool:
    if len(raw) < MIN_SIZE:
        return False
    sample = raw[:PREFIX_BYTES]
    ratio = int(1_000_000 * len(sample_c.compress(sample)) / max(1, len(sample)))
    return ratio <= MAX_RATIO_PPM


def _full_l15_admits(raw: bytes, l15_payload: bytes) -> bool:
    # Match the prior oracle's effective payload semantics: a failed Zstd
    # compression attempt contributes STORE/raw size, not its larger output.
    effective = _stored_size(raw, l15_payload)
    return len(raw) >= MIN_SIZE and int(1_000_000 * effective / len(raw)) <= MAX_RATIO_PPM


def _compress_checked(raw: bytes, level: int, expected_compressed: int) -> bytes:
    payload = BASE.V25.zc(raw, level)
    if len(payload) != expected_compressed:
        raise RuntimeError(
            f"zstd deterministic-size drift at L{level}: {len(payload)} != {expected_compressed}"
        )
    return payload


def _round(rows: list[dict], overhead: int, mode: str, sample_c: zstd.ZstdCompressor) -> dict:
    t0 = time.perf_counter()
    final_sizes = []
    admitted = 0
    if mode == "l15":
        for r in rows:
            payload = _compress_checked(r["raw"], 15, r["z15"])
            final_sizes.append(_stored_size(r["raw"], payload))
    elif mode == "l19":
        for r in rows:
            payload = _compress_checked(r["raw"], 19, r["z19"])
            final_sizes.append(_stored_size(r["raw"], payload))
    elif mode == "double":
        for r in rows:
            low = _compress_checked(r["raw"], 15, r["z15"])
            if _full_l15_admits(r["raw"], low):
                admitted += 1
                high = _compress_checked(r["raw"], 19, r["z19"])
                final_sizes.append(_stored_size(r["raw"], high))
            else:
                final_sizes.append(_stored_size(r["raw"], low))
    elif mode == "prefix":
        for r in rows:
            if _prefix_admits(r["raw"], sample_c):
                admitted += 1
                payload = _compress_checked(r["raw"], 19, r["z19"])
            else:
                payload = _compress_checked(r["raw"], 15, r["z15"])
            final_sizes.append(_stored_size(r["raw"], payload))
    else:
        raise ValueError(mode)
    wall = time.perf_counter() - t0
    return {"wall_s": wall, "archive_bytes": int(overhead + sum(final_sizes)), "admitted_packs": admitted}


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    rows, overhead, low, high = _prepare(work_root)
    sample_c = zstd.ZstdCompressor(level=1)

    # Freeze identity before timing. The prior oracle found exactly 45 prefix admissions.
    prefix_set = {r["sha256"] for r in rows if _prefix_admits(r["raw"], sample_c)}
    full_set = set()
    for r in rows:
        # Label-time payload is outside timing only for identity comparison; timed 'double' recomputes it.
        p = _compress_checked(r["raw"], 15, r["z15"])
        if _full_l15_admits(r["raw"], p):
            full_set.add(r["sha256"])
    if prefix_set != full_set:
        raise RuntimeError("4 KiB prefix selector no longer reproduces frozen full-L15 admission set")
    if len(prefix_set) != 45:
        raise RuntimeError(f"frozen admission-count drift: {len(prefix_set)} != 45")

    modes = ("l15", "l19", "double", "prefix")
    rounds = {m: [] for m in modes}
    # Rotate order to reduce monotonic thermal/order bias.
    for i in range(ROUNDS):
        order = modes[i % len(modes):] + modes[: i % len(modes)]
        for mode in order:
            rounds[mode].append(_round(rows, overhead, mode, sample_c))

    summary = {}
    for mode in modes:
        walls = [x["wall_s"] for x in rounds[mode]]
        bytes_set = {x["archive_bytes"] for x in rounds[mode]}
        admissions = {x["admitted_packs"] for x in rounds[mode]}
        if len(bytes_set) != 1 or len(admissions) != 1:
            raise RuntimeError(f"non-deterministic physical result for {mode}")
        summary[mode] = {
            "median_wall_s": statistics.median(walls),
            "min_wall_s": min(walls),
            "max_wall_s": max(walls),
            "archive_bytes": bytes_set.pop(),
            "admitted_packs": admissions.pop(),
            "round_wall_s": walls,
        }

    exact_bytes = summary["prefix"]["archive_bytes"] == EXPECTED_PREFIX_ARCHIVE_BYTES
    exact_choice = summary["prefix"]["admitted_packs"] == summary["double"]["admitted_packs"] == 45
    double_reduction = 1.0 - summary["prefix"]["median_wall_s"] / summary["double"]["median_wall_s"]
    l19_reduction = 1.0 - summary["prefix"]["median_wall_s"] / summary["l19"]["median_wall_s"]

    # Thresholds frozen before this physical run. These establish causal value only.
    if exact_bytes and exact_choice and double_reduction >= 0.20 and l19_reduction >= 0.10:
        verdict = "ADVANCE_PREFIX_SELECTOR_TO_COMPLETE_CREATE"
    elif not exact_bytes or not exact_choice:
        verdict = "INVALID_IDENTITY_OR_BYTE_DRIFT"
    elif double_reduction <= 0.05:
        verdict = "RETIRE_PREFIX_SELECTOR_NO_OVERHEAD_RELIEF"
    else:
        verdict = "PREFIX_SELECTOR_CAUSAL_GAIN_AMBIGUOUS"

    return {
        "schema": "cmpct-v030-analytics-prefix-selector-physical-referee-v1",
        "target": f"neutral_hostile_v1/{TARGET}",
        "status": "research-only compression-stage referee; no complete-create/product/release/R4 credit",
        "release_credit": False,
        "product_credit": False,
        "experiment_valid": verdict != "INVALID_IDENTITY_OR_BYTE_DRIFT",
        "frozen_rule": {
            "min_raw_bytes": MIN_SIZE,
            "prefix_bytes": PREFIX_BYTES,
            "prefix_codec": "zstd-1",
            "max_prefix_ratio_ppm": MAX_RATIO_PPM,
        },
        "rounds": ROUNDS,
        "pack_count": len(rows),
        "fixed_overhead_bytes": overhead,
        "accepted_v029_bytes": ACCEPTED_V029_BYTES,
        "oracle_expected_archive_bytes": EXPECTED_PREFIX_ARCHIVE_BYTES,
        "controls_complete_create_s": {
            "l15": low["complete_verified_create_s"],
            "l19": high["complete_verified_create_s"],
            "note": "context only; not directly compared to compression-stage timed verdict",
        },
        "summary": summary,
        "metrics": {
            "exact_archive_bytes": exact_bytes,
            "exact_admission_identity": exact_choice,
            "prefix_vs_double_median_wall_reduction": double_reduction,
            "prefix_vs_global_l19_median_wall_reduction": l19_reduction,
        },
        "verdict": verdict,
        "contract": {
            "same_raw_pack_identity": True,
            "same_final_admission_set_as_full_l15_oracle": exact_choice,
            "same_final_archive_bytes_as_prefix_oracle": exact_bytes,
            "same_process_controls": True,
            "rotated_measurement_order": True,
            "path_blind_selector": True,
            "no_full_pack_compression_feature": True,
            "complete_create_required_for_next_credit": True,
            "heldout_transfer_required_before_productization": True,
            "zstd_attempt_bytes_separated_from_selected_store_bytes": True,
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-analytics-prefix-physical-work"))
    ap.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-analytics-prefix-physical.json"))
    args = ap.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"verdict": result["verdict"], "summary": result["summary"], "metrics": result["metrics"]}, indent=2), flush=True)


if __name__ == "__main__":
    main()
