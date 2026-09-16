from __future__ import annotations

"""Frozen phase-labelled live-RSS attribution for complete r25 product construction."""

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
WORKER = ROOT / "benchmarks" / "v030_r25_product_lifetime_rss_phase_worker.py"
TARGET = ("resemblance_hostile_v1", "01_shifted_versions")
PREREG = "docs/v030-rnd/R25_PRODUCT_LIFETIME_RSS_PHASE_PREREG.md"
REPETITIONS = 3
CANDIDATE_PHASES = {"g04-build", "prefixgraph-build"}


def _head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def _run(source: Path, archive: Path) -> dict:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    proc = subprocess.run(
        [sys.executable, str(WORKER), "--source", str(source), "--archive", str(archive)],
        cwd=ROOT, env=env, capture_output=True, text=True,
    )
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    if proc.returncode or not lines:
        return {"worker_failed": True, "returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr}
    try:
        data = json.loads(lines[-1])
    except Exception as exc:
        return {"worker_failed": True, "returncode": 0, "failure": f"json:{exc}",
                "stdout": proc.stdout, "stderr": proc.stderr}
    data["worker_failed"] = False
    return data


def _first_entry(data: dict, phase: str) -> int | None:
    values = [int(row["vmrss_kib"]) for row in data.get("phase_events", [])
              if row.get("phase") == phase and row.get("event") == "enter"]
    return values[0] if values else None


def run(work_root: Path) -> dict:
    work_root = Path(work_root)
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)

    accepted = GENERAL._accepted_v029_rows()
    source = PERF._build_corpora(work_root / "corpora")[TARGET]
    expected_historical_tree = str(accepted[TARGET]["tree_sha256"])
    historical_tree = str(GENERAL._historical_treehash(source))
    product_tree = str(PRODUCT.treehash(source))
    if historical_tree != expected_historical_tree:
        raise RuntimeError("phase attribution source drifted from accepted repaired Shifted authority")

    rows: list[dict] = []
    failures: list[dict] = []
    valid = True
    identity = None

    for index in range(REPETITIONS):
        archive = work_root / "archives" / f"r{index}.cmpct"
        archive.parent.mkdir(parents=True, exist_ok=True)
        data = _run(source, archive)
        rows.append(data)
        owners = data.get("semantic_owners") or {}
        peak = data.get("sampled_global_peak") or {}
        coverage = float(peak.get("vmrss_kib", 0)) / max(1.0, float(data.get("peak_ru_maxrss_kib", 0)))
        pg_entry = _first_entry(data, "prefixgraph-build")
        g04_entry = _first_entry(data, "g04-build")
        data["sampled_to_ru_peak_coverage"] = coverage
        data["prefixgraph_entry_vmrss_kib"] = pg_entry
        data["g04_entry_vmrss_kib"] = g04_entry
        if pg_entry is not None and g04_entry is not None:
            first_entry = min(pg_entry, g04_entry)
            baseline = int(data["baseline_vmrss_kib"])
            sampled_peak = max(1, int(peak["vmrss_kib"]))
            data["first_candidate_entry_vmrss_kib"] = first_entry
            data["retained_entry_fraction"] = max(0, first_entry - baseline) / sampled_peak
        else:
            data["retained_entry_fraction"] = None

        ok = (
            not data.get("worker_failed")
            and data.get("expected_verification_tree_sha256") == product_tree
            and data.get("tree_sha256") == product_tree
            and data.get("verification_identity_domain") == "canonical-filesystem-user-tree-v1"
            and data.get("research_identity_domain") == "research-content-tree-v1"
            and owners.get("identity_exact") is True
            and owners.get("pg") == "experiments._v030_canonical_prefixgraph"
            and owners.get("g04") == "experiments._v030_canonical_shared_portfolio"
            and owners.get("reader") == "experiments._v030_canonical_release_reader_policy"
            and data.get("r24_product_bytes") is not None
            and data.get("r25_product_bytes") is not None
            and data.get("r25_attempted") is not False
            and data.get("wrappers_restored") is True
            and data.get("sampler_errors") == []
            and int(data.get("sample_count", 0)) >= 100
            and coverage >= 0.90
            and pg_entry is not None
            and g04_entry is not None
        )
        current_identity = tuple(data.get(key) for key in ("archive_bytes", "archive_sha256", "tree_sha256",
                                                            "selected", "format_revision", "r24_product_bytes",
                                                            "r25_product_bytes"))
        if identity is None:
            identity = current_identity
        elif current_identity != identity:
            ok = False
            data["identity_failure"] = "cross-repetition-complete-product-identity-mismatch"
        if not ok:
            valid = False
            failures.append({"repetition": index, **data})

    retained = [float(row["retained_entry_fraction"]) for row in rows if row.get("retained_entry_fraction") is not None]
    median_retained = statistics.median(retained) if retained else None
    peak_candidate_presence = []
    peak_combos = []
    for row in rows:
        active = set((row.get("sampled_global_peak") or {}).get("active") or [])
        peak_candidate_presence.append(bool(active & CANDIDATE_PHASES))
        peak_combos.append("+".join(sorted(active)) if active else "<none>")
    outside_count = sum(not value for value in peak_candidate_presence)
    consistent_combo = len(set(peak_combos)) == 1

    if not valid:
        decision = "INVALID"
    elif outside_count >= 2:
        decision = "PEAK_OUTSIDE_CANDIDATE_BUILDS"
    elif not consistent_combo:
        decision = "AMBIGUOUS_PHASE_OWNERSHIP"
    elif median_retained is not None and median_retained >= 0.20:
        decision = "SUPPORTS_PRE_CANDIDATE_RETAINED_STATE"
    elif median_retained is not None and median_retained < 0.10:
        decision = "RETIRES_PRE_CANDIDATE_RETAINED_STATE_PRIMARY"
    else:
        decision = "AMBIGUOUS_RETAINED_STATE"

    return {
        "schema": "cmpct-v030-r25-product-lifetime-rss-phase-v1",
        "source_commit": _head(),
        "preregistration": PREREG,
        "causal_predecessors": [
            "docs/v030-rnd/R25_PRODUCT_PHASE_RSS_RESULT.md",
            "docs/v030-rnd/R25_SEMANTIC_OWNER_RSS_V2_RESULT.md",
            "docs/v030-rnd/R25_CANDIDATE_SCHEDULING_RSS_V3_RESULT.md",
            "docs/v030-rnd/R25_OUTER_PRODUCT_SCHEDULING_RSS_RESULT.md",
        ],
        "target": list(TARGET),
        "accepted_historical_tree_sha256": expected_historical_tree,
        "product_tree_sha256": product_tree,
        "repetitions": rows,
        "median_retained_entry_fraction": median_retained,
        "global_peak_phase_combinations": peak_combos,
        "global_peak_candidate_presence": peak_candidate_presence,
        "global_peak_outside_candidate_count": outside_count,
        "phase_combination_consistent": consistent_combo,
        "decision": decision,
        "experiment_valid": valid,
        "worker_failures": failures,
        "release_credit": False,
        "contract": {
            "live_vmrss_diagnostic_only": True,
            "ru_maxrss_retained": True,
            "sample_interval_ms": 10,
            "minimum_sampler_coverage": 0.90,
            "minimum_samples": 100,
            "exact_product_identity_required": True,
            "production_source_changed": False,
            "scheduling_changed": False,
            "release_thresholds_changed": False,
            "decision_thresholds": {"support": 0.20, "retire": 0.10},
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r25-product-lifetime-rss-phase-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r25-product-lifetime-rss-phase.json"))
    args = parser.parse_args()
    data = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, indent=2) + "\n")
    print(json.dumps({key: data[key] for key in (
        "source_commit", "experiment_valid", "median_retained_entry_fraction",
        "global_peak_phase_combinations", "decision")}, indent=2), flush=True)
    if not data["experiment_valid"]:
        raise SystemExit("product-lifetime RSS phase evidence invalid")


if __name__ == "__main__":
    main()
