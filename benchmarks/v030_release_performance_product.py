"""Fresh-process runtime/RSS gate for the promoted v0.30 product front door.

Timing remains paired against accepted v0.29 with the exact frozen 1.10x/1.25x/RSS limits. The previous harness
assumed both engines used the historical research-tree hash domain; canonical r25 productization intentionally
uses a richer user-visible filesystem identity. This harness therefore validates each engine against its own
stable identity domain while keeping the *same source tree and same runner* for timing.

Size is not relaxed or ignored: historical no-regression/revision-sized compression is enforced by
``v030_release_ablation_product``'s historical ledger, and canonical product bytes are separately required to be
<= genuine r24 product bytes on the same filesystem tree. Duplicating those incomparable byte domains inside the
runtime gate would reintroduce the measurement defect T02 explicitly removed.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import statistics

from benchmarks import v030_release_performance as B
from benchmarks import v030_release_generalization as GENERAL

B.WORKER = B.ROOT / "benchmarks" / "v030_perf_worker_canonical.py"


def _ratio(new: float, old: float) -> float:
    return float(new) / max(float(old), 1e-9)


def _worst_rows(rows: list[dict], key: str, *, limit: int = 5) -> list[dict]:
    """Return the largest runtime offenders in a log-friendly stable shape."""
    ranked = sorted(rows, key=lambda row: float(row[key]), reverse=True)[:limit]
    return [
        {
            "suite": row["suite"],
            "name": row["name"],
            "ratio": float(row[key]),
        }
        for row in ranked
    ]


def _worst_rss_rows(rows: list[dict], *, limit: int = 5) -> list[dict]:
    ranked = sorted(
        rows,
        key=lambda row: max(float(row["max_pack_rss_ratio"]), float(row["max_extract_rss_ratio"])),
        reverse=True,
    )[:limit]
    return [
        {
            "suite": row["suite"],
            "name": row["name"],
            "pack_ratio": float(row["max_pack_rss_ratio"]),
            "extract_ratio": float(row["max_extract_rss_ratio"]),
            "max_ratio": max(float(row["max_pack_rss_ratio"]), float(row["max_extract_rss_ratio"])),
        }
        for row in ranked
    ]


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    accepted = GENERAL._accepted_v029_rows()
    roots = B._build_corpora(work_root)
    rows = []

    for suite, name in B.TARGETS:
        source = roots[(suite, name)]
        historical_tree = accepted[(suite, name)]["tree_sha256"]
        expected_v029_bytes = int(accepted[(suite, name)]["accepted_v029_bytes"])
        repetitions = []
        product_tree: str | None = None

        for rep, order in enumerate(B.REPETITION_ORDER):
            per_engine = {}
            for engine in order:
                archive = work_root / "archives" / f"{suite}-{name}-r{rep}-{engine}.cmpct"
                archive.parent.mkdir(parents=True, exist_ok=True)
                packed = B._run_worker(
                    "--engine", engine,
                    "--op", "pack",
                    "--source", str(source),
                    "--archive", str(archive),
                )
                verified = B._run_worker(
                    "--engine", engine,
                    "--op", "verify",
                    "--archive", str(archive),
                )
                destination = work_root / "extract" / f"{suite}-{name}-r{rep}-{engine}"
                extracted = B._run_worker(
                    "--engine", engine,
                    "--op", "extract",
                    "--archive", str(archive),
                    "--destination", str(destination),
                )

                if engine == "v029":
                    expected_tree = historical_tree
                    if int(packed["archive_bytes"]) != expected_v029_bytes:
                        raise RuntimeError(
                            f"v0.29 runtime baseline drift for {suite}/{name}: "
                            f"{packed['archive_bytes']} != {expected_v029_bytes}"
                        )
                else:
                    candidate_tree = packed.get("tree_sha256")
                    if not isinstance(candidate_tree, str) or len(candidate_tree) != 64:
                        raise RuntimeError(f"v0.30 product pack omitted user-tree identity for {suite}/{name}")
                    if product_tree is None:
                        product_tree = candidate_tree
                    elif product_tree != candidate_tree:
                        raise RuntimeError(f"v0.30 product tree identity changed across repetitions for {suite}/{name}")
                    expected_tree = product_tree

                if packed.get("tree_sha256") != expected_tree or verified.get("tree_sha256") != expected_tree:
                    raise RuntimeError(f"{engine} pack/verify tree mismatch for {suite}/{name}")
                if extracted.get("tree_sha256") != expected_tree:
                    raise RuntimeError(f"{engine} extracted tree mismatch for {suite}/{name}")

                per_engine[engine] = {
                    "archive_bytes": int(packed["archive_bytes"]),
                    "tree_sha256": expected_tree,
                    "pack_wall_s": float(packed["wall_s"]),
                    "pack_peak_rss_kib": int(packed["peak_rss_kib"]),
                    "verify_wall_s": float(verified["wall_s"]),
                    "verify_peak_rss_kib": int(verified["peak_rss_kib"]),
                    "extract_wall_s": float(extracted["wall_s"]),
                    "extract_peak_rss_kib": int(extracted["peak_rss_kib"]),
                    "build_stats": packed.get("build_stats"),
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
                }
            )

        assert product_tree is not None
        rows.append(
            {
                "suite": suite,
                "name": name,
                "historical_tree_sha256": historical_tree,
                "product_tree_sha256": product_tree,
                "accepted_v029_bytes": expected_v029_bytes,
                "repetitions": repetitions,
                "median_create_ratio": statistics.median(row["create_ratio"] for row in repetitions),
                "median_verify_ratio": statistics.median(row["verify_ratio"] for row in repetitions),
                "median_extract_ratio": statistics.median(row["extract_ratio"] for row in repetitions),
                "max_pack_rss_ratio": max(row["pack_rss_ratio"] for row in repetitions),
                "max_extract_rss_ratio": max(row["extract_rss_ratio"] for row in repetitions),
            }
        )

    median_create = statistics.median(row["median_create_ratio"] for row in rows)
    median_extract = statistics.median(row["median_extract_ratio"] for row in rows)
    max_create = max(row["median_create_ratio"] for row in rows)
    max_extract = max(row["median_extract_ratio"] for row in rows)
    max_rss = max(max(row["max_pack_rss_ratio"], row["max_extract_rss_ratio"]) for row in rows)
    gate = {
        "exact_target_count": len(rows) == len(B.TARGETS),
        "stable_historical_baseline_identity": all(len(row["historical_tree_sha256"]) == 64 for row in rows),
        "stable_product_identity": all(len(row["product_tree_sha256"]) == 64 for row in rows),
        "median_create_ratio": median_create <= B.MAX_MEDIAN_RATIO,
        "per_workload_create_ratio": max_create <= B.MAX_WORKLOAD_RATIO,
        "median_extract_ratio": median_extract <= B.MAX_MEDIAN_RATIO,
        "per_workload_extract_ratio": max_extract <= B.MAX_WORKLOAD_RATIO,
        "peak_rss_ratio": max_rss <= B.MAX_PEAK_RSS_RATIO,
    }
    gate["passed"] = all(gate.values())
    return {
        "schema": "cmpct-v030-release-performance-product-v1",
        "engine": "experiments/entropygraph_v030_release_product.py",
        "release_facade": "cmpct-v030-release-product-v1",
        "contract": {
            "targets": [list(item) for item in B.TARGETS],
            "repetition_order": [list(item) for item in B.REPETITION_ORDER],
            "maximum_median_create_ratio": B.MAX_MEDIAN_RATIO,
            "maximum_workload_create_ratio": B.MAX_WORKLOAD_RATIO,
            "maximum_median_extract_ratio": B.MAX_MEDIAN_RATIO,
            "maximum_workload_extract_ratio": B.MAX_WORKLOAD_RATIO,
            "maximum_peak_rss_ratio": B.MAX_PEAK_RSS_RATIO,
            "timing_semantics": "fresh-process same-run paired accepted-v0.29 vs canonical-v0.30 product",
            "identity_rule": "historical and canonical-product tree hashes are independently verified; they are not numerically conflated",
            "size_gate_binding": "historical compression + canonical r24-vs-r25 product parity in v030_release_ablation_product",
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
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-product-runtime-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-product-runtime.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    diagnostic = {
        "totals": result["totals"],
        "gate": result["gate"],
        "worst_workloads": {
            "create": _worst_rows(result["rows"], "median_create_ratio"),
            "verify": _worst_rows(result["rows"], "median_verify_ratio"),
            "extract": _worst_rows(result["rows"], "median_extract_ratio"),
            "rss": _worst_rss_rows(result["rows"]),
        },
    }
    print(json.dumps(diagnostic, indent=2), flush=True)
    if not result["gate"]["passed"]:
        raise SystemExit("v0.30 release-product runtime gate failed")


if __name__ == "__main__":
    main()
