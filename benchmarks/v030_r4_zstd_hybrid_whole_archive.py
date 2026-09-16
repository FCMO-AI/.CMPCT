from __future__ import annotations

"""R4 whole-archive validation for the Zstd parameter-decomposition signal.

The parameter oracle found that level-19 strategy/search parameters can recover much of the
Analytics level-15 byte gap without paying all of level 19's measured final-compression work.
This experiment converts that call-level prediction into complete authenticated CMPNX5 archives.
It keeps v0.25 discovery/representation behavior and all sub-19 probes unchanged, replacing only
final level-19 compression calls with explicit parameter hybrids. Every candidate is strongly
verified and restored to the canonical user-tree identity. No shipping policy is changed.
"""

import argparse
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import statistics
import time

from benchmarks import v030_external_competitors as EXT
from benchmarks import v030_release_generalization as GENERAL
from benchmarks import v030_r4_zstd_parameter_decomposition as ZD
from experiments import entropygraph_v025 as V25
from experiments import entropygraph_v030_product_fs as FS
from experiments import entropygraph_v030_release_product as PRODUCT

TARGETS = (
    "02_office_workspace",
    "04_analytics_and_database",
    "01_developer_repository",
    "08_many_tiny_files",
    "07_incompressible_and_encrypted_like",
)
FINAL_LEVEL = 19
REPS = 2
MAX_PATH_BYTES = 4096
POLICIES = (
    "level15",
    "l15_plus_strategy19",
    "l15_plus_strategy19_searchLog19",
    "level19",
)


def _params(policy: str, raw_n: int) -> dict[str, int]:
    lo = ZD._params(15, raw_n)
    hi = ZD._params(19, raw_n)
    if policy == "level15":
        return lo
    if policy == "level19":
        return hi
    p = dict(lo)
    p["strategy"] = hi["strategy"]
    if policy == "l15_plus_strategy19_searchLog19":
        p["searchLog"] = hi["searchLog"]
    elif policy != "l15_plus_strategy19":
        raise ValueError(policy)
    return p


def _prepare(stage: Path, root: Path) -> tuple[Path, float]:
    profile = root / "profile"
    started = time.perf_counter()
    FS.prepare_profile_tree(
        stage,
        profile,
        max_path_bytes=MAX_PATH_BYTES,
        max_profile_files=PRODUCT.MAX_PROFILE_FILES,
        max_profile_logical_bytes=PRODUCT.MAX_PROFILE_LOGICAL_BYTES,
        max_entries=PRODUCT.MAX_MANIFEST_ENTRIES,
    )
    return profile, time.perf_counter() - started


def _verify(profile: Path, archive: Path, out: Path, expected: str) -> float:
    V25.ROOT = profile
    V25.OUT = archive
    started = time.perf_counter()
    result = dict(V25.strong_verify())
    elapsed = time.perf_counter() - started
    if not result.get("ok"):
        raise RuntimeError(f"strong verification failed: {result!r}")
    shutil.rmtree(out, ignore_errors=True)
    V25.extract(out)
    manifest = out.joinpath(*PurePosixPath(FS.FILESYSTEM_MANIFEST).parts)
    decoded = FS.decode_manifest(
        manifest.read_bytes(),
        max_path_bytes=MAX_PATH_BYTES,
        max_entries=PRODUCT.MAX_MANIFEST_ENTRIES,
    )
    FS.restore_manifest_tree(out, decoded)
    actual = PRODUCT.treehash(out)
    if actual != expected:
        raise RuntimeError(f"restored tree mismatch: {actual} != {expected}")
    return elapsed


def _build_once(stage: Path, root: Path, policy: str) -> dict:
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True)
    profile, stage_s = _prepare(stage, root)
    archive = root / "candidate.cmpnx5"
    expected = PRODUCT.treehash(stage)
    V25.ROOT = profile
    V25.OUT = archive
    original = V25.zc

    def hybrid(raw: bytes, level: int = FINAL_LEVEL) -> bytes:
        requested = int(level)
        if requested < FINAL_LEVEL:
            return original(raw, requested)
        return ZD._compress_params(raw, _params(policy, len(raw)))

    V25.zc = hybrid
    try:
        started = time.perf_counter()
        stats = dict(V25.build())
        build_s = time.perf_counter() - started
    finally:
        V25.zc = original
    verify_s = _verify(profile, archive, root / "out", expected)
    return {
        "archive_bytes": archive.stat().st_size,
        "filesystem_stage_s": stage_s,
        "build_s": build_s,
        "strong_verify_s": verify_s,
        "complete_verified_create_s": stage_s + build_s + verify_s,
        "canonical_user_tree_sha256": expected,
        "build_stats": stats,
    }


def _measure(stage: Path, root: Path, policy: str) -> dict:
    reps = [_build_once(stage, root / f"rep-{i}", policy) for i in range(REPS)]
    sizes = {int(r["archive_bytes"]) for r in reps}
    trees = {r["canonical_user_tree_sha256"] for r in reps}
    if len(sizes) != 1 or len(trees) != 1:
        raise RuntimeError(f"nondeterministic whole-archive candidate: {policy}")
    return {
        "archive_bytes": next(iter(sizes)),
        "median_filesystem_stage_s": statistics.median(r["filesystem_stage_s"] for r in reps),
        "median_build_s": statistics.median(r["build_s"] for r in reps),
        "median_strong_verify_s": statistics.median(r["strong_verify_s"] for r in reps),
        "median_complete_verified_create_s": statistics.median(r["complete_verified_create_s"] for r in reps),
        "canonical_user_tree_sha256": next(iter(trees)),
        "repetitions": REPS,
        "build_stats": reps[0]["build_stats"],
    }


