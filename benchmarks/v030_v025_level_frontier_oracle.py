from __future__ import annotations

"""Exact speed/ratio frontier for the historical EntropyGraph v0.25 representation.

The strength-recovery lane proved that CMPNX5 still has enormous size headroom on office and analytics but misses
ZIP creation time. This oracle asks whether that is mostly self-inflicted Zstd-19 CPU cost. It preserves the exact
CMPNX5 grammar and candidate logic and caps only requested internal Zstd compression levels during build. Every
candidate pays build + mandatory strong verification, extracts back to the exact frozen tree, and is compared with
fresh ZIP/Deflate-9 and solid Zstd-19 measurements on the same runner.

This remains research evidence only. CMPNX5 is non-canonical; any winning mechanism must be re-expressed in bounded
canonical r25 with native/Android/recovery/locality parity before release credit.
"""

import argparse
import json
from pathlib import Path
import shutil
import statistics
import tempfile
import time

from benchmarks import v030_external_competitors as EXT
from benchmarks import v030_release_generalization as GENERAL
from experiments import entropygraph_v025 as V25

TARGETS = ("02_office_workspace", "04_analytics_and_database")
LEVELS = (1, 3, 6, 9, 12, 15, 19)
ROUNDS = 3


def _cmpnx5(stage: Path, root: Path, level_cap: int) -> dict:
    archive = root / f"candidate-l{level_cap}.cmpnx5"
    V25.ROOT = stage
    V25.OUT = archive
    original_zc = V25.zc

    def capped_zc(raw: bytes, level: int = 19) -> bytes:
        return original_zc(raw, min(int(level), int(level_cap)))

    V25.zc = capped_zc
    try:
        started = time.perf_counter()
        build_stats = dict(V25.build())
        build_s = time.perf_counter() - started
    finally:
        V25.zc = original_zc

    started = time.perf_counter()
    verified = dict(V25.strong_verify())
    verify_s = time.perf_counter() - started
    if not verified.get("ok"):
        raise RuntimeError(f"CMPNX5 level {level_cap} strong verification failed: {verified!r}")
    extracted = root / "out"
    V25.extract(extracted)
    EXT._verify_extracted(extracted, EXT._tree(stage), f"cmpnx5-l{level_cap}")
    return {
        "archive_bytes": archive.stat().st_size,
        "build_s": build_s,
        "strong_verify_s": verify_s,
        "verified_create_s": build_s + verify_s,
        "build_stats": build_stats,
    }


