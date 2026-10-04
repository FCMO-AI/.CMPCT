from __future__ import annotations

"""Frozen Shifted discovery-audition survival A/B.

Instrumentation only: compare unchanged attempt-5 with the same engine after ablating only the
position-independent *additional* candidate source. Inherited LSH candidates and every downstream
representation/verification rule stay intact.
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
import time

from benchmarks import v030_release_performance as PERF

ROOT = Path(__file__).resolve().parents[1]
TARGET = ("resemblance_hostile_v1", "01_shifted_versions")
REPETITIONS = 3


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _worker(kind: str, source: Path, archive: Path) -> dict:
    from experiments import entropygraph_v029_residual_fast as accepted

    placement = accepted.BASE.P
    original_delta = placement.delta_encode
    original_discovery = placement._position_independent_candidates
    counters = {"delta_calls": 0, "delta_s": 0.0}

    def timed_delta(*args, **kwargs):
        started = time.perf_counter()
        try:
            return original_delta(*args, **kwargs)
        finally:
            counters["delta_calls"] += 1
            counters["delta_s"] += time.perf_counter() - started

    def no_additional_discovery(sketches, nodes):
        return []

    placement.delta_encode = timed_delta
    if kind == "inherited-only":
        placement._position_independent_candidates = no_additional_discovery
    elif kind != "baseline":
        raise ValueError(kind)

    started = time.perf_counter()
    try:
        accepted.build_graph(source, archive)
    finally:
        child_s = time.perf_counter() - started
        placement.delta_encode = original_delta
        placement._position_independent_candidates = original_discovery

    verified = dict(accepted.strong_verify(archive))
    return {
        "kind": kind,
        "child_s": child_s,
        "archive_bytes": archive.stat().st_size,
        "archive_sha256": _sha(archive),
        "verify_ok": bool(verified.get("ok")),
        "tree_sha256": verified.get("tree_sha256"),
        **counters,
    }


def _fresh(kind: str, source: Path, archive: Path) -> dict:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    proc = subprocess.run(
        [sys.executable, __file__, "--worker", kind, "--source", os.fspath(source), "--archive", os.fspath(archive)],
        cwd=ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    if proc.returncode != 0 or not lines:
        raise RuntimeError(
            f"fresh discovery-survival worker failed kind={kind} rc={proc.returncode} "
            f"stdout={proc.stdout[-2000:]!r} stderr={proc.stderr[-4000:]!r}"
        )
    return json.loads(lines[-1])


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    source = PERF._build_corpora(work_root / "corpora")[TARGET]
    rows = []
    for rep in range(1, REPETITIONS + 1):
        order = ("baseline", "inherited-only") if rep % 2 else ("inherited-only", "baseline")
        measured = {}
        for kind in order:
            measured[kind] = _fresh(kind, source, work_root / f"rep-{rep}-{kind}.cmpct")
        rows.append({"rep": rep, "order": list(order), **measured})

    invalid = []
    expected_tree = rows[0]["baseline"]["tree_sha256"]
    for row in rows:
        for kind in ("baseline", "inherited-only"):
            item = row[kind]
            checks = {
                "verify": item["verify_ok"] is True,
                "tree_identity": item["tree_sha256"] == expected_tree,
                "positive_child": math.isfinite(float(item["child_s"])) and float(item["child_s"]) > 0,
                "positive_delta": math.isfinite(float(item["delta_s"])) and float(item["delta_s"]) > 0,
                "positive_calls": int(item["delta_calls"]) > 0,
            }
            item["checks"] = checks
            invalid.extend(f"rep-{row['rep']}:{kind}:{name}" for name, ok in checks.items() if not ok)

    for kind in ("baseline", "inherited-only"):
        sizes = {int(row[kind]["archive_bytes"]) for row in rows}
        shas = {row[kind]["archive_sha256"] for row in rows}
        if len(sizes) != 1:
            invalid.append(f"{kind}:archive-size-nondeterministic")
        if len(shas) != 1:
            invalid.append(f"{kind}:archive-sha-nondeterministic")

    baseline_bytes = int(rows[0]["baseline"]["archive_bytes"])
    inherited_bytes = int(rows[0]["inherited-only"]["archive_bytes"])
    baseline_sha = rows[0]["baseline"]["archive_sha256"]
    inherited_sha = rows[0]["inherited-only"]["archive_sha256"]

    if invalid:
        decision = "INVALID"
    elif inherited_bytes == baseline_bytes and inherited_sha == baseline_sha:
        decision = "SHIFTED_DISCOVERY_AUDITIONS_BYTE_DEAD"
    elif inherited_bytes > baseline_bytes:
        decision = "SHIFTED_DISCOVERY_AUDITIONS_SIZE_CONTRIBUTING"
    else:
        decision = "SHIFTED_DISCOVERY_AUDITIONS_ALTERNATE_SMALLER"

    def med(kind: str, field: str) -> float:
        return float(statistics.median(float(row[kind][field]) for row in rows))

    baseline_calls = med("baseline", "delta_calls")
    inherited_calls = med("inherited-only", "delta_calls")
    return {
        "schema": "cmpct-v030-shifted-g04-discovery-audition-survival-v1",
        "source_commit": os.environ.get("EVIDENCE_HEAD"),
        "target": "/".join(TARGET),
        "rows": rows,
        "decision": decision,
        "invalid_reasons": invalid,
        "summary": {
            "baseline_bytes": baseline_bytes,
            "inherited_only_bytes": inherited_bytes,
            "byte_delta": inherited_bytes - baseline_bytes,
            "baseline_sha256": baseline_sha,
            "inherited_only_sha256": inherited_sha,
            "baseline_child_median_s": med("baseline", "child_s"),
            "inherited_only_child_median_s": med("inherited-only", "child_s"),
            "baseline_delta_median_s": med("baseline", "delta_s"),
            "inherited_only_delta_median_s": med("inherited-only", "delta_s"),
            "baseline_delta_calls_median": baseline_calls,
            "inherited_only_delta_calls_median": inherited_calls,
            "delta_call_reduction_fraction": (baseline_calls - inherited_calls) / max(1.0, baseline_calls),
        },
        "contract": {
            "repetitions": REPETITIONS,
            "instrumentation_only": True,
            "product_changed": False,
            "release_credit": False,
            "single_ablation": "accepted.BASE.P._position_independent_candidates -> []",
        },
        "release_credit": False,
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path)
    p.add_argument("--output", type=Path)
    p.add_argument("--worker", choices=("baseline", "inherited-only"))
    p.add_argument("--source", type=Path)
    p.add_argument("--archive", type=Path)
    args = p.parse_args()
    if args.worker:
        print(json.dumps(_worker(args.worker, args.source, args.archive), separators=(",", ":")))
        return
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"decision": result["decision"], "summary": result["summary"]}, separators=(",", ":")))


if __name__ == "__main__":
    main()
