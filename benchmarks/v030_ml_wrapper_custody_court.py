from __future__ import annotations

"""Research-only same-source ML worker-custody court.

Executes the frozen 2026-10-03 preregistration. It compares the unchanged
v030_perf_worker_v2.py and v030_perf_worker_canonical.py on one deterministic
ML source tree. It changes no product code, worker code, benchmark threshold,
format, selector, comparator, or release law.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from benchmarks import v030_release_generalization as GENERAL
from benchmarks import v030_release_performance as BASE
from experiments import entropygraph_v030_release_product as PRODUCT

ROOT = Path(__file__).resolve().parents[1]
V2_WORKER = ROOT / "benchmarks" / "v030_perf_worker_v2.py"
CANONICAL_WORKER = ROOT / "benchmarks" / "v030_perf_worker_canonical.py"
ML_KEY = ("neutral_hostile_v1", "09_ml_artifacts")
ENGINE_ORDERS = (
    ("v029", "v030"),
    ("v030", "v029"),
    ("v030", "v029"),
    ("v029", "v030"),
)
WORKER_BLOCK_ORDER = (
    "v2", "canonical", "canonical", "v2",
    "canonical", "v2", "v2", "canonical",
)
CEILING = 1.25


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _worker(worker: Path, engine: str, source: Path, archive: Path) -> dict:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    p = subprocess.run(
        [sys.executable, str(worker), "--engine", engine, "--op", "pack",
         "--source", str(source), "--archive", str(archive)],
        cwd=ROOT, env=env, check=False, capture_output=True, text=True,
    )
    if p.returncode:
        raise RuntimeError(
            f"worker failure {worker.name}/{engine}: rc={p.returncode} stdout={p.stdout!r} stderr={p.stderr!r}"
        )
    lines = [line for line in p.stdout.splitlines() if line.strip()]
    if not lines:
        raise RuntimeError(f"worker emitted no JSON: {worker.name}/{engine}")
    result = json.loads(lines[-1])
    result["archive_sha256"] = _sha256_file(archive)
    result["worker"] = worker.name
    return result


def _source(work_root: Path) -> tuple[Path, dict]:
    original = BASE.TARGETS
    try:
        BASE.TARGETS = (ML_KEY,)
        roots = BASE._build_corpora(work_root / "source")
    finally:
        BASE.TARGETS = original

    source = roots[ML_KEY]
    accepted = GENERAL._accepted_v029_rows()[ML_KEY]
    historical = GENERAL._historical_treehash(source)
    if historical != accepted["tree_sha256"]:
        raise RuntimeError("ML historical source identity drift")
    return source, {
        "historical_tree_sha256": historical,
        "product_tree_sha256": PRODUCT.treehash(source),
        "accepted_v029_bytes": int(accepted["accepted_v029_bytes"]),
    }


def _even_median(values: list[float]) -> float:
    if len(values) != 4:
        raise RuntimeError("court requires exactly four ratios per worker")
    v = sorted(float(x) for x in values)
    return (v[1] + v[2]) / 2.0


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    source, identity = _source(work_root)
    workers = {"v2": V2_WORKER, "canonical": CANONICAL_WORKER}
    occurrence = {"v2": 0, "canonical": 0}
    blocks = []

    for block_i, label in enumerate(WORKER_BLOCK_ORDER):
        pair_i = occurrence[label]
        occurrence[label] += 1
        order = ENGINE_ORDERS[pair_i]
        observed = {}
        for ordinal, engine in enumerate(order):
            archive = work_root / "archives" / f"b{block_i}-{label}-p{pair_i}-{ordinal}-{engine}.cmpct"
            archive.parent.mkdir(parents=True, exist_ok=True)
            row = _worker(workers[label], engine, source, archive)
            expected_tree = identity["historical_tree_sha256"] if engine == "v029" else identity["product_tree_sha256"]
            if row.get("tree_sha256") != expected_tree:
                raise RuntimeError(f"{label}/{engine} tree identity drift")
            if engine == "v029" and int(row["archive_bytes"]) != identity["accepted_v029_bytes"]:
                raise RuntimeError(f"{label}/v029 accepted-byte drift")
            observed[engine] = row

        blocks.append({
            "block": block_i,
            "worker": label,
            "pair": pair_i,
            "engine_order": list(order),
            "create_ratio": float(observed["v030"]["wall_s"]) / max(float(observed["v029"]["wall_s"]), 1e-9),
            "v029": observed["v029"],
            "v030": observed["v030"],
        })

    if occurrence != {"v2": 4, "canonical": 4}:
        raise RuntimeError(f"worker-block drift: {occurrence!r}")

    identity_court = {}
    for engine in ("v029", "v030"):
        rows = [b[engine] for b in blocks]
        byte_values = {int(r["archive_bytes"]) for r in rows}
        tree_values = {str(r["tree_sha256"]) for r in rows}
        identity_court[engine] = {
            "archive_bytes": sorted(byte_values),
            "tree_sha256": sorted(tree_values),
            "archive_sha256_diagnostic": sorted({str(r["archive_sha256"]) for r in rows}),
        }
        if len(byte_values) != 1 or len(tree_values) != 1:
            raise RuntimeError(f"{engine} cross-worker identity drift")

    ratios = {
        label: [float(b["create_ratio"]) for b in blocks if b["worker"] == label]
        for label in ("v2", "canonical")
    }
    v2_median = _even_median(ratios["v2"])
    canonical_median = _even_median(ratios["canonical"])
    delta = canonical_median - v2_median

    if canonical_median > CEILING and v2_median <= CEILING:
        verdict = "WRAPPER_CUSTODY_SUFFICIENT_TO_EXPLAIN_GATE_SPLIT"
    elif delta <= 0:
        verdict = "WORKER_PATH_HYPOTHESIS_FALSIFIED"
    else:
        verdict = "DIRECTIONAL_CUSTODY_EFFECT_WITHOUT_GATE_SPLIT"

    return {
        "schema": "cmpct-v030-ml-wrapper-custody-court-v1",
        "claim_boundary": "research/custody attribution only; zero product or release credit",
        "product_source": "94f3309011ca6f6014b1f61ce6058e8ce01ca00f",
        "source_identity": identity,
        "engine_orders": [list(v) for v in ENGINE_ORDERS],
        "worker_block_order": list(WORKER_BLOCK_ORDER),
        "identity": identity_court,
        "blocks": blocks,
        "v2_ratios": ratios["v2"],
        "canonical_ratios": ratios["canonical"],
        "v2_conventional_median_ratio": v2_median,
        "canonical_conventional_median_ratio": canonical_median,
        "canonical_minus_v2_median_delta": delta,
        "unchanged_release_ceiling": CEILING,
        "verdict": verdict,
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-ml-wrapper-custody-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-ml-wrapper-custody.json"))
    args = p.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({
        "v2_median": result["v2_conventional_median_ratio"],
        "canonical_median": result["canonical_conventional_median_ratio"],
        "delta": result["canonical_minus_v2_median_delta"],
        "verdict": result["verdict"],
    }, indent=2))


if __name__ == "__main__":
    main()
