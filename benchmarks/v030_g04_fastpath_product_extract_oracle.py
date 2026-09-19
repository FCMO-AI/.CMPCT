from __future__ import annotations

"""Focused complete-product extraction oracle for the promoted G04 one-buffer inverse.

The microbenchmarks established transform-level headroom. This harness measures the shipping v0.30 front door
against accepted v0.29 on the exact neutral-hostile ML workload that exposed the delimiter hot path. Each extract
runs in a fresh process through ``v030_perf_worker.py``; archive construction is outside the extract timing, and
both extracted trees must match the source identity. This is diagnostic product evidence only: it changes no
frozen runtime threshold and does not replace the authoritative full runtime gate.
"""

import argparse
import json
import os
from pathlib import Path
import shutil
import statistics
import subprocess
import sys
import traceback

from benchmarks import v030_release_performance as PERF

ENGINE = "v030-g04-fastpath-product-extract-oracle-v1"
SUITE = "neutral_hostile_v1"
TARGET = "09_ml_artifacts"
REPS = 3


def _child(args: list[str]) -> dict:
    env = dict(os.environ)
    env["PYTHONHASHSEED"] = "0"
    proc = subprocess.run(args, text=True, capture_output=True, env=env, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"child failed {proc.returncode}: {proc.stderr}\n{proc.stdout}")
    rows = [line for line in proc.stdout.splitlines() if line.strip().startswith("{")]
    if not rows:
        raise RuntimeError(f"child emitted no JSON: {proc.stdout}")
    return json.loads(rows[-1])


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    roots = PERF._build_corpora(work_root / "corpora")
    source = roots[(SUITE, TARGET)]

    archives = {}
    packs = {}
    for engine in ("v029", "v030"):
        archive = work_root / f"{engine}.cmpct"
        packs[engine] = _child([
            sys.executable, str(PERF.WORKER), "--engine", engine, "--op", "pack",
            "--source", str(source), "--archive", str(archive),
        ])
        archives[engine] = archive

    source_tree_v029 = packs["v029"]["tree_sha256"]
    source_tree_v030 = packs["v030"]["tree_sha256"]
    samples = {"v029": [], "v030": []}
    for rep in range(REPS):
        order = ("v029", "v030") if rep % 2 == 0 else ("v030", "v029")
        for engine in order:
            dest = work_root / f"extract-{engine}-{rep}"
            row = _child([
                sys.executable, str(PERF.WORKER), "--engine", engine, "--op", "extract",
                "--archive", str(archives[engine]), "--destination", str(dest),
            ])
            expected = source_tree_v029 if engine == "v029" else source_tree_v030
            if row["tree_sha256"] != expected:
                raise RuntimeError(f"{engine} extracted tree identity mismatch")
            samples[engine].append(row)

    v029_times = [float(x["wall_s"]) for x in samples["v029"]]
    v030_times = [float(x["wall_s"]) for x in samples["v030"]]
    v029_rss = [int(x["peak_rss_kib"]) for x in samples["v029"]]
    v030_rss = [int(x["peak_rss_kib"]) for x in samples["v030"]]
    median_v029 = statistics.median(v029_times)
    median_v030 = statistics.median(v030_times)
    return {
        "schema": "cmpct-v030-g04-fastpath-product-extract-oracle-v1",
        "engine": ENGINE,
        "status": "PASS",
        "evidence_class": "focused-complete-product-runtime-oracle",
        "product_release_credit": False,
        "contract": {
            "suite": SUITE,
            "workload": TARGET,
            "repetitions_each": REPS,
            "fresh_process_each_extract": True,
            "shipping_v030_frontdoor": "experiments.entropygraph_v030_release_product",
            "accepted_v029_frontdoor": "experiments.entropygraph_v029_release",
            "frozen_runtime_thresholds_changed": False,
            "full_runtime_gate_replaced": False,
        },
        "pack": packs,
        "samples": samples,
        "comparison": {
            "v029_median_extract_s": median_v029,
            "v030_median_extract_s": median_v030,
            "v030_over_v029_extract_ratio": median_v030 / max(median_v029, 1e-12),
            "v029_max_rss_kib": max(v029_rss),
            "v030_max_rss_kib": max(v030_rss),
            "v030_over_v029_max_rss_ratio": max(v030_rss) / max(max(v029_rss), 1),
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/g04-fastpath-product-extract-work"))
    ap.add_argument("--output", type=Path, default=Path("benchmark-artifacts/g04-fastpath-product-extract.json"))
    args = ap.parse_args()
    try:
        payload = run(args.work_root)
    except BaseException as exc:
        payload = {
            "schema": "cmpct-v030-g04-fastpath-product-extract-oracle-v1",
            "engine": ENGINE,
            "status": "HARNESS_FAILURE",
            "evidence_class": "focused-complete-product-runtime-oracle",
            "product_release_credit": False,
            "error": {"type": type(exc).__name__, "message": str(exc), "traceback": traceback.format_exc(limit=32)},
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(payload, indent=2) + "\n")
        raise
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload["comparison"], indent=2), flush=True)


if __name__ == "__main__":
    main()
