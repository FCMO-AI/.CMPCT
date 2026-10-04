from __future__ import annotations

"""Decisive Analytics effort frontier against both strict competitors and accepted v0.29.

The complete level-1 canonical-filesystem candidate is already smaller/faster than ZIP and Zstd-19 but remains
422,093 bytes above accepted v0.29. Historical raw-CMPNX5 evidence tightens the pre-mortem: level 15 is still
6,568,522 B while level 19 reaches exactly the 6,135,172-B accepted floor only by slowing to 7.87 s versus ZIP's
1.526 s. Therefore this research-only oracle brackets levels 15-19 (plus level 1 control) after charging canonical
filesystem semantics and mandatory strong verification. If no interior point reaches the v0.29 floor inside the ZIP
budget, compression-effort tuning is saturated and Analytics must escalate representation rather than tune levels.
"""

import argparse
import json
from pathlib import Path
import shutil
import statistics

from benchmarks import v030_external_competitors as EXT
from benchmarks import v030_release_generalization as GENERAL
from benchmarks import v030_v025_canonical_fs_level1_oracle as CANON
from experiments import entropygraph_v030_release_product as PRODUCT

TARGET = "04_analytics_and_database"
LEVELS = (1, 15, 16, 17, 18, 19)
ROUNDS = 3


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)

    neutral = GENERAL.V029._load(
        GENERAL.V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py",
        "cmpct_v030_analytics_v029_effort_neutral",
    )
    repair = GENERAL.V029._load(GENERAL.V029.REPAIR_PATH, "cmpct_v030_analytics_v029_effort_repair")
    repair.install_generation_hooks(neutral)
    corpus = work_root / "neutral"
    neutral.build(corpus)
    repair.normalize_root(corpus)
    source = corpus / TARGET
    accepted = int(GENERAL._accepted_v029_rows()[("neutral_hostile_v1", TARGET)]["accepted_v029_bytes"])

    stage = EXT._normalized_stage(source, work_root / "normalized")
    expected_external_tree = EXT._tree(stage)
    expected_user_tree = PRODUCT.treehash(stage)

    comparator_samples = {"zip": [], "zstd19": []}
    comparator_sizes = {"zip": set(), "zstd19": set()}
    for rep in range(ROUNDS):
        order = ("zip", "zstd19") if rep % 2 == 0 else ("zstd19", "zip")
        for engine in order:
            root = work_root / "comparators" / f"r{rep}-{engine}"
            root.mkdir(parents=True, exist_ok=True)
            if engine == "zip":
                result = EXT._zip(stage, root / "archive.zip", root / "out")
                EXT._verify_extracted(root / "out", expected_external_tree, "zip_deflate9")
            else:
                result = EXT._tar_zstd(stage, root / "archive.tar.zst", root / "out", root)
                if not result.get("available"):
                    raise RuntimeError(f"Zstd-19 unavailable: {result!r}")
                EXT._verify_extracted(root / "out", expected_external_tree, "tar_zstd19_solid")
            comparator_samples[engine].append(float(result["create_s"]))
            comparator_sizes[engine].add(int(result["archive_bytes"]))

    if any(len(values) != 1 for values in comparator_sizes.values()):
        raise RuntimeError(f"comparator size nondeterminism: {comparator_sizes!r}")
    cmp = {
        engine: {
            "archive_bytes": next(iter(comparator_sizes[engine])),
            "median_create_s": statistics.median(comparator_samples[engine]),
            "raw_create_s": comparator_samples[engine],
        }
        for engine in ("zip", "zstd19")
    }

    rows = []
    original_cap = CANON.LEVEL_CAP
    try:
        for level in LEVELS:
            samples = []
            sizes = set()
            manifests = set()
            for rep in range(ROUNDS):
                CANON.LEVEL_CAP = level
                result = CANON._canonical_v25(stage, work_root / "candidate" / f"l{level}-r{rep}")
                if result["canonical_user_tree_sha256"] != expected_user_tree:
                    raise RuntimeError(f"level {level} user-tree drift")
                samples.append(float(result["complete_verified_create_s"]))
                sizes.add(int(result["archive_bytes"]))
                manifests.add(str(result["filesystem_manifest_sha256"]))
            if len(sizes) != 1 or len(manifests) != 1:
                raise RuntimeError(f"level {level} deterministic identity drift")
            archive_bytes = next(iter(sizes))
            median_s = statistics.median(samples)
            strict = {
                "no_regression_vs_v029": archive_bytes <= accepted,
                "smaller_than_zip": archive_bytes < cmp["zip"]["archive_bytes"],
                "smaller_than_zstd19": archive_bytes < cmp["zstd19"]["archive_bytes"],
                "faster_than_zip": median_s < cmp["zip"]["median_create_s"],
                "faster_than_zstd19": median_s < cmp["zstd19"]["median_create_s"],
            }
            strict["release_size_time_prerequisites"] = all(strict.values())
            rows.append({
                "level_cap": level,
                "archive_bytes": archive_bytes,
                "saving_vs_v029_bytes": accepted - archive_bytes,
                "median_complete_verified_create_s": median_s,
                "raw_complete_verified_create_s": samples,
                "strict": strict,
            })
            print(json.dumps(rows[-1], separators=(",", ":")), flush=True)
    finally:
        CANON.LEVEL_CAP = original_cap

    viable = [row for row in rows if row["strict"]["release_size_time_prerequisites"]]
    fastest = min(viable, key=lambda row: row["median_complete_verified_create_s"]) if viable else None
    return {
        "schema": "cmpct-v030-analytics-v029-effort-frontier-v1",
        "target": f"neutral_hostile_v1/{TARGET}",
        "levels": list(LEVELS),
        "rounds": ROUNDS,
        "accepted_v029_bytes": accepted,
        "historical_raw_bracket": {
            "level15_bytes": 6_568_522,
            "level19_bytes": 6_135_172,
            "level19_median_verified_create_s": 7.870632347999987,
            "historical_zip_median_create_s": 1.525825019000024,
        },
        "comparators": cmp,
        "rows": rows,
        "result": {
            "crosses_all_size_time_prerequisites": bool(viable),
            "fastest_viable": fastest,
        },
        "contract": {
            "canonical_filesystem_tax_inside_candidate_timing": True,
            "mandatory_strong_verify_inside_candidate_timing": True,
            "fresh_comparators_same_normalized_tree": True,
            "ties_fail": True,
            "production_selector_changed": False,
            "benchmark_identity_in_production_policy": False,
            "release_credit": False,
        },
        "experiment_valid": True,
        "release_credit": False,
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-analytics-v029-effort-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-analytics-v029-effort.json"))
    args = p.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["result"], indent=2), flush=True)


if __name__ == "__main__":
    main()
