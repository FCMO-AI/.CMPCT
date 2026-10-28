from __future__ import annotations

"""Research-only attribution of the dominant G04 verification cost.

The extraction-cost oracle showed that canonical strong verification owns ~91% of ML full-extract wall time.
This follow-up keeps one exact shipping G04 archive fixed and compares, in fresh processes:

* policy_verify: the promoted streamed reader's authenticated graph verification;
* canonical_verify: the shipping canonical verification wrapper, which additionally validates the filesystem
  manifest and re-reads regular user members through the selected representation.

The experiment changes no product code, archive bytes, reader policy, release threshold, or admission rule and
receives zero release credit.  Its only purpose is to decide whether the next optimization belongs inside the
streamed graph verifier or in the canonical wrapper's additional verification pass.
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

ENGINE = "v030-g04-verify-layer-attribution-v1"
SUITE = "neutral_hostile_v1"
TARGET = "09_ml_artifacts"
REPETITIONS = 5
OPERATIONS = ("policy_verify", "canonical_verify")


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
    if operation == "policy_verify":
        # Use the exact promoted policy facade and canonical r25 profile binding, but stop before the canonical
        # wrapper's manifest/member re-read pass.  This isolates the authenticated graph streamer's cost.
        with CANON.C._revision25_profile_context():
            result = dict(CANON.POLICY.strong_verify(archive))
        if not result.get("ok"):
            raise RuntimeError(f"policy verification failed: {result!r}")
        graph_tree = result.get("tree_sha256")
        user_tree = None
    elif operation == "canonical_verify":
        result = dict(CANON.strong_verify(archive))
        if not result.get("ok"):
            raise RuntimeError(f"canonical verification failed: {result!r}")
        graph_tree = result.get("content_graph_tree_sha256")
        user_tree = result.get("user_tree_sha256") or result.get("tree_sha256")
    else:
        raise ValueError(operation)
    wall = time.perf_counter() - started
    print(
        json.dumps(
            {
                "operation": operation,
                "wall_s": wall,
                "logical_bytes": int(result.get("logical_bytes", 0)),
                "content_graph_tree_sha256": graph_tree,
                "user_tree_sha256": user_tree,
            },
            separators=(",", ":"),
        ),
        flush=True,
    )
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
    pack = _json_child(
        [
            sys.executable,
            str(PERF.WORKER),
            "--engine",
            "v030",
            "--op",
            "pack",
            "--source",
            str(source),
            "--archive",
            str(archive),
        ]
    )
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
            sample = _json_child(
                [
                    sys.executable,
                    str(Path(__file__).resolve()),
                    "--worker",
                    "--archive",
                    str(archive),
                    "--operation",
                    op,
                ]
            )
            sample["rep"] = rep
            samples[op].append(sample)

    graph_tree = samples["policy_verify"][0]["content_graph_tree_sha256"]
    logical_bytes = int(samples["policy_verify"][0]["logical_bytes"])
    if not graph_tree or logical_bytes <= 0:
        raise RuntimeError("policy verification did not expose authenticated graph identity")
    for sample in samples["policy_verify"]:
        if sample.get("content_graph_tree_sha256") != graph_tree or int(sample["logical_bytes"]) != logical_bytes:
            raise RuntimeError("policy verification identity drift across repetitions")
    for sample in samples["canonical_verify"]:
        if sample.get("content_graph_tree_sha256") != graph_tree or int(sample["logical_bytes"]) != logical_bytes:
            raise RuntimeError("canonical verification content-graph identity drift")
        if sample.get("user_tree_sha256") != semantic_user_tree:
            raise RuntimeError("canonical verification semantic-user-tree drift")

    summaries = {
        op: {
            "median_wall_s": statistics.median(row["wall_s"] for row in values),
            "min_wall_s": min(row["wall_s"] for row in values),
            "max_wall_s": max(row["wall_s"] for row in values),
        }
        for op, values in samples.items()
    }
    policy = summaries["policy_verify"]["median_wall_s"]
    canonical = summaries["canonical_verify"]["median_wall_s"]
    comparison = {
        "canonical_minus_policy_s": canonical - policy,
        "canonical_over_policy_ratio": canonical / max(policy, 1e-9),
        "policy_fraction_of_canonical": policy / max(canonical, 1e-9),
        "canonical_wrapper_fraction_of_canonical": (canonical - policy) / max(canonical, 1e-9),
    }
    return {
        "engine": ENGINE,
        "status": "PASS",
        "evidence_class": "research-oracle",
        "product_release_credit": False,
        "claim": "attribute G04 canonical strong-verify wall time between streamed graph verification and canonical manifest/member verification",
        "contract": {
            "suite": SUITE,
            "workload": TARGET,
            "historical_substrate_tree_sha256": historical_tree,
            "semantic_user_tree_sha256": semantic_user_tree,
            "content_graph_tree_sha256": graph_tree,
            "content_graph_logical_bytes": logical_bytes,
            "accepted_v029_bytes": int(expected["accepted_v029_bytes"]),
            "v030_archive_bytes": int(pack["archive_bytes"]),
            "v030_selected": pack["build_stats"]["selected"],
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
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/g04-verify-layer-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/g04-verify-layer.json"))
    args = parser.parse_args()

    if args.worker:
        if args.archive is None or args.operation is None:
            parser.error("--worker requires --archive and --operation")
        raise SystemExit(_worker(args.archive, args.operation))

    try:
        result = run(args.work_root)
    except BaseException as exc:
        _write(
            args.output,
            {
                "engine": ENGINE,
                "status": "HARNESS_FAILURE",
                "evidence_class": "research-oracle",
                "product_release_credit": False,
                "error": {
                    "type": type(exc).__name__,
                    "message": str(exc),
                    "traceback": traceback.format_exc(limit=32),
                },
            },
        )
        raise

    _write(args.output, result)
    print(json.dumps(result["comparison"], indent=2), flush=True)


if __name__ == "__main__":
    main()
