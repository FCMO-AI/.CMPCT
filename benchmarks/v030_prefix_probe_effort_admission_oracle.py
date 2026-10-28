from __future__ import annotations

"""Research-only prefix-sample admission oracle for v0.30 high-effort compression.

Question: can a bounded 4 KiB content sample, plus pack size, recover enough of the
L15->L19 byte headroom on both Office and Analytics that we no longer need to run
L15 over the entire pack merely to decide whether L19 is worth attempting?

This is deliberately an oracle, not a product selector. L15 and L19 are both built
to label the same raw physical packs. The selector itself may use only pack size and
the Zstd-1 compression ratio of the first 4 KiB. One fixed coarse rule family is
applied identically to both primary workloads. No path, extension, workload label,
pack hash, full-pack compressed size, or post-hoc learned threshold is an input.

A positive result earns only a right to build a charged physical selector and then
held-out transfer tests. It earns no release/R4/product credit.
"""

import argparse
import json
from pathlib import Path
import shutil
import time

import zstandard as zstd

from benchmarks import v030_analytics_proof_directed_admission_oracle as BASE

TARGETS = ("02_office_workspace", "04_analytics_and_database")
ACCEPTED_V029 = {
    "02_office_workspace": 12_480_771,
    "04_analytics_and_database": 6_135_172,
}
LEVELS = (15, 19)
PREFIX = 4096
SIZES = (128 * 1024, 256 * 1024, 512 * 1024)
SAMPLE_RATIOS_PPM = (700_000, 850_000, 1_000_000)


def _prefix_ratio_ppm(raw: bytes, compressor: zstd.ZstdCompressor) -> int:
    sample = raw[:PREFIX]
    if not sample:
        return 0
    return int(1_000_000 * len(compressor.compress(sample)) / len(sample))


