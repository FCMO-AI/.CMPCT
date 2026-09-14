from __future__ import annotations

"""Research-only decomposition of the dominant v0.30 G04 extraction regression.

The frozen runtime gate and the phase-attribution oracle identify neutral_hostile_v1/09_ml_artifacts as the
strongest extraction failure: the v0.30 extract call is ~2.78x the accepted v0.29 path while the post-extraction
treehash is slightly faster. This experiment keeps one exact shipping v0.30 archive fixed and measures three
fresh-process operations over it:

1. strong_verify: authenticated graph decode + integrity/tree work, no output writes;
2. verified_staging: the exact release streamer into an unpublished staging tree, adding physical output writes;
3. full_extract: the public shipping extraction path, adding manifest restoration and transactional publication.

This receives zero release credit. It changes no bytes, reader policy, threshold or product code; it only locates
the owner of measured wall time so the next optimization attacks the right layer.
"""

import argparse
import json
import os
from pathlib import Path
import shutil
import statistics
import subprocess
import sys
import time
import traceback

from benchmarks import v030_release_performance as PERF

ENGINE = "v030-g04-extract-cost-attribution-v2"
SUITE = "neutral_hostile_v1"
TARGET = "09_ml_artifacts"
REPETITIONS = 3


def _json_child(cmd: list[str]) -> dict:
    env = dict(os.environ)
    env["PYTHONHASHSEED"] = "0"
    proc = subprocess.run(cmd, text=True, capture_output=True, env=env, check=False)
    if proc.returncode != 0:
        raise RuntimeError(
            f"child failed returncode={proc.returncode} cmd={cmd!r}\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    if not lines:
        raise RuntimeError(f"child emitted no JSON: {cmd!r}")
    return json.loads(lines[-1])


def _worker(archive: Path, destination: Path, operation: str) -> int:
    from experiments import entropygraph_v030_release_product as CANON

    started = time.perf_counter()
    if operation == "strong_verify":
        result = dict(CANON.strong_verify(archive))
        if not result.get("ok"):
            raise RuntimeError(f"strong verification failed: {result!r}")
        logical_bytes = int(result.get("logical_bytes", 0))
        tree_sha = result.get("tree_sha256")
    elif operation == "verified_staging":
        if destination.exists():
            shutil.rmtree(destination)
        destination.mkdir(parents=True, exist_ok=True)
        result = dict(CANON.POLICY.extract_verified_into_staging(archive, destination))
        if not result.get("ok"):
            raise RuntimeError(f"verified staging failed: {result!r}")
        logical_bytes = int(result.get("logical_bytes", 0))
        tree_sha = result.get("tree_sha256")
    elif operation == "full_extract":
        if destination.exists():
            shutil.rmtree(destination)
        CANON.extract(archive, destination)
        logical_bytes = sum(
            p.stat().st_size for p in destination.rglob("*") if p.is_file() and not p.is_symlink()
        )
        tree_sha = CANON.treehash(destination)
    else:
        raise ValueError(operation)
    wall = time.perf_counter() - started
    print(
        json.dumps(
            {
                "operation": operation,
                "wall_s": wall,
                "logical_bytes": logical_bytes,
                "tree_sha256": tree_sha,
            },
            separators=(",", ":"),
        ),
        flush=True,
    )
    return 0


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    accepted = PERF.GENERAL._accepted_v029_rows()
    roots = PERF._build_corpora(work_root / "corpora")
    source = roots[(SUITE, TARGET)]

    archive = work_root / "archive" / "v030.cmpct"
    archive.parent.mkdir(parents=True, exist_ok=True)
    pack = _json_child(
        [
            sys.executable,
            str(PERF.WORKER),
            "--engine",
            "v030",
            "--op",
            "pack",
            "--source",
            str(source),
            "--archive",
            str(archive),
        ]
    )
    if pack.get("build_stats", {}).get("selected") != "g04-overlay":
        raise RuntimeError(f"target no longer selects G04: {pack.get('build_stats', {}).get('selected')!r}")

    # Retain accepted-v0.29 provenance for the exact source identity without treating this oracle as a baseline run.
    expected = accepted[(SUITE, TARGET)]
    historical_tree = PERF.GENERAL._historical_treehash(source)
    if historical_tree != expected["tree_sha256"]:
        raise RuntimeError(f"historical source drift: {historical_tree} != {expected['tree_sha256']}")

    operations = ("strong_verify", "verified_staging", "full_extract")
    samples = {op: [] for op in operations}
    for rep in range(REPETITIONS):
        order = operations if rep % 2 == 0 else tuple(reversed(operations))
        for op in order:
            sample = _json_child(
                [
                    sys.executable,
                    str(Path(__file__).resolve()),
                    "--worker",
                    "--archive",
                    str(archive),
                    "--destination",
                    str(work_root / "out" / f"{op}-{rep}"),
                    "--operation",
                    op,
                ]
            )
            sample["rep"] = rep
            samples[op].append(sample)

    # Timing comparisons are admissible only if every measured path reconstructs/verifies the same logical object.
    # This prevents a faster operation from receiving causal credit for silently doing semantically different work.
    expected_logical_bytes = int(samples["strong_verify"][0]["logical_bytes"])
    for op, values in samples.items():
        for sample in values:
            if int(sample["logical_bytes"]) != expected_logical_bytes:
                raise RuntimeError(
                    f"semantic logical-byte drift in {op}: {sample['logical_bytes']} != {expected_logical_bytes}"
                )
            if sample.get("tree_sha256") != historical_tree:
                raise RuntimeError(
                    f"semantic tree drift in {op}: {sample.get('tree_sha256')} != {historical_tree}"
                )

    summaries = {
        op: {
            "median_wall_s": statistics.median(v["wall_s"] for v in values),
            "min_wall_s": min(v["wall_s"] for v in values),
            "max_wall_s": max(v["wall_s"] for v in values),
        }
        for op, values in samples.items()
    }
    verify = summaries["strong_verify"]["median_wall_s"]
    staging = summaries["verified_staging"]["median_wall_s"]
    full = summaries["full_extract"]["median_wall_s"]
    comparison = {
        "verified_staging_minus_verify_s": staging - verify,
        "full_extract_minus_verified_staging_s": full - staging,
        "verify_fraction_of_full_extract": verify / max(full, 1e-9),
        "verified_staging_fraction_of_full_extract": staging / max(full, 1e-9),
        "full_over_verify_ratio": full / max(verify, 1e-9),
        "full_over_verified_staging_ratio": full / max(staging, 1e-9),
    }
    return {
        "engine": ENGINE,
        "status": "PASS",
        "evidence_class": "research-oracle",
        "product_release_credit": False,
        "claim": "decompose G04 extraction wall time into decode/integrity, physical staging writes, and restoration/publication",
        "contract": {
            "suite": SUITE,
            "workload": TARGET,
            "historical_tree_sha256": historical_tree,
            "accepted_v029_bytes": int(expected["accepted_v029_bytes"]),
            "v030_archive_bytes": int(pack["archive_bytes"]),
            "v030_selected": pack["build_stats"]["selected"],
            "repetitions_per_operation": REPETITIONS,
            "fresh_process_per_sample": True,
            "same_archive_all_operations": True,
            "semantic_identity_checked": True,
            "product_code_changed": False,
            "release_thresholds_changed": False
        },
        "summaries": summaries,
        "comparison": comparison,
        "samples": samples,
    }


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--destination", type=Path)
    parser.add_argument("--operation", choices=("strong_verify", "verified_staging", "full_extract"))
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/g04-extract-cost-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/g04-extract-cost.json"))
    args = parser.parse_args()

    if args.worker:
        if args.archive is None or args.destination is None or args.operation is None:
            parser.error("--worker requires --archive, --destination and --operation")
        raise SystemExit(_worker(args.archive, args.destination, args.operation))

    try:
        result = run(args.work_root)
    except BaseException as exc:
        _write(
            args.output,
            {
                "engine": ENGINE,
                "status": "HARNESS_FAILURE",
                "evidence_class": "research-oracle",
                "product_release_credit": False,
                "error": {
                    "type": type(exc).__name__,
                    "message": str(exc),
                    "traceback": traceback.format_exc(limit=32),
                },
            },
        )
        raise

    _write(args.output, result)
    print(json.dumps(result["comparison"], indent=2), flush=True)


if __name__ == "__main__":
    main()
