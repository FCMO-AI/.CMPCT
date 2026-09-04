from __future__ import annotations

"""Frozen D1 attribution for the inherited Shifted G0-G4 shared candidate.

No product behavior changes. Each fresh worker constructs the exact staged filesystem, exact shipping
PrefixGraph process-executor incumbent, drains the shipping r24 prebuild so no unrelated compression
remains live, then runs the unchanged v0.30 shared v0.28+attempt5 builder and records child ownership.
"""

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import statistics
import subprocess
import sys
import tempfile
import time

from benchmarks import v030_release_performance as PERF

ROOT = Path(__file__).resolve().parents[1]
TARGET = ("resemblance_hostile_v1", "01_shifted_versions")
REPETITIONS = 3
LOCALITY_CEILING = 8.0


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _measure_once(source: Path, work: Path) -> dict:
    from experiments import entropygraph_v030_release_product as product
    from experiments.entropygraph_v030_prefixgraph_process_executor import PrefixGraphProcessExecutor

    C = product._BASE_IMPL.C
    work = Path(work)
    work.mkdir(parents=True, exist_ok=True)
    staged = work / "profile-tree"
    pg_path = work / "prefixgraph.cmpct"
    r24_path = work / "canonical-r24.cmpct"

    prepared = C._prepare_profile_tree(Path(source), staged)
    expected_graph_tree = C.RC.treehash(staged)
    eligible, reason = C.RC._prefixgraph_eligibility(staged, expected_graph_tree)
    if not eligible:
        raise RuntimeError(f"frozen Shifted target lost PrefixGraph eligibility: {reason}")

    pg_started = time.perf_counter()
    with C._revision25_profile_context():
        with PrefixGraphProcessExecutor() as executor:
            pg_stats = dict(executor.submit(C.RC.PG.build, staged, pg_path).result())
            pg_receipt = dict(executor.last_receipt or {})
        pg_locality = dict(C.RC._prefixgraph_locality(pg_path))
    pg_wall_s = time.perf_counter() - pg_started

    # _prepare_profile_tree on the promoted release surface starts the genuine r24 floor in a background
    # thread. Consume it before child attribution so neither shared child is accidentally timed against an
    # unrelated still-running r24 compressor. This does not gift any candidate bytes.
    r24_stats = dict(C._r24_build(Path(source), r24_path))

    pg_verify = dict(C.RC.PG.strong_verify(pg_path))
    if not pg_verify.get("ok") or pg_verify.get("tree_sha256") != expected_graph_tree:
        raise RuntimeError("PrefixGraph incumbent did not reproduce the exact staged content tree")
    pg_bytes = pg_path.stat().st_size
    pg_sha = _sha(pg_path)

    with tempfile.TemporaryDirectory(prefix=".cmpct-v030-shifted-shared-owner-", dir=work) as td:
        shared = C.SHARED._build_shared_candidates(staged, Path(td))
        v029 = dict(shared["v029_stats"])
        row = {
            "prefixgraph_bytes": pg_bytes,
            "prefixgraph_sha256": pg_sha,
            "prefixgraph_wall_s": pg_wall_s,
            "prefixgraph_process_receipt": pg_receipt,
            "prefixgraph_locality": pg_locality,
            "prefixgraph_verify": pg_verify,
            "profile_manifest_sha256": prepared["manifest_sha256"],
            "r24_product_bytes": r24_path.stat().st_size,
            "r24_create_s": r24_stats.get("create_s"),
            "shared_wall_s": float(shared["shared_build_s"]),
            "v028_child_s": float(v029["v028_child_s"]),
            "attempt5_child_s": float(v029["attempt5_child_s"]),
            "v028_bytes": int(shared["v028_bytes"]),
            "attempt5_graph_bytes": int(shared["graph_bytes"]),
            "v029_floor_bytes": int(shared["floor_bytes"]),
            "v029_floor_selected": shared["floor_selected"],
            "shared_scheduler_mode": v029["scheduler_mode"],
            "accepted_engine": v029["accepted_engine"],
        }
    row.update({
        "v028_gap_vs_prefixgraph_bytes": row["v028_bytes"] - pg_bytes,
        "attempt5_gap_vs_prefixgraph_bytes": row["attempt5_graph_bytes"] - pg_bytes,
        "v029_floor_gap_vs_prefixgraph_bytes": row["v029_floor_bytes"] - pg_bytes,
    })
    checks = {
        "pg_receipt_schema": pg_receipt.get("schema") == "cmpct-v030-prefixgraph-process-executor-v1",
        "pg_semantic_owner": pg_receipt.get("semantic_owner") == "experiments._v030_canonical_prefixgraph",
        "pg_level_15": int(pg_receipt.get("prefix_level", -1)) == 15,
        "pg_receipt_bytes": int(pg_receipt.get("archive_bytes", -1)) == pg_bytes,
        "pg_receipt_sha": pg_receipt.get("archive_sha256") == pg_sha,
        "pg_verify": bool(pg_verify.get("ok")) and pg_verify.get("tree_sha256") == expected_graph_tree,
        "pg_locality": bool(pg_locality.get("passed")) and float(pg_locality.get("max_member_read_amplification", 1e9)) <= LOCALITY_CEILING,
        "pg_beats_v028": pg_bytes < row["v028_bytes"],
        "pg_beats_attempt5": pg_bytes < row["attempt5_graph_bytes"],
        "pg_beats_v029_floor": pg_bytes < row["v029_floor_bytes"],
        "shared_scheduler": row["shared_scheduler_mode"] == "v030-shared-v028-attempt5-spawn",
        "accepted_engine": row["accepted_engine"] == "attempt5-residual-program-packing",
        "positive_finite_timings": all(
            math.isfinite(float(row[k])) and float(row[k]) > 0
            for k in ("shared_wall_s", "v028_child_s", "attempt5_child_s", "prefixgraph_wall_s")
        ),
    }
    row["checks"] = checks
    return row