def _one(label: str, source: Path, work: Path) -> dict:
    with tempfile.TemporaryDirectory(prefix="cmpct-v030-v025-levels-", dir=work) as td:
        root = Path(td)
        stage = EXT._normalized_stage(source, root / "stage-root")
        expected_tree = EXT._tree(stage)
        names = [f"l{level}" for level in LEVELS] + ["zip", "zstd19"]
        samples = {name: [] for name in names}
        sizes = {name: set() for name in names}
        parts = {f"l{level}": [] for level in LEVELS}
        base_order = list(names)

        for round_index in range(ROUNDS):
            # Deterministic rotation prevents a fixed first/last engine from owning warm-cache effects.
            shift = (round_index * 3) % len(base_order)
            order = base_order[shift:] + base_order[:shift]
            round_root = root / f"round-{round_index}"
            round_root.mkdir()
            for engine in order:
                engine_root = round_root / engine
                engine_root.mkdir()
                if engine.startswith("l"):
                    level = int(engine[1:])
                    result = _cmpnx5(stage, engine_root, level)
                    samples[engine].append(float(result["verified_create_s"]))
                    sizes[engine].add(int(result["archive_bytes"]))
                    parts[engine].append({
                        "build_s": float(result["build_s"]),
                        "strong_verify_s": float(result["strong_verify_s"]),
                    })
                elif engine == "zip":
                    result = EXT._zip(stage, engine_root / "archive.zip", engine_root / "out")
                    EXT._verify_extracted(engine_root / "out", expected_tree, "zip_deflate9")
                    samples[engine].append(float(result["create_s"]))
                    sizes[engine].add(int(result["archive_bytes"]))
                else:
                    result = EXT._tar_zstd(stage, engine_root / "archive.tar.zst", engine_root / "out", engine_root)
                    if not result.get("available"):
                        raise RuntimeError(f"solid Zstd-19 unavailable: {result!r}")
                    EXT._verify_extracted(engine_root / "out", expected_tree, "tar_zstd19_solid")
                    samples[engine].append(float(result["create_s"]))
                    sizes[engine].add(int(result["archive_bytes"]))

        if any(len(values) != 1 for values in sizes.values()):
            raise RuntimeError(f"nondeterministic archive size in {label}: {sizes!r}")
        medians = {name: statistics.median(values) for name, values in samples.items()}
        byte_values = {name: next(iter(values)) for name, values in sizes.items()}
        levels = []
        for level in LEVELS:
            name = f"l{level}"
            strict = {
                "smaller_than_zip": byte_values[name] < byte_values["zip"],
                "smaller_than_zstd19": byte_values[name] < byte_values["zstd19"],
                "verified_create_faster_than_zip": medians[name] < medians["zip"],
                "verified_create_faster_than_zstd19": medians[name] < medians["zstd19"],
            }
            strict["four_way"] = all(strict.values())
            levels.append({
                "level_cap": level,
                "archive_bytes": byte_values[name],
                "median_verified_create_s": medians[name],
                "raw_verified_create_s": samples[name],
                "build_verify_parts": parts[name],
                "strict": strict,
            })
        four_way = [row for row in levels if row["strict"]["four_way"]]
        return {
            "label": label,
            "tree_sha256": expected_tree,
            "comparators": {
                "zip": {"archive_bytes": byte_values["zip"], "median_create_s": medians["zip"], "raw_create_s": samples["zip"]},
                "zstd19": {"archive_bytes": byte_values["zstd19"], "median_create_s": medians["zstd19"], "raw_create_s": samples["zstd19"]},
            },
            "levels": levels,
            "best_four_way_level": min((row["level_cap"] for row in four_way), default=None),
            "fastest_size_valid_level": min(
                (row for row in levels if row["strict"]["smaller_than_zip"] and row["strict"]["smaller_than_zstd19"]),
                key=lambda row: row["median_verified_create_s"],
                default=None,
            ),
        }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    neutral = GENERAL.V029._load(GENERAL.V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py", "cmpct_v030_v025_levels_neutral")
    repair = GENERAL.V029._load(GENERAL.V029.REPAIR_PATH, "cmpct_v030_v025_levels_repair")
    repair.install_generation_hooks(neutral)
    corpus = work_root / "neutral"
    neutral.build(corpus)
    repair.normalize_root(corpus)

    rows = []
    for name in TARGETS:
        source = corpus / name
        if not source.is_dir():
            raise RuntimeError(f"missing frozen workload {name}")
        row = _one(f"neutral_hostile_v1/{name}", source, work_root)
        rows.append(row)
        print(json.dumps({
            "label": row["label"],
            "best_four_way_level": row["best_four_way_level"],
            "fastest_size_valid_level": row["fastest_size_valid_level"],
        }, separators=(",", ":")), flush=True)

    gate = {
        "exact_target_count": len(rows) == len(TARGETS),
        "all_level_rounds_complete": all(
            all(len(level["raw_verified_create_s"]) == ROUNDS for level in row["levels"])
            for row in rows
        ),
        "all_comparator_rounds_complete": all(
            len(row["comparators"][name]["raw_create_s"]) == ROUNDS
            for row in rows for name in ("zip", "zstd19")
        ),
        "all_level_sizes_deterministic": True,
        "all_tree_roundtrips_verified": all(bool(row["tree_sha256"]) for row in rows),
    }
    gate["passed"] = all(gate.values())
    return {
        "schema": "cmpct-v030-v025-level-frontier-v1",
        "targets": list(TARGETS),
        "levels": list(LEVELS),
        "rounds": ROUNDS,
        "rows": rows,
        "summary": {
            "four_way_rows": [row["label"] for row in rows if row["best_four_way_level"] is not None],
            "four_way_count": sum(row["best_four_way_level"] is not None for row in rows),
        },
        "measurement_gate": gate,
        "claim_boundary": (
            "research mechanism frontier only; changing CMPNX5's compression effort does not make CMPNX5 canonical. "
            "Any useful speed/ratio point must be re-expressed in bounded canonical r25 and pass all release gates."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-v025-level-frontier-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-v025-level-frontier.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"summary": result["summary"], "measurement_gate": result["measurement_gate"]}, indent=2))
    if not result["measurement_gate"]["passed"]:
        raise SystemExit("v0.25 level-frontier measurement invalid")


if __name__ == "__main__":
    main()