def _target(stage: Path, work: Path, accepted: int, compressor: zstd.ZstdCompressor) -> dict:
    builds = {level: BASE._build(stage, work / f"level-{level}", level) for level in LEVELS}
    low, high = builds[15], builds[19]
    lo = {p["sha256"]: p for p in low["packs"]}
    hi = {p["sha256"]: p for p in high["packs"]}
    if set(lo) != set(hi):
        raise RuntimeError("raw physical pack identity drift between fixed L15/L19 controls")

    rows = []
    observe_started = time.perf_counter()
    for hh in sorted(lo):
        a, b = lo[hh], hi[hh]
        if a["usize"] != b["usize"] or a["crc32"] != b["crc32"] or a["raw"] != b["raw"]:
            raise RuntimeError(f"raw pack proof drift for {hh}")
        rows.append({
            "sha256": hh,
            "usize": int(a["usize"]),
            "l15_csize": int(a["csize"]),
            "l19_csize": int(b["csize"]),
            "saving_bytes": int(a["csize"] - b["csize"]),
            "prefix_zstd1_ratio_ppm": _prefix_ratio_ppm(a["raw"], compressor),
        })
    observation_wall_s = time.perf_counter() - observe_started

    true_paying = sum(1 for r in rows if r["saving_bytes"] > 0)
    rules = []
    for min_size in SIZES:
        for max_ratio in SAMPLE_RATIOS_PPM:
            admitted = [
                r for r in rows
                if r["usize"] >= min_size and r["prefix_zstd1_ratio_ppm"] <= max_ratio
            ]
            saving = sum(r["saving_bytes"] for r in admitted)
            candidate = int(low["archive_bytes"] - saving)
            retained = sum(1 for r in admitted if r["saving_bytes"] > 0)
            false_positive = sum(1 for r in admitted if r["saving_bytes"] <= 0)
            rules.append({
                "min_size": min_size,
                "max_prefix_zstd1_ratio_ppm": max_ratio,
                "admitted_packs": len(admitted),
                "true_winners_retained": retained,
                "false_positives": false_positive,
                "oracle_saving_bytes": int(saving),
                "oracle_archive_bytes": candidate,
                "meets_v029_density": candidate <= accepted,
            })

    return {
        "accepted_v029_bytes": accepted,
        "l15_archive_bytes": int(low["archive_bytes"]),
        "l19_archive_bytes": int(high["archive_bytes"]),
        "l15_create_s": float(low["complete_verified_create_s"]),
        "l19_create_s": float(high["complete_verified_create_s"]),
        "pack_count": len(rows),
        "true_paying_packs": true_paying,
        "observation_wall_s": observation_wall_s,
        "rules": rules,
        "rows": rows,
    }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    neutral = BASE.GENERAL.V029._load(
        BASE.GENERAL.V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py",
        "cmpct_v030_prefix_probe_effort_neutral",
    )
    repair = BASE.GENERAL.V029._load(
        BASE.GENERAL.V029.REPAIR_PATH,
        "cmpct_v030_prefix_probe_effort_repair",
    )
    repair.install_generation_hooks(neutral)
    corpus = work_root / "neutral"
    neutral.build(corpus)
    repair.normalize_root(corpus)

    compressor = zstd.ZstdCompressor(level=1)
    targets = {}
    for name in TARGETS:
        stage = BASE.EXT._normalized_stage(corpus / name, work_root / f"normalized-{name}")
        targets[name] = _target(stage, work_root / name, ACCEPTED_V029[name], compressor)

    combined_rules = []
    for min_size in SIZES:
        for max_ratio in SAMPLE_RATIOS_PPM:
            per_target = {}
            all_meet = True
            admissions = 0
            aggregate_bytes = 0
            for name in TARGETS:
                match = next(
                    r for r in targets[name]["rules"]
                    if r["min_size"] == min_size
                    and r["max_prefix_zstd1_ratio_ppm"] == max_ratio
                )
                per_target[name] = match
                all_meet = all_meet and bool(match["meets_v029_density"])
                admissions += int(match["admitted_packs"])
                aggregate_bytes += int(match["oracle_archive_bytes"])
            combined_rules.append({
                "min_size": min_size,
                "max_prefix_zstd1_ratio_ppm": max_ratio,
                "all_targets_meet_v029_density": all_meet,
                "total_admitted_packs": admissions,
                "aggregate_oracle_archive_bytes": aggregate_bytes,
                "targets": per_target,
            })

    viable = [r for r in combined_rules if r["all_targets_meet_v029_density"]]
    if viable:
        best = min(viable, key=lambda r: (r["total_admitted_packs"], r["aggregate_oracle_archive_bytes"]))
        verdict = "PREFIX_ONLY_FAMILY_CLEARS_BOTH_DENSITY_FLOORS"
    else:
        best = min(combined_rules, key=lambda r: (r["aggregate_oracle_archive_bytes"], r["total_admitted_packs"]))
        verdict = "PREFIX_ONLY_FAMILY_INSUFFICIENT"

    return {
        "schema": "cmpct-v030-prefix-probe-effort-admission-oracle-v1",
        "status": "research-only causal oracle; no product, release, R4, runtime, or transfer credit",
        "release_credit": False,
        "experiment_valid": True,
        "fixed_levels": list(LEVELS),
        "prefix_bytes": PREFIX,
        "rule_family": {
            "min_size_bytes": list(SIZES),
            "max_prefix_zstd1_ratio_ppm": list(SAMPLE_RATIOS_PPM),
        },
        "targets": targets,
        "combined_rules": combined_rules,
        "best_rule": best,
        "verdict": verdict,
        "contract": {
            "same_normalized_source": True,
            "same_raw_pack_identity": True,
            "path_blind_features_only": True,
            "bounded_prefix_only": True,
            "no_full_pack_compression_feature": True,
            "same_rule_applied_to_both_targets": True,
            "no_format_change": True,
            "no_production_selector_change": True,
            "runtime_claim_requires_physical_builder": True,
            "heldout_transfer_required_before_productization": True,
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-prefix-probe-effort-work"))
    ap.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-prefix-probe-effort.json"))
    args = ap.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "verdict": result["verdict"],
        "best_rule": result["best_rule"],
        "targets": {
            name: {
                "l15_archive_bytes": row["l15_archive_bytes"],
                "l19_archive_bytes": row["l19_archive_bytes"],
                "accepted_v029_bytes": row["accepted_v029_bytes"],
            }
            for name, row in result["targets"].items()
        },
    }, indent=2), flush=True)


if __name__ == "__main__":
    main()