def _worker(source: Path, work: Path) -> dict:
    return _measure_once(source, work)


def _fresh(source: Path, work: Path) -> dict:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    proc = subprocess.run(
        [sys.executable, __file__, "--worker", "--source", os.fspath(source), "--work-root", os.fspath(work)],
        cwd=ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    if proc.returncode != 0 or not lines:
        raise RuntimeError(f"fresh attribution worker failed rc={proc.returncode} stdout={proc.stdout[-2000:]!r} stderr={proc.stderr[-4000:]!r}")
    return json.loads(lines[-1])


def run(work_root: Path) -> dict:
    work_root = Path(work_root)
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    roots = PERF._build_corpora(work_root / "corpora")
    source = roots[TARGET]
    rows = []
    for rep in range(1, REPETITIONS + 1):
        rows.append({"rep": rep, **_fresh(source, work_root / f"rep-{rep}")})

    invalid = [f"rep-{row['rep']}:{name}" for row in rows for name, ok in row["checks"].items() if not ok]
    med = lambda key: float(statistics.median(float(row[key]) for row in rows))
    shared = med("shared_wall_s")
    v028 = med("v028_child_s")
    attempt5 = med("attempt5_child_s")
    v_ratio = v028 / max(shared, 1e-12)
    a_ratio = attempt5 / max(shared, 1e-12)
    if invalid:
        decision = "INVALID"
    elif v_ratio >= 0.80 and a_ratio >= 0.80:
        decision = "SHIFTED_G04_SHARED_BOTH_CHILDREN_COOWN"
    elif v_ratio >= 0.80 and a_ratio < 0.50:
        decision = "SHIFTED_G04_SHARED_V028_DOMINATES"
    elif a_ratio >= 0.80 and v_ratio < 0.50:
        decision = "SHIFTED_G04_SHARED_ATTEMPT5_DOMINATES"
    else:
        decision = "SHIFTED_G04_SHARED_MIXED_OWNERSHIP"

    return {
        "schema": "cmpct-v030-shifted-g04-shared-child-attribution-v1",
        "source_commit": os.environ.get("EVIDENCE_HEAD"),
        "target": "/".join(TARGET),
        "rows": rows,
        "medians": {
            "shared_wall_s": shared,
            "v028_child_s": v028,
            "attempt5_child_s": attempt5,
            "v028_shared_ratio": v_ratio,
            "attempt5_shared_ratio": a_ratio,
            "prefixgraph_wall_s": med("prefixgraph_wall_s"),
            "prefixgraph_bytes": int(statistics.median(int(row["prefixgraph_bytes"]) for row in rows)),
            "v028_bytes": int(statistics.median(int(row["v028_bytes"]) for row in rows)),
            "attempt5_graph_bytes": int(statistics.median(int(row["attempt5_graph_bytes"]) for row in rows)),
            "v029_floor_bytes": int(statistics.median(int(row["v029_floor_bytes"]) for row in rows)),
        },
        "decision": decision,
        "invalid_reasons": invalid,
        "contract": {
            "repetitions": REPETITIONS,
            "coowner_min_shared_ratio": 0.80,
            "dominant_other_max_shared_ratio": 0.50,
            "locality_ceiling": LOCALITY_CEILING,
            "product_changed": False,
            "release_credit": False,
        },
        "release_credit": False,
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, required=True)
    p.add_argument("--output", type=Path)
    p.add_argument("--worker", action="store_true")
    p.add_argument("--source", type=Path)
    args = p.parse_args()
    if args.worker:
        if args.source is None:
            p.error("--worker requires --source")
        print(json.dumps(_worker(args.source, args.work_root), separators=(",", ":"), default=str))
        return
    if args.output is None:
        p.error("measurement mode requires --output")
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"decision": result["decision"], "medians": result["medians"]}, separators=(",", ":")))


if __name__ == "__main__":
    main()
