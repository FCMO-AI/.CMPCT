from __future__ import annotations

"""Fresh-process runtime promotion gate for CMPCT v0.30 versus current accepted v0.29.

Three preregistered public workloads cover the mechanisms expected to matter:
- resemblance-hostile shifted versions (cross-file/version structure);
- neutral logs/telemetry (hierarchical Geometry);
- neutral ML artifacts (large structured/tokenizer Geometry).

Two balanced repetitions run v0.29-first then v0.30-first.  Pack, strong verify and full extract are each
fresh processes.  Every produced tree must match the exact repaired source identity and every v0.29 archive
must reproduce its durable accepted byte floor.

Promotion thresholds are frozen before independent timing evidence:
- median workload create ratio v0.30/v0.29 <= 1.10;
- no workload create ratio > 1.25;
- median workload extract ratio <= 1.10;
- no workload extract ratio > 1.25;
- no measured v0.30 pack/extract peak-RSS ratio > 1.25;
- zero v0.30 archive-size regressions.

A miss is optimization debt, not permission to relax the gate.  The separate shared-portfolio benchmark must
also prove >=20% / >=5 s rehabilitation versus the older duplicated v0.30 implementation.

Footnote: hosted-runner timings are suitable for a same-run paired release gate, not for publishing absolute
throughput claims.  Public MB/s claims still belong on controlled benchmark hardware with raw repetitions.
"""

import argparse
import json
import os
from pathlib import Path
import shutil
import statistics
import subprocess
import sys

from benchmarks import v030_release_generalization as GENERAL

ROOT = Path(__file__).resolve().parents[1]
WORKER = ROOT / "benchmarks" / "v030_perf_worker.py"
REPETITION_ORDER = (("v029", "v030"), ("v030", "v029"))
MAX_MEDIAN_RATIO = 1.10
MAX_WORKLOAD_RATIO = 1.25
MAX_PEAK_RSS_RATIO = 1.25

TARGETS = (
    ("resemblance_hostile_v1", "01_shifted_versions"),
    ("neutral_hostile_v1", "05_logs_and_telemetry"),
    ("neutral_hostile_v1", "09_ml_artifacts"),
)


def _run_worker(*args: str) -> dict:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    completed = subprocess.run(
        [sys.executable, str(WORKER), *args],
        cwd=ROOT,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    if not lines:
        raise RuntimeError(f"performance worker produced no JSON: stderr={completed.stderr!r}")
    try:
        return json.loads(lines[-1])
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"performance worker final line was not JSON: {lines[-1]!r}; stderr={completed.stderr!r}"
        ) from exc


def _build_corpora(work_root: Path) -> dict[tuple[str, str], Path]:
    accepted = GENERAL._accepted_v029_rows()
    neutral = GENERAL.V029._load(
        GENERAL.V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py",
        "cmpct_v030_perf_neutral",
    )
    hostile = GENERAL.V029._load(
        GENERAL.V029.ROOT / "benchmarks" / "resemblance_hostile_corpus_v1.py",
        "cmpct_v030_perf_hostile",
    )
    repair = GENERAL.V029._load(GENERAL.V029.REPAIR_PATH, "cmpct_v030_perf_repair")
    repair.install_generation_hooks(neutral)

    neutral_root = work_root / "neutral"
    hostile_root = work_root / "resemblance"
    neutral.build(neutral_root)
    repair.normalize_root(neutral_root)
    hostile.build(hostile_root)

    roots = {
        ("neutral_hostile_v1", name): neutral_root / name
        for suite, name in TARGETS
        if suite == "neutral_hostile_v1"
    }
    roots.update(
        {
            ("resemblance_hostile_v1", name): hostile_root / name
            for suite, name in TARGETS
            if suite == "resemblance_hostile_v1"
        }
    )
    for key, source in roots.items():
        expected = accepted[key]["tree_sha256"]
        # Use the same tree implementation the frozen generalization gate uses.
        from experiments import entropygraph_v030_release as release

        got = release.treehash(source)
        if got != expected:
            raise RuntimeError(f"runtime-gate source drift for {key}: {got} != {expected}")
    return roots


