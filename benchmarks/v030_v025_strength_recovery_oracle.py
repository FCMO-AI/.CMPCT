from __future__ import annotations

"""Same-runner recovery probe for the two largest canonicalization gaps inherited from EntropyGraph v0.25.

The current v0.30 product is ~9.5 MiB above accepted v0.29 on office and ~4.3 MiB above it on analytics, even
though the historical CMPNX5 engine already stored those workloads near 5.95 MiB and 6.12 MiB respectively.  This
oracle does not propose shipping CMPNX5. It asks the more useful engineering question: on today's exact frozen
sources and runner, does that historical representation still beat ZIP and solid Zstd-19 after charging the
release-like boundary of *build plus mandatory strong verification*?

Every round rebuilds all three formats from the same normalized source, strongly verifies CMPNX5, extracts all
formats and checks the exact frozen regular-file tree. Three rounds are measured and medians are reported. A row
is called four-way only when the verified historical representation is strictly smaller and strictly faster than
both external comparators. Negative results are successful evidence too; this lane never authorizes promotion.
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
ROUNDS = 3


def _cmpnx5(stage: Path, root: Path) -> dict:
    archive = root / "candidate.cmpnx5"
    V25.ROOT = stage
    V25.OUT = archive
    started = time.perf_counter()
    build_stats = dict(V25.build())
    build_s = time.perf_counter() - started
    started = time.perf_counter()
    verified = dict(V25.strong_verify())
    verify_s = time.perf_counter() - started
    if not verified.get("ok"):
        raise RuntimeError(f"CMPNX5 strong verification failed: {verified!r}")
    extracted = root / "cmpnx5-out"
    V25.extract(extracted)
    EXT._verify_extracted(extracted, EXT._tree(stage), "cmpnx5")
    return {
        "archive_bytes": archive.stat().st_size,
        "build_s": build_s,
        "strong_verify_s": verify_s,
        "verified_create_s": build_s + verify_s,
        "build_stats": build_stats,
        "strong_verify": verified,
    }


def _one(label: str, source: Path, work: Path) -> dict:
    with tempfile.TemporaryDirectory(prefix="cmpct-v030-v025-strength-", dir=work) as td:
        root = Path(td)
        stage = EXT._normalized_stage(source, root / "stage-root")
        expected_tree = EXT._tree(stage)
        samples = {"cmpnx5": [], "zip": [], "zstd19": []}
        sizes = {"cmpnx5": set(), "zip": set(), "zstd19": set()}
        build_parts = []

        # Rotate the first measured engine so fixed order/cache effects cannot manufacture a millisecond win.
        orders = (
            ("cmpnx5", "zip", "zstd19"),
            ("zip", "zstd19", "cmpnx5"),
            ("zstd19", "cmpnx5", "zip"),
        )
        for round_index, order in enumerate(orders):
            round_root = root / f"round-{round_index}"
            round_root.mkdir()
            for engine in order:
                engine_root = round_root / engine
                engine_root.mkdir()
                if engine == "cmpnx5":
                    result = _cmpnx5(stage, engine_root)
                    samples[engine].append(float(result["verified_create_s"]))
                    sizes[engine].add(int(result["archive_bytes"]))
                    build_parts.append({
                        "build_s": float(result["build_s"]),
                        "strong_verify_s": float(result["strong_verify_s"]),
                    })
                elif engine == "zip":
                    result = EXT._zip(stage, engine_root / "archive.zip", engine_root / "out")
                    EXT._verify_extracted(engine_root / "out", expected_tree, "zip_deflate9")
                    samples[engine].append(float(result["create_s"]))
                    sizes[engine].add(int(result["archive_bytes"]))
                else:
                    result = EXT._tar_zstd(
                        stage,
                        engine_root / "archive.tar.zst",
                        engine_root / "out",
                        engine_root,
                    )
                    if not result.get("available"):
                        raise RuntimeError(f"solid Zstd-19 unavailable: {result!r}")
                    EXT._verify_extracted(engine_root / "out", expected_tree, "tar_zstd19_solid")
                    samples[engine].append(float(result["create_s"]))
                    sizes[engine].add(int(result["archive_bytes"]))

        if any(len(values) != 1 for values in sizes.values()):
            raise RuntimeError(f"nondeterministic archive size in {label}: {sizes!r}")
        medians = {name: statistics.median(values) for name, values in samples.items()}
        bytes_by_engine = {name: next(iter(values)) for name, values in sizes.items()}
        strict = {
            "smaller_than_zip": bytes_by_engine["cmpnx5"] < bytes_by_engine["zip"],
            "smaller_than_zstd19": bytes_by_engine["cmpnx5"] < bytes_by_engine["zstd19"],
            "verified_create_faster_than_zip": medians["cmpnx5"] < medians["zip"],
            "verified_create_faster_than_zstd19": medians["cmpnx5"] < medians["zstd19"],
        }
        strict["four_way"] = all(strict.values())
        return {
            "label": label,
            "tree_sha256": expected_tree,
            "archive_bytes": bytes_by_engine,
            "median_create_s": medians,
            "raw_create_s": samples,
            "cmpnx5_build_verify_parts": build_parts,
            "strict": strict,
        }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    neutral = GENERAL.V029._load(
        GENERAL.V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py",
        "cmpct_v030_v025_strength_neutral",
    )
    repair = GENERAL.V029._load(GENERAL.V029.REPAIR_PATH, "cmpct_v030_v025_strength_repair")
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
            "bytes": row["archive_bytes"],
            "median_create_s": row["median_create_s"],
            "strict": row["strict"],
        }, separators=(",", ":")), flush=True)

    measurement_gate = {
        "exact_target_count": len(rows) == len(TARGETS),
        "all_rounds_complete": all(all(len(v) == ROUNDS for v in row["raw_create_s"].values()) for row in rows),
        "all_sizes_deterministic": True,
        "all_tree_roundtrips_verified": all(bool(row["tree_sha256"]) for row in rows),
    }
    measurement_gate["passed"] = all(measurement_gate.values())
    return {
        "schema": "cmpct-v030-v025-strength-recovery-v1",
        "targets": list(TARGETS),
        "rounds": ROUNDS,
        "rows": rows,
        "summary": {
            "four_way_rows": [row["label"] for row in rows if row["strict"]["four_way"]],
            "size_wins_vs_zip": sum(row["strict"]["smaller_than_zip"] for row in rows),
            "size_wins_vs_zstd19": sum(row["strict"]["smaller_than_zstd19"] for row in rows),
            "verified_create_wins_vs_zip": sum(row["strict"]["verified_create_faster_than_zip"] for row in rows),
            "verified_create_wins_vs_zstd19": sum(row["strict"]["verified_create_faster_than_zstd19"] for row in rows),
        },
        "measurement_gate": measurement_gate,
        "claim_boundary": (
            "research recovery evidence only; CMPNX5 is non-canonical and cannot be selected by v0.30. Any useful "
            "mechanism must be re-expressed in bounded canonical r25 with native/Android/recovery/locality parity."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-v025-strength-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-v025-strength.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"summary": result["summary"], "measurement_gate": result["measurement_gate"]}, indent=2))
    if not result["measurement_gate"]["passed"]:
        raise SystemExit("v0.25 strength-recovery measurement invalid")


if __name__ == "__main__":
    main()
