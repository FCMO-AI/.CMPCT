from __future__ import annotations

import argparse
import json
import os
import shutil
import statistics
import subprocess
import sys
from pathlib import Path

from benchmarks import v030_release_performance as PERF
from experiments import entropygraph_v030_canonical_final as CANONICAL

ROOT = Path(__file__).resolve().parents[1]
WORKER = ROOT / "benchmarks" / "v030_r25_candidate_scheduling_rss_v3_worker.py"
ORDERS = (("concurrent", "serialized"), ("serialized", "concurrent"))
TARGET = ("resemblance_hostile_v1", "01_shifted_versions")


def _head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def _run(mode: str, source: Path, archive: Path) -> dict:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    p = subprocess.run([sys.executable, str(WORKER), "--mode", mode, "--source", str(source), "--archive", str(archive)], cwd=ROOT, env=env, capture_output=True, text=True)
    lines = [line for line in p.stdout.splitlines() if line.strip()]
    if p.returncode or not lines:
        return {"mode": mode, "worker_failed": True, "returncode": p.returncode, "stdout": p.stdout, "stderr": p.stderr}
    try:
        data = json.loads(lines[-1])
    except Exception as exc:
        return {"mode": mode, "worker_failed": True, "returncode": 0, "failure": f"json:{exc}", "stdout": p.stdout, "stderr": p.stderr}
    data["worker_failed"] = False
    return data


def run(root: Path) -> dict:
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True)
    source = PERF._build_corpora(root / "corpora")[TARGET]
    research_tree = str(CANONICAL.RC.treehash(source))
    product_tree = str(CANONICAL.treehash(source))
    repetitions, failures = [], []
    valid = True

    for round_index, order in enumerate(ORDERS):
        row = {"round": round_index, "execution_order": list(order)}
        for mode in order:
            archive = root / "archives" / f"r{round_index}-{mode}.cmpct"
            archive.parent.mkdir(parents=True, exist_ok=True)
            data = _run(mode, source, archive)
            row[mode] = data
            owners = data.get("semantic_owners") or {}
            ok = (
                not data.get("worker_failed")
                and data.get("research_tree_sha256") == research_tree
                and data.get("expected_verification_tree_sha256") == product_tree
                and data.get("verified_tree_sha256") == product_tree
                and data.get("tree_sha256") == product_tree
                and data.get("research_identity_domain") == "research-content-tree-v1"
                and data.get("verification_identity_domain") == "canonical-filesystem-user-tree-v1"
                and owners.get("identity_exact") is True
                and owners.get("pg") == "experiments._v030_canonical_prefixgraph"
                and owners.get("g04") == "experiments._v030_canonical_shared_portfolio"
                and owners.get("reader") == "experiments._v030_canonical_release_reader_policy"
                and data.get("selected") == "prefixgraph"
            )
            if mode == "serialized":
                ok = ok and data.get("intercepted_prefixgraph_executor_constructions") == 1 and data.get("intercepted_prefixgraph_submissions") == 1
            else:
                ok = ok and data.get("intercepted_prefixgraph_executor_constructions") == 0 and data.get("intercepted_prefixgraph_submissions") == 0
            if not ok:
                valid = False
                failures.append({"round": round_index, **data})

        a, b = row["concurrent"], row["serialized"]
        if not a.get("worker_failed") and not b.get("worker_failed"):
            if any(a.get(k) != b.get(k) for k in ("archive_bytes", "archive_sha256", "verified_tree_sha256", "selected")):
                valid = False
                failures.append({"round": round_index, "failure": "paired-product-identity-mismatch"})
        repetitions.append(row)

    def med(mode: str, key: str) -> float:
        return statistics.median(float(row[mode][key]) for row in repetitions)

    cp, sp = med("concurrent", "peak_rss_kib"), med("serialized", "peak_rss_kib")
    cw, sw = med("concurrent", "wall_s"), med("serialized", "wall_s")
    reduction = (cp - sp) / cp if cp else 0.0
    decision = "supports-concurrency-lifetime-ownership" if reduction >= 0.20 else "retires-concurrency-primary-explanation" if reduction < 0.10 else "ambiguous"
    return {
        "schema": "cmpct-v030-r25-candidate-scheduling-rss-v3",
        "source_commit": _head(),
        "preregistration": "docs/v030-rnd/R25_CANDIDATE_SCHEDULING_RSS_V3_PREREG.md",
        "supersedes": {"v2_record": "docs/v030-rnd/R25_CANDIDATE_SCHEDULING_RSS_V2_INVALID_RESULT.md", "v2_source": "198e7e124b5b56be29d21a94ecc2a8896d156478", "v2_run": 33598181893, "v2_artifact": 9834409346},
        "target": list(TARGET),
        "research_tree_sha256": research_tree,
        "expected_verification_tree_sha256": product_tree,
        "research_identity_domain": "research-content-tree-v1",
        "verification_identity_domain": "canonical-filesystem-user-tree-v1",
        "orders": [list(x) for x in ORDERS],
        "repetitions": repetitions,
        "concurrent_median_peak_rss_kib": int(cp),
        "serialized_median_peak_rss_kib": int(sp),
        "serialized_peak_rss_reduction": reduction,
        "concurrent_median_wall_s": cw,
        "serialized_median_wall_s": sw,
        "serialized_wall_ratio": sw / cw if cw else None,
        "decision": decision,
        "experiment_valid": valid,
        "worker_failures": failures,
        "release_credit": False,
        "contract": {"routing_only_prefixgraph_executor": True, "exact_product_identity_required": True, "dual_identity_domains_explicit": True, "fresh_process_per_measurement": True, "total_peak_rss_is_causal_metric": True, "decision_thresholds_changed": False, "production_source_changed": False},
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r25-candidate-scheduling-rss-v3-work"))
    ap.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r25-candidate-scheduling-rss-v3.json"))
    args = ap.parse_args()
    data = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, indent=2) + "\n")
    print(json.dumps({k: data[k] for k in ("source_commit", "experiment_valid", "concurrent_median_peak_rss_kib", "serialized_median_peak_rss_kib", "serialized_peak_rss_reduction", "concurrent_median_wall_s", "serialized_median_wall_s", "decision")}, indent=2))
    if not data["experiment_valid"]:
        raise SystemExit("candidate scheduling RSS v3 evidence invalid")


if __name__ == "__main__":
    main()
