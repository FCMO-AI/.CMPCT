from __future__ import annotations

"""Charged physical referee for the frozen Analytics prefix-effort selector.

This is the physical follow-up required by the prefix-only admission oracle.  It asks
one narrow question: can the frozen path-blind 256 KiB + 4 KiB Zstd-1-ratio<=0.70
rule preserve the oracle's byte win while avoiding the full-L15-then-L19 double
compression that killed the earlier proof-directed selector?

The selector is charged exactly where the CMPNX5 research engine would otherwise
perform each level-19 physical-pack compression.  Every such pack pays one bounded
4 KiB Zstd-1 probe; admitted packs are then compressed once at L19 and rejected
packs once at L15.  No workload/path/hash/type label is available to the policy.

Research only.  CMPNX5 is non-canonical and this referee earns no product/release
credit even if it passes.  A pass only authorizes held-out transfer and complete
product integration work.
"""

import argparse
import json
from pathlib import Path
import shutil
import statistics
import time

from benchmarks import v030_analytics_proof_directed_admission_oracle as BASE
from benchmarks import v030_v025_canonical_fs_level1_oracle as CANON
from benchmarks import v030_external_competitors as EXT
from experiments import entropygraph_v025 as V25

TARGET = "04_analytics_and_database"
ACCEPTED_V029_BYTES = 6_135_172
EXPECTED_ORACLE_BYTES = 6_134_940
PREFIX_BYTES = 4096
MIN_SIZE_BYTES = 256 * 1024
MAX_PREFIX_ZSTD1_RATIO_PPM = 700_000
ROUNDS = 3
MIN_MATERIAL_L19_SPEEDUP = 0.20


def _control(stage: Path, root: Path, level: int) -> dict:
    old_cap = CANON.LEVEL_CAP
    CANON.LEVEL_CAP = level
    try:
        return CANON._canonical_v25(stage, root)
    finally:
        CANON.LEVEL_CAP = old_cap


def _selector(stage: Path, root: Path) -> dict:
    original_zc = V25.zc
    old_cap = CANON.LEVEL_CAP
    stats = {
        "probed_packs": 0,
        "selected_l19_packs": 0,
        "rejected_l15_packs": 0,
        "prefix_probe_wall_s": 0.0,
        "selected_full_wall_s": 0.0,
        "rejected_full_wall_s": 0.0,
    }

    def selective_zc(raw: bytes, level: int = 19) -> bytes:
        # Only replace the physical-pack L19 decision point.  Cheap L3 auditions,
        # metadata L12, and other codec work retain their original semantics.
        if int(level) != 19:
            return original_zc(raw, int(level))

        t0 = time.perf_counter()
        sample = raw[:PREFIX_BYTES]
        prefix = original_zc(sample, 1) if sample else b""
        stats["prefix_probe_wall_s"] += time.perf_counter() - t0
        ratio_ppm = 0 if not sample else int(1_000_000 * len(prefix) / len(sample))
        admitted = len(raw) >= MIN_SIZE_BYTES and ratio_ppm <= MAX_PREFIX_ZSTD1_RATIO_PPM
        stats["probed_packs"] += 1

        t1 = time.perf_counter()
        if admitted:
            out = original_zc(raw, 19)
            stats["selected_l19_packs"] += 1
            stats["selected_full_wall_s"] += time.perf_counter() - t1
        else:
            out = original_zc(raw, 15)
            stats["rejected_l15_packs"] += 1
            stats["rejected_full_wall_s"] += time.perf_counter() - t1
        return out

    V25.zc = selective_zc
    CANON.LEVEL_CAP = 19
    try:
        result = dict(CANON._canonical_v25(stage, root))
    finally:
        V25.zc = original_zc
        CANON.LEVEL_CAP = old_cap
    result["selector_stats"] = stats
    return result


