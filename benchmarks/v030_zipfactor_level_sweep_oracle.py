from __future__ import annotations

"""Repeated exact-product timing sweep for ZIP-factor binary-control compression levels.

The current compact-v3 profile already clears ZIP and solid-Zstd-19 on size but misses ZIP creation wall-clock.
This oracle changes only the Zstd level used for the already-bounded canonical candidate. Every measured candidate
pays fused source scanning, archive publication and cold strong identity verification; all candidates retain the
same format grammar, exact semantic tree, <=8x member-read amplification and <=8 MiB decode-unit requirements.

This is research evidence only. A winning level does not authorize selector/native/Android/recovery promotion.
"""

import argparse
import json
from pathlib import Path
import shutil
import statistics
import tempfile
import time

from benchmarks import resemblance_hostile_corpus_v1 as CORPUS
from benchmarks import v030_external_competitors as EXT
from experiments import entropygraph_v030_canonical_final_impl as CANON
from experiments import entropygraph_v030_zipfactor_compact_v3 as V3

LEVELS = (1, 2, 3, 4, 5, 6, 7, 9)
ROUNDS = 9


def _semantic(scan: dict) -> str:
    return CANON._semantic_tree_sha(scan["manifest"])


def _candidate(stage: Path, archive: Path, *, level: int) -> dict:
    started = time.perf_counter()
    build = V3.build(stage, archive, level=level, group_size=7)
    build_s = time.perf_counter() - started
    started = time.perf_counter()
    scan = V3.verify_and_identities(archive)
    verify_s = time.perf_counter() - started
    return {
        **build,
        "archive_bytes": archive.stat().st_size,
        "build_s": build_s,
        "verify_s": verify_s,
        "create_s": build_s + verify_s,
        "semantic_tree_sha256": _semantic(scan),
        "verified_user_files": scan["verified_user_files"],
        "verified_max_member_read_amplification": scan["max_member_read_amplification"],
        "verified_max_decode_unit_bytes": scan["max_decode_unit_bytes"],
        "strong_verify_green": scan["ok"] is True,
        "identity_count": len(scan["identities"]),
    }


def _median(values: list[float]) -> float:
    return float(statistics.median(values))


