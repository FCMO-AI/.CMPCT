from __future__ import annotations

"""Frozen parent-phase whole-process-tree RSS attribution for Shifted."""

import argparse
import json
import os
import shutil
import statistics
import subprocess
import sys
from pathlib import Path

from benchmarks import v030_release_generalization as GENERAL
from benchmarks import v030_release_performance as PERF
from experiments import entropygraph_v030_release_product as PRODUCT

ROOT = Path(__file__).resolve().parents[1]
WORKER = ROOT / "benchmarks" / "v030_r25_parent_phase_rss_worker.py"
TARGET = ("resemblance_hostile_v1", "01_shifted_versions")
PREREG = "docs/v030-rnd/R25_PARENT_PHASE_RSS_PREREG.md"
REPETITIONS = 3


def _head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def _run(source: Path, archive: Path) -> dict:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    proc = subprocess.run(
        [sys.executable, str(WORKER), "--source", str(source), "--archive", str(archive)],
        cwd=ROOT, env=env, capture_output=True, text=True
    )
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    if proc.returncode or not lines:
        return {"worker_failed": True, "returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr}
    try:
        data = json.loads(lines[-1])
    except Exception as exc:
        return {"worker_failed": True, "failure": f"json:{exc}", "stdout": proc.stdout, "stderr": proc.stderr}
    data["worker_failed"] = False
    return data


def _decision(signatures: list[set[str]]) -> str:
    if all("g04-build" in s for s in signatures):
        return "RESIDUAL_PEAK_LOCALIZED_G04"
    if all("final-verify" in s for s in signatures):
        return "RESIDUAL_PEAK_LOCALIZED_FINAL_VERIFY"
    if all("publication" in s for s in signatures):
        return "RESIDUAL_PEAK_LOCALIZED_PUBLICATION"
    if all("profile-prepare" in s for s in signatures):
        return "RESIDUAL_PEAK_LOCALIZED_PROFILE_PREPARE"
    if all("r24-build" in s for s in signatures) and all("g04-build" not in s for s in signatures):
        return "RESIDUAL_PEAK_LOCALIZED_R24_OR_OUTER_OVERLAP"
    return "RESIDUAL_PEAK_NOT_NARROWLY_LOCALIZED"


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    accepted = GENERAL._accepted_v029_rows()
    source = PERF._build_corpora(work_root / "corpora")[TARGET]
    expected_historical_tree = str(accepted[TARGET]["tree_sha256"])
    if str(GENERAL._historical_treehash(source)) != expected_historical_tree:
        raise RuntimeError("parent-phase source drifted from accepted repaired Shifted authority")
    product_tree = str(PRODUCT.treehash(source))

    rows: list[dict] = []
    failures: list[dict] = []
    identities: set[tuple] = set()
    allowed = {"profile-prepare", "r24-build", "r25-build", "g04-build", "publication", "final-verify"}

    for rep in range(REPETITIONS):
        archive = work_root / "archives" / f"rep-{rep}.cmpct"
        archive.parent.mkdir(parents=True, exist_ok=True)
        data = _run(source, archive)
        data["repetition"] = rep
        rows.append(data)
        owners = data.get("semantic_owners") or {}
        sig = data.get("tree_peak_phase_signature")
        ok = (
            not data.get("worker_failed")
            and data.get("tree_sha256") == product_tree
            and data.get("expected_verification_tree_sha256") == product_tree
            and data.get("selected") == "prefixgraph"
            and data.get("r24_product_bytes") is not None
            and data.get("r25_product_bytes") is not None
            and int(data.get("tree_peak_rss_kib", 0)) > 0
            and int(data.get("tree_samples", 0)) >= 100
            and data.get("tree_sampler_errors") == []
            and float(data.get("tree_sampler_interval_s", 1.0)) <= 0.01
            and isinstance(sig, list)
            and set(sig).issubset(allowed)
            and data.get("prefixgraph_executor_intercepts") == 1
            and data.get("prefixgraph_submissions") == 1
            and data.get("prefixgraph_children") == 1
            and data.get("prefixgraph_returncodes") == [0]
            and data.get("g04_children") == 0
            and data.get("all_wrappers_restored") is True
            and owners.get("identity_exact") is True
            and owners.get("pg") == "experiments._v030_canonical_prefixgraph"
            and owners.get("g04") == "experiments._v030_canonical_shared_portfolio"
            and owners.get("reader") == "experiments._v030_canonical_release_reader_policy"
        )
        identities.add(tuple(data.get(k) for k in (
            "archive_bytes", "archive_sha256", "tree_sha256", "selected",
            "format_revision", "r24_product_bytes", "r25_product_bytes"
        )))
        if not ok:
            failures.append({"repetition": rep, **data})

    valid = not failures and len(rows) == REPETITIONS and len(identities) == 1
    peak_signatures = [set(r["tree_peak_phase_signature"]) for r in rows] if valid else []
    decision = _decision(peak_signatures) if valid else "INVALID"

    summary = {}
    if valid:
        summary = {
            "median_tree_peak_rss_kib": float(statistics.median(float(r["tree_peak_rss_kib"]) for r in rows)),
            "median_parent_peak_ru_maxrss_kib": float(statistics.median(float(r["parent_peak_ru_maxrss_kib"]) for r in rows)),
            "median_wall_s": float(statistics.median(float(r["wall_s"]) for r in rows)),
            "peak_phase_signatures": [r["tree_peak_phase_signature"] for r in rows],
            "peak_process_counts": [int(r["tree_peak_processes"]) for r in rows],
            "median_samples": float(statistics.median(float(r["tree_samples"]) for r in rows)),
        }

    return {
        "schema": "cmpct-v030-r25-parent-phase-rss-v1",
        "source_commit": _head(),
        "preregistration": PREREG,
        "causal_predecessor": "docs/v030-rnd/R25_DUAL_CANDIDATE_PROCESS_ISOLATION_RSS_RESULT.md",
        "target": list(TARGET),
        "accepted_historical_tree_sha256": expected_historical_tree,
        "product_tree_sha256": product_tree,
        "repetitions": REPETITIONS,
        "rows": rows,
        "summary": summary,
        "decision": decision,
        "experiment_valid": valid,
        "worker_failures": failures,
        "release_credit": False,
        "contract": {
            "whole_process_tree_rss_decisive": True,
            "parent_ru_maxrss_diagnostic_only": True,
            "sampler_interval_s_max": 0.01,
            "min_samples_per_row": 100,
            "phase_labels_observational_only": True,
            "preserve_concurrency": True,
            "prefixgraph_process_boundary_preserved": True,
            "g04_parent_execution_required": True,
            "exact_product_identity_required": True,
            "production_source_changed": False,
            "candidate_semantics_changed": False,
            "release_thresholds_changed": False,
        },
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r25-parent-phase-rss-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r25-parent-phase-rss.json"))
    a = p.parse_args()
    data = run(a.work_root)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(data, indent=2) + "\n")
    print(json.dumps({k: data[k] for k in ("source_commit", "experiment_valid", "summary", "decision")}, indent=2), flush=True)
    if not data["experiment_valid"]:
        raise SystemExit("parent-phase RSS evidence invalid")


if __name__ == "__main__":
    main()
