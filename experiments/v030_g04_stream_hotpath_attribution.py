from __future__ import annotations

"""Research-only hotpath attribution inside promoted G04 one-pass verification.

Prior paired oracles localized the ML extraction regression to POLICY.strong_verify, then falsified session-open
cost and physical-record reread/cache churn. This instrument monkeypatches only method timing/counters in one
fresh process and executes the unchanged promoted policy verifier. It separates session construction, top-level
node reconstruction, direct preflate-record reads, nested record decode time, cache hit/miss counts, and residual
file/tree/integrity loop work. The monkeypatch changes no returned bytes or verifier decisions and gets zero
release credit.
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

ENGINE = "v030-g04-stream-hotpath-attribution-v1"
SUITE = "neutral_hostile_v1"
TARGET = "09_ml_artifacts"
REPETITIONS = 3


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


def _worker(archive: Path) -> int:
    from experiments import entropygraph_v030_release_product as CANON

    R = CANON.POLICY.R
    Session = R._G04Session
    original_init = Session.__init__
    original_record = Session.record
    original_node = Session.node
    state = {
        "session_init_wall_s": 0.0,
        "record_call_wall_s": 0.0,
        "record_call_wall_inside_node_s": 0.0,
        "record_call_wall_direct_s": 0.0,
        "top_node_call_wall_s": 0.0,
        "record_calls": 0,
        "record_cache_hits": 0,
        "record_cache_misses": 0,
        "node_calls": 0,
        "node_cache_hits": 0,
        "node_cache_misses": 0,
        "top_node_calls": 0,
    }
    depth = {"node": 0}

    def timed_init(self, *args, **kwargs):
        started = time.perf_counter()
        try:
            return original_init(self, *args, **kwargs)
        finally:
            state["session_init_wall_s"] += time.perf_counter() - started

    def timed_record(self, record_id):
        hit = record_id in self.record_cache
        nested = depth["node"] > 0
        state["record_calls"] += 1
        state["record_cache_hits" if hit else "record_cache_misses"] += 1
        started = time.perf_counter()
        try:
            return original_record(self, record_id)
        finally:
            dt = time.perf_counter() - started
            state["record_call_wall_s"] += dt
            state["record_call_wall_inside_node_s" if nested else "record_call_wall_direct_s"] += dt

    def timed_node(self, node_id):
        hit = node_id in self.node_cache
        top = depth["node"] == 0
        state["node_calls"] += 1
        state["node_cache_hits" if hit else "node_cache_misses"] += 1
        if top:
            state["top_node_calls"] += 1
        depth["node"] += 1
        started = time.perf_counter()
        try:
            return original_node(self, node_id)
        finally:
            dt = time.perf_counter() - started
            depth["node"] -= 1
            if top:
                state["top_node_call_wall_s"] += dt

    Session.__init__ = timed_init
    Session.record = timed_record
    Session.node = timed_node
    try:
        started = time.perf_counter()
        with CANON.C._revision25_profile_context():
            result = dict(CANON.POLICY.strong_verify(archive))
        total = time.perf_counter() - started
    finally:
        Session.__init__ = original_init
        Session.record = original_record
        Session.node = original_node

    if not result.get("ok"):
        raise RuntimeError(f"policy verification failed: {result!r}")
    accounted_inclusive = (
        state["session_init_wall_s"] + state["top_node_call_wall_s"] + state["record_call_wall_direct_s"]
    )
    state.update({
        "wall_s": total,
        "residual_outside_session_topnodes_directrecords_s": total - accounted_inclusive,
        "physical_record_reads": int(result.get("physical_record_reads", 0)),
        "logical_bytes": int(result.get("logical_bytes", 0)),
        "content_graph_tree_sha256": result.get("tree_sha256"),
    })
    print(json.dumps(state, separators=(",", ":")), flush=True)
    return 0


def run(work_root: Path) -> dict:
    from experiments import entropygraph_v030_release_product as CANON

    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    accepted = PERF.GENERAL._accepted_v029_rows()
    roots = PERF._build_corpora(work_root / "corpora")
    source = roots[(SUITE, TARGET)]
    archive = work_root / "archive" / "v030.cmpct"
    archive.parent.mkdir(parents=True, exist_ok=True)
    pack = _json_child([
        sys.executable, str(PERF.WORKER), "--engine", "v030", "--op", "pack",
        "--source", str(source), "--archive", str(archive),
    ])
    if pack.get("build_stats", {}).get("selected") != "g04-overlay":
        raise RuntimeError(f"target no longer selects G04: {pack.get('build_stats', {}).get('selected')!r}")

    expected = accepted[(SUITE, TARGET)]
    historical_tree = PERF.GENERAL._historical_treehash(source)
    if historical_tree != expected["tree_sha256"]:
        raise RuntimeError(f"historical source drift: {historical_tree} != {expected['tree_sha256']}")
    semantic_user_tree = CANON.treehash(source)

    samples = []
    for rep in range(REPETITIONS):
        row = _json_child([
            sys.executable, str(Path(__file__).resolve()), "--worker", "--archive", str(archive),
        ])
        row["rep"] = rep
        samples.append(row)

    graph_tree = samples[0]["content_graph_tree_sha256"]
    logical_bytes = int(samples[0]["logical_bytes"])
    physical_reads = int(samples[0]["physical_record_reads"])
    for row in samples:
        if row["content_graph_tree_sha256"] != graph_tree or int(row["logical_bytes"]) != logical_bytes:
            raise RuntimeError("hotpath attribution identity drift")
        if int(row["physical_record_reads"]) != physical_reads:
            raise RuntimeError("physical-record-read drift across repetitions")
        if int(row["record_cache_misses"]) != physical_reads:
            raise RuntimeError("instrumented record misses disagree with promoted reader physical-record counter")

    numeric = [
        "wall_s", "session_init_wall_s", "record_call_wall_s", "record_call_wall_inside_node_s",
        "record_call_wall_direct_s", "top_node_call_wall_s",
        "residual_outside_session_topnodes_directrecords_s",
    ]
    med = {key: statistics.median(float(row[key]) for row in samples) for key in numeric}
    total = med["wall_s"]
    comparison = dict(med)
    comparison.update({
        "session_init_fraction": med["session_init_wall_s"] / max(total, 1e-9),
        "top_node_inclusive_fraction": med["top_node_call_wall_s"] / max(total, 1e-9),
        "record_calls_inclusive_fraction": med["record_call_wall_s"] / max(total, 1e-9),
        "record_calls_inside_nodes_fraction": med["record_call_wall_inside_node_s"] / max(total, 1e-9),
        "direct_record_fraction": med["record_call_wall_direct_s"] / max(total, 1e-9),
        "residual_fraction": med["residual_outside_session_topnodes_directrecords_s"] / max(total, 1e-9),
        "median_record_calls": statistics.median(int(row["record_calls"]) for row in samples),
        "median_record_cache_hits": statistics.median(int(row["record_cache_hits"]) for row in samples),
        "median_record_cache_misses": statistics.median(int(row["record_cache_misses"]) for row in samples),
        "median_node_calls": statistics.median(int(row["node_calls"]) for row in samples),
        "median_node_cache_hits": statistics.median(int(row["node_cache_hits"]) for row in samples),
        "median_node_cache_misses": statistics.median(int(row["node_cache_misses"]) for row in samples),
        "median_top_node_calls": statistics.median(int(row["top_node_calls"]) for row in samples),
        "physical_record_reads": physical_reads,
    })
    return {
        "engine": ENGINE,
        "status": "PASS",
        "evidence_class": "research-oracle-instrumented",
        "product_release_credit": False,
        "claim": "attribute promoted G04 one-pass verification wall time to session construction, record decode/cache calls, node reconstruction/cache calls, and residual file/tree work",
        "contract": {
            "suite": SUITE,
            "workload": TARGET,
            "historical_substrate_tree_sha256": historical_tree,
            "semantic_user_tree_sha256": semantic_user_tree,
            "content_graph_tree_sha256": graph_tree,
            "logical_bytes": logical_bytes,
            "accepted_v029_bytes": int(expected["accepted_v029_bytes"]),
            "v030_archive_bytes": int(pack["archive_bytes"]),
            "v030_selected": pack["build_stats"]["selected"],
            "repetitions": REPETITIONS,
            "fresh_process_per_sample": True,
            "same_archive_all_samples": True,
            "instrumentation_only": True,
            "product_code_changed": False,
            "release_thresholds_changed": False,
        },
        "comparison": comparison,
        "samples": samples,
    }


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/g04-stream-hotpath-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/g04-stream-hotpath.json"))
    args = parser.parse_args()
    if args.worker:
        if args.archive is None:
            parser.error("--worker requires --archive")
        raise SystemExit(_worker(args.archive))
    try:
        result = run(args.work_root)
    except BaseException as exc:
        _write(args.output, {
            "engine": ENGINE, "status": "HARNESS_FAILURE", "evidence_class": "research-oracle-instrumented",
            "product_release_credit": False,
            "error": {"type": type(exc).__name__, "message": str(exc), "traceback": traceback.format_exc(limit=32)},
        })
        raise
    _write(args.output, result)
    print(json.dumps(result["comparison"], indent=2), flush=True)


if __name__ == "__main__":
    main()
