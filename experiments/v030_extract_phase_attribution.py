from __future__ import annotations

"""Research-only attribution of the v0.30 runtime extraction regressions.

The frozen runtime worker intentionally times both archive extraction and the subsequent engine-owned treehash of
the restored destination. That total is a valid end-to-end gate, but a red ratio does not by itself identify
whether the cost belongs to decoding/restoration or to post-extraction identity measurement. This oracle preserves
the same engine front doors, archives and tree identities while timing those two phases separately in fresh child
processes.

It targets only the two frozen runtime workloads whose extraction ratios exceed 1.25. It changes no product code,
threshold, comparator, archive grammar, selector or release evidence and receives zero product-release credit.
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

ENGINE = "v030-extract-phase-attribution-v1"
TARGETS = (
    ("neutral_hostile_v1", "05_logs_and_telemetry"),
    ("neutral_hostile_v1", "09_ml_artifacts"),
)
REPETITIONS = 3


def _engine(name: str):
    if name == "v029":
        from experiments import entropygraph_v029_release as engine
    elif name == "v030":
        from experiments import entropygraph_v030_release_product as engine
    else:
        raise ValueError(name)
    return engine


def _phase_worker(engine_name: str, archive: Path, destination: Path) -> int:
    engine = _engine(engine_name)
    if destination.exists():
        shutil.rmtree(destination)

    started = time.perf_counter()
    extract_started = started
    engine.extract(archive, destination)
    extracted_at = time.perf_counter()
    tree_sha = engine.treehash(destination)
    finished = time.perf_counter()

    print(
        json.dumps(
            {
                "engine": engine_name,
                "tree_sha256": tree_sha,
                "extract_call_wall_s": extracted_at - extract_started,
                "post_treehash_wall_s": finished - extracted_at,
                "combined_wall_s": finished - started,
            },
            separators=(",", ":"),
        ),
        flush=True,
    )
    return 0


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


def _pack(engine: str, source: Path, archive: Path) -> dict:
    archive.parent.mkdir(parents=True, exist_ok=True)
    return _json_child(
        [
            sys.executable,
            str(PERF.WORKER),
            "--engine",
            engine,
            "--op",
            "pack",
            "--source",
            str(source),
            "--archive",
            str(archive),
        ]
    )


def _sample(engine: str, archive: Path, destination: Path) -> dict:
    return _json_child(
        [
            sys.executable,
            str(Path(__file__).resolve()),
            "--worker",
            "--engine",
            engine,
            "--archive",
            str(archive),
            "--destination",
            str(destination),
        ]
    )


def _ratio(new: float, old: float) -> float:
    return float(new) / max(float(old), 1e-9)


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    accepted = PERF.GENERAL._accepted_v029_rows()
    roots = PERF._build_corpora(work_root / "corpora")
    rows = []

    for suite, name in TARGETS:
        source = roots[(suite, name)]
        packs = {}
        archives = {}
        for engine_name in ("v029", "v030"):
            archive = work_root / "archives" / f"{suite}-{name}-{engine_name}.cmpct"
            packed = _pack(engine_name, source, archive)
            archives[engine_name] = archive
            packs[engine_name] = packed

        expected_v029 = accepted[(suite, name)]
        if int(packs["v029"]["archive_bytes"]) != int(expected_v029["accepted_v029_bytes"]):
            raise RuntimeError(
                f"v0.29 baseline drift for {suite}/{name}: "
                f"{packs['v029']['archive_bytes']} != {expected_v029['accepted_v029_bytes']}"
            )

        samples = {"v029": [], "v030": []}
        for rep in range(REPETITIONS):
            order = ("v029", "v030") if rep % 2 == 0 else ("v030", "v029")
            for engine_name in order:
                sample = _sample(
                    engine_name,
                    archives[engine_name],
                    work_root / "extract" / f"{suite}-{name}-{engine_name}-r{rep}",
                )
                if sample["tree_sha256"] != packs[engine_name]["tree_sha256"]:
                    raise RuntimeError(
                        f"extracted identity mismatch for {suite}/{name}/{engine_name}: "
                        f"{sample['tree_sha256']} != {packs[engine_name]['tree_sha256']}"
                    )
                sample["rep"] = rep
                samples[engine_name].append(sample)

        summary = {}
        for engine_name, values in samples.items():
            summary[engine_name] = {
                "median_extract_call_wall_s": statistics.median(v["extract_call_wall_s"] for v in values),
                "median_post_treehash_wall_s": statistics.median(v["post_treehash_wall_s"] for v in values),
                "median_combined_wall_s": statistics.median(v["combined_wall_s"] for v in values),
                "archive_bytes": int(packs[engine_name]["archive_bytes"]),
                "tree_sha256": packs[engine_name]["tree_sha256"],
            }
        old = summary["v029"]
        new = summary["v030"]
        comparison = {
            "extract_call_ratio_v030_over_v029": _ratio(
                new["median_extract_call_wall_s"], old["median_extract_call_wall_s"]
            ),
            "post_treehash_ratio_v030_over_v029": _ratio(
                new["median_post_treehash_wall_s"], old["median_post_treehash_wall_s"]
            ),
            "combined_ratio_v030_over_v029": _ratio(new["median_combined_wall_s"], old["median_combined_wall_s"]),
            "v030_treehash_fraction_of_combined": new["median_post_treehash_wall_s"]
            / max(new["median_combined_wall_s"], 1e-9),
            "v029_treehash_fraction_of_combined": old["median_post_treehash_wall_s"]
            / max(old["median_combined_wall_s"], 1e-9),
        }
        rows.append(
            {
                "suite": suite,
                "name": name,
                "packs": packs,
                "summary": summary,
                "comparison": comparison,
                "samples": samples,
            }
        )

    return {
        "engine": ENGINE,
        "status": "PASS",
        "evidence_class": "research-oracle",
        "product_release_credit": False,
        "claim": "attribute frozen runtime extraction debt between extract call and post-extraction treehash",
        "contract": {
            "targets": [list(row) for row in TARGETS],
            "repetitions_per_engine": REPETITIONS,
            "fresh_process_per_extract_sample": True,
            "same_product_front_doors_as_runtime_gate": True,
            "same_treehash_inside_combined_boundary": True,
            "product_code_changed": False,
            "release_thresholds_changed": False,
        },
        "rows": rows,
    }


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--engine", choices=("v029", "v030"))
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--destination", type=Path)
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/extract-phase-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/extract-phase-attribution.json"))
    args = parser.parse_args()

    if args.worker:
        if args.engine is None or args.archive is None or args.destination is None:
            parser.error("--worker requires --engine, --archive, and --destination")
        raise SystemExit(_phase_worker(args.engine, args.archive, args.destination))

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
                "claim": "attribute frozen runtime extraction debt between extract call and post-extraction treehash",
                "error": {
                    "type": type(exc).__name__,
                    "message": str(exc),
                    "traceback": traceback.format_exc(limit=32),
                },
            },
        )
        raise

    _write(args.output, result)
    print(json.dumps({row["name"]: row["comparison"] for row in result["rows"]}, indent=2), flush=True)


if __name__ == "__main__":
    main()
