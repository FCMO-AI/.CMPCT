from __future__ import annotations

"""Research-only attribution inside the promoted G04 streamed verifier.

The verification-layer oracle falsified the canonical wrapper as a dominant runtime owner: ~98.7% of canonical
strong verification remained inside POLICY.strong_verify on the ML G04 substrate. This follow-up keeps one exact
shipping archive fixed and distinguishes session-open/authenticated-metadata/preflight cost from full graph
streaming, while exposing physical-record read multiplicity against the archive's unique physical record count.

Zero release credit. No product bytes, policy, thresholds, caches, or semantics are changed.
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

ENGINE = "v030-g04-streamer-work-attribution-v1"
SUITE = "neutral_hostile_v1"
TARGET = "09_ml_artifacts"
REPETITIONS = 5
OPERATIONS = ("session_open", "policy_verify")


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


def _worker(archive: Path, operation: str) -> int:
    from experiments import entropygraph_v030_release_product as CANON

    started = time.perf_counter()
    if operation == "session_open":
        with CANON.C._revision25_profile_context():
            session = CANON.POLICY.R._G04Session(archive)
            try:
                payload = {
                    "record_count": len(session.offsets),
                    "node_count": len(session.nodes),
                    "file_count": len(session.meta["files"]),
                    "content_graph_tree_sha256": session.meta["tree_sha256"],
                    "physical_record_reads": session.physical_record_reads,
                }
            finally:
                session.close()
    elif operation == "policy_verify":
        with CANON.C._revision25_profile_context():
            result = dict(CANON.POLICY.strong_verify(archive))
        if not result.get("ok"):
            raise RuntimeError(f"policy verification failed: {result!r}")
        # Open after the measured interval only to obtain immutable archive topology for the denominator.
        with CANON.C._revision25_profile_context():
            session = CANON.POLICY.R._G04Session(archive)
            try:
                record_count = len(session.offsets)
                node_count = len(session.nodes)
                file_count = len(session.meta["files"])
            finally:
                session.close()
        payload = {
            "record_count": record_count,
            "node_count": node_count,
            "file_count": file_count,
            "content_graph_tree_sha256": result.get("tree_sha256"),
            "physical_record_reads": int(result.get("physical_record_reads", 0)),
            "logical_bytes": int(result.get("logical_bytes", 0)),
            "max_physical_record_bytes": int(result.get("max_physical_record_bytes", 0)),
            "max_logical_node_bytes": int(result.get("max_logical_node_bytes", 0)),
        }
    else:
        raise ValueError(operation)
    wall = time.perf_counter() - started
    payload.update({"operation": operation, "wall_s": wall})
    print(json.dumps(payload, separators=(",", ":")), flush=True)
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

    samples = {op: [] for op in OPERATIONS}
    for rep in range(REPETITIONS):
        order = OPERATIONS if rep % 2 == 0 else tuple(reversed(OPERATIONS))
        for op in order:
            row = _json_child([
                sys.executable, str(Path(__file__).resolve()), "--worker",
                "--archive", str(archive), "--operation", op,
            ])
            row["rep"] = rep
            samples[op].append(row)

    topology_keys = ("record_count", "node_count", "file_count", "content_graph_tree_sha256")
    reference = {key: samples["session_open"][0][key] for key in topology_keys}
    if int(reference["record_count"]) <= 0:
        raise RuntimeError("G04 topology exposes no physical records")
    for op in OPERATIONS:
        for row in samples[op]:
            for key in topology_keys:
                if row[key] != reference[key]:
                    raise RuntimeError(f"G04 topology drift op={op} key={key}: {row[key]!r} != {reference[key]!r}")
    for row in samples["session_open"]:
        if int(row["physical_record_reads"]) != 0:
            raise RuntimeError("opening a G04 session unexpectedly decoded a physical record")

    summaries = {
        op: {
            "median_wall_s": statistics.median(row["wall_s"] for row in values),
            "min_wall_s": min(row["wall_s"] for row in values),
            "max_wall_s": max(row["wall_s"] for row in values),
        }
        for op, values in samples.items()
    }
    open_wall = summaries["session_open"]["median_wall_s"]
    verify_wall = summaries["policy_verify"]["median_wall_s"]
    physical_reads = [int(row["physical_record_reads"]) for row in samples["policy_verify"]]
    median_reads = statistics.median(physical_reads)
    record_count = int(reference["record_count"])
    comparison = {
        "session_open_fraction_of_policy_verify": open_wall / max(verify_wall, 1e-9),
        "stream_after_open_fraction_of_policy_verify": (verify_wall - open_wall) / max(verify_wall, 1e-9),
        "policy_verify_minus_open_s": verify_wall - open_wall,
        "median_physical_record_reads": median_reads,
        "unique_physical_record_count": record_count,
        "physical_record_read_multiplicity": median_reads / max(1, record_count),
    }
    return {
        "engine": ENGINE,
        "status": "PASS",
        "evidence_class": "research-oracle",
        "product_release_credit": False,
        "claim": "attribute promoted G04 policy verification between session-open/preflight and graph streaming, and measure physical-record reread multiplicity",
        "contract": {
            "suite": SUITE,
            "workload": TARGET,
            "historical_substrate_tree_sha256": historical_tree,
            "semantic_user_tree_sha256": semantic_user_tree,
            "content_graph_tree_sha256": reference["content_graph_tree_sha256"],
            "accepted_v029_bytes": int(expected["accepted_v029_bytes"]),
            "v030_archive_bytes": int(pack["archive_bytes"]),
            "v030_selected": pack["build_stats"]["selected"],
            "record_count": record_count,
            "node_count": int(reference["node_count"]),
            "file_count": int(reference["file_count"]),
            "repetitions_per_operation": REPETITIONS,
            "fresh_process_per_sample": True,
            "same_archive_all_operations": True,
            "product_code_changed": False,
            "release_thresholds_changed": False,
        },
        "summaries": summaries,
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
    parser.add_argument("--operation", choices=OPERATIONS)
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/g04-streamer-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/g04-streamer-work.json"))
    args = parser.parse_args()
    if args.worker:
        if args.archive is None or args.operation is None:
            parser.error("--worker requires --archive and --operation")
        raise SystemExit(_worker(args.archive, args.operation))
    try:
        result = run(args.work_root)
    except BaseException as exc:
        _write(args.output, {
            "engine": ENGINE, "status": "HARNESS_FAILURE", "evidence_class": "research-oracle",
            "product_release_credit": False,
            "error": {"type": type(exc).__name__, "message": str(exc), "traceback": traceback.format_exc(limit=32)},
        })
        raise
    _write(args.output, result)
    print(json.dumps(result["comparison"], indent=2), flush=True)


if __name__ == "__main__":
    main()
