from __future__ import annotations

"""Physical referee for the frozen Analytics proof-directed admission rule.

This is the mandatory materialization step after
`v030_analytics_proof_directed_admission_oracle.py` returned
`BUILD_FROZEN_SELECTIVE_ADMISSION` at commit 98de2e7854534b78097219dc28d04fa7374269bc.

Frozen rule (chosen before this physical timing run):
- raw stream size >= 256 KiB
- level-15 compressed/raw ratio <= 0.70
- only requests whose ordinary requested effort exceeds 15 may escalate to level 19

The rule is path-blind and content-derived.  Every admitted stream first pays the ordinary level-15
compression needed by the proof, then also pays level 19; the emitted payload is the smaller of the
two.  This deliberately charges the real exported compute cost that the oracle could not measure.
It changes no archive grammar and earns no product/release credit.
"""

import argparse
import json
from pathlib import Path
import shutil
import statistics
import time

from benchmarks import v030_analytics_proof_directed_admission_oracle as ORACLE
from benchmarks import v030_external_competitors as EXT
from benchmarks import v030_release_generalization as GENERAL
from benchmarks import v030_v025_canonical_fs_level1_oracle as CANON
from experiments import entropygraph_v025 as V25

TARGET = "04_analytics_and_database"
ACCEPTED_V029_BYTES = 6_135_172
FROZEN_MIN_SIZE = 256 * 1024
FROZEN_MAX_CHEAP_RATIO_PPM = 700_000
ORACLE_PROJECTED_BYTES = 6_134_940
ROUNDS = 3


def _fixed(stage: Path, root: Path, level: int) -> dict:
    old_cap = CANON.LEVEL_CAP
    CANON.LEVEL_CAP = level
    try:
        return CANON._canonical_v25(stage, root)
    finally:
        CANON.LEVEL_CAP = old_cap


def _selective(stage: Path, root: Path) -> dict:
    real_zc = V25.zc
    metrics = {
        "zc_calls": 0,
        "cheap_calls": 0,
        "high_calls": 0,
        "admitted_calls": 0,
        "raw_bytes_seen": 0,
        "raw_bytes_admitted": 0,
        "cheap_cpu_s": 0.0,
        "high_cpu_s": 0.0,
        "high_payload_saving_bytes": 0,
    }

    def selective_zc(raw: bytes, level: int = 19) -> bytes:
        requested = int(level)
        metrics["zc_calls"] += 1
        metrics["raw_bytes_seen"] += len(raw)

        cheap_level = min(requested, 15)
        t0 = time.process_time()
        cheap = real_zc(raw, cheap_level)
        metrics["cheap_cpu_s"] += time.process_time() - t0
        metrics["cheap_calls"] += 1

        if requested <= 15 or len(raw) < FROZEN_MIN_SIZE:
            return cheap
        ratio_ppm = int(1_000_000 * len(cheap) / max(1, len(raw)))
        if ratio_ppm > FROZEN_MAX_CHEAP_RATIO_PPM:
            return cheap

        metrics["admitted_calls"] += 1
        metrics["raw_bytes_admitted"] += len(raw)
        t0 = time.process_time()
        high = real_zc(raw, min(requested, 19))
        metrics["high_cpu_s"] += time.process_time() - t0
        metrics["high_calls"] += 1
        if len(high) < len(cheap):
            metrics["high_payload_saving_bytes"] += len(cheap) - len(high)
            return high
        return cheap

    old_cap = CANON.LEVEL_CAP
    V25.zc = selective_zc
    CANON.LEVEL_CAP = 19
    try:
        result = dict(CANON._canonical_v25(stage, root))
    finally:
        CANON.LEVEL_CAP = old_cap
        V25.zc = real_zc
    result["selector_metrics"] = metrics
    return result