def run(work_root: Path, *, rounds: int = ROUNDS) -> dict:
    if rounds < 5 or rounds % 2 == 0:
        raise ValueError("rounds must be an odd integer >=5")
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    corpus = work_root / "corpus"
    CORPUS.build(corpus)
    source = corpus / "04_deflate_family"

    with tempfile.TemporaryDirectory(prefix="cmpct-zf-level-sweep-", dir=work_root) as td_raw:
        td = Path(td_raw)
        stage = EXT._normalized_stage(source, td)
        truth = CANON._prepare_profile_tree(stage, td / "truth")
        source_semantic = CANON._semantic_tree_sha(CANON._decode_manifest(truth["manifest_raw"]))

        zip_times: list[float] = []
        zstd_times: list[float] = []
        level_rows: dict[int, list[dict]] = {level: [] for level in LEVELS}
        zip_bytes = None
        zstd_bytes = None

        # Rotate order each round so millisecond-scale comparisons cannot borrow a fixed warm-cache/order bias.
        operations = ["zip", "zstd", *[f"l{level}" for level in LEVELS]]
        for round_index in range(rounds):
            order = operations[round_index % len(operations):] + operations[:round_index % len(operations)]
            round_dir = td / f"round-{round_index:02d}"
            round_dir.mkdir()
            for op in order:
                if op == "zip":
                    result = EXT._zip(stage, round_dir / "base.zip", round_dir / "zip-out")
                    zip_times.append(float(result["create_s"]))
                    zip_bytes = int(result["archive_bytes"])
                elif op == "zstd":
                    result = EXT._tar_zstd(
                        stage,
                        round_dir / "base.tar.zst",
                        round_dir / "zstd-out",
                        round_dir,
                    )
                    if not result.get("available"):
                        raise RuntimeError("zstd comparator unavailable")
                    zstd_times.append(float(result["create_s"]))
                    zstd_bytes = int(result["archive_bytes"])
                else:
                    level = int(op[1:])
                    row = _candidate(stage, round_dir / f"candidate-l{level}.cmpct", level=level)
                    row["semantic_tree_exact"] = row["semantic_tree_sha256"] == source_semantic
                    row["locality_green"] = (
                        float(row["verified_max_member_read_amplification"]) <= 8.0
                        and int(row["verified_max_decode_unit_bytes"]) <= 8 * 1024 * 1024
                    )
                    if not row["strong_verify_green"] or not row["semantic_tree_exact"] or not row["locality_green"]:
                        raise RuntimeError(f"ZIP-factor level {level} failed exactness/locality")
                    level_rows[level].append(row)

        if zip_bytes is None or zstd_bytes is None:
            raise RuntimeError("competitor measurements missing")

        levels = []
        for level in LEVELS:
            rows = level_rows[level]
            sizes = {int(row["archive_bytes"]) for row in rows}
            identities = {row["semantic_tree_sha256"] for row in rows}
            if len(sizes) != 1 or identities != {source_semantic}:
                raise RuntimeError(f"ZIP-factor level {level} was not deterministic")
            create_times = [float(row["create_s"]) for row in rows]
            build_times = [float(row["build_s"]) for row in rows]
            verify_times = [float(row["verify_s"]) for row in rows]
            archive_bytes = sizes.pop()
            levels.append({
                "level": level,
                "archive_bytes": archive_bytes,
                "median_create_s": _median(create_times),
                "min_create_s": min(create_times),
                "max_create_s": max(create_times),
                "median_build_s": _median(build_times),
                "median_verify_s": _median(verify_times),
                "beats_zip_size": archive_bytes < zip_bytes,
                "beats_zstd19_size": archive_bytes < zstd_bytes,
                "beats_zip_create_median": _median(create_times) < _median(zip_times),
                "beats_zstd19_create_median": _median(create_times) < _median(zstd_times),
                "all_rounds_exact": all(
                    row["strong_verify_green"] and row["semantic_tree_exact"] and row["locality_green"]
                    for row in rows
                ),
            })

        viable = [
            row for row in levels
            if row["all_rounds_exact"]
            and row["beats_zip_size"]
            and row["beats_zstd19_size"]
            and row["beats_zip_create_median"]
            and row["beats_zstd19_create_median"]
        ]
        best = min(viable, key=lambda row: (row["median_create_s"], row["archive_bytes"])) if viable else None
        return {
            "schema": "cmpct-v030-zipfactor-level-sweep-v1",
            "claim_boundary": (
                "research level selection only; no selector/native/Android/recovery promotion authority"
            ),
            "workload": "resemblance_hostile_v1/04_deflate_family",
            "rounds": rounds,
            "source_semantic_tree_sha256": source_semantic,
            "comparators": {
                "zip_deflate9": {
                    "archive_bytes": zip_bytes,
                    "median_create_s": _median(zip_times),
                    "min_create_s": min(zip_times),
                    "max_create_s": max(zip_times),
                },
                "tar_zstd19_solid": {
                    "archive_bytes": zstd_bytes,
                    "median_create_s": _median(zstd_times),
                    "min_create_s": min(zstd_times),
                    "max_create_s": max(zstd_times),
                },
            },
            "levels": levels,
            "best_four_way": best,
            "gate": {
                "all_levels_exact": all(row["all_rounds_exact"] for row in levels),
                "four_way_level_found": best is not None,
                "passed": all(row["all_rounds_exact"] for row in levels) and best is not None,
            },
        }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-zf-level-sweep-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-zf-level-sweep.json"))
    parser.add_argument("--rounds", type=int, default=ROUNDS)
    args = parser.parse_args()
    result = run(args.work_root, rounds=args.rounds)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "comparators": result["comparators"],
        "levels": result["levels"],
        "best_four_way": result["best_four_way"],
        "gate": result["gate"],
    }, indent=2), flush=True)
    if not result["gate"]["passed"]:
        raise SystemExit("ZIP-factor level sweep found no exact four-way level")


if __name__ == "__main__":
    main()