def _one(name: str, source: Path, accepted_v029: int, work: Path) -> dict:
    stage = EXT._normalized_stage(source, work / name / "normalized")
    expected_external = EXT._tree(stage)
    rows = {p: _measure(stage, work / name / p, p) for p in POLICIES}
    zip_root = work / name / "zip"
    zip_root.mkdir(parents=True, exist_ok=True)
    z = EXT._zip(stage, zip_root / "archive.zip", zip_root / "out")
    EXT._verify_extracted(zip_root / "out", expected_external, "zip_deflate9")

    low = rows["level15"]
    high = rows["level19"]
    candidate = rows["l15_plus_strategy19_searchLog19"]
    gap = max(1, int(low["archive_bytes"]) - accepted_v029)
    recovered = int(low["archive_bytes"]) - int(candidate["archive_bytes"])
    high_recovered = max(1, int(low["archive_bytes"]) - int(high["archive_bytes"]))
    low_t = float(low["median_complete_verified_create_s"])
    high_extra_t = max(1e-9, float(high["median_complete_verified_create_s"]) - low_t)
    candidate_extra_t = max(0.0, float(candidate["median_complete_verified_create_s"]) - low_t)
    return {
        "workload": name,
        "accepted_v029_bytes": accepted_v029,
        "policies": rows,
        "zip_deflate9": {"archive_bytes": int(z["archive_bytes"]), "create_s": float(z["create_s"])},
        "strategy_search_tests": {
            "bytes_recovered_vs_level15": recovered,
            "fraction_of_v029_gap_recovered": recovered / gap,
            "fraction_of_level19_saving_recovered": recovered / high_recovered,
            "fraction_of_level19_incremental_complete_time": candidate_extra_t / high_extra_t,
            "not_larger_than_level15": int(candidate["archive_bytes"]) <= int(low["archive_bytes"]),
            "beats_v029_floor": int(candidate["archive_bytes"]) < accepted_v029,
            "faster_than_level19_complete": float(candidate["median_complete_verified_create_s"]) < float(high["median_complete_verified_create_s"]),
        },
    }


def run(work: Path) -> dict:
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    neutral = GENERAL.V029._load(GENERAL.V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py", "cmpct_v030_zstd_hybrid_neutral")
    repair = GENERAL.V029._load(GENERAL.V029.REPAIR_PATH, "cmpct_v030_zstd_hybrid_repair")
    repair.install_generation_hooks(neutral)
    corpus = work / "neutral"
    neutral.build(corpus)
    repair.normalize_root(corpus)
    accepted = GENERAL._accepted_v029_rows()

    rows = []
    for name in TARGETS:
        row = _one(name, corpus / name, int(accepted[("neutral_hostile_v1", name)]["accepted_v029_bytes"]), work)
        rows.append(row)
        print(json.dumps({"workload": name, **row["strategy_search_tests"]}, separators=(",", ":")), flush=True)

    analytics = next(r for r in rows if r["workload"] == "04_analytics_and_database")
    controls = [r for r in rows if r["workload"] in ("01_developer_repository", "08_many_tiny_files", "07_incompressible_and_encrypted_like")]
    tests = analytics["strategy_search_tests"]
    hypothesis = {
        "analytics_recovers_ge_70pct_v029_gap": tests["fraction_of_v029_gap_recovered"] >= 0.70,
        "analytics_uses_lt_70pct_level19_incremental_complete_time": tests["fraction_of_level19_incremental_complete_time"] < 0.70,
        "analytics_faster_than_level19_complete": tests["faster_than_level19_complete"],
        "no_control_size_regression_vs_level15": all(r["strategy_search_tests"]["not_larger_than_level15"] for r in controls),
        "all_candidates_exact_and_deterministic": all(len({p["canonical_user_tree_sha256"] for p in r["policies"].values()}) == 1 for r in rows),
    }
    hypothesis["supported"] = all(hypothesis.values())
    return {
        "schema": "cmpct-v030-r4-zstd-hybrid-whole-archive-v1",
        "source_commit": os.environ.get("EVIDENCE_HEAD"),
        "targets": list(TARGETS),
        "policies": list(POLICIES),
        "rows": rows,
        "hypothesis": hypothesis,
        "contract": {
            "diagnostic_only": True,
            "release_credit": False,
            "production_selector_changed": False,
            "representation_discovery_changed": False,
            "sub19_probe_behavior_preserved": True,
            "mandatory_strong_verify": True,
            "canonical_filesystem_semantics_preserved": True,
            "same_input_same_semantics": True,
        },
        "next_if_supported": "test a workload-blind bounded admission rule and exact all-15 product costs before any shipping integration",
        "next_if_falsified": "close zstd parameter recombination as primary R4; move to a new representation/execution primitive",
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-zstd-hybrid-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-zstd-hybrid-whole-archive.json"))
    args = p.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["hypothesis"], indent=2), flush=True)


if __name__ == "__main__":
    main()