def _median(values: list[float]) -> float:
    return float(statistics.median(values))


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)

    neutral = GENERAL.V029._load(
        GENERAL.V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py",
        "cmpct_v030_analytics_selective_physical_neutral",
    )
    repair = GENERAL.V029._load(
        GENERAL.V029.REPAIR_PATH,
        "cmpct_v030_analytics_selective_physical_repair",
    )
    repair.install_generation_hooks(neutral)
    corpus = work_root / "neutral"
    neutral.build(corpus)
    repair.normalize_root(corpus)
    stage = EXT._normalized_stage(corpus / TARGET, work_root / "normalized")
    expected_tree = EXT._tree(stage)

    names = ["selective", "l15", "l19", "zip", "zstd19"]
    times: dict[str, list[float]] = {name: [] for name in names}
    sizes: dict[str, set[int]] = {name: set() for name in names}
    selector_rounds: list[dict] = []

    for round_index in range(ROUNDS):
        shift = round_index % len(names)
        order = names[shift:] + names[:shift]
        round_root = work_root / f"round-{round_index}"
        round_root.mkdir()
        for name in order:
            root = round_root / name
            root.mkdir()
            if name == "selective":
                result = _selective(stage, root)
                times[name].append(float(result["complete_verified_create_s"]))
                sizes[name].add(int(result["archive_bytes"]))
                selector_rounds.append(result["selector_metrics"])
            elif name in {"l15", "l19"}:
                result = _fixed(stage, root, 15 if name == "l15" else 19)
                times[name].append(float(result["complete_verified_create_s"]))
                sizes[name].add(int(result["archive_bytes"]))
            elif name == "zip":
                result = EXT._zip(stage, root / "archive.zip", root / "out")
                EXT._verify_extracted(root / "out", expected_tree, "zip_deflate9")
                times[name].append(float(result["create_s"]))
                sizes[name].add(int(result["archive_bytes"]))
            else:
                result = EXT._tar_zstd(stage, root / "archive.tar.zst", root / "out", root)
                if not result.get("available"):
                    raise RuntimeError(f"solid Zstd-19 unavailable: {result!r}")
                EXT._verify_extracted(root / "out", expected_tree, "tar_zstd19_solid")
                times[name].append(float(result["create_s"]))
                sizes[name].add(int(result["archive_bytes"]))

    if any(len(v) != 1 for v in sizes.values()):
        raise RuntimeError(f"nondeterministic archive sizes: {sizes!r}")
    b = {name: next(iter(v)) for name, v in sizes.items()}
    med = {name: _median(v) for name, v in times.items()}

    physical = {
        "beats_v029_bytes": b["selective"] < ACCEPTED_V029_BYTES,
        "matches_oracle_projection": b["selective"] == ORACLE_PROJECTED_BYTES,
        "faster_than_zip": med["selective"] < med["zip"],
        "faster_than_zstd19": med["selective"] < med["zstd19"],
        "faster_than_global_l19": med["selective"] < med["l19"],
        "size_time_prerequisite": (
            b["selective"] < ACCEPTED_V029_BYTES
            and med["selective"] < med["zip"]
            and med["selective"] < med["zstd19"]
        ),
    }

    # This measurement is decisive even when the mechanism loses.  Promotion remains impossible here:
    # CMPNX5 is research framing and this referee intentionally grants no release credit.
    return {
        "schema": "cmpct-v030-analytics-frozen-selective-admission-physical-v1",
        "target": f"neutral_hostile_v1/{TARGET}",
        "release_credit": False,
        "experiment_valid": True,
        "rounds": ROUNDS,
        "accepted_v029_bytes": ACCEPTED_V029_BYTES,
        "oracle_source_commit": "98de2e7854534b78097219dc28d04fa7374269bc",
        "oracle_projected_bytes": ORACLE_PROJECTED_BYTES,
        "frozen_rule": {
            "min_size": FROZEN_MIN_SIZE,
            "max_cheap_ratio_ppm": FROZEN_MAX_CHEAP_RATIO_PPM,
            "path_blind": True,
            "content_only": True,
        },
        "archive_bytes": b,
        "median_create_s": med,
        "raw_create_s": times,
        "selector_rounds": selector_rounds,
        "physical_gate": physical,
        "next_decision": (
            "ADVANCE_GENERIC_SELECTIVE_ADMISSION"
            if physical["size_time_prerequisite"]
            else "RETIRE_DOUBLE_COMPRESSION_SELECTOR"
        ),
        "claim_boundary": (
            "Research-only physical cost referee. It materializes the frozen content-only selector and charges both "
            "the cheap proof compression and every admitted high-effort compression. No canonical-r25 or release credit."
        ),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--work-root",
        type=Path,
        default=Path("benchmark-artifacts/v030-analytics-selective-physical-work"),
    )
    ap.add_argument(
        "--output",
        type=Path,
        default=Path("benchmark-artifacts/v030-analytics-selective-physical.json"),
    )
    args = ap.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "archive_bytes": result["archive_bytes"],
                "median_create_s": result["median_create_s"],
                "physical_gate": result["physical_gate"],
                "next_decision": result["next_decision"],
            },
            indent=2,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
