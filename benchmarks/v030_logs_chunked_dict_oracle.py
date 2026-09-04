from __future__ import annotations

"""Targeted chunk-trained shared-dictionary oracle for the v0.30 logs blocker.

The first segmented shared-dictionary experiment never actually exercised ``logs_and_telemetry``: locality-safe
segmentation produces only four or five large segments, while the generic trainer required at least eight whole
segments. That is a harness limitation, not negative compression evidence.

This oracle keeps the exact same <=8x / <=8 MiB independently decodable segment representation, but trains the
shared Zstd dictionary from bounded, non-overlapping 64 KiB samples cut from those same segments. Sampling and
training are inside ``dictionary_train_s`` and therefore charged to creation time. No source bytes are hidden or
precomputed, and each candidate is still fully extracted and exact-tree verified before receiving credit.

Research only: even a four-way win does not become canonical r25 until a bounded product grammar, recovery,
Python/native/Android readers and the normal exact-product release gates all pass.
"""

import argparse
import json
from pathlib import Path
import shutil
import time

import zstandard as zstd

from benchmarks import v030_external_competitors as B
from benchmarks import v030_release_generalization as GENERAL
from benchmarks import v030_segmented_dict_oracle as BASE

TARGET = "05_logs_and_telemetry"
SAMPLE_BYTES = 64 * 1024
MAX_SAMPLES = 128
DICT_SIZES = (8 * 1024, 16 * 1024, 32 * 1024)
LEVELS = (1, 3, 6, 9, 12)


def _chunk_train(raw_segments: list[bytes], dict_size: int) -> tuple[bytes | None, float, str | None]:
    """Train from bounded non-overlapping samples while charging sample construction to the timer."""
    started = time.perf_counter()
    samples: list[bytes] = []
    for raw in raw_segments:
        for offset in range(0, len(raw), SAMPLE_BYTES):
            sample = raw[offset : offset + SAMPLE_BYTES]
            if len(sample) >= 256:
                samples.append(sample)
            if len(samples) >= MAX_SAMPLES:
                break
        if len(samples) >= MAX_SAMPLES:
            break

    total = sum(map(len, samples))
    if len(samples) < 8 or total < max(32 * 1024, dict_size * 4):
        return None, time.perf_counter() - started, "insufficient-chunk-training-samples"
    size = min(dict_size, max(1024, total // 8))
    try:
        trained = zstd.train_dictionary(size, samples)
        dictionary = trained.as_bytes()
    except Exception as exc:
        return None, time.perf_counter() - started, f"train-failed:{type(exc).__name__}"
    return dictionary, time.perf_counter() - started, None


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)

    accepted = GENERAL._accepted_v029_rows()
    neutral = GENERAL.V029._load(
        GENERAL.V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py",
        "cmpct_logs_chunked_dict_neutral",
    )
    repair = GENERAL.V029._load(
        GENERAL.V029.REPAIR_PATH,
        "cmpct_logs_chunked_dict_repair",
    )
    repair.install_generation_hooks(neutral)

    root = work_root / "neutral"
    neutral.build(root)
    repair.normalize_root(root)
    workload = root / TARGET
    key = ("neutral_hostile_v1", TARGET)
    if B._tree(workload) != accepted[key]["tree_sha256"]:
        raise RuntimeError("logs chunked-dictionary source drift")

    original_train = BASE._train
    original_dict_sizes = BASE.DICT_SIZES
    original_levels = BASE.LEVELS
    try:
        BASE._train = _chunk_train
        BASE.DICT_SIZES = DICT_SIZES
        BASE.LEVELS = LEVELS
        row = BASE._one("neutral_hostile_v1/05_logs_and_telemetry", workload, work_root)
    finally:
        BASE._train = original_train
        BASE.DICT_SIZES = original_dict_sizes
        BASE.LEVELS = original_levels

    available = [candidate for candidate in row["candidates"] if candidate.get("available")]
    viable = [candidate for candidate in available if candidate.get("viable")]
    best = min(
        viable,
        key=lambda candidate: (
            candidate["archive_bytes"],
            candidate["create_s"],
            candidate["dict_bytes"],
            candidate["level"],
        ),
        default=None,
    )
    closest = min(
        available,
        key=lambda candidate: (
            max(0, int(candidate["archive_bytes"]) - int(row["tar_zstd19"]["archive_bytes"])),
            max(0.0, float(candidate["create_s"]) - float(row["zip"]["create_s"])),
            candidate["archive_bytes"],
            candidate["create_s"],
        ),
        default=None,
    )

    return {
        "schema": "cmpct-v030-logs-chunked-dict-oracle-v1",
        "claim_boundary": (
            "research-only targeted disproof surface for logs; chunk-trained shared dictionary keeps the existing "
            "locality-safe segmented representation and cannot authorize canonical r25"
        ),
        "target": "neutral_hostile_v1/05_logs_and_telemetry",
        "sample_policy": {
            "sample_bytes": SAMPLE_BYTES,
            "max_samples": MAX_SAMPLES,
            "non_overlapping": True,
            "sampling_time_charged_inside_dictionary_train_s": True,
        },
        "dictionary_sizes": list(DICT_SIZES),
        "levels": list(LEVELS),
        "max_member_read_amplification": BASE.BASE.MAX_MEMBER_AMPLIFICATION,
        "max_decode_unit_bytes": BASE.BASE.MAX_DECODE_UNIT,
        "row": row,
        "summary": {
            "available_candidates": len(available),
            "viable_candidates": len(viable),
            "four_way_win": best is not None,
            "best": best,
            "closest": closest,
            "all_available_tree_verified": all(candidate.get("tree_verified") is True for candidate in available),
            "all_available_locality_green": all(candidate.get("locality_green") is True for candidate in available),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--work-root",
        type=Path,
        default=Path("benchmark-artifacts/v030-logs-chunked-dict-work"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("benchmark-artifacts/v030-logs-chunked-dict.json"),
    )
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    summary = result["summary"]
    print(
        json.dumps(
            {
                "four_way_win": summary["four_way_win"],
                "best": summary["best"],
                "closest": summary["closest"],
            },
            indent=2,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