def _ratio(new: float, old: float) -> float:
    return float(new) / max(float(old), 1e-9)


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    accepted = GENERAL._accepted_v029_rows()
    roots = _build_corpora(work_root)
    rows = []

    for suite, name in TARGETS:
        source = roots[(suite, name)]
        expected_tree = accepted[(suite, name)]["tree_sha256"]
        expected_v029_bytes = int(accepted[(suite, name)]["accepted_v029_bytes"])
        repetitions = []

        for rep, order in enumerate(REPETITION_ORDER):
            per_engine = {}
            for engine in order:
                archive = work_root / "archives" / f"{suite}-{name}-r{rep}-{engine}.cmpct"
                archive.parent.mkdir(parents=True, exist_ok=True)
                packed = _run_worker(
                    "--engine", engine,
                    "--op", "pack",
                    "--source", str(source),
                    "--archive", str(archive),
                )
                verified = _run_worker(
                    "--engine", engine,
                    "--op", "verify",
                    "--archive", str(archive),
                )
                destination = work_root / "extract" / f"{suite}-{name}-r{rep}-{engine}"
                extracted = _run_worker(
                    "--engine", engine,
                    "--op", "extract",
                    "--archive", str(archive),
                    "--destination", str(destination),
                )
                if packed["tree_sha256"] != expected_tree or verified["tree_sha256"] != expected_tree:
                    raise RuntimeError(f"{engine} pack/verify tree mismatch for {suite}/{name}")
                if extracted["tree_sha256"] != expected_tree:
                    raise RuntimeError(f"{engine} extracted tree mismatch for {suite}/{name}")
                if engine == "v029" and int(packed["archive_bytes"]) != expected_v029_bytes:
                    raise RuntimeError(
                        f"v0.29 runtime baseline drift for {suite}/{name}: "
                        f"{packed['archive_bytes']} != {expected_v029_bytes}"
                    )
                per_engine[engine] = {
                    "archive_bytes": int(packed["archive_bytes"]),
                    "pack_wall_s": float(packed["wall_s"]),
                    "pack_peak_rss_kib": int(packed["peak_rss_kib"]),
                    "verify_wall_s": float(verified["wall_s"]),
                    "verify_peak_rss_kib": int(verified["peak_rss_kib"]),
                    "extract_wall_s": float(extracted["wall_s"]),
                    "extract_peak_rss_kib": int(extracted["peak_rss_kib"]),
                }

            old = per_engine["v029"]
            new = per_engine["v030"]
            repetitions.append(
                {
                    "rep": rep,
                    "execution_order": list(order),
                    "v029": old,
                    "v030": new,
                    "create_ratio": _ratio(new["pack_wall_s"], old["pack_wall_s"]),
                    "verify_ratio": _ratio(new["verify_wall_s"], old["verify_wall_s"]),
                    "extract_ratio": _ratio(new["extract_wall_s"], old["extract_wall_s"]),
                    "pack_rss_ratio": _ratio(new["pack_peak_rss_kib"], old["pack_peak_rss_kib"]),
                    "extract_rss_ratio": _ratio(new["extract_peak_rss_kib"], old["extract_peak_rss_kib"]),
                    "size_regression": new["archive_bytes"] > old["archive_bytes"],
                }
            )

        workload = {
            "suite": suite,
            "name": name,
            "tree_sha256": expected_tree,
            "accepted_v029_bytes": expected_v029_bytes,
            "repetitions": repetitions,
            "median_create_ratio": statistics.median(row["create_ratio"] for row in repetitions),
            "median_verify_ratio": statistics.median(row["verify_ratio"] for row in repetitions),
            "median_extract_ratio": statistics.median(row["extract_ratio"] for row in repetitions),
            "max_pack_rss_ratio": max(row["pack_rss_ratio"] for row in repetitions),
            "max_extract_rss_ratio": max(row["extract_rss_ratio"] for row in repetitions),
            "v030_bytes": repetitions[-1]["v030"]["archive_bytes"],
        }
        workload["saving_vs_v029_bytes"] = expected_v029_bytes - workload["v030_bytes"]
        rows.append(workload)

    median_create = statistics.median(row["median_create_ratio"] for row in rows)
    median_extract = statistics.median(row["median_extract_ratio"] for row in rows)
    max_create = max(row["median_create_ratio"] for row in rows)
    max_extract = max(row["median_extract_ratio"] for row in rows)
    max_rss = max(
        max(row["max_pack_rss_ratio"], row["max_extract_rss_ratio"])
        for row in rows
    )
    gate = {
        "exact_target_count": len(rows) == len(TARGETS),
        "no_size_regressions": all(row["saving_vs_v029_bytes"] >= 0 for row in rows),
        "median_create_ratio": median_create <= MAX_MEDIAN_RATIO,
        "per_workload_create_ratio": max_create <= MAX_WORKLOAD_RATIO,
        "median_extract_ratio": median_extract <= MAX_MEDIAN_RATIO,
        "per_workload_extract_ratio": max_extract <= MAX_WORKLOAD_RATIO,
        "peak_rss_ratio": max_rss <= MAX_PEAK_RSS_RATIO,
    }
    gate["passed"] = all(gate.values())
    return {
        "schema": "cmpct-v030-release-performance-v1",
        "contract": {
            "targets": [list(item) for item in TARGETS],
            "repetition_order": [list(item) for item in REPETITION_ORDER],
            "maximum_median_create_ratio": MAX_MEDIAN_RATIO,
            "maximum_workload_create_ratio": MAX_WORKLOAD_RATIO,
            "maximum_median_extract_ratio": MAX_MEDIAN_RATIO,
            "maximum_workload_extract_ratio": MAX_WORKLOAD_RATIO,
            "maximum_peak_rss_ratio": MAX_PEAK_RSS_RATIO,
            "size_regression_tolerance_bytes": 0,
            "timing_semantics": "fresh-process same-run paired hosted-runner release gate",
        },
        "rows": rows,
        "totals": {
            "median_create_ratio": median_create,
            "max_workload_create_ratio": max_create,
            "median_extract_ratio": median_extract,
            "max_workload_extract_ratio": max_extract,
            "max_peak_rss_ratio": max_rss,
        },
        "gate": gate,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-release-performance-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-release-performance.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"totals": result["totals"], "gate": result["gate"]}, indent=2), flush=True)
    if not result["gate"]["passed"]:
        raise SystemExit("v0.30 runtime promotion gate failed")


if __name__ == "__main__":
    main()