def _prepare(work_root: Path) -> Path:
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
    return EXT._normalized_stage(corpus / TARGET, work_root / "normalized")


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    stage = _prepare(work_root)
    expected_tree = EXT._tree(stage)

    samples = {"selector": [], "l15": [], "l19": [], "zip": []}
    sizes = {name: set() for name in samples}
    selector_stats = []
    engines = ("selector", "l15", "zip", "l19")

    for round_index in range(ROUNDS):
        order = list(engines[round_index:] + engines[:round_index])
        round_root = work_root / f"round-{round_index}"
        round_root.mkdir()
        for engine in order:
            root = round_root / engine
            root.mkdir()
            if engine == "selector":
                row = _selector(stage, root)
                samples[engine].append(float(row["complete_verified_create_s"]))
                sizes[engine].add(int(row["archive_bytes"]))
                selector_stats.append(row["selector_stats"])
            elif engine == "l15":
                row = _control(stage, root, 15)
                samples[engine].append(float(row["complete_verified_create_s"]))
                sizes[engine].add(int(row["archive_bytes"]))
            elif engine == "l19":
                row = _control(stage, root, 19)
                samples[engine].append(float(row["complete_verified_create_s"]))
                sizes[engine].add(int(row["archive_bytes"]))
            else:
                row = EXT._zip(stage, root / "archive.zip", root / "out")
                EXT._verify_extracted(root / "out", expected_tree, "zip_deflate9")
                samples[engine].append(float(row["create_s"]))
                sizes[engine].add(int(row["archive_bytes"]))

    if any(len(v) != 1 for v in sizes.values()):
        raise RuntimeError(f"nondeterministic archive sizes: {sizes!r}")
    med = {k: statistics.median(v) for k, v in samples.items()}
    b = {k: next(iter(v)) for k, v in sizes.items()}

    exact_oracle_bytes = b["selector"] == EXPECTED_ORACLE_BYTES
    clears_v029 = b["selector"] <= ACCEPTED_V029_BYTES
    faster_than_zip = med["selector"] < med["zip"]
    l19_speedup = 1.0 - med["selector"] / med["l19"] if med["l19"] else 0.0
    material_l19_speedup = l19_speedup >= MIN_MATERIAL_L19_SPEEDUP

    selector_shape_stable = len({
        (s["probed_packs"], s["selected_l19_packs"], s["rejected_l15_packs"])
        for s in selector_stats
    }) == 1
    selector_shape = {
        key: int(selector_stats[0][key])
        for key in ("probed_packs", "selected_l19_packs", "rejected_l15_packs")
    }

    if exact_oracle_bytes and clears_v029 and faster_than_zip:
        verdict = "ADVANCE_TO_HELDOUT_AND_COMPLETE_PRODUCT"
    elif exact_oracle_bytes and clears_v029 and material_l19_speedup:
        verdict = "NARROW_TO_EXECUTION_SPEED_DEBT"
    else:
        verdict = "RETIRE_PREFIX_SELECTOR_AS_CURRENT_ECONOMIC_ROUTE"

    return {
        "schema": "cmpct-v030-analytics-prefix-probe-physical-referee-v1",
        "status": "research-only charged physical referee; no product/release/R4 credit",
        "release_credit": False,
        "product_credit": False,
        "target": f"neutral_hostile_v1/{TARGET}",
        "rounds": ROUNDS,
        "frozen_rule": {
            "min_size_bytes": MIN_SIZE_BYTES,
            "prefix_bytes": PREFIX_BYTES,
            "prefix_codec": "zstd-1",
            "max_prefix_zstd1_ratio_ppm": MAX_PREFIX_ZSTD1_RATIO_PPM,
        },
        "predeclared_decision": {
            "accepted_v029_bytes": ACCEPTED_V029_BYTES,
            "expected_oracle_bytes": EXPECTED_ORACLE_BYTES,
            "must_reproduce_oracle_bytes_exactly": True,
            "product_economics_target": "median complete verified selector create must be strictly faster than fresh ZIP/Deflate-9",
            "material_l19_speedup_fraction": MIN_MATERIAL_L19_SPEEDUP,
            "interpretation": "If density survives but ZIP still wins, retain only if selector removes >=20% of global-L19 complete-create time; otherwise retire this selector as the current economic route.",
        },
        "bytes": b,
        "times": {
            k: {"raw_s": samples[k], "median_s": med[k]}
            for k in samples
        },
        "selector_stats": selector_stats,
        "selector_shape": selector_shape,
        "gates": {
            "sizes_deterministic": all(len(v) == 1 for v in sizes.values()),
            "selector_shape_stable": selector_shape_stable,
            "exact_oracle_bytes": exact_oracle_bytes,
            "clears_accepted_v029_floor": clears_v029,
            "strictly_faster_than_zip": faster_than_zip,
            "material_speedup_vs_global_l19": material_l19_speedup,
        },
        "derived": {
            "selector_saving_vs_l15_bytes": b["l15"] - b["selector"],
            "selector_margin_vs_v029_bytes": b["selector"] - ACCEPTED_V029_BYTES,
            "selector_speedup_vs_l19_fraction": l19_speedup,
            "selector_to_zip_time_ratio": med["selector"] / med["zip"] if med["zip"] else None,
        },
        "verdict": verdict,
        "claim_boundary": (
            "This proves only physical selector economics on the frozen Analytics workload and CMPNX5 research surface. "
            "It does not establish held-out transfer, canonical-r25 integration, 15-workload domination, or release readiness."
        ),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-analytics-prefix-physical-work"))
    ap.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-analytics-prefix-physical.json"))
    args = ap.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "verdict": result["verdict"],
        "bytes": result["bytes"],
        "medians_s": {k: v["median_s"] for k, v in result["times"].items()},
        "selector_shape": result["selector_shape"],
        "derived": result["derived"],
    }, indent=2), flush=True)


if __name__ == "__main__":
    main()
